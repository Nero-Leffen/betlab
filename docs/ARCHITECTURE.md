# 🏗️ BetLab Architecture

## Overview

BetLab is a **local-first sports betting analytics engine** that transforms raw betting tips into mathematically optimized, risk-managed recommendations. It's built on a transparent, modular pipeline that processes bets through five distinct phases, each with a clear responsibility and measurable output.

Think of it as a **bet filter + portfolio manager**: you feed in tips and odds, it applies rigorous EV analysis, stake-sizing via Half-Kelly, and bankroll risk controls, then outputs actionable recommendations.

---

## System Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BetLab 5-Phase Pipeline                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INPUT: bets.txt (raw tips)                                                │
│         └─ Match | Market | Selection | Odds | [Confidence]               │
│                                                                             │
│         ┌────────────────────────────────────────────────────────┐          │
│         │  Phase 1: PARSING & VALIDATION                         │          │
│         │  ┌─ Normalise odds (decimal, american, fractional)    │          │
│         │  ├─ Extract confidence (high/medium/low)              │          │
│         │  └─ Log errors → error_log.txt                         │          │
│         └────────────────────────────────────────────────────────┘          │
│                            ↓ (valid bets)                                  │
│         ┌────────────────────────────────────────────────────────┐          │
│         │  Phase 2: EV ANALYSIS & FILTERING                      │          │
│         │  ┌─ Calculate implied probability                      │          │
│         │  ├─ Compute Expected Value vs source accuracy          │          │
│         │  ├─ Tag as SINGLE_CANDIDATE or PARLAY_CANDIDATE       │          │
│         │  └─ Filter: keep only EV ≥ 2% (configurable)         │          │
│         └────────────────────────────────────────────────────────┘          │
│                            ↓ (filtered bets)                               │
│         ┌────────────────────────────────────────────────────────┐          │
│         │  Phase 3: STAKE SIZING & BANKROLL MANAGEMENT           │          │
│         │  ├─ Apply Half-Kelly Criterion (0.5 × optimal Kelly)  │          │
│         │  ├─ Scale by confidence level (high=2u, medium=1u)   │          │
│         │  ├─ Check daily cap (₹200 max)                         │          │
│         │  ├─ Check stop-loss (50% loss → halt)                │          │
│         │  └─ Detect losing streaks (>5 losses/7d → reduce)    │          │
│         └────────────────────────────────────────────────────────┘          │
│                            ↓ (sized bets)                                  │
│         ┌────────────────────────────────────────────────────────┐          │
│         │  Phase 4: PARLAY CONSTRUCTION                           │          │
│         │  ├─ Pool top 2–4 PARLAY_CANDIDATE bets by EV          │          │
│         │  ├─ Check correlation (no highly correlated pairs)    │          │
│         │  └─ Assemble 2–4 leg parlays                           │          │
│         └────────────────────────────────────────────────────────┘          │
│                            ↓ (parlays)                                     │
│         ┌────────────────────────────────────────────────────────┐          │
│         │  Phase 5: OUTPUT GENERATION                             │          │
│         │  ├─ Generate recommendations.md (formatted report)     │          │
│         │  └─ Generate bet_log_template.csv (tracking sheet)    │          │
│         └────────────────────────────────────────────────────────┘          │
│                                                                             │
│  OUTPUT: recommendations.md + bet_log_template.csv                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Design Principles

| Principle | Why It Matters |
| --- | --- |
| **Transparency** 📊 | Every calculation is visible. No black boxes. EV, Kelly %, hit probability—all shown in output. Users understand *why* a bet is recommended. |
| **Local-First** 🏠 | No cloud, no external API dependencies (except Streamlit for UI). All data stays on your machine. No betting syndicate profiling. |
| **Risk Management** 🛡️ | Hard-coded stop-loss, daily caps, streak detection. Designed to prevent catastrophic losses and emotional chasing. |
| **Modularity** 🧩 | Each phase is independent: swap out the parser, redesign the bankroll rules, or add new bet types without touching other modules. |
| **Bankroll-First** 💰 | The system optimizes for *sustainable growth*, not maximum wins. Kelly Criterion + Half-Kelly + daily caps = rational portfolio management. |

---

## Module Overview

