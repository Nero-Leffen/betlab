"""
bankroll_mgr.py
===============
Bankroll management logic for BetLab.

Responsibilities:
  - Load current bankroll state
  - Assign stakes using Half-Kelly (clamped to unit boundaries)
  - Enforce daily cap (200 INR / 4 units)
  - Enforce stop-loss threshold (250 INR)
  - Tiebreak by confidence when cap is hit
  - Detect losing streaks in rolling 7-day window
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml

from src.math_engine import kelly_stake_inr, calculate_ev, get_implied_probability

logger = logging.getLogger(__name__)

CONFIDENCE_ORDER = {"high": 3, "medium": 2, "low": 1}


@dataclass
class BankrollConfig:
    total_inr: float
    unit_inr: float
    max_daily_stake_inr: float
    stop_loss_inr: float
    losing_streak_window_days: int
    losing_streak_threshold: int
    reduced_unit_multiplier: float
    confidence_stake_map: dict  # {'high': 2, 'medium': 1, 'low': 1}


@dataclass
class SizedBet:
    """A bet that has passed EV filtering and has an assigned stake."""
    match_name: str
    market_type: str
    selection: str
    decimal_odds: float
    confidence: str
    sport: str
    ev: float
    implied_probability: float
    true_probability: float
    kelly_fraction: float
    stake_inr: float
    tag: str = "SINGLE_CANDIDATE"      # or PARLAY_CANDIDATE (set later)
    bet_id: str = ""


@dataclass
class BankrollSession:
    """Output of the bankroll manager for one analysis cycle."""
    sized_bets: list[SizedBet] = field(default_factory=list)
    total_stake_inr: float = 0.0
    bankroll_inr: float = 500.0
    stop_loss_triggered: bool = False
    streak_warning: bool = False
    streak_count: int = 0
    effective_unit_inr: float = 25.0
    cap_hit: bool = False


def load_config(config_path: str | Path = "config/settings.yaml") -> BankrollConfig:
    """Load bankroll settings from YAML config file."""
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    br = cfg["bankroll"]
    risk = cfg["risk"]
    conf_map = cfg.get("confidence_stake_map", {"high": 2, "medium": 1, "low": 1})

    return BankrollConfig(
        total_inr=br["total_inr"],
        unit_inr=br["unit_inr"],
        max_daily_stake_inr=br["max_daily_stake_inr"],
        stop_loss_inr=br["stop_loss_inr"],
        losing_streak_window_days=risk["losing_streak_window_days"],
        losing_streak_threshold=risk["losing_streak_threshold"],
        reduced_unit_multiplier=risk["reduced_unit_multiplier"],
        confidence_stake_map=conf_map,
    )


def get_current_bankroll(results_path: str | Path = "data/results.csv") -> float:
    """
    Calculate current bankroll from results history.
    Starts at 500 INR and applies all historical P&L.
    Returns 500.0 if no results file exists yet.
    """
    results_path = Path(results_path)
    if not results_path.exists():
        return 500.0

    try:
        df = pd.read_csv(results_path)
        if "pnl_inr" not in df.columns:
            return 500.0
        total_pnl = df["pnl_inr"].fillna(0).sum()
        return round(500.0 + total_pnl, 2)
    except Exception as e:
        logger.warning("Could not read results.csv: %s", e)
        return 500.0


def check_losing_streak(
    results_path: str | Path,
    window_days: int,
    threshold: int,
) -> tuple[bool, int]:
    """
    Check for losing streak in the past `window_days` days.

    Returns (streak_warning: bool, streak_count: int)
    """
    results_path = Path(results_path)
    if not results_path.exists():
        return False, 0

    try:
        df = pd.read_csv(results_path)
        if "date" not in df.columns or "result" not in df.columns:
            return False, 0

        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        cutoff = pd.Timestamp(date.today() - timedelta(days=window_days))
        recent = df[df["date"] >= cutoff]

        losses = recent[recent["result"].str.upper() == "LOSS"]
        count = len(losses)
        return count >= threshold, count
    except Exception as e:
        logger.warning("Streak check failed: %s", e)
        return False, 0


def assign_stake(
    decimal_odds: float,
    true_probability: float,
    confidence: str,
    bankroll_inr: float,
    unit_inr: float,
    config: BankrollConfig,
) -> tuple[float, float]:
    """
    Determine stake using Half-Kelly, clamped to confidence-based unit limits.

    Returns (stake_inr, kelly_fraction)
    """
    max_units = config.confidence_stake_map.get(confidence.lower(), 1)
    min_units = 1

    stake = kelly_stake_inr(
        decimal_odds=decimal_odds,
        true_probability=true_probability,
        bankroll_inr=bankroll_inr,
        unit_inr=unit_inr,
        min_units=min_units,
        max_units=max_units,
    )

    from src.math_engine import kelly_criterion
    fraction = kelly_criterion(decimal_odds, true_probability)
    return stake, fraction


def run_bankroll_session(
    filtered_bets: list,          # list of dicts with keys from analyser
    config: BankrollConfig,
    results_path: str | Path = "data/results.csv",
) -> BankrollSession:
    """
    Core bankroll session:
      1. Check stop-loss
      2. Check streak warning (apply reduced unit if triggered)
      3. Assign Half-Kelly stakes to each bet
      4. Sort by EV desc, tiebreak by confidence
      5. Enforce daily cap (200 INR), drop lowest-priority bets if needed

    Returns a BankrollSession with fully sized bets.
    """
    session = BankrollSession()
    session.bankroll_inr = get_current_bankroll(results_path)
    session.effective_unit_inr = config.unit_inr

    # --- Stop-loss check ---
    if session.bankroll_inr <= config.stop_loss_inr:
        session.stop_loss_triggered = True
        logger.warning(
            "STOP-LOSS TRIGGERED. Bankroll %.2f INR ≤ %.2f INR threshold.",
            session.bankroll_inr, config.stop_loss_inr
        )
        return session

    # --- Streak check ---
    streak_warning, streak_count = check_losing_streak(
        results_path,
        config.losing_streak_window_days,
        config.losing_streak_threshold,
    )
    session.streak_warning = streak_warning
    session.streak_count = streak_count

    if streak_warning:
        session.effective_unit_inr = round(
            config.unit_inr * config.reduced_unit_multiplier, 2
        )
        logger.warning(
            "Losing streak detected (%d losses in %d days). Unit reduced to %.2f INR.",
            streak_count, config.losing_streak_window_days, session.effective_unit_inr
        )

    unit = session.effective_unit_inr

    # --- Size each bet ---
    sized = []
    for i, b in enumerate(filtered_bets, start=1):
        stake, fraction = assign_stake(
            decimal_odds=b["decimal_odds"],
            true_probability=b["true_probability"],
            confidence=b["confidence"],
            bankroll_inr=session.bankroll_inr,
            unit_inr=unit,
            config=config,
        )
        sized.append(SizedBet(
            match_name=b["match_name"],
            market_type=b["market_type"],
            selection=b["selection"],
            decimal_odds=b["decimal_odds"],
            confidence=b["confidence"],
            sport=b["sport"],
            ev=b["ev"],
            implied_probability=b["implied_probability"],
            true_probability=b["true_probability"],
            kelly_fraction=fraction,
            stake_inr=stake,
            tag=b.get("tag", "SINGLE_CANDIDATE"),
            bet_id=f"BL-{date.today().strftime('%Y%m%d')}-{i:03d}",
        ))

    # --- Sort: EV desc, then confidence desc as tiebreaker ---
    sized.sort(
        key=lambda x: (x.ev, CONFIDENCE_ORDER.get(x.confidence.lower(), 0)),
        reverse=True,
    )

    # --- Enforce daily cap ---
    selected = []
    running_total = 0.0
    cap = config.max_daily_stake_inr

    for bet in sized:
        if running_total + bet.stake_inr <= cap:
            selected.append(bet)
            running_total += bet.stake_inr
        else:
            session.cap_hit = True
            logger.info(
                "Cap hit: dropped '%s' (stake %.0f would exceed %.0f limit).",
                bet.selection, bet.stake_inr, cap
            )

    session.sized_bets = selected
    session.total_stake_inr = running_total
    return session
