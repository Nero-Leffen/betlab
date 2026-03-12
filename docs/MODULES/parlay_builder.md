# Parlay Builder Module

## Purpose

The Parlay Builder module constructs optimized parlays from filtered betting opportunities. It checks for correlation between events, generates leg combinations, and ranks parlays by expected value. This module transforms independent bets into combo opportunities while managing correlation risk.

## Key Responsibilities

- Detect correlated betting events (same league, related teams, etc.)
- Generate valid parlay combinations respecting correlation rules
- Calculate EV for each potential parlay
- Rank parlays by risk-adjusted return metrics
- Validate legs before adding to parlay structure

## Dependencies

```python
from typing import List, Dict, Any, Tuple
from itertools import combinations
from betlab.math_engine import calculate_parlay_odds, calculate_parlay_probability
```

## Function Reference

### `check_correlation(bet_a: Dict, bet_b: Dict) -> bool`

**Purpose:** Determine if two bets are correlated (not independent). Prevents combining heavily related events that violate parlay assumptions.

**Parameters:**
- `bet_a` (dict): First bet with fields: 'sport', 'league', 'team_a', 'team_b', 'bet_type'
- `bet_b` (dict): Second bet with fields: 'sport', 'league', 'team_a', 'team_b', 'bet_type'

**Returns:**
- `bool`: True if correlated (should not combine), False if independent

**Raises:**
- `KeyError`: If required fields missing

**Example:**
```python
from betlab.parlay_builder import check_correlation

# Independent bets (different sports)
bet1 = {
    "sport": "NFL",
    "league": "NFL",
    "team_a": "Patriots",
    "team_b": "Chiefs",
    "bet_type": "moneyline"
}
bet2 = {
    "sport": "NBA",
    "league": "NBA",
    "team_a": "Lakers",
    "team_b": "Celtics",
    "bet_type": "moneyline"
}
correlated = check_correlation(bet1, bet2)
print(f"Correlated: {correlated}")
# Output: Correlated: False

# Correlated bets (same team in same sport)
bet3 = {
    "sport": "NFL",
    "league": "NFL",
    "team_a": "Patriots",
    "team_b": "Chiefs",
    "bet_type": "moneyline"
}
bet4 = {
    "sport": "NFL",
    "league": "NFL",
    "team_a": "Patriots",
    "team_b": "Chargers",
    "bet_type": "spread"
}
correlated = check_correlation(bet3, bet4)
print(f"Correlated: {correlated}")
# Output: Correlated: True (both involve Patriots)
```

**Notes:**
- Same sport/league = correlated (league outcomes influence each other)
- Same team involved = definitely correlated
- Different sports = independent (assumed)
- Moneyline + Spread on same game = correlated
- Sports-specific: NBA travel schedules affect multiple games; NFL divisional matchups create correlation

---

### `generate_combinations(bets: List[Dict], min_legs: int = 2, max_legs: int = 4) -> List[List[Dict]]`

**Purpose:** Generate all valid parlay combinations from candidate bets, respecting correlation constraints and leg count limits.

**Parameters:**
- `bets` (list[dict]): Filtered, tagged bets from analyser module
- `min_legs` (int): Minimum legs per parlay (default 2)
- `max_legs` (int): Maximum legs per parlay (default 4)

**Returns:**
- `list[list[dict]]`: List of valid parlay combinations, each containing bet dicts

**Raises:**
- `ValueError`: If min_legs > max_legs or limits unreasonable

**Example:**
```python
from betlab.parlay_builder import generate_combinations

bets = [
    {
        "id": "NFL_001",
        "sport": "NFL",
        "league": "NFL",
        "team_a": "Patriots",
        "team_b": "Chiefs",
        "odds": 2.50,
        "ev": 0.25
    },
    {
        "id": "NBA_001",
        "sport": "NBA",
        "league": "NBA",
        "team_a": "Lakers",
        "team_b": "Celtics",
        "odds": 1.91,
        "ev": 0.15
    },
    {
        "id": "MLB_001",
        "sport": "MLB",
        "league": "MLB",
        "team_a": "Yankees",
        "team_b": "Red Sox",
        "odds": 2.20,
        "ev": 0.20
    },
]

# Generate all valid combinations (2-3 legs)
combos = generate_combinations(bets, min_legs=2, max_legs=3)
print(f"Total combinations: {len(combos)}")
# Output: Total combinations: 3
# (Each pair from different sports)

for i, combo in enumerate(combos):
    bet_ids = [b['id'] for b in combo]
    print(f"  Combo {i+1}: {' + '.join(bet_ids)}")
    # Output: Combo 1: NFL_001 + NBA_001
    # Output: Combo 2: NFL_001 + MLB_001
    # Output: Combo 3: NBA_001 + MLB_001
```

