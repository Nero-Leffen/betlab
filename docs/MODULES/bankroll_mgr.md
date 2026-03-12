# Bankroll Manager Module

## Purpose

The Bankroll Manager module handles stake sizing, daily betting limits, and losing streak detection. It applies responsible risk management techniques including Kelly Criterion fractions, confidence-based adjustments, and automated circuit-breakers to protect bankroll during downswings.

## Key Responsibilities

- Calculate unit sizes based on bankroll and multipliers
- Determine stake amounts using Kelly Criterion with confidence adjustments
- Track daily staking and enforce caps
- Detect prolonged losing streaks
- Monitor overall bankroll health and drawdown

## Dependencies

```python
from typing import List, Dict
from datetime import datetime, timedelta
from decimal import Decimal
```

## Function Reference

### `get_unit_size(unit_multiplier: float = 1.0) -> float`

**Purpose:** Calculate the base unit size for betting, representing the minimum stake amount. All bets are expressed as multiples of units.

**Parameters:**
- `unit_multiplier` (float): Scaling factor for unit size (default 1.0 = standard unit)

**Returns:**
- `float`: Unit size in currency units

**Raises:**
- `ValueError`: If multiplier < 0.1 or > 10.0

**Example:**
```python
from betlab.bankroll_mgr import get_unit_size

# Standard unit with $10,000 bankroll
unit = get_unit_size(unit_multiplier=1.0)
print(f"Unit size: ${unit:.2f}")
# Output: Unit size: $100.00  (typically 1% of bankroll)

# Half units for reduced risk period
half_unit = get_unit_size(unit_multiplier=0.5)
print(f"Half-unit size: ${half_unit:.2f}")
# Output: Half-unit size: $50.00

# Double units for high-confidence period
double_unit = get_unit_size(unit_multiplier=2.0)
print(f"Double-unit size: ${double_unit:.2f}")
# Output: Double-unit size: $200.00
```

**Notes:**
- Unit typically = 1% of total bankroll
- Multiplier allows temporary adjustment without changing base bankroll calculation
- Use 0.5x-1.0x for normal periods, 0.25x-0.5x after losing streaks
- Multiplier bounds prevent reckless over-sizing

---

### `calculate_stake(kelly_fraction: float, confidence: str, daily_staked: float = 0.0) -> float`

**Purpose:** Calculate optimal stake amount for a bet, adjusting Kelly fraction based on confidence level and daily staking exposure.

**Parameters:**
- `kelly_fraction` (float): Kelly percentage from math_engine (e.g., 0.15 = 15%)
- `confidence` (str): Confidence level: 'high', 'medium', 'low' (applies fraction multipliers)
- `daily_staked` (float): Amount already staked today (default 0.0)

**Returns:**
- `float`: Recommended stake amount

**Raises:**
- `ValueError`: If kelly_fraction < 0, or daily_staked exceeds daily limit

**Example:**
```python
from betlab.bankroll_mgr import calculate_stake, get_unit_size

# Setup: $10,000 bankroll, unit = $100
unit = get_unit_size(1.0)

# Scenario 1: High confidence bet with 15% Kelly
kelly = 0.15
stake_high = calculate_stake(kelly_fraction=kelly, confidence='high', daily_staked=0.0)
print(f"High confidence stake: ${stake_high:.2f}")
# Output: High confidence stake: $150.00 (1.5 units at 100% of Kelly)

# Scenario 2: Medium confidence with 15% Kelly
stake_medium = calculate_stake(kelly_fraction=kelly, confidence='medium', daily_staked=0.0)
print(f"Medium confidence stake: ${stake_medium:.2f}")
# Output: Medium confidence stake: $75.00 (0.75 units at 50% of Kelly)

# Scenario 3: Low confidence with 15% Kelly
stake_low = calculate_stake(kelly_fraction=kelly, confidence='low', daily_staked=0.0)
print(f"Low confidence stake: ${stake_low:.2f}")
# Output: Low confidence stake: $38.00 (0.38 units at 25% of Kelly)

# Scenario 4: Already staked $500 today (approaching daily limit of $1000)
stake_capped = calculate_stake(kelly_fraction=0.10, confidence='medium', daily_staked=500.0)
print(f"Capped stake: ${stake_capped:.2f}")
# Output: Capped stake: $25.00 (limited by daily cap)
```

