"""
analyser.py
===========
Phase 2 of the BetLab pipeline: Analysis & Filtering.

For each parsed bet:
  1. Look up sport-specific source accuracy (or calibrated market prior)
  2. Calculate Implied Probability and EV
  3. Filter out bets below the min EV threshold
  4. Tag bets: ALL passing bets = SINGLE_CANDIDATE
                top N by EV    = also PARLAY_CANDIDATE

Calibration (Phase 2 upgrade):
  - Market-specific priors replace the single sport-level accuracy.
  - If settled results are provided and sample >= min_sample_size,
    a time-decayed win rate is blended with the prior.
  - Each bet output carries prob_source and prob_sample_count metadata.
"""

from __future__ import annotations
import logging
import math
from datetime import date
from typing import Any, Optional

import pandas as pd

from collections import defaultdict

from src.math_engine import get_implied_probability, calculate_ev
from src.parser import BetInput, normalize_market_type

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Market-family mapping (mirrors parlay_builder._market_family)
# ---------------------------------------------------------------------------

def _market_to_prior_key(market_type: str) -> str:
    """Map a raw market label to the canonical prior key used in config."""
    raw = market_type.lower().strip()
    if any(x in raw for x in ["1x2", "money line", "moneyline", "ml"]):
        return "moneyline"
    if any(x in raw for x in ["btts", "both teams"]):
        return "btts"
    if any(x in raw for x in ["over", "under", "o/u", "total"]):
        return "totals"
    if any(x in raw for x in ["asian", "handicap", "ah"]):
        return "handicap"
    if raw == "freeform":
        return "freeform"
    return "default"


def get_market_prior(market_type: str, market_priors: dict) -> float:
    """Return the configured prior probability for a market family."""
    key = _market_to_prior_key(market_type)
    return float(market_priors.get(key, market_priors.get("default", 0.53)))


# ---------------------------------------------------------------------------
# Time-decay calibration
# ---------------------------------------------------------------------------

def _time_decay_weight(result_date: date, today: date, halflife_days: int) -> float:
    """Exponential decay: weight = 0.5^(days_ago / halflife)."""
    days_ago = max(0, (today - result_date).days)
    return math.pow(0.5, days_ago / max(1, halflife_days))


def compute_calibrated_probability(
    market_type: str,
    sport: str,
    accuracy_map: dict,
    market_priors: Optional[dict],
    results_df: Optional[pd.DataFrame],
    calibration_cfg: Optional[dict],
) -> dict[str, Any]:
    """
    Compute the true probability to use for EV analysis.

    Priority:
      1. If market_priors provided: use market-specific prior as base.
      2. Else: fall back to sport-level accuracy_map.
      3. If results_df has enough samples: blend time-decayed win rate with prior.

    Returns dict with:
      - true_probability (float)
      - prob_source ('prior' | 'calibrated' | 'sport')
      - prob_sample_count (int, effective decayed sample weight rounded)
    """
    # Base prior
    if market_priors:
        prior = get_market_prior(market_type, market_priors)
        base_source = "prior"
    else:
        prior = float(accuracy_map.get(sport.lower(), accuracy_map.get("default", 0.53)))
        base_source = "sport"

    # No calibration config or no results → use prior only
    if not calibration_cfg or results_df is None or results_df.empty:
        return {
            "true_probability": round(prior, 4),
            "prob_source": base_source,
            "prob_sample_count": 0,
        }

    min_sample = int(calibration_cfg.get("min_sample_size", 10))
    halflife = int(calibration_cfg.get("time_decay_halflife_days", 30))
    smoothing = float(calibration_cfg.get("smoothing_weight", 0.30))

    # Filter to completed WIN/LOSS rows only
    try:
        completed = results_df[
            results_df["result"].str.upper().isin(["WIN", "LOSS"])
        ].copy()
    except (KeyError, AttributeError):
        return {"true_probability": round(prior, 4), "prob_source": base_source, "prob_sample_count": 0}

    if completed.empty:
        return {"true_probability": round(prior, 4), "prob_source": base_source, "prob_sample_count": 0}

    # Parse dates; drop rows with unparseable dates
    try:
        completed["_date"] = pd.to_datetime(completed["date"], errors="coerce").dt.date
        completed = completed.dropna(subset=["_date"])
    except KeyError:
        return {"true_probability": round(prior, 4), "prob_source": base_source, "prob_sample_count": 0}

    today = date.today()
    weights = completed["_date"].apply(lambda d: _time_decay_weight(d, today, halflife))
    wins = (completed["result"].str.upper() == "WIN").astype(float)

    total_weight = weights.sum()
    if total_weight < min_sample:
        return {
            "true_probability": round(prior, 4),
            "prob_source": base_source,
            "prob_sample_count": int(total_weight),
        }

    decayed_win_rate = (wins * weights).sum() / total_weight
    blended = smoothing * prior + (1.0 - smoothing) * decayed_win_rate
    blended = max(0.01, min(0.99, blended))

    return {
        "true_probability": round(blended, 4),
        "prob_source": "calibrated",
        "prob_sample_count": round(int(total_weight)),
    }


