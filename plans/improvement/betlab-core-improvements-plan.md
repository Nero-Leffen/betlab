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

| # | Phase | Status | Tests Added | Notes |
| - | ----- | ------ | ----------- | ----- |
| 1 | Correlation-aware parlay engine | ✅ Done | 17 | `apply_correlation_penalty`, soft-penalty in `parlay_builder.py`, `math_engine.py` |
| 2 | Dynamic probability calibration from results | ✅ Done | 17 | Market priors, time-decay blending, `prob_source` / `prob_sample_count` metadata |
| 3 | Session-level bankroll optimizer | ✅ Done | 8 | Exposure caps (team/market/confidence), drawdown governor tiers, rejection log |
| 4 | Market and selection dedupe plus conflict rules | ✅ Done | 18 | `normalize_market_type`, `dedupe_bets`, `filter_conflicts` wired into pipeline |
| 5 | EV robustness gates and uncertainty display | ✅ Done | 14 | `ev_robustness_label`, `apply_robustness_gate`, `is_no_bet_day`; `ev_label` field on `SizedBet`; EV Quality line in output; config block `ev_robustness` (disabled by default) |
| 6 | Free-form market classification fix (MVP bug) | ✅ Done | 0 | Added `_infer_market_from_selection()` to `parser.py`; freeform bets now correctly tagged BTTS/O/U/Handicap/1X2 so market-specific priors are applied |

**Total tests: 135 passing** (up from 0 at project start).

## Current Runtime Profile

- Bankroll baseline: `₹800`
- Stop-loss threshold: `₹400`
- First-run policy: `cold_start`
- Cold-start singles stake: `₹25`
- Cold-start total singles exposure: `₹125` _(raised from 75 on 2026-03-13 to allow 4-5 qualifying bets through)_
- Cold-start adaptive unlock: after `20` completed results
- Parlay behavior in cold-start: capped to `1` option, suppressed entirely if exposure would be exceeded

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
All 5 phases are complete. The roadmap is fully delivered and the app is ready for a first run under the cold-start bankroll policy.

**Optional next steps (not planned):**

- Enable `ev_robustness.enabled: true` in `config/settings.yaml` to activate the parlay quality gate in live use.

---

## Session Log

### 2026-03-13 — MVP First Run

**Status:** First real run completed on live bets from Bets.txt (Friday–Sunday picks).

**Bugs found and fixed:**
1. **Market classification broken for free-form input** — all 31 parsed bets were tagged `freeform`, so market-specific priors (BTTS 0.52, Over/Under 0.54) were never applied. Fixed by adding `_infer_market_from_selection()` in `src/parser.py`.
2. **Cold-start exposure cap too tight** — cap of ₹75 blocked the 4th qualifying EV-positive bet. Raised to ₹125 in `config/settings.yaml`.

**Results after fix:**

| Metric | Before | After |
|--------|--------|-------|
| Qualifying singles | 3 | **4** |
| Parlay options | 0 | **1** (4-leg, 21.6x combined odds) |
| Total at risk | ₹75 | **₹125** |
| Risk % of bankroll | 9.4% | **15.6%** |

**Qualifying bets (2026-03-13):**

| Bet | Market | Odds | EV |
|-----|--------|------|----|
| Napoli vs Lecce — Both Teams to Score | BTTS | 2.65 | +37.8% |
| Charlotte vs Inter Miami — Miami ML | 1X2 | 2.02 | +7.1% |
| FC Dallas vs San Diego FC — San Diego ML | 1X2 | 2.02 | +7.1% |
| Le Havre vs Lyon — Lyon ML | 1X2 | 2.00 | +6.0% |

**Key insight:** 27 of 31 picks (87%) failed EV — correct, not a bug. Most picks are short-odds favorites (1.30–1.85) with no mathematical edge at a 53% prior win rate.

**Next action:** Log results once matches settle. Upload via "Update Results" tab. 20 settled bets unlocks Kelly sizing.
- Add multi-sport support by extending `_detect_sport` in `src/parser.py` and `source_accuracy` in config.
- Add team alias dictionary to `src/parser.py` for better entity resolution.
- Decide whether the policy-level `10%` per-bet and `20%` open-exposure limits should become explicit hard-enforced runtime controls.