**Notes:**
- Confidence multipliers: high=100%, medium=50%, low=25% of Kelly
- Daily limit typically 10% of bankroll per day
- Function returns stake amount, not units
- Fractional Kelly recommended; never full Kelly in practice

---

### `detect_losing_streak(results: List[str], window_days: int = 7, threshold: int = 5) -> bool`

**Purpose:** Identify prolonged losing streaks requiring strategic pause or reduced stake sizing. Prevents compounding losses during downswings.

**Parameters:**
- `results` (list[str]): List of bet results ('W' for win, 'L' for loss), sorted chronologically
- `window_days` (int): Time period to analyze (default 7 = past week)
- `threshold` (int): Number of losses to trigger streak detection (default 5)

**Returns:**
- `bool`: True if losing streak detected, False otherwise

**Raises:**
- `ValueError`: If results list malformed or threshold negative

**Example:**
```python
from betlab.bankroll_mgr import detect_losing_streak

# Scenario 1: Normal results with wins and losses mixed
results = ['W', 'W', 'L', 'W', 'L', 'L', 'W', 'W', 'L', 'W']
streak = detect_losing_streak(results, window_days=7, threshold=5)
print(f"Losing streak detected: {streak}")
# Output: Losing streak detected: False (only 4 losses in recent history)

# Scenario 2: Prolonged losing streak
results = ['W', 'W', 'L', 'L', 'L', 'L', 'L', 'L', 'W', 'W']
streak = detect_losing_streak(results, window_days=7, threshold=5)
print(f"Losing streak detected: {streak}")
# Output: Losing streak detected: True (6 consecutive losses)

# Scenario 3: Recently turned around from streak
results = ['L', 'L', 'L', 'L', 'L', 'W', 'W', 'W', 'W', 'W']
streak = detect_losing_streak(results, window_days=7, threshold=5)
print(f"Losing streak detected: {streak}")
# Output: Losing streak detected: False (streak ended, recent wins)
```

**Notes:**
- Detects consecutive losses (true streaks), not just loss percentage
- Streak triggers automatic stake reduction or pause for 2-3 days
- Historical reference: 5 losses = ~3% bankroll loss assuming units = 1% bankroll
- Can be customized by sport or season (tighter during variance-heavy periods)

---

### `calculate_bankroll_status(current_pnl: float, total_bankroll: float) -> Dict`

**Purpose:** Generate comprehensive bankroll health report including ROI, drawdown, and action recommendations.

**Parameters:**
- `current_pnl` (float): Profit/loss from betting activity (can be negative)
- `total_bankroll` (float): Current available bankroll

**Returns:**
- `dict`: Status report with keys: 'status', 'roi', 'drawdown_pct', 'recommendation', 'remaining_bankroll'

**Raises:**
- `ValueError`: If bankroll <= 0

**Example:**
```python
from betlab.bankroll_mgr import calculate_bankroll_status

# Scenario 1: Strong performance
status = calculate_bankroll_status(current_pnl=2000.0, total_bankroll=10000.0)
print(f"Status: {status['status']}")
print(f"ROI: {status['roi']:.2%}")
print(f"Recommendation: {status['recommendation']}")
# Output: Status: Healthy
# Output: ROI: 20.00%
# Output: Recommendation: Continue standard betting

# Scenario 2: Moderate drawdown
status = calculate_bankroll_status(current_pnl=-1500.0, total_bankroll=10000.0)
print(f"Status: {status['status']}")
print(f"Drawdown: {status['drawdown_pct']:.2%}")
print(f"Recommendation: {status['recommendation']}")
# Output: Status: Caution
# Output: Drawdown: 15.00%
# Output: Recommendation: Reduce unit size to 0.5x multiplier

# Scenario 3: Severe drawdown
status = calculate_bankroll_status(current_pnl=-4000.0, total_bankroll=10000.0)
print(f"Status: {status['status']}")
print(f"Drawdown: {status['drawdown_pct']:.2%}")
print(f"Recommendation: {status['recommendation']}")
# Output: Status: Critical
# Output: Drawdown: 40.00%
# Output: Recommendation: Pause betting, review model accuracy
```

