# Analyser Module

## Purpose

The Analyser module filters betting opportunities based on expected value thresholds and applies intelligent tagging for bet classification. It serves as the decision layer between raw market data and final recommendations, enabling data-driven bet selection and categorization into singles and parlay candidates.

## Key Responsibilities

- Filter bets by expected value thresholds
- Apply candidate tags for various strategies
- Generate rejection reasons for filtered bets
- Categorize bets for different bankroll allocation strategies
- Provide audit trail for decision logic

## Dependencies

```python
from typing import List, Dict, Any
from enum import Enum
```

## Function Reference

### `filter_by_ev(bets: List[Dict], threshold: float = 0.02) -> List[Dict]`

**Purpose:** Filter betting opportunities to only those exceeding minimum expected value threshold. Removes marginal bets to focus on higher-conviction opportunities.

**Parameters:**
- `bets` (list[dict]): List of bet dictionaries, each containing 'ev', 'odds', 'probability', etc.
- `threshold` (float): Minimum EV threshold to accept bet (default 0.02 = 2%)

**Returns:**
- `list[dict]`: Filtered list of bets meeting EV threshold

**Raises:**
- `ValueError`: If threshold outside valid range (-1.0 to 1.0)
- `KeyError`: If required fields missing from bet dictionaries

**Example:**
```python
from betlab.analyser import filter_by_ev

bets = [
    {"id": "bet1", "odds": 2.50, "probability": 0.50, "ev": 0.25},
    {"id": "bet2", "odds": 2.00, "probability": 0.45, "ev": -0.10},
    {"id": "bet3", "odds": 1.91, "probability": 0.58, "ev": 0.11},
    {"id": "bet4", "odds": 1.50, "probability": 0.65, "ev": -0.025},
]

# Filter for EV >= 2%
high_ev_bets = filter_by_ev(bets, threshold=0.02)
print(f"High EV bets: {len(high_ev_bets)}")
# Output: High EV bets: 2
# Includes bet1 (25% EV) and bet3 (11% EV)

# Stricter filter: EV >= 5%
premium_bets = filter_by_ev(bets, threshold=0.05)
print(f"Premium bets: {len(premium_bets)}")
# Output: Premium bets: 1
# Includes only bet1 (25% EV)
```

**Notes:**
- Default 2% threshold balances edge against variance
- Lower threshold (1%) captures more marginal bets but increases variance
- Higher threshold (5%+) only for high-confidence models
- Threshold should reflect confidence in probability estimates
- Negative EV bets all filtered if threshold > 0

---

### `tag_candidates(bets: List[Dict], parlay_pool_size: int = 4) -> List[Dict]`

**Purpose:** Apply strategy tags to bets, marking them as suitable for singles, parlays, or both. Organizes bets for different bankroll allocation strategies.

**Parameters:**
- `bets` (list[dict]): Filtered list of bets with EV analysis
- `parlay_pool_size` (int): Maximum number of legs to consider for parlays (default 4)

**Returns:**
- `list[dict]`: Same bets with added 'tags' and 'candidate_tier' fields

**Raises:**
- `ValueError`: If parlay_pool_size < 2

**Example:**
```python
from betlab.analyser import tag_candidates

bets = [
    {"id": "bet1", "odds": 2.50, "probability": 0.50, "ev": 0.25},
    {"id": "bet2", "odds": 1.91, "probability": 0.58, "ev": 0.11},
    {"id": "bet3", "odds": 1.85, "probability": 0.55, "ev": 0.02},
]

tagged_bets = tag_candidates(bets, parlay_pool_size=4)

for bet in tagged_bets:
    print(f"{bet['id']}: tags={bet['tags']}, tier={bet['candidate_tier']}")
    # Output: bet1: tags=['singles', 'parlay'], tier='premium'
    # Output: bet2: tags=['singles', 'parlay'], tier='standard'
    # Output: bet3: tags=['singles'], tier='marginal'
```

**Notes:**
- Tagging logic: High EV bets → both singles and parlay candidates; Moderate EV → singles; Low EV → singles only
- Parlay pool limited to highest EV bets (avoid low-confidence legs)
- Tier classification aids in bankroll allocation: premium/standard/marginal
- Tags enable flexible filtering downstream

---

### `calculate_rejection_reason(bet: Dict, ev: float, threshold: float) -> str`

**Purpose:** Generate descriptive explanation for why a bet was rejected during filtering. Helps with audit trail and strategy refinement.

**Parameters:**
- `bet` (dict): Bet dictionary with metadata
- `ev` (float): Expected value of bet
- `threshold` (float): EV threshold that was applied

**Returns:**
- `str`: Human-readable rejection reason

**Raises:**
- `ValueError`: If inputs malformed