# ---------------------------------------------------------------------------
# Phase 4: Deduplication and conflict detection
# ---------------------------------------------------------------------------

def dedupe_bets(bets: list[BetInput]) -> tuple[list[BetInput], list[dict]]:
    """
    Remove duplicate picks, keeping the copy with better decimal odds.

    Two bets are considered duplicates when they share the same
    (canonical_match, canonical_market, canonical_selection) key.
    Market aliases (e.g. 'Money Line' == '1X2') are resolved before comparison.

    Returns (deduped_bets, dropped_records).
    """
    seen: dict[str, BetInput] = {}
    dropped: list[dict] = []

    for bet in bets:
        market_norm = normalize_market_type(bet.market_type).lower()
        key = (
            f"{bet.match_name.lower().strip()}"
            f"::{market_norm}"
            f"::{bet.selection.lower().strip()}"
        )
        if key not in seen:
            seen[key] = bet
        else:
            existing = seen[key]
            if bet.decimal_odds > existing.decimal_odds:
                dropped.append({
                    "match_name": existing.match_name,
                    "selection": existing.selection,
                    "reason": (
                        f"duplicate: replaced by better odds "
                        f"{bet.decimal_odds} > {existing.decimal_odds}"
                    ),
                })
                seen[key] = bet
            else:
                dropped.append({
                    "match_name": bet.match_name,
                    "selection": bet.selection,
                    "reason": (
                        f"duplicate: existing odds "
                        f"{existing.decimal_odds} >= {bet.decimal_odds}"
                    ),
                })

    return list(seen.values()), dropped


def _conflict_direction(market_type: str, selection: str) -> tuple[str, str] | None:
    """
    Return (family, direction) used to identify opposing bet pairs.
    Returns None if this market has no conflict semantics here.
    """
    family = _market_to_prior_key(market_type)
    sel = selection.lower().strip()

    if family == "moneyline":
        return (family, sel)

    if family == "btts":
        direction = "yes" if "yes" in sel else ("no" if "no" in sel else sel)
        return (family, direction)

    if family == "totals":
        if sel.startswith("over"):
            return (family, "over")
        if sel.startswith("under"):
            return (family, "under")
        return None

    return None