**Notes:**
- Rejects combinations with correlated bets
- 4+ leg parlays rare; only include if all legs very high confidence
- Output includes only valid combinations (all legs independent)
- Filtering by max_legs reduces computational complexity
- Correlation check is performed internally before yielding combinations

---

### `calculate_parlay_ev(individual_evs: List[float], parlay_odds: float) -> float`

**Purpose:** Calculate expected value for complete parlay, accounting for compounding odds and combined probability.

**Parameters:**
- `individual_evs` (list[float]): EV for each leg as decimal (e.g., [0.15, 0.10, 0.20])
- `parlay_odds` (float): Combined parlay odds (product of individual odds)

**Returns:**
- `float`: Parlay EV as decimal (e.g., 0.30 = 30% expected return)

**Formula:**
```
Parlay Probability = (1 + EV_1) × (1 + EV_2) × ... × (1 + EV_N)
Parlay EV = Parlay Probability - 1
```

**Example:**
```python
from betlab.parlay_builder import calculate_parlay_ev

# 2-leg parlay: +15% and +10% EVs
evs = [0.15, 0.10]
parlay_odds = 3.50  # Combined odds (example)
parlay_ev = calculate_parlay_ev(evs, parlay_odds)
print(f"Parlay EV: {parlay_ev:.2%}")
# Output: Parlay EV: 26.50%

# 3-leg parlay: +20%, +15%, +10% EVs
evs = [0.20, 0.15, 0.10]
parlay_odds = 7.50  # Combined odds (example)
parlay_ev = calculate_parlay_ev(evs, parlay_odds)
print(f"Parlay EV: {parlay_ev:.2%}")
# Output: Parlay EV: 40.30%

# Note: Higher leg count compounds EV but increases variance dramatically
```

**Notes:**
- Accounts for diminishing probability with each additional leg
- Positive EV parlays excellent for bankroll growth if accurate
- Variance increases exponentially with leg count
- 2-leg parlays more stable than 4+ legs
- Compare parlay EV to single-bet alternatives

---

### `rank_parlays(parlays: List[Dict]) -> List[Dict]`

**Purpose:** Score and rank parlays by risk-adjusted metrics including EV, variance, and implied probability. Helps identify optimal combos for betting.

**Parameters:**
- `parlays` (list[dict]): Parlay dictionaries, each with 'legs', 'odds', 'ev', 'probability' fields

**Returns:**
- `list[dict]`: Same parlays sorted by ranking score, with new 'rank_score' and 'rank' fields

**Raises:**
- `ValueError`: If required fields missing

**Example:**
```python
from betlab.parlay_builder import rank_parlays

parlays = [
    {
        "id": "parlay_1",
        "legs": 2,
        "odds": 3.50,
        "ev": 0.25,
        "probability": 0.35
    },
    {
        "id": "parlay_2",
        "legs": 3,
        "odds": 7.50,
        "ev": 0.40,
        "probability": 0.18
    },
    {
        "id": "parlay_3",
        "legs": 2,
        "odds": 2.80,
        "ev": 0.15,
        "probability": 0.42
    },
]

ranked = rank_parlays(parlays)

print("Ranked parlays:")
for parlay in ranked:
    print(f"  #{parlay['rank']}: {parlay['id']} - Score: {parlay['rank_score']:.3f}")
    print(f"     Legs: {parlay['legs']}, Odds: {parlay['odds']:.2f}, EV: {parlay['ev']:.2%}, Prob: {parlay['probability']:.2%}")
# Output: #1: parlay_2 - Score: 0.892
# Output:      Legs: 3, Odds: 7.50, EV: 40.00%, Prob: 18.00%
# Output: #2: parlay_1 - Score: 0.745
# Output:      Legs: 2, Odds: 3.50, EV: 25.00%, Prob: 35.00%
# Output: #3: parlay_3 - Score: 0.623
# Output:      Legs: 2, Odds: 2.80, EV: 15.00%, Prob: 42.00%
```

**Notes:**
- Ranking formula: `(EV × 0.6 + Probability × 0.4)` adjusted for leg count
- Higher EV weighted more (60%) than raw probability (40%)
- Fewer legs preferred (lower variance risk)
- Rankings used to select which parlays to actually place
- Typically only place top 3-5 ranked parlays to manage risk