**Example:**
```python
from betlab.analyser import calculate_rejection_reason

# Rejected for insufficient EV
bet = {"id": "bet1", "odds": 2.00, "probability": 0.45, "sport": "NFL"}
reason = calculate_rejection_reason(bet, ev=-0.10, threshold=0.02)
print(reason)
# Output: "Rejected: Negative EV (-10.00%). Odds 2.00 imply 50% win, but analysis estimates 45%."

# Another example
bet = {"id": "bet2", "odds": 1.50, "probability": 0.63}
reason = calculate_rejection_reason(bet, ev=0.005, threshold=0.02)
print(reason)
# Output: "Rejected: EV (0.50%) below threshold (2.00%). Limited edge in this opportunity."
```

**Notes:**
- Messages include: EV value, threshold, odds, estimated probability, and market implication
- Useful for backtesting analysis and strategy tuning
- Can be aggregated to identify systematic bias in probability estimates
- Include in reports for transparency

---

## Code Example: End-to-End Usage

```python
from betlab.math_engine import calculate_ev, calculate_implied_probability
from betlab.analyser import filter_by_ev, tag_candidates, calculate_rejection_reason

# Scenario: Process raw market data into actionable betting opportunities

raw_bets = [
    {"id": "NFL_001", "event": "Patriots vs Chiefs", "odds": 2.50, "my_prob": 0.50},
    {"id": "NFL_002", "event": "Ravens vs Dolphins", "odds": 1.91, "my_prob": 0.58},
    {"id": "NFL_003", "event": "Cowboys vs Eagles", "odds": 2.00, "my_prob": 0.45},
    {"id": "NFL_004", "event": "49ers vs Seahawks", "odds": 1.85, "my_prob": 0.55},
    {"id": "MLB_001", "event": "Yankees vs Red Sox", "odds": 1.80, "my_prob": 0.52},
]

# Step 1: Enrich with EV and probability analysis
for bet in raw_bets:
    bet['ev'] = calculate_ev(bet['odds'], bet['my_prob'])
    bet['implied_prob'] = calculate_implied_probability(bet['odds'])

# Step 2: Filter by EV threshold
ev_threshold = 0.02
filtered_bets = filter_by_ev(raw_bets, threshold=ev_threshold)

print(f"Original bets: {len(raw_bets)}")
print(f"After EV filter (>{ev_threshold:.1%}): {len(filtered_bets)}")

# Log rejections
rejected = [b for b in raw_bets if b not in filtered_bets]
for bet in rejected:
    reason = calculate_rejection_reason(bet, bet['ev'], ev_threshold)
    print(f"  {bet['id']}: {reason}")

# Step 3: Tag candidates for singles/parlays
tagged_bets = tag_candidates(filtered_bets, parlay_pool_size=4)

# Step 4: Organize output
singles_candidates = [b for b in tagged_bets if 'singles' in b['tags']]
parlay_candidates = [b for b in tagged_bets if 'parlay' in b['tags']]

print(f"\nSingles candidates: {len(singles_candidates)}")
for bet in singles_candidates:
    print(f"  {bet['id']}: {bet['ev']:.2%} EV, tier={bet['candidate_tier']}")

print(f"\nParlay candidates: {len(parlay_candidates)}")
for bet in parlay_candidates:
    print(f"  {bet['id']}: {bet['ev']:.2%} EV, tier={bet['candidate_tier']}")
```

## Configuration

Key parameters for analysis:

```python
# EV thresholds by use case
EV_THRESHOLDS = {
    "conservative": 0.05,   # 5%+ for maximum confidence
    "standard": 0.02,       # 2%+ default balanced approach
    "aggressive": 0.00,     # 0%+ any positive EV
}

# Tier classification
TIER_THRESHOLDS = {
    "premium": 0.15,        # 15%+ EV
    "standard": 0.05,       # 5-15% EV
    "marginal": 0.00,       # 0-5% EV
}

# Parlay configuration
DEFAULT_PARLAY_POOL = 4  # Maximum legs per parlay
MIN_PARLAY_LEGS = 2       # Minimum legs to consider
```

## Testing

The analyser module includes comprehensive tests in `tests/test_analyser.py`:

- **test_filter_by_ev**: Various threshold levels, edge cases
- **test_tag_candidates**: Tag assignment logic, tier classification
- **test_calculate_rejection_reason**: Accuracy of rejection messages
- **test_filtering_logic**: Integration with math engine outputs
- **test_empty_inputs**: Handling of edge cases (empty lists, zero EV)

Run tests with:
```bash
pytest tests/test_analyser.py -v
```

## Integration Notes

- Works as middle layer between math_engine and parlay_builder modules
- Requires EV/probability fields from math_engine before calling
- Output feeds into parlay_builder and bankroll_mgr for stake sizing
- Rejection reasons valuable for strategy backtesting