def filter_conflicts(results: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Remove logically conflicting picks from the same match.

    When two qualifying bets oppose each other (e.g. Home Win vs Away Win,
    Over 2.5 vs Under 2.5, BTTS Yes vs No), the lower-EV bet is dropped.

    Returns (clean_results, dropped_results).
    """
    # Group by (match_key, market_family)
    groups: dict[tuple, list[tuple[int, dict]]] = defaultdict(list)
    for i, r in enumerate(results):
        match_key = r["match_name"].lower().strip()
        family = _market_to_prior_key(r["market_type"])
        groups[(match_key, family)].append((i, r))

    dropped_indices: set[int] = set()
    dropped: list[dict] = []

    for group in groups.values():
        if len(group) < 2:
            continue

        for idx_a in range(len(group)):
            for idx_b in range(idx_a + 1, len(group)):
                i_a, r_a = group[idx_a]
                i_b, r_b = group[idx_b]

                if i_a in dropped_indices or i_b in dropped_indices:
                    continue

                dir_a = _conflict_direction(r_a["market_type"], r_a["selection"])
                dir_b = _conflict_direction(r_b["market_type"], r_b["selection"])

                if dir_a is None or dir_b is None:
                    continue

                fam_a, d_a = dir_a
                fam_b, d_b = dir_b

                # Same family, different direction → opposing outcomes
                if fam_a == fam_b and d_a != d_b:
                    if r_a["ev"] >= r_b["ev"]:
                        dropped_indices.add(i_b)
                        dropped.append({**r_b, "conflict_with": r_a["selection"]})
                        logger.info(
                            "Conflict: dropped '%s' (EV %.4f) — conflicts with '%s' (EV %.4f) in '%s'.",
                            r_b["selection"], r_b["ev"],
                            r_a["selection"], r_a["ev"],
                            r_b["match_name"],
                        )
                    else:
                        dropped_indices.add(i_a)
                        dropped.append({**r_a, "conflict_with": r_b["selection"]})
                        logger.info(
                            "Conflict: dropped '%s' (EV %.4f) — conflicts with '%s' (EV %.4f) in '%s'.",
                            r_a["selection"], r_a["ev"],
                            r_b["selection"], r_b["ev"],
                            r_a["match_name"],
                        )

    clean = [r for i, r in enumerate(results) if i not in dropped_indices]
    return clean, dropped


# ---------------------------------------------------------------------------
# Phase 5: EV Robustness Quality Gates
# ---------------------------------------------------------------------------

def ev_robustness_label(
    bet: dict,
    robustness_cfg: dict,
    min_ev_threshold: float,
    min_sample: int,
) -> str:
    """
    Assign a quality label to a bet based on EV margin and probability source.

    Labels:
      'robust'   — calibrated from live data with sufficient sample AND EV above margin.
      'marginal' — EV above margin but using prior only (no live calibration).
      'thin'     — EV barely above threshold (within margin_pct); treat with caution.

    When gate is disabled (enabled: false), always returns 'marginal' so existing
    behaviour is unchanged.
    """
    if not robustness_cfg.get("enabled", False):
        return "marginal"

    margin = float(robustness_cfg.get("margin_pct", 0.02))
    ev_robust_threshold = min_ev_threshold + margin

    if bet["ev"] < ev_robust_threshold:
        return "thin"

    if bet["prob_source"] == "calibrated" and bet["prob_sample_count"] >= min_sample:
        return "robust"

    return "marginal"


def apply_robustness_gate(
    results: list[dict],
    parlay_pool_size: int,
    robustness_cfg: Optional[dict],
    min_ev_threshold: float,
    min_sample: int,
) -> list[dict]:
    """
    Tag bets as PARLAY_CANDIDATE, respecting the robustness gate.

    When gate is enabled, bets labelled 'thin' are kept as SINGLE_CANDIDATE only.
    Results must already be sorted by EV descending and have ev_label set.

    When gate is disabled (robustness_cfg is None or enabled: false), behaves
    identically to the original top-N tagging loop.
    """
    gate_enabled = bool(robustness_cfg and robustness_cfg.get("enabled", False))
    parlay_count = 0

    for bet in results:
        if gate_enabled and bet.get("ev_label") == "thin":
            bet["tag"] = "SINGLE_CANDIDATE"
            continue
        if parlay_count < parlay_pool_size:
            bet["tag"] = "PARLAY_CANDIDATE"
            parlay_count += 1
        else:
            bet["tag"] = "SINGLE_CANDIDATE"

    return results


def is_no_bet_day(results: list[dict]) -> bool:
    """
    Return True when there are no actionable recommendations.

    Triggers when the results list is empty or every bet is labelled 'thin'.
    Use this to suppress output or show a no-bet warning in the UI.
    """
    if not results:
        return True
    return all(b.get("ev_label") == "thin" for b in results)


# ---------------------------------------------------------------------------
# Legacy helper (kept for backward-compat in tests)
# ---------------------------------------------------------------------------

def get_true_probability(sport: str, accuracy_map: dict) -> float:
    """
    Return the source accuracy (true probability) for a given sport.
    Falls back to 'default' if sport not found in config.
    """
    sport_key = sport.lower()
    return accuracy_map.get(sport_key, accuracy_map.get("default", 0.53))


# ---------------------------------------------------------------------------
# Main analysis pass
# ---------------------------------------------------------------------------

def analyse_bets(
    bets: list[BetInput],
    accuracy_map: dict,
    min_ev_threshold: float,
    parlay_pool_size: int,
    market_priors: Optional[dict] = None,
    results_df: Optional[pd.DataFrame] = None,
    calibration_cfg: Optional[dict] = None,
    robustness_cfg: Optional[dict] = None,
) -> list[dict[str, Any]]:
    """
    Run EV analysis on all parsed bets.

    Returns a list of qualifying bet dicts, enriched with:
      - true_probability
      - implied_probability
      - ev
      - tag (SINGLE_CANDIDATE / PARLAY_CANDIDATE)
      - prob_source ('prior' | 'calibrated' | 'sport')
      - prob_sample_count (int)

    Bets below min_ev_threshold are excluded entirely.
    Top `parlay_pool_size` bets by EV are dual-tagged as PARLAY_CANDIDATE.
    """
    # Phase 4: Deduplicate inputs before EV analysis
    bets, dup_dropped = dedupe_bets(bets)
    if dup_dropped:
        logger.info("Dedupe: dropped %d duplicate pick(s).", len(dup_dropped))

    results = []

    for bet in bets:
        cal = compute_calibrated_probability(
            market_type=bet.market_type,
            sport=bet.sport,
            accuracy_map=accuracy_map,
            market_priors=market_priors,
            results_df=results_df,
            calibration_cfg=calibration_cfg,
        )
        true_prob = cal["true_probability"]
        implied_prob = get_implied_probability(bet.decimal_odds)

        try:
            ev = calculate_ev(bet.decimal_odds, true_prob)
        except ValueError as e:
            logger.warning("EV calculation failed for '%s': %s", bet.selection, e)
            continue

        if ev < min_ev_threshold:
            logger.info(
                "FILTERED OUT: '%s @ %.2f' — EV %.4f below threshold %.4f",
                bet.selection, bet.decimal_odds, ev, min_ev_threshold
            )
            continue

        results.append({
            "match_name": bet.match_name,
            "market_type": bet.market_type,
            "selection": bet.selection,
            "decimal_odds": bet.decimal_odds,
            "confidence": bet.confidence,
            "sport": bet.sport,
            "true_probability": true_prob,
            "implied_probability": round(implied_prob, 4),
            "ev": round(ev, 6),
            "tag": "SINGLE_CANDIDATE",
            "prob_source": cal["prob_source"],
            "prob_sample_count": cal["prob_sample_count"],
        })

    # Phase 4: Filter conflicting picks (keep higher-EV side)
    results, conf_dropped = filter_conflicts(results)
    if conf_dropped:
        logger.info("Conflict filter: dropped %d conflicting pick(s).", len(conf_dropped))

    # Sort descending by EV for parlay tagging
    results.sort(key=lambda x: x["ev"], reverse=True)

    # Phase 5: Assign EV robustness label to each bet
    min_sample = int((calibration_cfg or {}).get("min_sample_size", 10))
    ev_rob_cfg = robustness_cfg or {}
    for bet in results:
        bet["ev_label"] = ev_robustness_label(bet, ev_rob_cfg, min_ev_threshold, min_sample)

    # Phase 5: Tag parlay candidates, respecting robustness gate
    results = apply_robustness_gate(results, parlay_pool_size, robustness_cfg, min_ev_threshold, min_sample)

    logger.info(
        "%d bets passed EV filter. %d tagged as PARLAY_CANDIDATE.",
        len(results),
        min(len(results), parlay_pool_size),
    )
    return results
