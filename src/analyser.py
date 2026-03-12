"""
analyser.py
===========
Phase 2 of the BetLab pipeline: Analysis & Filtering.

For each parsed bet:
  1. Look up sport-specific source accuracy
  2. Calculate Implied Probability and EV
  3. Filter out bets below the min EV threshold
  4. Tag bets: ALL passing bets = SINGLE_CANDIDATE
                top N by EV    = also PARLAY_CANDIDATE
"""

from __future__ import annotations
import logging
from typing import Any

from src.math_engine import get_implied_probability, calculate_ev
from src.parser import BetInput

logger = logging.getLogger(__name__)


def get_true_probability(sport: str, accuracy_map: dict) -> float:
    """
    Return the source accuracy (true probability) for a given sport.
    Falls back to 'default' if sport not found in config.
    """
    sport_key = sport.lower()
    return accuracy_map.get(sport_key, accuracy_map.get("default", 0.53))


def analyse_bets(
    bets: list[BetInput],
    accuracy_map: dict,
    min_ev_threshold: float,
    parlay_pool_size: int,
) -> list[dict[str, Any]]:
    """
    Run EV analysis on all parsed bets.

    Returns a list of qualifying bet dicts, enriched with:
      - true_probability
      - implied_probability
      - ev
      - tag (SINGLE_CANDIDATE / PARLAY_CANDIDATE)

    Bets below min_ev_threshold are excluded entirely.
    Top `parlay_pool_size` bets by EV are dual-tagged as PARLAY_CANDIDATE.
    """
    results = []

    for bet in bets:
        true_prob = get_true_probability(bet.sport, accuracy_map)
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
            "true_probability": round(true_prob, 4),
            "implied_probability": round(implied_prob, 4),
            "ev": round(ev, 6),
            "tag": "SINGLE_CANDIDATE",   # default; parlay tag added below
        })

    # Sort descending by EV for parlay tagging
    results.sort(key=lambda x: x["ev"], reverse=True)

    # Dual-tag top N as PARLAY_CANDIDATE
    for i, bet in enumerate(results):
        if i < parlay_pool_size:
            bet["tag"] = "PARLAY_CANDIDATE"   # implies SINGLE too

    logger.info(
        "%d bets passed EV filter. %d tagged as PARLAY_CANDIDATE.",
        len(results),
        min(len(results), parlay_pool_size),
    )
    return results
