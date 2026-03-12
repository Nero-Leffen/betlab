# Math Engine Module

## Purpose

The Math Engine module implements core betting mathematics including probability calculations, expected value (EV) analysis, Kelly Criterion sizing, and parlay mathematics. This module is the analytical backbone of the BetLab system, providing precise quantitative decision support for bet selection and stake sizing.

## Key Responsibilities

- Calculate implied probabilities from odds
- Compute expected value (EV) for individual bets
- Apply Kelly Criterion for optimal stake sizing
- Analyze parlay mathematics (combined odds and probabilities)
- Handle precision for financial calculations

## Dependencies

```python
from typing import List
from decimal import Decimal, ROUND_HALF_UP
import math
```

## Function Reference

### `calculate_implied_probability(decimal_odds: float) -> float`

**Purpose:** Extract the implied probability from decimal odds, representing what the market believes is the probability of an outcome.

**Parameters:**
- `decimal_odds` (float): Decimal format odds (e.g., 2.50)

**Returns:**
- `float`: Implied probability as decimal (0.0 to 1.0)

**Raises:**
- `ValueError`: If odds < 1.0

**Formula:**
```
Implied Probability = 1 / Decimal Odds
```

**Example:**
```python
from betlab.math_engine import calculate_implied_probability

# Odds of 2.50 imply 40% probability
prob = calculate_implied_probability(2.50)
print(prob)  # Output: 0.4

# Odds of 1.50 imply 66.67% probability
prob = calculate_implied_probability(1.50)
print(f"{prob:.4f}")  # Output: 0.6667
```

**Notes:**
- Implied probability often exceeds 100% across all outcomes in a market (overround/vigorish)
- Market efficient when odds reflect true probabilities
- Lower odds = higher implied probability = likely outcome
- Foundation for all EV calculations

---

### `calculate_ev(odds: float, true_probability: float) -> float`

**Purpose:** Calculate expected value for a single bet given your estimated probability vs. market odds. Positive EV indicates profitable long-term betting.

**Parameters:**
- `odds` (float): Decimal odds offered by sportsbook
- `true_probability` (float): Your estimated probability of outcome (0.0 to 1.0)

**Returns:**
- `float`: Expected value as decimal (e.g., 0.15 = 15% ROI)

**Raises:**
- `ValueError`: If probability < 0 or > 1, or odds < 1.0

**Formula:**
```
EV = (True Probability × Odds) - 1
```

**Example:**
```python
from betlab.math_engine import calculate_ev

# You believe outcome has 50% probability, odds are 2.50
# EV = (0.50 × 2.50) - 1 = 0.25 = 25% profit per $1 bet
ev = calculate_ev(odds=2.50, true_probability=0.50)
print(f"EV: {ev:.2%}")  # Output: EV: 25.00%

# You believe 45% probability, odds are 2.00
# EV = (0.45 × 2.00) - 1 = -0.10 = 10% expected loss
ev = calculate_ev(odds=2.00, true_probability=0.45)
print(f"EV: {ev:.2%}")  # Output: EV: -10.00%
```

**Notes:**
- Positive EV: Expected long-term profit
- Negative EV: Expected long-term loss (avoid unless special circumstances)
- Assumes even-money market (no overround adjustment shown)
- Critical metric for bet selection

---

### `calculate_kelly_fraction(odds: float, probability: float) -> float`

**Purpose:** Calculate optimal stake fraction using Kelly Criterion, maximizing long-term bankroll growth while minimizing ruin risk.

**Parameters:**
- `odds` (float): Decimal odds
- `probability` (float): Estimated win probability (0.0 to 1.0)

**Returns:**
- `float`: Fraction of bankroll to stake (e.g., 0.05 = 5%)

**Raises:**
- `ValueError`: If parameters invalid

**Formula:**
```
Kelly Fraction = (Probability × Odds - 1) / (Odds - 1)
```

**Example:**
```python
from betlab.math_engine import calculate_kelly_fraction

# 60% probability at 2.00 odds
kelly = calculate_kelly_fraction(odds=2.00, probability=0.60)
print(f"Kelly: {kelly:.4f}")  # Output: Kelly: 0.2000 (20% of bankroll)

# 55% probability at 1.91 odds (typical market)
kelly = calculate_kelly_fraction(odds=1.91, probability=0.55)
print(f"Kelly: {kelly:.4f}")  # Output: Kelly: 0.1620 (16.2%)

# 45% probability at 2.50 odds (positive EV)
kelly = calculate_kelly_fraction(odds=2.50, probability=0.45)
print(f"Kelly: {kelly:.4f}")  # Output: Kelly: 0.1111 (11.11%)
```

**Notes:**
- Kelly is theoretical maximum; fractional Kelly (0.5x or 0.25x) used for risk management
- Negative Kelly (losing EV) returns 0
- Assumes unlimited divisibility of stakes
- Bankroll should never reach zero mathematically, but practice differs
- Kelly > 0.10 (10%) indicates very high confidence edge

---

### `calculate_parlay_probability(individual_probabilities: List[float]) -> float`

**Purpose:** Calculate combined probability for parlay (all-or-nothing) win. Assumes independent events.

**Parameters:**
- `individual_probabilities` (list[float]): Probability of each leg winning (0.0 to 1.0)

**Returns:**
- `float`: Probability all legs win (0.0 to 1.0)