| Module | Responsibility | Input | Output |
| --- | --- | --- | --- |
| **parser.py** | Parse bets.txt (pipe-delimited) into structured objects. Handle all odds formats (decimal, American, fractional). | Raw text lines | `BetInput` objects + error log |
| **math_engine.py** | Pure math: odds conversion, EV calculation, Kelly Criterion, parlay hit probability. | Odds strings, probabilities | Decimal odds, EV %, Kelly fractions |
| **analyser.py** | Filter bets by EV threshold. Tag as `SINGLE_CANDIDATE` or `PARLAY_CANDIDATE`. | Parsed bets, source accuracy, min EV | Filtered bets with tags |
| **bankroll_mgr.py** | Stake sizing (Half-Kelly, confidence scaling, daily cap). Check stop-loss and losing streaks. | Filtered bets, config | Sized bets + session state (warnings, effective unit) |
| **parlay_builder.py** | Construct multi-leg parlays from top candidates. Correlation checks to avoid redundant bets. | Sized bets | Parlay objects with combined odds + hit probability |
| **output_generator.py** | Render recommendations.md and bet_log_template.csv. Process feedback loop (result upload). | Sized bets, parlays, results | Markdown report + CSV template |

---

## Data Flow Example: Single Bet Through the Pipeline

**Input:** `"Man City vs Arsenal | 1X2 | Man City | 1.85 | High"`

**Phase 1 — Parser:**

- Parse line: `match="Man City vs Arsenal"`, `selection="Man City"`, `odds_str="1.85"`, `confidence="high"`
- Detect odds format: `"1.85"` → decimal
- Create `BetInput(decimal_odds=1.85, confidence="high", ...)`

**Phase 2 — Analyser:**

- Source accuracy (football): 53% (from config)
- Implied probability: `1 / 1.85 = 0.5405` (54%)
- Expected Value: `(1.85 × 0.53) − 1 = 0.981 − 1 = −0.019` ✗ (−1.9% EV)
- **Result:** Filtered out (below 2% threshold)

**Alternative Scenario** (if EV ≥ 2%):

- Tag: `SINGLE_CANDIDATE` (+ maybe `PARLAY_CANDIDATE` if top 4)
- Cold-start stake on first run: `1 unit = ₹25`
- Adaptive stake after cold-start: confidence and Kelly logic can increase this

**Phase 3 — Bankroll Manager:**

- Half-Kelly fraction: `0.35 × 0.5 = 0.175` (17.5% of bankroll)
- Bankroll: ₹800 → Half-Kelly reference stake: `₹140.00`
- Cold-start mode currently overrides this to flat `₹25` stakes until enough settled history exists
- Daily cap check: Cumulative stake must remain under the active session cap ✓
- **First-run stake: ₹25**

**Phase 4 — Parlay Builder:**

- If `PARLAY_CANDIDATE`: eligible for 2–4 leg parlays
- Correlation check with other bets: no conflicts
- In cold-start mode, parlays may be reduced or suppressed to stay within the tighter exposure cap

**Phase 5 — Output:**

- Recommendation: *"Bet ₹25 on Man City @ 1.85 (cold-start mode, +1.9% EV)"*
- CSV row: `["bet_001", "Man City vs Arsenal", "Man City", "1.85", "0.53", "0.019", "high", "25", "SINGLE_CANDIDATE", "pending"]`

---

## Technology Stack

| Layer | Technologies |
| --- | --- |
| **UI/Frontend** | Streamlit (web interface) |
| **Backend Logic** | Python 3.8+ (dataclasses, pathlib, logging) |
| **Configuration** | YAML (settings.yaml) |
| **Data Storage** | Plain text (bets.txt), CSV (results.csv), Markdown (recommendations.md) |
| **Testing** | pytest, Python unittest |
| **Dependencies** | pandas, numpy, pyyaml, streamlit |

**Philosophy:** Minimal external dependencies. Most math is stdlib-only (no scipy/sklearn). Data is human-readable (text, CSV, YAML, Markdown).

---

## File Structure

