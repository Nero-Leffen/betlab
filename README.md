# 📊 BetLab — Sports Betting Analytics Engine

> **Educational tool only.** See [DISCLAIMER.txt](DISCLAIMER.txt) before use.

BetLab is a math-driven, local-first analytics engine for football betting.
It analyses tips, filters for positive Expected Value (+EV), sizes stakes using
the Half-Kelly Criterion, and manages bankroll risk — all with full transparency
into the underlying maths.

**Bankroll:** ₹800 INR | **Unit:** ₹25 INR | **Daily Cap:** ₹200 INR

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/betlab.git
cd betlab
pip install -r requirements.txt
```

### 2. Add Your Bets

Edit `data/bets.txt`:

```text
Man City vs Arsenal | 1X2 | Man City | 1.85 | High
Liverpool vs Chelsea | Over/Under | Over 2.5 | 1.95 | Medium
Real Madrid vs Barcelona | 1X2 | Real Madrid | +115 | Medium
Porto vs Benfica | 1X2 | Porto | 5/2 | Low
```

**Format:** `Match Name | Market Type | Selection | Odds | [Confidence]`

| Field | Required | Notes |
| --- | --- | --- |
| Match Name | ✅ | Used for correlation checks |
| Market Type | ✅ | 1X2, Over/Under, Asian Handicap, etc. |
| Selection | ✅ | What you're betting on |
| Odds | ✅ | Decimal (1.85), American (+150/-110), or Fractional (5/2) |
| Confidence | ✗ | High / Medium / Low. Defaults to Medium |

### 3. Run the Web UI

```bash
streamlit run src/main.py
```

Opens at `http://localhost:8501`

### 4. Run Tests

```bash
pytest tests/ -v
```

---

## 📐 How It Works

### Pipeline (5 Phases)

```text
bets.txt
  ↓
Phase 1: Parse & Validate        → error_log.txt
  ↓
Phase 2: EV Analysis & Filter    → Keep bets where EV ≥ 2%
  ↓
Phase 3: Half-Kelly Stake Sizing → Capped at 4 units/day (₹200)
  ↓
Phase 4: Parlay Construction     → Correlation-checked combos
  ↓
Phase 5: Output                  → recommendations.md + bet_log_template.csv
```

### Key Formulas

| Formula | Implementation |
| --- | --- |
| Implied Probability | `1 / decimal_odds` |
| Expected Value | `(odds × true_prob) − 1` |
| Half-Kelly | `((b×p − q) / b) × 0.5` |
| Parlay Probability | `p1 × p2 × ... × pN` |

### Bet Tagging Logic

- **ALL** bets that pass the EV filter → `SINGLE_CANDIDATE`
- **Top 2–4 bets by EV** → also tagged `PARLAY_CANDIDATE`
- Parlays are constructed only from `PARLAY_CANDIDATE` bets, with correlation checks

### Stake Sizing

| Confidence | Units | Stake (₹) |
| --- | --- | --- |
| High | 2 | ₹50 |
| Medium | 1 | ₹25 |
| Low | 1 | ₹25 |

Stakes are further refined by Half-Kelly and capped at the daily limit.

---

## 📚 Documentation & Architecture

New to BetLab? Start here:

### Quick Overview

- **[System Architecture](docs/ARCHITECTURE.md)** — How BetLab works at 10,000 ft
- **[Design Decisions](docs/DESIGN_DECISIONS.md)** — Why we chose Half-Kelly, correlation checks, local-first, etc.

### Development Docs (Tier 1)

- **[Setup Guide](docs/SETUP.md)** — Python 3.11 setup, run, lint, test
- **[API Reference](docs/API_REFERENCE.md)** — Actual function contracts from `src/`
- **[Configuration Reference](docs/CONFIGURATION_REFERENCE.md)** — Every `settings.yaml` key explained
- **[Data Formats](docs/DATA_FORMATS.md)** — Input/output schemas and examples
- **[Contributing](docs/CONTRIBUTING.md)** — Lightweight solo-dev workflow
- **[Risk Mechanics](docs/RISK_MECHANICS.md)** — Bankroll and safety formulas/rules
- **[Parlay Correlation](docs/PARLAY_CORRELATION.md)** — Current rejection heuristics and scoring roadmap
- **[Copilot AI Skills Plan](docs/plans/2026-03-13-copilot-ai-skills-implementation.md)** — Step-by-step AI-assisted development rollout

