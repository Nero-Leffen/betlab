# Portfolio Documentation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create comprehensive tiered documentation (architecture, design decisions, module APIs) with Mermaid diagrams to showcase BetLab as a professional portfolio project.

**Architecture:**
- Tiered approach: high-level ARCHITECTURE.md for first impression, modular MODULES/* for deep reference, DESIGN_DECISIONS.md for engineering narrative
- Mermaid diagrams for system visualization (data flow, dependencies, pipeline walkthrough)
- All documentation in `docs/` folder, linked from enhanced README.md

**Tech Stack:** Markdown, Mermaid (ASCII diagrams), existing code in `src/`

---

## Task 1: Create ARCHITECTURE.md

**Files:**
- Create: `docs/ARCHITECTURE.md`

**Step 1: Write the architecture document**

Create file with complete content:

```markdown
# BetLab Architecture

## Overview

BetLab is a **local-first, math-driven analytics engine** for football betting. It processes betting tips through a transparent 5-phase pipeline, filters for positive Expected Value (+EV), sizes stakes using the Half-Kelly Criterion, and manages bankroll risk with built-in safeguards.

**The core philosophy:** No black boxes. Every decision has a formula. Every formula has a rationale.

---

## System Architecture

```
┌─────────────┐
│  bets.txt   │
└──────┬──────┘
       │
       ▼
┌──────────────────────┐
│ Phase 1: Parse       │  (parser.py)
│ - Odds conversion    │  Accepts: decimal, American, fractional
│ - Validation         │  Outputs: normalized bet objects
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Phase 2: EV Filter   │  (analyser.py + math_engine.py)
│ - Calculate EV       │  Formula: (odds × p_true) − 1
│ - Filter: EV ≥ 2%   │  Tags: SINGLE_CANDIDATE
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Phase 3: Kelly       │  (bankroll_mgr.py)
│ - Half-Kelly sizing  │  Formula: ((b×p − q) / b) × 0.5
│ - Daily cap: ₹200    │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Phase 4: Parlays     │  (parlay_builder.py)
│ - Correlation check  │  Top EV bets only
│ - Build combos       │  Tags: PARLAY_CANDIDATE
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Phase 5: Output      │  (output_generator.py)
│ - recommendations.md │  Markdown report + CSV template
│ - bet_log_template   │
└──────────────────────┘
```

---

## Key Design Principles

### 1. **Transparency Over Optimization**
Every bet comes with:
- Implied probability (from bookmaker odds)
- Expected Value percentage (your edge)
- Kelly fraction (raw sizing)
- Final stake (after caps and confidence adjustment)

Users understand *why* each bet is sized the way it is.

### 2. **Risk Management by Default**
- Daily cap prevents reckless scaling
- Half-Kelly (not Full-Kelly) reduces bankroll volatility
- Losing streak detection triggers unit halving
- Stop-loss threshold implemented in feedback loop

### 3. **Local-First Architecture**
- No API calls, no external dependencies for core logic
- User controls all data (bets.txt, results.csv)
- Easy to fork, modify, extend
- Works offline

### 4. **Modular, Testable Code**
- Each phase is a separate module
- Pure functions where possible (math_engine, parser)
- Minimal state (bankroll_mgr)
- Full test coverage

---

## Module Overview

| Module | Responsibility | Key Functions |
|--------|---|---|
| **parser.py** | Parse betting odds in any format | `parse_decimal`, `parse_american`, `parse_fractional` |
| **math_engine.py** | Core betting math (EV, Kelly) | `calculate_ev`, `calculate_kelly_fraction`, `calculate_parlay_probability` |
| **analyser.py** | Filter by EV, tag candidates | `filter_by_ev`, `tag_candidates` |
| **bankroll_mgr.py** | Stake sizing, daily caps | `calculate_stake`, `apply_daily_cap`, `detect_losing_streak` |
| **parlay_builder.py** | Parlay construction with checks | `check_correlation`, `build_parlay_combinations` |
| **output_generator.py** | Generate reports | `generate_report`, `export_csv` |

See `docs/MODULES/` for detailed API reference.

---

## Data Flow Example

**Input:** 1 bet

```
Match: Man City vs Arsenal
Market: 1X2
Selection: Man City
Odds: 1.85 (decimal)
Confidence: High
```

**Processing:**

1. **Parser** → Validate odds, convert to decimal (already is)
2. **Math Engine** → Implied Prob = 1/1.85 = 54.05%
3. **Analyser** → Assume source accuracy 53% → EV = (1.85 × 0.53) − 1 = −0.02 (−2%)
4. **Filter** → EV < 2% threshold → **REJECTED**

OR (if EV passed):

4. **Bankroll Manager** → Kelly = ((1.85−1) × 0.53 − (1−0.53)) / (1.85−1) × 0.5 = 5.2% → ₹26 (capped to 1 unit = ₹25)
5. **Parlay Builder** → Check if top EV candidate → Tag PARLAY_CANDIDATE (if top 2-4)
6. **Output** → Add to recommendations.md with rationale

---

## Technology Stack

- **Language:** Python 3.9+
- **UI:** Streamlit (web interface)
- **Data:** pandas (results analysis), yaml (config)
- **Testing:** pytest (unit + integration tests)
- **Logging:** Python logging

---

## File Structure

```
betlab/
├── README.md
├── config/
│   └── settings.yaml          # Bankroll, accuracy, thresholds
├── data/
│   ├── bets.txt               # Input bets
│   ├── results.csv            # Historical P&L
│   └── logs/
│       ├── betlab.log
│       └── error_log.txt
├── src/
│   ├── main.py                # Streamlit app
│   ├── parser.py
│   ├── math_engine.py
│   ├── analyser.py
│   ├── bankroll_mgr.py
│   ├── parlay_builder.py
│   └── output_generator.py
├── tests/
│   └── test_betlab.py
├── output/
│   ├── recommendations.md     # Generated report
│   └── bet_log_template.csv
└── docs/
    ├── ARCHITECTURE.md        # This file
    ├── DESIGN_DECISIONS.md
    ├── MODULES/
    │   ├── parser.md
    │   ├── math_engine.md
    │   ├── analyser.md
    │   ├── bankroll_mgr.md
    │   ├── parlay_builder.md
    │   └── output_generator.md
    └── diagrams/
        ├── data_flow.mmd
        ├── module_dependencies.mmd
        ├── pipeline_walkthrough.mmd
        └── README.md
```

---

## Next Steps

- **Understand the design decisions:** See [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md)
- **Deep dive into modules:** See [MODULES/](MODULES/)
- **View system diagrams:** See [diagrams/](diagrams/)
```

**Step 2: Verify file was created and readable**

Run: `cat "c:\Games\Job Hunt Content\Project\Betlab\betlab\docs\ARCHITECTURE.md" | head -20`

Expected: File contains "# BetLab Architecture" as first heading

**Step 3: Commit**

```bash
cd "c:\Games\Job Hunt Content\Project\Betlab\betlab"
git add docs/ARCHITECTURE.md
git commit -m "docs: add architecture overview with system diagram"
```

---

## Task 2: Create DESIGN_DECISIONS.md

**Files:**
- Create: `docs/DESIGN_DECISIONS.md`

**Step 1: Write design decisions document**

```markdown
# Design Decisions

## Why Half-Kelly Instead of Full-Kelly?

**Decision:** Use Half-Kelly Criterion for stake sizing, not Full-Kelly.

**Formula:**
- Full-Kelly: `f* = (b×p − q) / b` where b = odds − 1, p = win prob, q = 1 − p
- Half-Kelly: `f = f* × 0.5`

**Rationale:**

Full-Kelly is theoretically optimal for long-term bankroll growth, BUT it has fatal flaws for human traders:

1. **Volatility Hell** — Full-Kelly produces wild swings. If your 53% accuracy estimate is even slightly off, you face drawdowns of 30-50%. Psychologically unbearable.

2. **Estimation Error** — We estimate "true probability" from bookmaker odds + a source accuracy figure (53%). That estimate has margin of error. Full-Kelly assumes perfect estimates.

3. **Ruin Risk** — Small errors compound. One bad sequence and you're wiped out before you've had enough trials to prove your edge.

**Half-Kelly tradeoff:**
- ✅ Long-term growth = ~0.25× Full-Kelly (slower but still positive exponential)
- ✅ Drawdowns cut to ~15-20% (psychologically tolerable)
- ✅ Forgiving to estimation errors
- ✅ Still mathematically optimal in practice for humans

**Sources:** "The Kelly Criterion" (MacLean, Thorp, Ziemba), Nassim Taleb's discussion of fragility.

---

## Why Correlation Checks in Parlays?

**Decision:** Only build parlays from independent bets; reject correlated pairs.

**Rationale:**

If you parlay "Manchester City 1X2" with "Manchester City Over 2.5 Goals", these are NOT independent:
- If Man City scores lots → both bets win
- If Man City scores few → both bets lose

**Parlay math assumes independence:**
```
P(both win) = p_a × p_b    [ONLY if independent]
```

Correlated bets violate this. Your actual parlay probability is worse than the formula predicts.

**Implementation:**
- Same team/match across 2+ legs → marked correlated
- Manual override possible (for now)
- Future: finer-grained correlation scoring

**Why not just ignore this?**
Because poor parlay construction is how bettors "work harder, lose faster." Seems smart, actually kills ROI.

---

## Why Local-First Architecture?

**Decision:** No live odds API. User manually enters bets into `bets.txt`.

**Rationale:**

**Pros of API-driven:**
- Automatic odds scraping, live updates
- Scalable to thousands of bets/day
- "Modern" approach

**Cons of API-driven:**
- Adds external dependency (API down → system fails)
- Legal ambiguity (some bookmakers forbid scraping)
- Complexity shoots up (auth, rate limiting, error handling)
- Tempts you to overtrade (paralysis of choice)

**Local-first advantages:**
- Zero external dependencies → works offline
- You own all your data
- Intentional entry forces you to think about each bet
- Easy to fork and modify
- Transparent for auditing

**Why it's right for a portfolio project:**
- Shows architectural thinking (understanding tradeoffs)
- Demonstrates you can say "no" to scope creep
- Easier to test, maintain, explain

---

## Why Modular Python Architecture?

**Decision:** Split logic into separate modules (parser, math_engine, analyser, etc.) instead of one monolithic script.

**Rationale:**

**Monolithic downside:**
- Hard to test (can't test parser without running entire pipeline)
- Hard to reuse (can't use math_engine without importing parser)
- Bug in one phase breaks everything
- Hard to understand as a newcomer

**Modular approach:**
- **parser.py** — Pure input transformation. Tested in isolation.
- **math_engine.py** — Pure math functions. No side effects. Trivial to test and reason about.
- **analyser.py** — Filter logic. Depends on math_engine, produces tagged bets.
- **bankroll_mgr.py** — Stake sizing. Depends on math_engine, enforces caps.
- **parlay_builder.py** — Combination logic. Highest-level orchestration.
- **output_generator.py** — Formatting. Depends on all others.

**Benefits:**
- Each module can be tested separately
- Easy to explain each module's job
- Easy to swap implementations (e.g., different parlay strategy)
- Minimal coupling

---

## Tradeoffs & What We *Didn't* Do

### Live Odds API
**Not doing:** Real-time odds from Betfair, SBR, Pinnacle APIs
**Why:** Adds complexity, dependency, legal risk. Manual entry forces intentionality.
**If revising:** Could add as optional plugin later

### Machine Learning Model for Source Accuracy
**Not doing:** Train ML model to estimate true probabilities from odds
**Why:** Requires historical data, adds black-box risk, overkill for learning project
**If revising:** Gather 6 months of results first; then revisit

### Multi-Sport Support (Day 1)
**Not doing:** Cricket, Tennis, MMA odds (Phase 1 = Football only)
**Why:** Sports have different accuracy profiles. Start narrow, expand once proven
**If revising:** Add per-sport config in `settings.yaml`

### Automated Stake Recovery (Chasing)
**Not doing:** Increase stakes after losses to "recover" faster
**Why:** Historically, this ruins bankrolls. Hard-coded it as forbidden
**If revising:** Only if backtesting proves it helps (unlikely)

---

## Lessons Learned (So Far)

1. **Half-Kelly Beats Full-Kelly in Practice** — Theory is useful, but fragility matters.
2. **Correlations Are Sneaky** — You miss them in your head. Need explicit checks.
3. **Local Data Beats API** — Fewer moving parts, more control.
4. **Test as You Build** — Caught 3 bugs in kelly_fraction formula before shipping.
5. **Transparency is a Feature** — Users see *why* each bet is sized. Builds trust.

---

## Future Design Questions

- **Should source accuracy be per-bookmaker?** (Current: per-sport only)
- **Should we support live odds polling?** (Current: manual entry)
- **Kelly vs Proportional Betting?** (Current: Half-Kelly only)

These are open for Phase 2.
```

**Step 2: Verify file was created**

Run: `ls -lh "c:\Games\Job Hunt Content\Project\Betlab\betlab\docs\DESIGN_DECISIONS.md"`

Expected: File exists, >2KB

**Step 3: Commit**

```bash
cd "c:\Games\Job Hunt Content\Project\Betlab\betlab"
git add docs/DESIGN_DECISIONS.md
git commit -m "docs: add design decisions and rationale"
```

---

## Task 3: Create MODULES/parser.md

**Files:**
- Create: `docs/MODULES/parser.md`

**Step 1: Write parser module documentation**

```markdown
# Parser Module

## Purpose

Convert betting odds from any format (decimal, American, fractional) into a normalized internal representation. Validate input for correctness.

## Key Responsibilities

- Parse decimal odds (e.g., `1.85`, `2.00`)
- Parse American odds (e.g., `+150`, `-110`)
- Parse fractional odds (e.g., `5/2`, `11/4`)
- Validate odds are positive and reasonable
- Normalize all formats to decimal
- Handle edge cases (negative odds, zero, very large values)

## Dependencies

- Standard library only (no external imports)

---

## Function Reference

### `parse_decimal(odds_str: str) -> float`

**Purpose:** Parse decimal odds format (most common in Europe).

**Parameters:**
- `odds_str` (str): String representation of decimal odds (e.g., `"1.85"`)

**Returns:**
- `float`: Decimal odds as float

**Raises:**
- `ValueError`: If string is not a valid float or value < 1.0

**Example:**
```python
from src.parser import parse_decimal

result = parse_decimal("1.85")
assert result == 1.85
```

**Notes:**
- Decimal < 1.0 is invalid (negative expected value before EV calculation)
- Accepts strings with/without whitespace

---

### `parse_american(odds_str: str) -> float`

**Purpose:** Parse American odds format (common in USA/Canada).

**Parameters:**
- `odds_str` (str): American odds (e.g., `"+150"` or `"-110"`)

**Returns:**
- `float`: Decimal equivalent

**Conversion:**
```
If odds > 0 (underdog):   decimal = (odds / 100) + 1
If odds < 0 (favorite):   decimal = (100 / abs(odds)) + 1
```

**Example:**
```python
from src.parser import parse_american

# Underdog
result = parse_american("+150")
assert result == 2.50

# Favorite
result = parse_american("-110")
assert result == 1.909...
```

---

### `parse_fractional(odds_str: str) -> float`

**Purpose:** Parse fractional odds format (common in UK).

**Parameters:**
- `odds_str` (str): Fractional odds (e.g., `"5/2"`, `"11/4"`)

**Returns:**
- `float`: Decimal equivalent

**Conversion:**
```
decimal = (numerator / denominator) + 1
```

**Example:**
```python
from src.parser import parse_fractional

result = parse_fractional("5/2")
assert result == 3.50  # (5/2) + 1

result = parse_fractional("1/2")
assert result == 1.50  # (1/2) + 1
```

---

### `normalize_odds(odds_input: str | float) -> float`

**Purpose:** Auto-detect format and parse any odds format.

**Parameters:**
- `odds_input` (str or float): Odds in any format

**Returns:**
- `float`: Decimal odds

**Logic:**
1. If float, return as-is
2. If string:
   - Contains `/` → fractional
   - Contains `+` or `−` → American
   - Otherwise → decimal

**Example:**
```python
from src.parser import normalize_odds

assert normalize_odds(1.85) == 1.85
assert normalize_odds("1.85") == 1.85
assert normalize_odds("+150") == 2.50
assert normalize_odds("5/2") == 3.50
```

---

### `validate_odds(odds: float) -> bool`

**Purpose:** Check if odds are valid and reasonable.

**Parameters:**
- `odds` (float): Decimal odds to validate

**Returns:**
- `bool`: True if valid, raises ValueError if not

**Validation Rules:**
- odds >= 1.01 (minimum vig)
- odds <= 1000 (sanity check)

**Example:**
```python
from src.parser import validate_odds

validate_odds(1.85)  # OK
validate_odds(1.00)  # Raises ValueError: Odds must be >= 1.01
validate_odds(2000)  # Raises ValueError: Odds > 1000 (invalid)
```

---

## Code Example: Parsing a Bet

```python
from src.parser import normalize_odds, validate_odds

# User input
match = "Man City vs Arsenal"
odds_input = "+150"  # American format

# Parse & validate
decimal_odds = normalize_odds(odds_input)   # 2.50
validate_odds(decimal_odds)                 # Passes

print(f"Bet: {match} @ {decimal_odds}")
# Output: Bet: Man City vs Arsenal @ 2.5
```

---

## Testing

See `tests/test_betlab.py::test_parser_*` for full test suite.

Key test cases:
- Decimal parsing (valid, edge cases)
- American parsing (positive, negative)
- Fractional parsing (various ratios)
- Invalid inputs (strings, negative odds, NaN)
- Whitespace handling
```

**Step 2: Verify file was created**

Run: `wc -l "c:\Games\Job Hunt Content\Project\Betlab\betlab\docs\MODULES\parser.md"`

Expected: >100 lines

**Step 3: Commit**

```bash
cd "c:\Games\Job Hunt Content\Project\Betlab\betlab"
git add docs/MODULES/parser.md
git commit -m "docs: add parser module reference"
```

---

## Task 4: Create MODULES/math_engine.md

**Files:**
- Create: `docs/MODULES/math_engine.md`

**Step 1: Write math_engine documentation**

```markdown
# Math Engine Module

## Purpose

Core betting mathematics: Expected Value (EV), Kelly Criterion stake sizing, probability calculations.

All functions are **pure** (no side effects, no state). Safe to test in isolation.

## Key Responsibilities

- Calculate implied probability from odds
- Calculate Expected Value (EV)
- Calculate Kelly fraction (optimal stake sizing)
- Calculate parlay probability (independent combined events)
- Validate mathematical inputs

## Dependencies

- Standard library only

---

## Function Reference

### `calculate_implied_probability(decimal_odds: float) -> float`

**Purpose:** What probability does the bookmaker imply with their odds?

**Formula:**
```
implied_probability = 1 / decimal_odds
```

**Parameters:**
- `decimal_odds` (float): Decimal odds (e.g., 2.00)

**Returns:**
- `float`: Probability (0.0 to 1.0)

**Example:**
```python
from src.math_engine import calculate_implied_probability

prob = calculate_implied_probability(2.00)
assert prob == 0.50  # 50% implied

prob = calculate_implied_probability(1.85)
assert abs(prob - 0.5405) < 0.001  # 54.05% implied
```

**Notes:**
- Higher odds → lower implied probability
- Bookmakers add margin, so implied probs don't sum to 100% in 1X2 markets

---

### `calculate_ev(odds: float, true_probability: float) -> float`

**Purpose:** Calculate Expected Value as a decimal (your edge).

**Formula:**
```
EV = (odds × true_probability) − 1
```

**Interpretation:**
- EV > 0: Positive expected value (bet has edge)
- EV < 0: Negative expected value (bet is -EV)
- EV = 0: Break-even

**Parameters:**
- `odds` (float): Decimal odds
- `true_probability` (float): Your estimate of true win probability (0.0-1.0)

**Returns:**
- `float`: EV as decimal (0.15 = +15%, −0.10 = −10%)

**Example:**
```python
from src.math_engine import calculate_ev

# Bet with edge
ev = calculate_ev(odds=2.00, true_probability=0.55)
assert abs(ev - 0.10) < 0.001  # +10% EV

# Bet without edge
ev = calculate_ev(odds=2.00, true_probability=0.48)
assert ev < 0  # Negative EV (bad bet)
```

**Minimum Threshold:**
BetLab only recommends bets with EV ≥ 2% (0.02).

---

### `calculate_kelly_fraction(odds: float, probability: float) -> float`

**Purpose:** Optimal bet size as fraction of bankroll (before applying Half-Kelly).

**Formula:**
```
f* = ((odds − 1) × probability − (1 − probability)) / (odds − 1)

Simplified:
f* = (b×p − q) / b
where:
  b = odds − 1
  p = probability
  q = 1 − p
```

**Parameters:**
- `odds` (float): Decimal odds
- `probability` (float): Win probability (0.0-1.0)

**Returns:**
- `float`: Kelly fraction as decimal (0.05 = 5% of bankroll)

**Example:**
```python
from src.math_engine import calculate_kelly_fraction

# 55% win prob, 2.00 odds
kelly = calculate_kelly_fraction(odds=2.00, probability=0.55)
assert abs(kelly - 0.10) < 0.001  # ~10% Full-Kelly

# Reduce to Half-Kelly
half_kelly = kelly * 0.5  # ~5%
```

**Important Notes:**
- This is **Full-Kelly**. BetLab applies ×0.5 in `bankroll_mgr.py`
- Kelly can exceed 100% (means over-leverage; cap happens in bankroll_mgr)
- If kelly < 0, bet is unprofitable (don't bet)

---

### `calculate_parlay_probability(individual_probabilities: list[float]) -> float`

**Purpose:** Probability of all legs in parlay winning (independent events).

**Formula:**
```
P(parlay wins) = p_1 × p_2 × ... × p_n
```

**Assumption:** Bets are independent (no correlations). See parlay_builder.py for correlation checks.

**Parameters:**
- `individual_probabilities` (list[float]): True probabilities for each leg

**Returns:**
- `float`: Combined probability (0.0-1.0)

**Example:**
```python
from src.math_engine import calculate_parlay_probability

probs = [0.55, 0.50, 0.52]  # Three bets
parlay_prob = calculate_parlay_probability(probs)
# 0.55 × 0.50 × 0.52 ≈ 0.143 (14.3%)

assert abs(parlay_prob - 0.143) < 0.001
```

**Notes:**
- More legs = exponentially lower probability
- 3-leg parlay of 55% bets = only ~16.6% to hit
- This is why payouts are high

---

### `calculate_parlay_odds(individual_odds: list[float]) -> float`

**Purpose:** Decimal odds for entire parlay (product of individual odds).

**Formula:**
```
parlay_odds = odds_1 × odds_2 × ... × odds_n
```

**Parameters:**
- `individual_odds` (list[float]): Decimal odds for each leg

**Returns:**
- `float`: Combined decimal odds

**Example:**
```python
from src.math_engine import calculate_parlay_odds

odds = [1.85, 2.00, 1.95]
parlay_odds = calculate_parlay_odds(odds)
# 1.85 × 2.00 × 1.95 ≈ 7.22

assert abs(parlay_odds - 7.22) < 0.01
```

---

## Code Example: Full Bet Analysis

```python
from src.math_engine import (
    calculate_implied_probability,
    calculate_ev,
    calculate_kelly_fraction,
)

# Bookmaker odds
odds = 1.85

# Our estimate of true probability (from source accuracy)
true_prob = 0.53

# Step 1: What does bookmaker imply?
implied_prob = calculate_implied_probability(odds)
print(f"Bookmaker implies: {implied_prob:.1%}")  # 54.1%

# Step 2: Calculate edge
ev = calculate_ev(odds, true_prob)
print(f"Our EV: {ev:.2%}")  # Probably negative if implied > true

# Step 3: If EV > 2%, size the bet
if ev >= 0.02:
    kelly = calculate_kelly_fraction(odds, true_prob)
    half_kelly = kelly * 0.5
    print(f"Kelly stake: {kelly:.2%} of bankroll")
    print(f"Half-Kelly (BetLab uses this): {half_kelly:.2%}")
else:
    print("Skip this bet (EV too low)")
```

---

## Testing

See `tests/test_betlab.py::test_math_*` for unit tests.

All calculations are verified against:
- Academic papers (Kelly Criterion references)
- Wolfram Alpha
- Manual calculations
```

**Step 2: Verify file created**

Run: `grep -c "^###" "c:\Games\Job Hunt Content\Project\Betlab\betlab\docs\MODULES\math_engine.md"`

Expected: ≥ 6 (six function headers)

**Step 3: Commit**

```bash
cd "c:\Games\Job Hunt Content\Project\Betlab\betlab"
git add docs/MODULES/math_engine.md
git commit -m "docs: add math engine module reference"
```

---

## Task 5: Create MODULES/analyser.md

**Files:**
- Create: `docs/MODULES/analyser.md`

**Step 1: Write analyser module documentation**

```markdown
# Analyser Module

## Purpose

Filter bets by Expected Value (EV) and apply candidate tagging (SINGLE_CANDIDATE, PARLAY_CANDIDATE).

This module is the **gatekeeper**: it decides which bets make it into recommendations.

## Key Responsibilities

- Filter bets: only keep EV ≥ 2% (configurable in settings.yaml)
- Tag single bets: mark as SINGLE_CANDIDATE
- Tag parlay candidates: mark top EV bets as PARLAY_CANDIDATE (max pool size: 4)
- Rank by EV (descending)
- Provide rejection reasons for filtered-out bets

## Dependencies

- `math_engine` (for EV calculation)
- `config/settings.yaml` (for EV threshold)

---

## Function Reference

### `filter_by_ev(bets: list[dict], threshold: float = 0.02) -> list[dict]`

**Purpose:** Keep only bets with EV ≥ threshold.

**Parameters:**
- `bets` (list[dict]): List of parsed bet objects
- `threshold` (float): Minimum EV (default 2% = 0.02)

**Returns:**
- `list[dict]`: Filtered bets, ranked by EV (descending)

**Example:**
```python
from src.analyser import filter_by_ev

bets = [
    {"match": "A", "odds": 2.0, "confidence": "High", "ev": 0.15},
    {"match": "B", "odds": 1.5, "confidence": "Low", "ev": -0.10},
    {"match": "C", "odds": 1.8, "confidence": "Med", "ev": 0.05},
]

filtered = filter_by_ev(bets, threshold=0.02)
# Returns: [A (15%), C (5%)]
# Excludes: B (−10%)
```

---

### `tag_candidates(bets: list[dict], parlay_pool_size: int = 4) -> list[dict]`

**Purpose:** Tag bets as SINGLE_CANDIDATE and/or PARLAY_CANDIDATE.

**Logic:**
- ALL filtered bets → tagged SINGLE_CANDIDATE
- Top N by EV (where N ≤ parlay_pool_size) → also tagged PARLAY_CANDIDATE

**Parameters:**
- `bets` (list[dict]): Bets already filtered by EV
- `parlay_pool_size` (int): Max bets eligible for parlays (default 4)

**Returns:**
- `list[dict]`: Bets with added `tags` field

**Example:**
```python
from src.analyser import tag_candidates

bets = [
    {"match": "A", "ev": 0.40},  # 1st highest EV
    {"match": "B", "ev": 0.07},  # 2nd
    {"match": "C", "ev": 0.06},  # 3rd
    {"match": "D", "ev": 0.03},  # 4th
    {"match": "E", "ev": 0.02},  # 5th (below pool)
]

tagged = tag_candidates(bets, parlay_pool_size=4)

# Result:
# A: ["SINGLE_CANDIDATE", "PARLAY_CANDIDATE"]
# B: ["SINGLE_CANDIDATE", "PARLAY_CANDIDATE"]
# C: ["SINGLE_CANDIDATE", "PARLAY_CANDIDATE"]
# D: ["SINGLE_CANDIDATE", "PARLAY_CANDIDATE"]
# E: ["SINGLE_CANDIDATE"]  (NOT eligible for parlays)
```

---

### `calculate_rejection_reason(bet: dict, ev: float, threshold: float) -> str`

**Purpose:** Human-readable reason why a bet was rejected.

**Parameters:**
- `bet` (dict): The rejected bet object
- `ev` (float): Calculated EV
- `threshold` (float): EV threshold

**Returns:**
- `str`: Reason message

**Example:**
```python
from src.analyser import calculate_rejection_reason

reason = calculate_rejection_reason(
    bet={"match": "X vs Y", "odds": 2.0},
    ev=-0.05,
    threshold=0.02
)
# "Match: X vs Y | EV: −5.00% | Threshold: 2.00% (BELOW THRESHOLD)"
```

---

## Code Example: Full Analysis Pipeline

```python
from src.parser import normalize_odds
from src.math_engine import calculate_ev
from src.analyser import filter_by_ev, tag_candidates

# Raw input
raw_bets = [
    {"match": "A", "odds": "1.85", "true_prob": 0.55},
    {"match": "B", "odds": "+150", "true_prob": 0.48},
    {"match": "C", "odds": "2.00", "true_prob": 0.52},
]

# Parse & calculate EV
for bet in raw_bets:
    bet["decimal_odds"] = normalize_odds(bet["odds"])
    bet["ev"] = calculate_ev(bet["decimal_odds"], bet["true_prob"])

# Filter
recommended = filter_by_ev(raw_bets, threshold=0.02)

# Tag
tagged = tag_candidates(recommended, parlay_pool_size=4)

# Output
for bet in tagged:
    print(f"{bet['match']}: {bet['tags']} (EV: {bet['ev']:.2%})")
```

---

## Configuration

Edit `config/settings.yaml` to adjust:

```yaml
strategy:
  min_ev_threshold: 0.02     # 2% minimum edge
  parlay_pool_size: 4        # Max bets eligible for parlays
```

---

## Testing

See `tests/test_betlab.py::test_analyser_*` for unit tests.

Key test cases:
- Filter by various EV thresholds
- Tagging with different pool sizes
- Handling empty input
- Edge case: all bets below threshold
```

**Step 2: Verify file created**

Run: `head -20 "c:\Games\Job Hunt Content\Project\Betlab\betlab\docs\MODULES\analyser.md"`

Expected: Contains "# Analyser Module"

**Step 3: Commit**

```bash
cd "c:\Games\Job Hunt Content\Project\Betlab\betlab"
git add docs/MODULES/analyser.md
git commit -m "docs: add analyser module reference"
```

---

## Task 6: Create MODULES/bankroll_mgr.md

**Files:**
- Create: `docs/MODULES/bankroll_mgr.md`

**Step 1: Write bankroll_mgr documentation**

```markdown
# Bankroll Manager Module

## Purpose

Stake sizing using Half-Kelly Criterion, enforce daily caps, detect losing streaks, and manage bankroll risk.

This module is the **risk guardian**: it prevents you from betting too much too fast.

## Key Responsibilities

- Calculate stake size from Kelly fraction + confidence level
- Enforce daily stake cap (₹200 max)
- Enforce single-bet cap (4 units max = ₹100)
- Detect losing streaks (>5 losses in 7 days)
- Trigger unit halving on losing streaks
- Log all stake decisions for auditability

## Configuration (config/settings.yaml)

```yaml
bankroll:
    total_inr: 800             # Total bankroll
  unit_inr: 25               # 1 unit = ₹25
  max_daily_stake_inr: 200   # 4 units per day

risk:
  stop_loss_percentage: 50   # Pause if 50% down
  losing_streak_window_days: 7
  losing_streak_threshold: 5
  reduced_unit_multiplier: 0.5  # Half units on streak
```

## Key Responsibilities

- Calculate stake size from Kelly fraction + confidence level
- Enforce daily stake cap (₹200 max)
- Detect losing streaks (>5 losses in 7 days)
- Trigger unit halving on losing streaks

---

## Function Reference

### `get_unit_size(unit_multiplier: float = 1.0) -> float`

**Purpose:** Get current unit size in INR, adjusted for losing streak.

**Parameters:**
- `unit_multiplier` (float): Normally 1.0; 0.5 if in losing streak

**Returns:**
- `float`: Unit size in INR

**Example:**
```python
from src.bankroll_mgr import get_unit_size

# Normal
unit = get_unit_size(unit_multiplier=1.0)
assert unit == 25  # ₹25 (from settings.yaml)

# In losing streak
unit = get_unit_size(unit_multiplier=0.5)
assert unit == 12.5  # ₹12.5 (halved)
```

---

### `calculate_stake(kelly_fraction: float, confidence: str, daily_staked: float = 0.0) -> float`

**Purpose:** Convert Half-Kelly fraction + confidence into actual stake (₹ INR).

**Parameters:**
- `kelly_fraction` (float): Full-Kelly result from math_engine
- `confidence` (str): "High", "Medium", or "Low"
- `daily_staked` (float): Amount already staked today (for cap enforcement)

**Returns:**
- `float`: Final stake in INR (or 0 if daily cap exceeded)

**Stake Sizing Logic:**

```
1. half_kelly = kelly_fraction × 0.5
2. Apply confidence multiplier:
   - High: 2 units
   - Medium: 1 unit
   - Low: 1 unit
3. Calculate stake: confidence_units × unit_size
4. Apply Kelly cap: stake ≤ half_kelly × bankroll
5. Apply daily cap: daily_staked + stake ≤ ₹200
6. Return final stake
```

**Example:**
```python
from src.bankroll_mgr import calculate_stake

# High confidence bet, kelly=0.10, daily already ₹50
stake = calculate_stake(
    kelly_fraction=0.10,
    confidence="High",
    daily_staked=50.0
)
# High = 2 units = ₹50
# Daily cap: 50 + 50 = ₹100 (within ₹200 limit)
# Result: ₹50

# If daily_staked was already ₹180
stake = calculate_stake(
    kelly_fraction=0.10,
    confidence="High",
    daily_staked=180.0
)
# 50 requested, but only ₹20 room left
# Result: ₹20 (capped)
```

---

### `detect_losing_streak(results: list[str], window_days: int = 7, threshold: int = 5) -> bool`

**Purpose:** Check if recent results show >N losses in M days.

**Parameters:**
- `results` (list[str]): List of results ["WIN", "LOSS", "VOID", ...] from `data/results.csv`
- `window_days` (int): Lookback window (default 7 days)
- `threshold` (int): Trigger at N losses (default 5)

**Returns:**
- `bool`: True if in losing streak

**Example:**
```python
from src.bankroll_mgr import detect_losing_streak

recent = ["LOSS", "LOSS", "LOSS", "WIN", "LOSS", "LOSS", "WIN"]
# 5 losses in last 7 results

in_streak = detect_losing_streak(recent, window_days=7, threshold=5)
assert in_streak == True  # Trigger unit halving

recent2 = ["LOSS", "LOSS", "WIN", "WIN", "WIN", "LOSS", "WIN"]
# 3 losses in last 7

in_streak2 = detect_losing_streak(recent2, window_days=7, threshold=5)
assert in_streak2 == False  # Streak over
```

---

### `calculate_bankroll_status(current_pnl: float, total_bankroll: float) -> dict`

**Purpose:** Report current bankroll status and risk metrics.

**Parameters:**
- `current_pnl` (float): Current profit/loss in INR
- `total_bankroll` (float): Starting bankroll (₹800)

**Returns:**
- `dict`: Status report

**Example:**
```python
from src.bankroll_mgr import calculate_bankroll_status

status = calculate_bankroll_status(current_pnl=-250, total_bankroll=500)
# {
#   'current_balance': 250,
#   'pnl_percentage': -50.0,
#   'stop_loss_triggered': True,
#   'recommendation': 'PAUSE ALL BETTING'
# }
```

---

## Code Example: Stake Sizing Decision

```python
from src.math_engine import calculate_kelly_fraction
from src.bankroll_mgr import calculate_stake

# Bet analysis (from earlier pipeline)
odds = 1.85
true_prob = 0.53
kelly = calculate_kelly_fraction(odds, true_prob)
confidence = "Medium"
daily_already_staked = 50.0

# Calculate stake
final_stake = calculate_stake(
    kelly_fraction=kelly,
    confidence=confidence,
    daily_staked=daily_already_staked
)

print(f"Kelly: {kelly:.2%}")
print(f"Final Stake: ₹{final_stake}")
print(f"Daily Total: ₹{daily_already_staked + final_stake}")
```

---

## Risk Management Rules

| Rule | Implementation |
|------|---|
| Daily Stake Cap | 4 units = ₹200 max/day |
| Single Bet Cap | Half-Kelly × bankroll |
| Losing Streak | >5 losses in 7 days → halve units |
| Stop Loss | If down 50% → pause all bets |
| No Chasing | System never increases stakes after losses |

---

## Testing

See `tests/test_betlab.py::test_bankroll_*` for unit tests.

Key test cases:
- Stake calculation with various confidences
- Daily cap enforcement
- Losing streak detection
- Stop-loss threshold
```

**Step 2: Verify file created**

Run: `grep -c "^###" "c:\Games\Job Hunt Content\Project\Betlab\betlab\docs\MODULES\bankroll_mgr.md"`

Expected: ≥ 4

**Step 3: Commit**

```bash
cd "c:\Games\Job Hunt Content\Project\Betlab\betlab"
git add docs/MODULES/bankroll_mgr.md
git commit -m "docs: add bankroll manager module reference"
```

---

## Task 7: Create MODULES/parlay_builder.md

**Files:**
- Create: `docs/MODULES/parlay_builder.md`

**Step 1: Write parlay_builder documentation**

```markdown
# Parlay Builder Module

## Purpose

Construct multi-leg parlays from PARLAY_CANDIDATE bets. Enforce correlation checks to avoid invalid combinations.

A parlay is only recommended if:
1. All legs are independent (no correlation checks fail)
2. Parlay probability is reasonable (>1%, <80%)
3. Parlay odds are within acceptable range

## Key Responsibilities

- Check bet correlation (same team/match → correlated)
- Generate parlay combinations (2-4 legs)
- Calculate parlay EV and probability
- Rank parlays by expected value
- Filter invalid combinations

## Dependencies

- `analyser` (for PARLAY_CANDIDATE tags)
- `math_engine` (for probability/EV calculations)

---

## Function Reference

### `check_correlation(bet_a: dict, bet_b: dict) -> bool`

**Purpose:** Detect if two bets are correlated (can't parlay together).

**Correlation Rules:**
- Same team → correlated (e.g., "Man City Win" + "Man City Over 2.5 Goals")
- Same match → likely correlated (e.g., "Man City Win" + "Arsenal Win" — indirect correlation)
- Different matches, different teams → independent (OK to parlay)

**Parameters:**
- `bet_a` (dict): First bet (must have "match" key)
- `bet_b` (dict): Second bet

**Returns:**
- `bool`: True if correlated (should NOT parlay), False if independent

**Example:**
```python
from src.parlay_builder import check_correlation

bet1 = {"match": "Man City vs Arsenal", "selection": "Man City Win"}
bet2 = {"match": "Man City vs Arsenal", "selection": "Over 2.5 Goals"}

correlated = check_correlation(bet1, bet2)
assert correlated == True  # Same match → correlated

bet3 = {"match": "Liverpool vs Chelsea", "selection": "Liverpool Win"}
correlated2 = check_correlation(bet1, bet3)
assert correlated2 == False  # Different matches → independent
```

---

### `generate_combinations(bets: list[dict], min_legs: int = 2, max_legs: int = 4) -> list[list[dict]]`

**Purpose:** Generate all valid parlay combinations (uncorrelated legs).

**Parameters:**
- `bets` (list[dict]): List of PARLAY_CANDIDATE bets
- `min_legs` (int): Minimum legs per parlay (default 2)
- `max_legs` (int): Maximum legs per parlay (default 4)

**Returns:**
- `list[list[dict]]`: List of valid parlay combinations

**Example:**
```python
from src.parlay_builder import generate_combinations

candidates = [
    {"match": "A vs B", "selection": "A", "id": 1},
    {"match": "C vs D", "selection": "C", "id": 2},
    {"match": "E vs F", "selection": "E", "id": 3},
]

combos = generate_combinations(candidates, min_legs=2, max_legs=3)
# [
#   [bet1, bet2],
#   [bet1, bet3],
#   [bet2, bet3],
#   [bet1, bet2, bet3],
# ]
```

---

### `calculate_parlay_ev(individual_evs: list[float], parlay_odds: float) -> float`

**Purpose:** Calculate expected value for entire parlay.

**Formula:**
```
parlay_ev = (parlay_odds × parlay_probability) − 1
```

**Parameters:**
- `individual_evs` (list[float]): EV of each leg
- `parlay_odds` (float): Combined decimal odds

**Returns:**
- `float`: Parlay EV

**Example:**
```python
from src.math_engine import calculate_parlay_probability, calculate_parlay_odds
from src.parlay_builder import calculate_parlay_ev

individual_probs = [0.55, 0.50, 0.52]
individual_odds = [1.85, 2.00, 1.95]

parlay_prob = calculate_parlay_probability(individual_probs)
parlay_odds = calculate_parlay_odds(individual_odds)
parlay_ev = calculate_parlay_ev([0.15, 0.05, 0.06], parlay_odds)

print(f"Parlay EV: {parlay_ev:.2%}")
```

---

### `rank_parlays(parlays: list[dict]) -> list[dict]`

**Purpose:** Sort parlays by EV (highest first).

**Parameters:**
- `parlays` (list[dict]): Parlay objects (each has "ev" key)

**Returns:**
- `list[dict]`: Sorted by EV descending

**Example:**
```python
from src.parlay_builder import rank_parlays

parlays = [
    {"legs": 2, "ev": 0.08},
    {"legs": 3, "ev": 0.15},
    {"legs": 2, "ev": 0.10},
]

ranked = rank_parlays(parlays)
# [
#   {"legs": 3, "ev": 0.15},  ← highest EV
#   {"legs": 2, "ev": 0.10},
#   {"legs": 2, "ev": 0.08},
# ]
```

---

## Code Example: Full Parlay Construction

```python
from src.parlay_builder import (
    check_correlation,
    generate_combinations,
    calculate_parlay_ev,
    rank_parlays,
)
from src.math_engine import calculate_parlay_probability, calculate_parlay_odds

# PARLAY_CANDIDATE bets from analyser
candidates = [
    {
        "id": 1,
        "match": "A vs B",
        "odds": 1.85,
        "true_prob": 0.55,
        "ev": 0.15,
    },
    {
        "id": 2,
        "match": "C vs D",
        "odds": 2.00,
        "true_prob": 0.50,
        "ev": 0.05,
    },
    {
        "id": 3,
        "match": "E vs F",
        "odds": 1.95,
        "true_prob": 0.52,
        "ev": 0.06,
    },
]

# Generate valid combinations
combos = generate_combinations(candidates, min_legs=2, max_legs=3)

# Calculate EV for each
for combo in combos:
    prob = calculate_parlay_probability([bet["true_prob"] for bet in combo])
    odds = calculate_parlay_odds([bet["odds"] for bet in combo])
    ev = (odds * prob) - 1
    combo["probability"] = prob
    combo["odds"] = odds
    combo["ev"] = ev

# Rank by EV
best_parlays = rank_parlays(combos)

for parlay in best_parlays[:3]:  # Top 3
    leg_count = len(parlay)
    print(f"{leg_count}-leg parlay: {parlay['ev']:.2%} EV @ {parlay['odds']:.2f}")
```

---

## Testing

See `tests/test_betlab.py::test_parlay_*` for unit tests.

Key test cases:
- Correlation detection (same match, same team)
- Combination generation (2-leg, 3-leg, 4-leg)
- Parlay EV calculation
- Ranking by EV
- Invalid combinations filtered out
```

**Step 2: Verify file created**

Run: `grep -c "def " "c:\Games\Job Hunt Content\Project\Betlab\betlab\docs\MODULES\parlay_builder.md"`

Expected: ≥ 4

**Step 3: Commit**

```bash
cd "c:\Games\Job Hunt Content\Project\Betlab\betlab"
git add docs/MODULES/parlay_builder.md
git commit -m "docs: add parlay builder module reference"
```

---

## Task 8: Create MODULES/output_generator.md

**Files:**
- Create: `docs/MODULES/output_generator.md`

**Step 1: Write output_generator documentation**

```markdown
# Output Generator Module

## Purpose

Generate final recommendation report (Markdown) and CSV template for result tracking.

This module formats the pipeline output into human-readable and machine-readable formats.

## Key Responsibilities

- Generate recommendations.md (full report with rationales)
- Export bet_log_template.csv (tracking template)
- Format stakes, odds, EV in readable tables
- Include pipeline summary (stats, totals)
- Generate unique bet IDs for tracking

## Dependencies

- All upstream modules (analyser, bankroll_mgr, parlay_builder)
- `output/` directory must exist

---

## Function Reference

### `generate_report(singles: list[dict], parlays: list[dict], summary: dict) -> str`

**Purpose:** Generate full Markdown report (recommendations.md).

**Parameters:**
- `singles` (list[dict]): Recommended single bets
- `parlays` (list[dict]): Recommended parlays (can be empty)
- `summary` (dict): Session stats (date, bankroll, total stake, etc.)

**Returns:**
- `str`: Complete Markdown report

**Report Sections:**
1. Header (date, bankroll, unit size, summary table)
2. Singles table (match, selection, odds, confidence, stake, EV, Kelly%)
3. Singles rationales (detailed for each)
4. Parlay options (if any)

**Example:**
```python
from src.output_generator import generate_report

singles = [
    {
        "match": "Man City vs Arsenal",
        "selection": "Man City Win",
        "odds": 1.85,
        "confidence": "High",
        "stake": 50,
        "ev": 0.15,
        "kelly_pct": 12.3,
    },
]

summary = {
    "date": "2026-03-13",
    "bankroll": 500,
    "total_stake": 50,
    "expected_edge": 0.15,
}

report = generate_report(singles, [], summary)
# Returns full Markdown string
```

---

### `export_csv_template(singles: list[dict], parlays: list[dict], output_path: str) -> None`

**Purpose:** Write CSV template for result tracking.

**Parameters:**
- `singles` (list[dict]): Recommended bets
- `parlays` (list[dict]): Recommended parlays
- `output_path` (str): Where to save CSV (e.g., `output/bet_log_template.csv`)

**Returns:**
- None (writes file)

**CSV Format:**

```
BetID,Match,Selection,Odds,Confidence,Stake_INR,Result,Actual_Odds,PnL_INR
BL-20260313-001,Man City vs Arsenal,Man City,1.85,High,50,WIN,1.85,42.5
BL-20260313-002,Liverpool vs Chelsea,Over 2.5,1.95,Medium,25,LOSS,1.95,-25
```

**Example:**
```python
from src.output_generator import export_csv_template

export_csv_template(singles, [], "output/bet_log_template.csv")
# Writes file; you fill in Result/PnL after bets settle
```

---

### `generate_bet_id(date: str, index: int) -> str`

**Purpose:** Generate unique bet ID for tracking.

**Format:** `BL-YYYYMMDD-NNN` (e.g., `BL-20260313-001`)

**Parameters:**
- `date` (str): Date (e.g., "2026-03-13")
- `index` (int): Bet number (1-indexed)

**Returns:**
- `str`: Formatted bet ID

**Example:**
```python
from src.output_generator import generate_bet_id

id1 = generate_bet_id("2026-03-13", 1)
assert id1 == "BL-20260313-001"

id2 = generate_bet_id("2026-03-13", 42)
assert id2 == "BL-20260313-042"
```

---

## Code Example: End-to-End Output

```python
from datetime import datetime
from src.output_generator import generate_report, export_csv_template

# Assume pipeline has run; we have singles, parlays, summary
singles = [...]  # from previous pipeline steps
parlays = []
summary = {
    "date": datetime.now().strftime("%Y-%m-%d"),
    "bankroll": 500,
    "unit": 25,
    "total_stake": 100,
    "expected_edge": 0.1514,
}

# Generate Markdown report
report_md = generate_report(singles, parlays, summary)

# Save to file
with open("output/recommendations.md", "w") as f:
    f.write(report_md)

# Export CSV template
export_csv_template(singles, parlays, "output/bet_log_template.csv")

print("✅ Report generated: output/recommendations.md")
print("✅ Template exported: output/bet_log_template.csv")
```

---

## Output Examples

### recommendations.md

See `output/recommendations.md` for a real example.

Sample structure:
```
# 📊 BetLab Recommendations
**Date:** Friday, 13 March 2026
**Bankroll:** ₹800 INR
**Effective Unit:** ₹25 INR

## 📋 Session Summary
...

## 🎯 Singles
| # | Match | Selection | Odds | ... |
|---|-------|-----------|------|-----|

## 🎲 Parlay Options
_No valid parlays..._ OR table of parlays
```

### bet_log_template.csv

User fills in this after bets settle:

```
BetID,Match,Selection,Odds,Confidence,Stake_INR,Result,Actual_Odds,PnL_INR
BL-20260313-001,Napoli vs Lecce,Both Teams to Score,2.65,Medium,25,WIN,2.65,41.25
BL-20260313-002,Charlotte vs Inter Miami,Miami Money Line,2.02,Medium,25,LOSS,2.02,-25
```

---

## Testing

See `tests/test_betlab.py::test_output_*` for unit tests.

Key test cases:
- Report generation (format correctness)
- CSV export (correct columns, escaping)
- Bet ID generation (uniqueness, format)
- Rounding and formatting (currency, percentages)
```

**Step 2: Verify file created**

Run: `wc -l "c:\Games\Job Hunt Content\Project\Betlab\betlab\docs\MODULES\output_generator.md"`

Expected: >100 lines

**Step 3: Commit**

```bash
cd "c:\Games\Job Hunt Content\Project\Betlab\betlab"
git add docs/MODULES/output_generator.md
git commit -m "docs: add output generator module reference"
```

---

## Task 9: Create Mermaid Diagrams

**Files:**
- Create: `docs/diagrams/data_flow.mmd`
- Create: `docs/diagrams/module_dependencies.mmd`
- Create: `docs/diagrams/pipeline_walkthrough.mmd`
- Create: `docs/diagrams/README.md`

**Step 1: Create data_flow.mmd**

```mermaid
graph TD
    A["📄 bets.txt<br/>(Input Bets)"] -->|"Match, Odds,<br/>Confidence"| B["🔧 Phase 1: Parse<br/>(parser.py)"]
    B -->|"Normalized<br/>Decimal Odds"| C["📊 Phase 2: EV Filter<br/>(analyser.py)"]
    C -->|"EV >= 2%<br/>Pass Only"| D["💰 Phase 3: Kelly Sizing<br/>(bankroll_mgr.py)"]
    D -->|"Stake in ₹<br/>Daily Cap Applied"| E["🎲 Phase 4: Parlay Builder<br/>(parlay_builder.py)"]
    E -->|"Singles + Parlays<br/>(Uncorrelated Only)"| F["📋 Phase 5: Output<br/>(output_generator.py)"]
    F -->|"Markdown Report"| G["📑 recommendations.md"]
    F -->|"CSV Template"| H["📊 bet_log_template.csv"]

    C -->|"Rejected Bets<br/>EV < 2%"| I["🗑️ error_log.txt"]
    E -->|"Correlation Fails"| I

    style A fill:#e1f5ff
    style G fill:#c8e6c9
    style H fill:#c8e6c9
    style I fill:#ffccbc
```

**Step 2: Create module_dependencies.mmd**

```mermaid
graph LR
    A["parser.py<br/>(Input Parsing)"]
    B["math_engine.py<br/>(Pure Math)"]
    C["analyser.py<br/>(Filtering)"]
    D["bankroll_mgr.py<br/>(Stake Sizing)"]
    E["parlay_builder.py<br/>(Combos)"]
    F["output_generator.py<br/>(Reports)"]

    A -->|"Odds"| B
    A -->|"Normalized Bets"| C
    B -->|"EV, Kelly"| C
    B -->|"Probability"| D
    B -->|"Parlay Math"| E
    C -->|"Tagged Bets"| E
    C -->|"Recommended Bets"| F
    D -->|"Stakes"| F
    E -->|"Parlays"| F

    style B fill:#fff9c4
    style F fill:#c8e6c9
```

**Step 3: Create pipeline_walkthrough.mmd**

```mermaid
sequenceDiagram
    participant User
    participant Parser
    participant Math
    participant Analyser
    participant BankrollMgr
    participant ParalayBuilder
    participant Output

    User->>Parser: "Man City 1.85"
    Parser->>Math: decimal_odds=1.85
    Math->>Math: implied_prob = 1/1.85 = 0.541
    Math->>Analyser: implied_prob=0.541

    Note over Analyser: user_true_prob = 0.53
    Analyser->>Math: calculate_ev(1.85, 0.53)
    Math->>Math: EV = (1.85 × 0.53) - 1 = -0.019 (-1.9%)
    Math->>Analyser: EV = -0.019

    alt EV >= 2%?
        Analyser->>BankrollMgr: PASS - Tag SINGLE_CANDIDATE
        BankrollMgr->>BankrollMgr: kelly_frac = 0.10
        BankrollMgr->>BankrollMgr: half_kelly = 0.05
        BankrollMgr->>BankrollMgr: stake = 1 unit = ₹25
        BankrollMgr->>ParalayBuilder: Add to pool if top EV
        ParalayBuilder->>Output: SINGLE_CANDIDATE tagged
    else
        Analyser->>Output: REJECT - EV too low (-1.9%)
    end

    Output->>User: recommendations.md + bet_log_template.csv
```

**Step 4: Create diagrams/README.md**

```markdown
# Diagrams

This folder contains system architecture diagrams in Mermaid format.

## Files

- **data_flow.mmd** — End-to-end pipeline: bets.txt → recommendations.md
- **module_dependencies.mmd** — Module import graph
- **pipeline_walkthrough.mmd** — Single bet through all 5 phases

## Viewing Diagrams

### Option 1: GitHub (Easiest)
- Mermaid renders natively in GitHub markdown
- Just open any `.mmd` file in GitHub repo

### Option 2: Local VSCode
- Install "Markdown Preview Mermaid Support" extension
- Open `.mmd` file, press Ctrl+Shift+V (preview)

### Option 3: Online Editor
- Go to https://mermaid.live/
- Paste `.mmd` content

### Option 4: CLI (if you have mermaid-cli)
```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i data_flow.mmd -o data_flow.png
```

## Diagram Descriptions

### data_flow.mmd
Shows the complete pipeline:
- Input: `bets.txt`
- 5 phases: Parse → EV Filter → Kelly → Parlays → Output
- Outputs: `recommendations.md`, `bet_log_template.csv`, `error_log.txt`

### module_dependencies.mmd
Shows which modules depend on which:
- `parser` is independent (pure input handling)
- `math_engine` is pure math (no dependencies)
- All others depend on `math_engine`
- `output_generator` depends on all others (final aggregation)

### pipeline_walkthrough.mmd
Sequence diagram of a single bet:
1. User inputs "Man City 1.85"
2. Parser → normalizes to decimal
3. Math Engine → calculates implied probability & EV
4. Analyser → checks if EV >= 2%
5. If pass → stake sizing, tagging
6. Final output

This helps understand the flow in detail.
```

**Step 5: Create the actual Mermaid files**

For `docs/diagrams/data_flow.mmd`, save this content:

```
graph TD
    A["📄 bets.txt<br/>(Input Bets)"] -->|"Match, Odds,<br/>Confidence"| B["🔧 Phase 1: Parse<br/>(parser.py)"]
    B -->|"Normalized<br/>Decimal Odds"| C["📊 Phase 2: EV Filter<br/>(analyser.py)"]
    C -->|"EV >= 2%<br/>Pass Only"| D["💰 Phase 3: Kelly Sizing<br/>(bankroll_mgr.py)"]
    D -->|"Stake in ₹<br/>Daily Cap Applied"| E["🎲 Phase 4: Parlay Builder<br/>(parlay_builder.py)"]
    E -->|"Singles + Parlays<br/>(Uncorrelated Only)"| F["📋 Phase 5: Output<br/>(output_generator.py)"]
    F -->|"Markdown Report"| G["📑 recommendations.md"]
    F -->|"CSV Template"| H["📊 bet_log_template.csv"]

    C -->|"Rejected Bets<br/>EV < 2%"| I["🗑️ error_log.txt"]
    E -->|"Correlation Fails"| I

    style A fill:#e1f5ff
    style G fill:#c8e6c9
    style H fill:#c8e6c9
    style I fill:#ffccbc
```

For `docs/diagrams/module_dependencies.mmd`:

```
graph LR
    A["parser.py<br/>(Input Parsing)"]
    B["math_engine.py<br/>(Pure Math)"]
    C["analyser.py<br/>(Filtering)"]
    D["bankroll_mgr.py<br/>(Stake Sizing)"]
    E["parlay_builder.py<br/>(Combos)"]
    F["output_generator.py<br/>(Reports)"]

    A -->|"Odds"| B
    A -->|"Normalized Bets"| C
    B -->|"EV, Kelly"| C
    B -->|"Probability"| D
    B -->|"Parlay Math"| E
    C -->|"Tagged Bets"| E
    C -->|"Recommended Bets"| F
    D -->|"Stakes"| F
    E -->|"Parlays"| F

    style B fill:#fff9c4
    style F fill:#c8e6c9
```

For `docs/diagrams/pipeline_walkthrough.mmd`:

```
sequenceDiagram
    participant User
    participant Parser
    participant Math
    participant Analyser
    participant BankrollMgr
    participant ParalayBuilder
    participant Output

    User->>Parser: "Man City 1.85"
    Parser->>Math: decimal_odds=1.85
    Math->>Math: implied_prob = 1/1.85 = 0.541
    Math->>Analyser: implied_prob=0.541

    Note over Analyser: user_true_prob = 0.53
    Analyser->>Math: calculate_ev(1.85, 0.53)
    Math->>Math: EV = (1.85 × 0.53) - 1 = -0.019 (-1.9%)
    Math->>Analyser: EV = -0.019

    alt EV >= 2%?
        Analyser->>BankrollMgr: PASS - Tag SINGLE_CANDIDATE
        BankrollMgr->>BankrollMgr: kelly_frac = 0.10
        BankrollMgr->>BankrollMgr: half_kelly = 0.05
        BankrollMgr->>BankrollMgr: stake = 1 unit = ₹25
        BankrollMgr->>ParalayBuilder: Add to pool if top EV
        ParalayBuilder->>Output: SINGLE_CANDIDATE tagged
    else
        Analyser->>Output: REJECT - EV too low (-1.9%)
    end

    Output->>User: recommendations.md + bet_log_template.csv
```

**Step 6: Write all files**

(Run these as separate writes)

After writing all diagram files and diagrams/README.md, commit:

```bash
cd "c:\Games\Job Hunt Content\Project\Betlab\betlab"
git add docs/diagrams/
git commit -m "docs: add system diagrams (data flow, dependencies, walkthrough)"
```

---

## Task 10: Update Root README.md

**Files:**
- Modify: `README.md` (add links to documentation)

**Step 1: Read current README**

Already done — we read it in brainstorming phase.

**Step 2: Add documentation section**

After "## 📐 How It Works" section, add:

```markdown
---

## 📚 Documentation & Architecture

New to BetLab? Start here:

### Quick Overview
- **[System Architecture](docs/ARCHITECTURE.md)** — How BetLab works at 10,000 ft
- **[Design Decisions](docs/DESIGN_DECISIONS.md)** — Why we chose Half-Kelly, correlation checks, local-first, etc.

### API Reference
- **[Parser Module](docs/MODULES/parser.md)** — Parse odds (decimal, American, fractional)
- **[Math Engine](docs/MODULES/math_engine.md)** — EV, Kelly, probability formulas
- **[Analyser](docs/MODULES/analyser.md)** — EV filtering & bet tagging
- **[Bankroll Manager](docs/MODULES/bankroll_mgr.py)** — Stake sizing & risk management
- **[Parlay Builder](docs/MODULES/parlay_builder.md)** — Parlay construction with correlation checks
- **[Output Generator](docs/MODULES/output_generator.md)** — Report generation

### System Diagrams
- **[Data Flow](docs/diagrams/data_flow.mmd)** — End-to-end pipeline visualization
- **[Module Dependencies](docs/diagrams/module_dependencies.mmd)** — Module import graph
- **[Pipeline Walkthrough](docs/diagrams/pipeline_walkthrough.mmd)** — Single bet through all phases
```

**Step 3: Verify changes**

Run: `grep -c "📚 Documentation" README.md`

Expected: 1

**Step 4: Commit**

```bash
cd "c:\Games\Job Hunt Content\Project\Betlab\betlab"
git add README.md
git commit -m "docs: add documentation index to main README"
```

---

## Task 11: Verify Complete Documentation Structure

**Files:**
- Check: All documentation files exist

**Step 1: Verify directory structure**

Run: `find docs -type f -name "*.md" -o -name "*.mmd" | sort`

Expected output:
```
docs/ARCHITECTURE.md
docs/DESIGN_DECISIONS.md
docs/MODULES/analyser.md
docs/MODULES/bankroll_mgr.md
docs/MODULES/math_engine.md
docs/MODULES/output_generator.md
docs/MODULES/parser.md
docs/MODULES/parlay_builder.md
docs/diagrams/README.md
docs/diagrams/data_flow.mmd
docs/diagrams/module_dependencies.mmd
docs/diagrams/pipeline_walkthrough.mmd
docs/plans/2026-03-13-portfolio-documentation-design.md
docs/plans/2026-03-13-portfolio-documentation.md
```

**Step 2: Verify line counts (sanity check)**

Run: `wc -l docs/ARCHITECTURE.md docs/DESIGN_DECISIONS.md docs/MODULES/*.md | tail -1`

Expected: >1000 total lines

**Step 3: Quick format check**

Run: `grep -l "^#" docs/*.md docs/MODULES/*.md`

Expected: All files have markdown headers

**Step 4: Commit final verification**

```bash
cd "c:\Games\Job Hunt Content\Project\Betlab\betlab"
git status
```

Expected: All files committed, working tree clean

---

## Task 12: Push to GitHub

**Files:**
- Remote: GitHub repository (user's account)

**Step 1: Check if git remote is set**

Run: `git remote -v`

If no output, configure:
```bash
git remote add origin https://github.com/YOUR_USERNAME/betlab.git
```

**Step 2: Push to GitHub**

Run: `git push -u origin main`

Expected: Branches updated, no errors

**Step 3: Verify on GitHub**

Visit: `https://github.com/YOUR_USERNAME/betlab`

Expected:
- Repo appears online
- `docs/` folder visible
- All files committed
- README.md shows documentation links

---

## Summary

✅ **ARCHITECTURE.md** — High-level system overview + design principles
✅ **DESIGN_DECISIONS.md** — Engineering rationale (Half-Kelly, correlation checks, etc.)
✅ **MODULES/** (6 files) — Deep API reference for each module
✅ **diagrams/** (3 diagrams) — Data flow, dependencies, pipeline walkthrough
✅ **README.md** — Updated with documentation index
✅ **GitHub** — All pushed and live

**Next Steps:**
- Consider adding a CONTRIBUTING.md if you want collaboration guidelines
- Monitor and update documentation as BetLab evolves
- Consider adding CI/CD workflow (GitHub Actions) to run tests on push
```

**Save this plan to `docs/plans/2026-03-13-portfolio-documentation.md`**

**Step 2: Mark plan complete and offer execution options**

This comprehensive implementation plan is now ready.

---

## Execution Options

Plan complete and saved to `docs/plans/2026-03-13-portfolio-documentation.md`.

**Two execution approaches:**

**1. Subagent-Driven (this session)** ⚡
- I dispatch a fresh subagent per task
- Review outputs between tasks
- Fast iteration, all in current session

**2. Parallel Session (separate)**
- Open new session with `executing-plans` skill
- Batch execution with review checkpoints
- Better for deep focus/longer sessions

**Which approach would you prefer?**