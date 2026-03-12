# BetLab Prototype Improvement Plan (Solo Builder)

## Context
This roadmap is for a one-person project focused on practical learning and a usable personal prototype.

Design principles:
- Ship in small weekly increments.
- Prefer explainable heuristics over heavy modeling.
- Keep risky features behind config toggles.
- Prioritize tests for core safety and decision quality.

## Prototype Goal (6 Weeks)
By the end of this plan, BetLab should:
- Parse noisy free-form text into reliable bet candidates.
- Produce better singles and realistic parlays.
- Enforce risk constraints consistently.
- Explain every recommendation and rejection clearly.

## Comprehensive Improvement Backlog

### Highest-Impact Improvements
1. Calibrated probability model instead of fixed 0.53.
- Replace static sport accuracy with dynamic estimates by market type, odds band, and source.
- Use rolling Bayesian-style update or Elo-style confidence update from settled results.
- File touchpoints: [src/analyser.py](src/analyser.py), [src/output_generator.py](src/output_generator.py), [config/settings.yaml](config/settings.yaml).

2. Better parlay math with correlation-aware probability.
- Keep base independence product and apply correlation penalty factor.
- Formula: $P_{parlay}=\left(\prod_i p_i\right)\times c,\;0<c\le1$.
- Penalties from shared league, kickoff window, market family, and team overlap.
- File touchpoints: [src/parlay_builder.py](src/parlay_builder.py), [src/math_engine.py](src/math_engine.py).

3. Smarter bankroll allocation (portfolio optimization).
- Move from per-bet local sizing to session-level allocation under constraints.
- Optimize expected growth under total cap and exposure constraints.
- Constraints: daily cap, max exposure per league/team, max per confidence band.
- File touchpoints: [src/bankroll_mgr.py](src/bankroll_mgr.py).

4. Duplicate and market conflict resolution.
- Detect equivalent picks from wording variants (ML, Money Line, Home Win).
- Detect mutually conflicting picks in same event and avoid overexposure.
- File touchpoints: [src/parser.py](src/parser.py), [src/analyser.py](src/analyser.py), [src/parlay_builder.py](src/parlay_builder.py).

5. Expected value quality gates.
- Add EV confidence band and minimum sample gates.
- Promote to parlay pool only if EV robustness passes quality checks.
- File touchpoints: [src/analyser.py](src/analyser.py), [config/settings.yaml](config/settings.yaml).

### Core Engine Enhancements
1. Multi-market support with market-specific priors.
- Separate priors for BTTS, O/U, Asian Handicap, 1X2.

2. Time-decay learning.
- Weight recent outcomes more than old outcomes during calibration.

3. Outcome-grade handling.
- Add half-win, half-loss, push/void handling for Asian lines in PnL and learning.
- File touchpoints: [src/output_generator.py](src/output_generator.py), [src/bankroll_mgr.py](src/bankroll_mgr.py).

4. Confidence auto-derivation.
- Derive confidence from edge plus uncertainty instead of only manual high/medium/low.

5. Dynamic thresholds.
- Tighten EV threshold during drawdowns and loosen during strong calibrated periods.

### Data and Parsing Upgrades
1. Canonical parser pipeline.
- Ingest free-form text, normalize entities, produce canonical structured bets.
- Add normalization dictionaries for team and market aliases.
- File touchpoint: [src/parser.py](src/parser.py).

2. Entity resolution.
- Standardize match and team labels to stable IDs for better dedupe/correlation behavior.

3. Input quality scoring.
- Add parse-confidence score and route low-confidence rows to review bucket.

### Risk Controls to Add
1. Exposure caps by dimension.
- Per-team, per-league, per-day, per-market caps.

2. Drawdown-based governor.
- Dynamic risk reduction as drawdown deepens (not only binary stop-loss).

3. Variance-aware stake scaling.
- Lower stake for high-variance markets/parlays even when EV is high.

4. No-bet day mode.
- Recommend no bets when edges are weak or candidate set is too correlated.

## Practical Build Order (Execution Priority)
1. Correlation-aware parlay engine.
2. Dynamic probability calibration from results.
3. Session-level bankroll optimizer.
4. Market and selection dedupe plus conflict rules.
5. EV robustness gates and uncertainty display.

## 6-Week Implementation Map