**Notes:**
- Status tiers: Healthy (<5% drawdown), Caution (5-15%), Warning (15-25%), Critical (>25%)
- Drawdown based on peak bankroll, not initial
- Recommendations are advisory; user makes final decision
- ROI normalized to (PnL / Initial Bankroll) for tracking over time

---

## Code Example: End-to-End Usage

```python
from betlab.bankroll_mgr import (
    get_unit_size,
    calculate_stake,
    detect_losing_streak,
    calculate_bankroll_status
)

# Initialize bankroll management for session
total_bankroll = 10000.0
unit = get_unit_size(unit_multiplier=1.0)

print(f"Bankroll: ${total_bankroll:.2f}")
print(f"Unit size: ${unit:.2f}\n")

# Process bets throughout the day
daily_staked = 0.0
bet_results = ['W', 'W', 'L', 'W']

bets_to_place = [
    {"kelly": 0.12, "confidence": "high"},
    {"kelly": 0.08, "confidence": "medium"},
    {"kelly": 0.05, "confidence": "low"},
    {"kelly": 0.15, "confidence": "high"},
]

# Place bets with proper sizing
for i, bet in enumerate(bets_to_place):
    stake = calculate_stake(
        kelly_fraction=bet['kelly'],
        confidence=bet['confidence'],
        daily_staked=daily_staked
    )
    daily_staked += stake
    print(f"Bet {i+1}: Stake ${stake:.2f}, Kelly={bet['kelly']:.1%}, Confidence={bet['confidence']}")
    print(f"  Result: {bet_results[i]}\n")

# End-of-session analysis
current_pnl = 150.0  # Up $150 after bets
remaining_bankroll = total_bankroll + current_pnl

# Check for losing streaks (need more historical data for this)
recent_results = ['W', 'W', 'L', 'W', 'L', 'L', 'W', 'L', 'L', 'L']
streak = detect_losing_streak(recent_results, window_days=7, threshold=5)
if streak:
    print("WARNING: Losing streak detected!")
    print("Recommend: Reduce unit multiplier to 0.5x for next session")
    multiplier_adjustment = 0.5
else:
    multiplier_adjustment = 1.0
    print("No losing streak. Continue with standard units.")

# Bankroll status report
status = calculate_bankroll_status(current_pnl, remaining_bankroll)
print(f"\nBankroll Status Report:")
print(f"  Status: {status['status']}")
print(f"  ROI: {status['roi']:.2%}")
print(f"  Drawdown: {status['drawdown_pct']:.2%}")
print(f"  Recommendation: {status['recommendation']}")
```

## Configuration

Key parameters for bankroll management:

```python
# Unit sizing
UNIT_BASE_PERCENTAGE = 0.01  # 1% of bankroll per unit
UNIT_MULTIPLIER_MIN = 0.1    # Absolute minimum 0.1x
UNIT_MULTIPLIER_MAX = 10.0   # Absolute maximum 10x

# Daily limits
DAILY_STAKE_LIMIT_PCT = 0.10  # 10% of bankroll per day

# Streak detection
LOSING_STREAK_WINDOW = 7      # Days to analyze
LOSING_STREAK_THRESHOLD = 5   # Losses to trigger

# Status thresholds
DRAWDOWN_HEALTHY = 0.05       # < 5%
DRAWDOWN_CAUTION = 0.15       # 5-15%
DRAWDOWN_WARNING = 0.25       # 15-25%
# > 25% = Critical

# Confidence multipliers for Kelly
CONFIDENCE_MULTIPLIERS = {
    "high": 1.00,
    "medium": 0.50,
    "low": 0.25,
}
```

## Testing

The bankroll manager module includes comprehensive tests in `tests/test_bankroll_mgr.py`:

- **test_get_unit_size**: Various multipliers, boundary cases
- **test_calculate_stake**: Confidence levels, daily caps
- **test_detect_losing_streak**: Various streak patterns, edge cases
- **test_calculate_bankroll_status**: Status classifications, recommendation accuracy
- **test_integration**: Daily workflow scenarios

Run tests with:
```bash
pytest tests/test_bankroll_mgr.py -v
```

## Integration Notes

- Works with parlay_builder to ensure combo stakes don't exceed daily limits
- Receives Kelly fractions from math_engine
- Feeds stake recommendations to output_generator for reports
- Tracks all bets for historical PnL calculation and streak detection