### API Reference

- **[Parser Module](docs/MODULES/parser.md)** — Parse odds (decimal, American, fractional)
- **[Math Engine](docs/MODULES/math_engine.md)** — EV, Kelly, probability formulas
- **[Analyser](docs/MODULES/analyser.md)** — EV filtering & bet tagging
- **[Bankroll Manager](docs/MODULES/bankroll_mgr.md)** — Stake sizing & risk management
- **[Parlay Builder](docs/MODULES/parlay_builder.md)** — Parlay construction with correlation checks
- **[Output Generator](docs/MODULES/output_generator.md)** — Report generation

### System Diagrams

- **[Data Flow](docs/diagrams/data_flow.mmd)** — End-to-end pipeline visualization
- **[Module Dependencies](docs/diagrams/module_dependencies.mmd)** — Module import graph
- **[Pipeline Walkthrough](docs/diagrams/pipeline_walkthrough.mmd)** — Single bet through all phases

---

## 🛡️ Risk Management

| Rule | Value |
| --- | --- |
| Daily stake cap | ₹200 INR (4 units) |
| Stop-loss threshold | ₹250 INR (pause all activity) |
| Losing streak detection | >5 losses in rolling 7-day window |
| Streak response | Unit size halved temporarily |
| No chasing losses | Hard-coded — system never increases stakes after losses |

---

## 🔄 Feedback Loop

After your bets settle:

1. Open `output/bet_log_template.csv`
2. Fill in `result` (WIN / LOSS / VOID) and `pnl_inr`
3. Upload to the **"Update Results"** tab in the UI
4. BetLab will calculate your actual source accuracy and ask to confirm before updating

---

## 📁 Project Structure

```text
betlab/
├── config/
│   └── settings.yaml          # Bankroll, units, source accuracy, thresholds
├── data/
│   ├── bets.txt               # Your input bets
│   ├── results.csv            # Historical P&L (auto-created)
│   └── logs/
│       ├── betlab.log         # Execution log
│       └── error_log.txt      # Parse errors
├── src/
│   ├── main.py                # Streamlit entry point
│   ├── parser.py              # Input parsing (all odds formats)
│   ├── math_engine.py         # EV, Kelly, probability formulas
│   ├── analyser.py            # EV filtering + bet tagging
│   ├── bankroll_mgr.py        # Stake sizing + cap enforcement
│   ├── parlay_builder.py      # Correlation checks + parlay construction
│   └── output_generator.py   # recommendations.md + CSV output
├── output/
│   ├── recommendations.md     # Generated report
│   └── bet_log_template.csv   # Tracking template
├── tests/
│   └── test_betlab.py         # Full test suite
├── requirements.txt
├── DISCLAIMER.txt
└── README.md
```

---

## ⚙️ Configuration

Edit `config/settings.yaml` to adjust defaults:

For full parameter behavior and safe presets, see **[docs/CONFIGURATION_REFERENCE.md](docs/CONFIGURATION_REFERENCE.md)**.

```yaml
bankroll:
  total_inr: 800
  unit_inr: 25
  max_daily_stake_inr: 200

strategy:
  min_ev_threshold: 0.02  # 2% minimum edge
  kelly_enabled: true
  parlay_max_legs: 4
  parlay_pool_size: 4

source_accuracy:
  football: 0.53          # Update after gathering results data
  default: 0.53

risk:
  stop_loss_percentage: 50
  losing_streak_window_days: 7
  losing_streak_threshold: 5
  reduced_unit_multiplier: 0.5
```

---

## 🔭 Roadmap (Future Expansion)

- [ ] Multi-sport support (Cricket, Tennis) with per-sport accuracy
- [ ] Live odds ingestion via public APIs
- [ ] Historical backtesting module
- [ ] Value bet screener across multiple bookmakers
- [ ] Bankroll growth chart and ROI dashboard
- [ ] CLI mode (`python src/main.py --cli`)
- [ ] Docker deployment

---

## ⚠️ Disclaimer

**BetLab is for educational purposes only.** See [DISCLAIMER.txt](DISCLAIMER.txt).
Online betting is illegal in Telangana and Andhra Pradesh, India.
Never bet more than you can afford to lose.
