# BetLab Sports Betting Analytics Engine

Educational tool for systematic bankroll management. Processes sports betting tips through a 5-phase pipeline and recommends stakes using Half-Kelly sizing. All amounts in INR. Prototype bankroll baseline: **800 INR**.

## Key Commands

```bash
# Install dependencies
python -m pip install -r requirements.txt

# Run tests
python -m pytest tests -v

# Run app
streamlit run src/main.py
```

Always run the full test suite after any changes: `python -m pytest tests -v`

## Pipeline (5 Phases)

```
Parse (parser.py)
  → Analyse & EV filter (analyser.py, math_engine.py)
  → Size stakes via Half-Kelly + bankroll rules (bankroll_mgr.py)
  → Build parlays with correlation checks (parlay_builder.py)
  → Generate output files + Streamlit display (output_generator.py, main.py)
```

## Source Files

| File | Role |
|------|------|
| `src/parser.py` | Parses `bets.txt` — supports decimal, American, fractional odds |
| `src/analyser.py` | Computes EV, filters bets, calibrates probability from results history |
| `src/math_engine.py` | Kelly formula, EV calculation, correlation penalty |
| `src/bankroll_mgr.py` | Half-Kelly stake sizing, stop-loss, streak detection |
| `src/parlay_builder.py` | Builds parlay combos with soft correlation penalties |
| `src/output_generator.py` | Writes `output/recommendations.md` and `output/bet_log_template.csv` |
| `src/main.py` | Streamlit UI — wires all phases together |

## Configuration (`config/settings.yaml`)

| Block | Key settings |
|-------|-------------|
| `bankroll` | `total_inr: 800`, `unit_inr: 25`, `max_daily_stake_inr: 200` |
| `strategy` | `min_ev_threshold: 0.02`, `kelly_enabled: true`, `parlay_correlation` |
| `market_priors` | Per-market base probabilities (moneyline, btts, totals, handicap) |
| `calibration` | `min_sample_size: 10`, `time_decay_halflife_days: 30`, `smoothing_weight: 0.30` |
| `risk` | `stop_loss_percentage: 50`, `losing_streak_threshold: 5` |
| `source_accuracy` | Per-sport historical win rate (default: 0.53) |

## Data Paths

| Path | Purpose |
|------|---------|
| `data/bets.txt` | Input bets written by the pipeline at analysis time |
| `data/results.csv` | Settled results uploaded via UI; used for probability calibration |
| `output/recommendations.md` | Generated report from last session |
| `output/bet_log_template.csv` | CSV template for recording bet outcomes |
| `data/logs/betlab.log` | Append-only application log |

## Implementation Status

| Phase | Feature | Status |
|-------|---------|--------|
| 1 | Correlation-Aware Parlay Engine | ✅ Done |
| 2 | Dynamic Probability Calibration | ✅ Done |
| 3 | Session-Level Bankroll Optimizer | ✅ Done |
| 4 | Dedupe and Conflict Rules | ✅ Done |
| 5 | EV Robustness Quality Gates | ✅ Done |

Plan details: `plans/improvement/betlab-core-improvements-plan.md`
Build order: `plans/implementation/05-practical-build-order.md`

## Conventions

- **Bankroll baseline**: 800 INR for current prototype sizing
- **Stake sizing**: Half-Kelly (`f × 0.5`) — `kelly_enabled: true` in config
- **EV threshold**: Minimum 2% edge required (`min_ev_threshold: 0.02`)
- **Probability calibration**: Falls back to market priors when `results.csv` has fewer than 10 effective samples
- **Tests**: 117 tests in `tests/test_betlab.py` — all must pass before committing
- **Per-phase loop**: update config → implement → add tests → run full suite → smoke test with `Bets.txt`
