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

from src.math_engine import parlay_combined_odds, parlay_hit_probability
from src.bankroll_mgr import SizedBet

logger = logging.getLogger(__name__)


@dataclass
class ParlayOption:
    """Represents a constructed parlay bet."""
    legs: list[SizedBet]
    combined_odds: float
    hit_probability: float
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
            hit_prob = parlay_hit_probability(prob_list)

            # EV of the parlay itself
            parlay_ev = round((combined_odds * hit_prob) - 1.0, 6)

            valid_parlays.append(ParlayOption(
                legs=legs,
                combined_odds=combined_odds,
                hit_probability=hit_prob,
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