```text
betlab/
├── config/
│   └── settings.yaml              # Bankroll, units, source accuracy, thresholds
│
├── data/
│   ├── bets.txt                   # Input: your raw betting tips
│   ├── results.csv                # Historical P&L (auto-created after feedback)
│   └── logs/
│       ├── betlab.log             # Execution log (info/debug)
│       └── error_log.txt          # Parse errors (invalid lines)
│
├── src/
│   ├── __init__.py
│   ├── main.py                    # Streamlit app entry point (phases 1–5)
│   ├── parser.py                  # Phase 1: Parse & validate bets
│   ├── math_engine.py             # Pure math (EV, Kelly, odds conversion)
│   ├── analyser.py                # Phase 2: EV filtering + tagging
│   ├── bankroll_mgr.py            # Phase 3: Stake sizing + risk checks
│   ├── parlay_builder.py          # Phase 4: Parlay construction + correlation
│   └── output_generator.py        # Phase 5: Generate recommendations + CSV
│
├── output/
│   ├── recommendations.md         # Generated report (last session)
│   └── bet_log_template.csv       # Template for result tracking
│
├── tests/
│   └── test_betlab.py             # Full test suite (pytest)
│
├── docs/
│   ├── ARCHITECTURE.md            # This file
│   ├── DESIGN_DECISIONS.md        # Why certain choices were made
│   └── MODULES/                   # Detailed API docs per module
│
├── requirements.txt               # Python dependencies
├── README.md                      # Quick start guide
├── DISCLAIMER.txt                 # Legal/educational disclaimer
└── .gitignore
```

---

## Configuration & Customization

All runtime parameters live in `config/settings.yaml`:

```yaml
bankroll:
  total_inr: 800                    # Current bankroll baseline
  unit_inr: 25                      # 1 unit = ₹25
  max_daily_stake_inr: 200          # 4 units/day max

bankroll_policy:
  mode: cold_start
  cold_start_min_settled_bets: 20
  cold_start_flat_stake_inr: 25
  cold_start_max_total_exposure_inr: 75

strategy:
  min_ev_threshold: 0.02            # 2% minimum edge (configurable)
  kelly_enabled: true               # Enable Half-Kelly sizing
  parlay_max_legs: 4                # Max legs per parlay
  parlay_pool_size: 4               # Top N by EV for parlays

source_accuracy:
  football: 0.53                    # Your tip source win rate (update after results)
  default: 0.53                     # Fallback

risk:
  stop_loss_percentage: 50          # Halt if bankroll ≤ 50% of start
  losing_streak_window_days: 7      # Rolling window
  losing_streak_threshold: 5        # Trigger reduction after 5 losses
  reduced_unit_multiplier: 0.5      # Unit halved during streaks
```

The Streamlit UI allows **session-only overrides** of these values without modifying the file.

---

## Key Formulas Reference

| Formula | Equation | Use Case |
| --- | --- | --- |
| **Decimal Odds** | Decimal / American / Fractional input → `decimal` | Standardization |
| **Implied Probability** | `1 / decimal_odds` | Market expectation |
| **Expected Value** | `(decimal_odds × true_prob) − 1` | Bet quality metric |
| **Half-Kelly** | `((b × p − q) / b) × 0.5` | Stake sizing (conservative) |
| **Parlay Probability** | `p₁ × p₂ × ... × pₙ` | Multi-leg hit chance |
| **Parlay EV** | `(combined_odds × parlay_prob) − 1` | Parlay quality |

---

## Feedback & Calibration Loop

BetLab includes a **live recalibration** mechanism:

1. After bets settle, you fill in `result` (WIN/LOSS/VOID) and `pnl_inr` in the CSV.
2. Upload to the **"Update Results"** tab.
3. The system calculates your actual win rate from the last 5+ results.
4. You confirm the new accuracy, and it updates `config/settings.yaml`.

This closes the loop: **tips → bets → results → improved accuracy → better EV analysis.**

---

## Related Documentation

- **[DESIGN_DECISIONS.md](../DESIGN_DECISIONS.md)** — Deep dive into architectural choices (why Half-Kelly, why local-first, etc.)
- **MODULES/** — Detailed API docs and function signatures for each module
- **[README.md](../README.md)** — Quick start, disclaimers, roadmap

---

## Future Expansion Points

The modular design allows for:

- **Multi-sport support** (Cricket, Tennis) with per-sport accuracy tracking
- **Live odds ingestion** from public APIs (Pinnacle, CoinDrop)
- **Backtesting engine** to validate strategy against historical data
- **Value screener** to identify edge opportunities across bookmakers
- **CLI mode** (`python src/main.py --cli`) for headless deployments
- **Docker containerization** for easy deployment

---

**Built with ❤️ for transparency in sports betting analytics.**
