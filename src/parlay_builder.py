"""
parlay_builder.py
=================
Phase 4 of the BetLab pipeline: Parlay Construction.

Rules (per spec):
  - Only PARLAY_CANDIDATE bets are eligible
  - Max legs per parlay: configurable (default 4)
  - Max parlay options generated: 2
  - Correlation rejection:
      ❌ Two legs from the same match
      ❌ Two legs involving the same team
  - Calculates combined odds and hit probability for each parlay
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from itertools import combinations
import re

from src.math_engine import (
    parlay_combined_odds,
    parlay_hit_probability,
    apply_correlation_penalty,
)
from src.bankroll_mgr import SizedBet

logger = logging.getLogger(__name__)


DEFAULT_CORRELATION_SETTINGS = {
    "enabled": True,
    "min_factor": 0.85,
    "same_market_weight": 0.10,
    "shared_token_weight": 0.10,
    "shared_sport_weight": 0.00,
}


@dataclass
class ParlayOption:
    """Represents a constructed parlay bet."""
    legs: list[SizedBet]
    combined_odds: float
    base_hit_probability: float
    hit_probability: float
    penalty_factor: float
    stake_inr: float
    parlay_ev: float
    parlay_id: str = ""

    @property
    def leg_count(self) -> int:
        return len(self.legs)

    @property
    def leg_summary(self) -> str:
        return " + ".join(
            f"{b.selection} ({b.decimal_odds:.2f})" for b in self.legs
        )


def _extract_teams(match_name: str, selection: str) -> set[str]:
    """
    Extract team names from a football match entry.

    Tries to split on 'vs', 'v', '-' to get home/away teams.
    Also includes the selection text itself for same-team detection.
    """
    teams = set()
    for sep in [" vs ", " v ", " - "]:
        if sep in match_name.lower():
            parts = match_name.lower().split(sep)
            teams.update(p.strip() for p in parts)
            break
    # Also include words in selection (e.g. "Man City Win" → "man city")
    teams.add(selection.lower().strip())
    return teams


def _market_family(market_type: str) -> str:
    """Map market labels into broad families for lightweight correlation scoring."""
    raw = market_type.lower().strip()
    if any(x in raw for x in ["1x2", "money line", "moneyline", "ml"]):
        return "moneyline"
    if any(x in raw for x in ["btts", "both teams"]):
        return "btts"
    if any(x in raw for x in ["over", "under", "o/u", "total"]):
        return "totals"
    if any(x in raw for x in ["asian", "handicap", "ah"]):
        return "handicap"
    return raw or "unknown"


def _tokenize(text: str) -> set[str]:
    return {
        t for t in re.findall(r"[a-zA-Z]{3,}", text.lower())
        if t not in {"over", "under", "line", "total", "teams", "both"}
    }


def _pair_soft_penalty(bet_a: SizedBet, bet_b: SizedBet, settings: dict) -> float:
    """Return a 0..1 soft-correlation penalty score for one pair of legs."""
    penalty = 0.0

    if _market_family(bet_a.market_type) == _market_family(bet_b.market_type):
        penalty += float(settings.get("same_market_weight", 0.0))

    tokens_a = _tokenize(f"{bet_a.match_name} {bet_a.selection}")
    tokens_b = _tokenize(f"{bet_b.match_name} {bet_b.selection}")
    union = tokens_a | tokens_b
    if union:
        overlap_ratio = len(tokens_a & tokens_b) / len(union)
        penalty += overlap_ratio * float(settings.get("shared_token_weight", 0.0))

    if bet_a.sport.lower().strip() == bet_b.sport.lower().strip():
        penalty += float(settings.get("shared_sport_weight", 0.0))

    return max(0.0, min(1.0, penalty))


def _resolve_correlation_settings(correlation_settings: dict | None) -> dict:
    settings = dict(DEFAULT_CORRELATION_SETTINGS)
    if correlation_settings:
        settings.update(correlation_settings)
    return settings


def _parlay_penalty_factor(legs: list[SizedBet], settings: dict) -> float:
    if not settings.get("enabled", True) or len(legs) < 2:
        return 1.0

    pair_penalties: list[float] = []
    for a, b in combinations(legs, 2):
        pair_penalties.append(_pair_soft_penalty(a, b, settings))

    if not pair_penalties:
        return 1.0

    avg_penalty = sum(pair_penalties) / len(pair_penalties)
    min_factor = float(settings.get("min_factor", 0.85))
    min_factor = max(0.0, min(1.0, min_factor))

    return round(max(min_factor, 1.0 - avg_penalty), 6)


def _is_correlated(bet_a: SizedBet, bet_b: SizedBet) -> bool:
    """
    Return True if two bets should NOT be combined:
      1. Same match (exact match name comparison, case-insensitive)
      2. Same team involved in both legs
    """
    # Rule 1: Same match
    if bet_a.match_name.lower().strip() == bet_b.match_name.lower().strip():
        logger.debug(
            "Correlation rejected (same match): '%s' + '%s'",
            bet_a.selection, bet_b.selection
        )
        return True

    # Rule 2: Team overlap
    teams_a = _extract_teams(bet_a.match_name, bet_a.selection)
    teams_b = _extract_teams(bet_b.match_name, bet_b.selection)
    overlap = teams_a & teams_b

    if overlap:
        logger.debug(
            "Correlation rejected (team overlap: %s): '%s' + '%s'",
            overlap, bet_a.selection, bet_b.selection
        )
        return True

    return False


def _validate_parlay_legs(legs: list[SizedBet]) -> bool:
    """Check all pairwise combinations of legs for correlation."""
    for a, b in combinations(legs, 2):
        if _is_correlated(a, b):
            return False
    return True


def build_parlays(
    sized_bets: list[SizedBet],
    parlay_stake_inr: float,
    max_legs: int = 4,
    max_options: int = 2,
    correlation_settings: dict | None = None,
) -> list[ParlayOption]:
    """
    Build up to `max_options` parlay combinations from PARLAY_CANDIDATE bets.

    Strategy:
      - Filter to PARLAY_CANDIDATE bets only
      - Try combinations from largest (max_legs) to smallest (2 legs)
      - Reject any combination with correlated legs
      - Return top `max_options` by combined EV

    parlay_stake_inr: fixed stake per parlay (1 unit = 25 INR)
    """
    settings = _resolve_correlation_settings(correlation_settings)
    candidates = [b for b in sized_bets if b.tag == "PARLAY_CANDIDATE"]

    if len(candidates) < 2:
        logger.info("Not enough PARLAY_CANDIDATE bets to build a parlay (need ≥ 2).")
        return []

    valid_parlays: list[ParlayOption] = []

    # Try combos from max_legs down to 2
    for n_legs in range(min(max_legs, len(candidates)), 1, -1):
        for combo in combinations(candidates, n_legs):
            legs = list(combo)

            if not _validate_parlay_legs(legs):
                continue

            odds_list = [b.decimal_odds for b in legs]
            prob_list = [b.true_probability for b in legs]

            combined_odds = parlay_combined_odds(odds_list)
            base_hit_prob = parlay_hit_probability(prob_list)
            penalty_factor = _parlay_penalty_factor(legs, settings)
            hit_prob = apply_correlation_penalty(base_hit_prob, penalty_factor)

            # EV of the parlay itself
            parlay_ev = round((combined_odds * hit_prob) - 1.0, 6)

            valid_parlays.append(ParlayOption(
                legs=legs,
                combined_odds=combined_odds,
                base_hit_probability=base_hit_prob,
                hit_probability=hit_prob,
                penalty_factor=penalty_factor,
                stake_inr=parlay_stake_inr,
                parlay_ev=parlay_ev,
            ))

    if not valid_parlays:
        logger.info("No valid (non-correlated) parlays could be constructed.")
        return []

    # Sort by EV descending, return top N
    valid_parlays.sort(key=lambda p: p.parlay_ev, reverse=True)
    top_parlays = valid_parlays[:max_options]

    # Assign IDs
    for i, p in enumerate(top_parlays, start=1):
        p.parlay_id = f"PARLAY-{i}"

    logger.info("Built %d parlay option(s).", len(top_parlays))
    return top_parlays