---

## Code Example: End-to-End Usage

```python
from betlab.parlay_builder import (
    check_correlation,
    generate_combinations,
    calculate_parlay_ev,
    rank_parlays
)
from betlab.math_engine import calculate_parlay_odds, calculate_parlay_probability

# Input: Filtered candidate bets from analyser
candidates = [
    {
        "id": "NFL_001",
        "sport": "NFL",
        "league": "NFL",
        "team_a": "Patriots",
        "team_b": "Chiefs",
        "odds": 2.50,
        "probability": 0.50,
        "ev": 0.25
    },
    {
        "id": "NBA_001",
        "sport": "NBA",
        "league": "NBA",
        "team_a": "Lakers",
        "team_b": "Celtics",
        "odds": 1.91,
        "probability": 0.58,
        "ev": 0.11
    },
    {
        "id": "MLB_001",
        "sport": "MLB",
        "league": "MLB",
        "team_a": "Yankees",
        "team_b": "Red Sox",
        "odds": 2.20,
        "probability": 0.50,
        "ev": 0.10
    },
]

# Step 1: Generate valid combinations
print("Step 1: Generating parlay combinations...")
combos = generate_combinations(candidates, min_legs=2, max_legs=3)
print(f"  Found {len(combos)} valid combinations\n")

# Step 2: Build parlay structs and calculate EV
print("Step 2: Building parlays and calculating EV...")
parlays = []

for combo in combos:
    combo_ids = [b['id'] for b in combo]
    combo_odds = calculate_parlay_odds([b['odds'] for b in combo])
    combo_probs = calculate_parlay_probability([b['probability'] for b in combo])
    combo_evs = [b['ev'] for b in combo]
    combo_ev = calculate_parlay_ev(combo_evs, combo_odds)

    parlay = {
        "id": "_".join(combo_ids),
        "legs": len(combo),
        "leg_ids": combo_ids,
        "odds": combo_odds,
        "probability": combo_probs,
        "ev": combo_ev,
    }
    parlays.append(parlay)
    print(f"  {parlay['id']}: {parlay['legs']} legs, {parlay['odds']:.2f} odds, {parlay['ev']:.2%} EV")

# Step 3: Rank by EV and variance
print("\nStep 3: Ranking parlays...")
ranked = rank_parlays(parlays)

print("\nTop-ranked parlays:")
for parlay in ranked[:3]:  # Show top 3
    print(f"  #{parlay['rank']}: {parlay['id']}")
    print(f"     Score: {parlay['rank_score']:.3f}, Legs: {parlay['legs']}, EV: {parlay['ev']:.2%}")

# Step 4: Select for betting (typically top 2-3)
recommended = ranked[:2]
print(f"\nRecommended parlays for betting: {len(recommended)}")
for p in recommended:
    print(f"  - {p['id']} (rank #{p['rank']})")
```

## Configuration

Key parameters for parlay construction:

```python
# Correlation rules
SAME_SPORT_CORRELATED = True   # Same sport = correlated
SAME_LEAGUE_CORRELATED = True  # Same league = correlated
SAME_TEAM_CORRELATED = True    # Same team involved = correlated

# Combination limits
MIN_PARLAY_LEGS = 2            # Minimum legs
MAX_PARLAY_LEGS = 4            # Maximum legs (higher = risky)

# Ranking weights
RANK_EV_WEIGHT = 0.60          # 60% weight to EV
RANK_PROB_WEIGHT = 0.40        # 40% weight to probability
RANK_LEG_PENALTY = 0.05        # 5% penalty per leg beyond 2

# Selection
TOP_PARLAYS_TO_RECOMMEND = 3   # How many to recommend
```

## Testing

The parlay builder module includes comprehensive tests in `tests/test_parlay_builder.py`:

- **test_check_correlation**: Same sport, same league, same team scenarios
- **test_generate_combinations**: Valid combinations, correlation filtering
- **test_calculate_parlay_ev**: Multi-leg EVs, compounding accuracy
- **test_rank_parlays**: Ranking order, score calculation
- **test_full_workflow**: End-to-end parlay generation

Run tests with:
```bash
pytest tests/test_parlay_builder.py -v
```

## Integration Notes

- Input: Filtered bets from analyser (with EV tags)
- Uses math_engine functions for odds/probability calculations
- Output: Ranked parlays feed into output_generator and bankroll_mgr for final staking
- Correlation detection critical for accurate parlay probability (prevents overestimating)
- Ranking allows downstream modules to select best combos for bankroll allocation
