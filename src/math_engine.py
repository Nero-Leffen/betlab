"""
math_engine.py
==============
Core mathematical engine for BetLab.

Implements all formulas exactly as specified in the PRD:
  - Implied Probability
  - Expected Value (EV)
  - Kelly Criterion (Half-Kelly)
  - Parlay Hit Probability
  - Odds format conversion (Decimal / American / Fractional)

No approximations. No external dependencies beyond Python stdlib.
"""

from __future__ import annotations
import re


# ---------------------------------------------------------------------------
# Odds Conversion
# ---------------------------------------------------------------------------

def detect_odds_format(raw: str) -> str:
    """
    Detect whether a raw odds string is decimal, american, or fractional.

    Rules:
      - Contains '/'  → fractional  (e.g. "5/2", "11/4")
      - Starts with '+' or '-' (and not a float like -0.5) → american
      - Otherwise → decimal

    Returns: 'decimal' | 'american' | 'fractional'
    """
    raw = str(raw).strip()
    if "/" in raw:
        return "fractional"
    if re.match(r"^[+-]\d+$", raw):
        return "american"
    return "decimal"


def american_to_decimal(american: float) -> float:
    """
    Convert American moneyline odds to decimal.

    Positive (e.g. +150): profit on 100 stake → decimal = (american / 100) + 1
    Negative (e.g. -110): stake needed to win 100 → decimal = (100 / abs(american)) + 1
    """
    if american >= 100:
        return round((american / 100.0) + 1.0, 4)
    else:
        return round((100.0 / abs(american)) + 1.0, 4)


def fractional_to_decimal(fractional: str) -> float:
    """
    Convert fractional odds (e.g. "5/2") to decimal.

    decimal = (numerator / denominator) + 1
    """
    parts = fractional.strip().split("/")
    if len(parts) != 2:
        raise ValueError(f"Invalid fractional odds: '{fractional}'")
    numerator, denominator = float(parts[0]), float(parts[1])
    if denominator == 0:
        raise ValueError("Fractional odds denominator cannot be zero.")
    return round((numerator / denominator) + 1.0, 4)


def to_decimal_odds(raw: str) -> float:
    """
    Master converter. Accepts decimal, american, or fractional odds string.
    Always returns a float decimal odds value > 1.0.

    Raises ValueError for unresolvable inputs.
    """
    raw = str(raw).strip()
    fmt = detect_odds_format(raw)

    if fmt == "fractional":
        return fractional_to_decimal(raw)

    if fmt == "american":
        return american_to_decimal(float(raw))

    # Decimal — strip any non-numeric chars except '.'
    cleaned = re.sub(r"[^\d.]", "", raw)
    if not cleaned:
        raise ValueError(f"Cannot parse odds value: '{raw}'")
    return float(cleaned)


# ---------------------------------------------------------------------------
# Core Probability & EV Formulas (exact per PRD)
# ---------------------------------------------------------------------------

def get_implied_probability(decimal_odds: float) -> float:
    """
    Implied probability = 1 / decimal_odds.
    Represents the break-even win rate at those odds.
    """
    if decimal_odds <= 1.0:
        raise ValueError(f"Decimal odds must be > 1.0, got {decimal_odds}")
    return 1.0 / decimal_odds


def calculate_ev(decimal_odds: float, true_probability: float) -> float:
    """
    Expected Value = (Decimal Odds × True Probability) − 1

    Positive EV → the bet has a mathematical edge.
    Negative EV → the bookmaker has the edge.

    true_probability: estimated win probability (0.0 – 1.0)
    """
    if not (0.0 < true_probability < 1.0):
        raise ValueError(f"true_probability must be between 0 and 1, got {true_probability}")
    return round((decimal_odds * true_probability) - 1.0, 6)


def kelly_criterion(decimal_odds: float, true_probability: float) -> float:
    """
    Half-Kelly Criterion for stake sizing.

    Full Kelly: f = (b×p − q) / b
    Half Kelly:  f × 0.5   (reduces variance significantly)

    b = decimal_odds - 1  (net profit per unit staked)
    p = true_probability
    q = 1 - p

    Returns fraction of bankroll to stake (0.0 if bet has no edge).
    """
    if decimal_odds <= 1.0:
        raise ValueError(f"Decimal odds must be > 1.0, got {decimal_odds}")
    if not (0.0 < true_probability < 1.0):
        raise ValueError(f"true_probability must be between 0 and 1, got {true_probability}")

    b = decimal_odds - 1.0
    p = true_probability
    q = 1.0 - p

    full_kelly = (b * p - q) / b
    half_kelly = full_kelly * 0.5
    return round(max(0.0, half_kelly), 6)


def parlay_hit_probability(leg_probabilities: list[float]) -> float:
    """
    Combined hit probability for a parlay.

    Assumes legs are independent (no correlated outcomes).
    probability = p1 × p2 × ... × pN
    """
    if not leg_probabilities:
        raise ValueError("leg_probabilities list cannot be empty.")
    probability = 1.0
    for prob in leg_probabilities:
        probability *= prob
    return round(probability, 6)


def apply_correlation_penalty(independent_probability: float, penalty_factor: float) -> float:
    """
    Apply a correlation penalty factor to a parlay hit probability.

    independent_probability: base probability from independent leg multiplication.
    penalty_factor: multiplier in (0, 1].
    """
    if not (0.0 <= independent_probability <= 1.0):
        raise ValueError(
            f"independent_probability must be between 0 and 1, got {independent_probability}"
        )
    if not (0.0 < penalty_factor <= 1.0):
        raise ValueError(f"penalty_factor must be in (0, 1], got {penalty_factor}")
    return round(independent_probability * penalty_factor, 6)


def parlay_combined_odds(leg_odds: list[float]) -> float:
    """
    Combined decimal odds for a parlay.
    combined = odds1 × odds2 × ... × oddsN
    """
    if not leg_odds:
        raise ValueError("leg_odds list cannot be empty.")
    combined = 1.0
    for odds in leg_odds:
        combined *= odds
    return round(combined, 4)


def kelly_stake_inr(
    decimal_odds: float,
    true_probability: float,
    bankroll_inr: float,
    unit_inr: float,
    min_units: int = 1,
    max_units: int = 2,
) -> float:
    """
    Convert Half-Kelly fraction to an INR stake, clamped to unit boundaries.

    Steps:
      1. Calculate Half-Kelly fraction.
      2. Multiply by bankroll to get raw INR stake.
      3. Round to nearest unit.
      4. Clamp between min_units and max_units.
    """
    if bankroll_inr <= 0:
        raise ValueError(f"bankroll_inr must be > 0, got {bankroll_inr}")
    if unit_inr <= 0:
        raise ValueError(f"unit_inr must be > 0, got {unit_inr}")
    if min_units < 0:
        raise ValueError(f"min_units must be >= 0, got {min_units}")
    if max_units < min_units:
        raise ValueError(
            f"max_units must be >= min_units, got min_units={min_units}, max_units={max_units}"
        )

    fraction = kelly_criterion(decimal_odds, true_probability)
    raw_inr = fraction * bankroll_inr

    # Round to nearest unit
    units = round(raw_inr / unit_inr)
    units = max(min_units, min(units, max_units))

    return units * unit_inr