**Raises:**
- `ValueError`: If any probability invalid

**Formula:**
```
Parlay Probability = Probability_1 × Probability_2 × ... × Probability_N
```

**Example:**
```python
from betlab.math_engine import calculate_parlay_probability

# 2-leg parlay: 65% and 60% individual probabilities
parlay_prob = calculate_parlay_probability([0.65, 0.60])
print(f"Parlay Probability: {parlay_prob:.4f}")  # Output: 0.3900 (39%)

# 3-leg parlay
parlay_prob = calculate_parlay_probability([0.65, 0.60, 0.55])
print(f"Parlay Probability: {parlay_prob:.4f}")  # Output: 0.2145 (21.45%)

# 4-leg parlay with high confidence bets
parlay_prob = calculate_parlay_probability([0.70, 0.70, 0.70, 0.70])
print(f"Parlay Probability: {parlay_prob:.4f}")  # Output: 0.2401 (24.01%)
```

**Notes:**
- Assumes legs are statistically independent (correlation ignored)
- Probability decreases multiplicatively with legs
- 4+ legs rarely justified unless very high individual confidence
- Doesn't account for correlation or book correlation (see parlay_builder module)

---

### `calculate_parlay_odds(individual_odds: List[float]) -> float`

**Purpose:** Calculate total payout odds for a parlay by multiplying individual decimal odds.

**Parameters:**
- `individual_odds` (list[float]): Decimal odds for each leg

**Returns:**
- `float`: Combined parlay decimal odds

**Raises:**
- `ValueError`: If any odds < 1.0

**Formula:**
```
Parlay Odds = Odds_1 × Odds_2 × ... × Odds_N
```

**Example:**
```python
from betlab.math_engine import calculate_parlay_odds

# 2-leg parlay: 2.00 × 1.91
parlay_odds = calculate_parlay_odds([2.00, 1.91])
print(parlay_odds)  # Output: 3.82

# 3-leg parlay: 2.00 × 1.91 × 1.85
parlay_odds = calculate_parlay_odds([2.00, 1.91, 1.85])
print(parlay_odds)  # Output: 7.067

# 4-leg parlay with stronger favorites
parlay_odds = calculate_parlay_odds([1.50, 1.60, 1.70, 1.80])
print(parlay_odds)  # Output: 6.552
```

**Notes:**
- Simple multiplication of decimal odds
- Larger parlays create exponential returns but exponential risk
- Example: $100 on 3.82 parlay odds returns $382 (including original stake)
- Combined with probability for EV analysis

---

## Code Example: End-to-End Usage

```python
from betlab.math_engine import (
    calculate_implied_probability,
    calculate_ev,
    calculate_kelly_fraction,
    calculate_parlay_probability,
    calculate_parlay_odds
)

# Scenario: Analyzing a set of bets for parlay construction

# Single bet analysis
market_odds = 2.50
my_probability = 0.50  # I believe 50% chance

implied_prob = calculate_implied_probability(market_odds)
ev = calculate_ev(market_odds, my_probability)
kelly = calculate_kelly_fraction(market_odds, my_probability)

print(f"Market odds: {market_odds}")
print(f"Implied probability: {implied_prob:.2%}")
print(f"My probability: {my_probability:.2%}")
print(f"Expected value: {ev:.2%}")
print(f"Kelly fraction: {kelly:.4f}")

# Parlay analysis
leg1_odds, leg1_prob = 2.00, 0.55
leg2_odds, leg2_prob = 1.91, 0.58
leg3_odds, leg3_prob = 2.20, 0.50

parlay_total_odds = calculate_parlay_odds([leg1_odds, leg2_odds, leg3_odds])
parlay_total_prob = calculate_parlay_probability([leg1_prob, leg2_prob, leg3_prob])
parlay_ev = (parlay_total_prob * parlay_total_odds) - 1

print(f"\n3-Leg Parlay:")
print(f"Combined odds: {parlay_total_odds:.2f}")
print(f"Combined probability: {parlay_total_prob:.2%}")
print(f"Parlay EV: {parlay_ev:.2%}")

# Stake sizing recommendation
recommended_stake = kelly * 100  # Assuming $100 bankroll
print(f"Recommended stake (full Kelly): ${recommended_stake:.2f}")
print(f"Recommended stake (half Kelly): ${recommended_stake * 0.5:.2f}")
```

## Configuration

Key constants for mathematical operations:

```python
# Precision settings
DECIMAL_PLACES = 4  # Rounding precision
PROBABILITY_MIN = 0.0
PROBABILITY_MAX = 1.0

# Kelly Criterion limits
KELLY_FRACTION_MAX = 0.50  # Practical upper limit
KELLY_FRACTION_MIN = 0.0   # No negative Kelly

# Parlay limits
MAX_PARLAY_LEGS = 6  # Reasonable maximum for analysis
```

## Testing

The math engine module includes comprehensive tests in `tests/test_math_engine.py`:

- **test_implied_probability**: Boundary cases, precision
- **test_calculate_ev**: Positive/negative EV scenarios
- **test_kelly_criterion**: Various probability/odds combinations
- **test_parlay_mathematics**: Leg combinations, accuracy
- **test_edge_cases**: Zero probability, very high odds

Run tests with:
```bash
pytest tests/test_math_engine.py -v
```