## Week 1: Reliability and Baseline
Objective:
Lock in deterministic end-to-end behavior before adding more logic.

Tasks:
- Add end-to-end smoke test: parse -> analyse -> bankroll -> parlay -> output.
- Add noisy input fixtures with mixed free-form and structured rows.
- Add baseline metrics output (qualified singles, parlays, average EV).

Files:
- [src/parser.py](src/parser.py)
- [tests/test_betlab.py](tests/test_betlab.py)
- [src/output_generator.py](src/output_generator.py)

## Week 2: Correlation-Aware Parlay Engine
Objective:
Reduce optimistic parlay estimates.

Tasks:
- Add soft-correlation scoring in [src/parlay_builder.py](src/parlay_builder.py).
- Add probability adjustment helper in [src/math_engine.py](src/math_engine.py).
- Add config weights in [config/settings.yaml](config/settings.yaml).
- Add tests for same-league and same-market penalties.

## Week 3: Probability Calibration and Priors
Objective:
Upgrade from fixed probabilities to calibrated estimates.

Tasks:
- Add market-specific priors and odds-band adjustments.
- Implement rolling/time-decay update from settled results.
- Implement minimum sample-size fallback rules.
- Add calibration summary in output/report.

Files:
- [src/analyser.py](src/analyser.py)
- [src/output_generator.py](src/output_generator.py)
- [config/settings.yaml](config/settings.yaml)

## Week 4: Session-Level Bankroll Optimization
Objective:
Allocate capital as a portfolio under constraints.

Tasks:
- Add optimizer pass after candidate generation.
- Enforce exposure caps by team/league/market/day.
- Add drawdown governor and variance-aware scaling.
- Keep stop-loss behavior as hard fail-safe.

Files:
- [src/bankroll_mgr.py](src/bankroll_mgr.py)
- [config/settings.yaml](config/settings.yaml)
- [tests/test_betlab.py](tests/test_betlab.py)

## Week 5: Canonicalization, Dedupe, and Conflict Handling
Objective:
Clean candidate set from noisy social data.

Tasks:
- Add market alias dictionary and team alias dictionary.
- Add entity-resolution helper for stable IDs.
- Deduplicate equivalent picks.
- Add conflict detection for opposite outcomes in same event.
- Add input quality score and low-confidence review bucket.

Files:
- [src/parser.py](src/parser.py)
- [src/analyser.py](src/analyser.py)
- [src/parlay_builder.py](src/parlay_builder.py)

## Week 6: Decision Transparency and Quality Gates
Objective:
Make decisions auditable and safer in daily use.

Tasks:
- Add EV robustness gate and uncertainty labels.
- Add confidence auto-derivation and dynamic thresholds.
- Add no-bet day mode when quality conditions fail.
- Expand report rationale for each recommendation and rejection.

Files:
- [src/analyser.py](src/analyser.py)
- [src/output_generator.py](src/output_generator.py)
- [src/main.py](src/main.py)

## Acceptance Criteria
- No silent drops from parser to output pipeline.
- Parlays generated when eligible and correlation-adjusted.
- Calibration updates are stable under sparse data.
- Exposure constraints always respected.
- Rejections include explicit reasons in output.
- Test suite remains green with expanded coverage.

## Minimal Metrics to Track Weekly
- Number of parsed picks.
- Number of qualified singles.
- Number of generated parlays.
- Average singles EV.
- Predicted vs realized parlay hit rate.
- Win rate and net PnL from settled picks.
- Weekly max drawdown.

## Resources and References

### Project references
- [README.md](README.md)
- [config/settings.yaml](config/settings.yaml)
- [src/main.py](src/main.py)
- [src/analyser.py](src/analyser.py)
- [src/bankroll_mgr.py](src/bankroll_mgr.py)
- [src/parlay_builder.py](src/parlay_builder.py)
- [src/parser.py](src/parser.py)
- [src/output_generator.py](src/output_generator.py)
- [tests/test_betlab.py](tests/test_betlab.py)

### Learning resources
- Kelly criterion and half-Kelly risk control.
- Calibration and reliability curves for probabilistic models.
- Lightweight constrained optimization for portfolio allocation.

## Immediate Next Step
Start with Week 2 from the practical build order if you want fastest quality gain:
- Implement soft-correlation penalties and adjusted parlay EV first.
- Then rerun your current Bets.txt flow and compare parlay output quality.
