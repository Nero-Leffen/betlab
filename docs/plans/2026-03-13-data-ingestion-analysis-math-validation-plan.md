# Data Ingestion, Analysis, and Math Engine Refinement Plan

**Date:** 2026-03-13  
**Project:** BetLab  
**Objective:** Use the new dataset to harden ingestion, refine EV and bankroll math behavior, and run a reproducible validation loop.

## 1) Scope and Success Criteria

1. Ingestion is stable on real dataset inputs with clear parse-error reporting.
1. Analysis logic remains mathematically consistent and explainable.
1. Stake sizing and risk controls stay within configured constraints.
1. Parlay generation remains correlation-aware and transparent.
1. All changes are validated through tests plus dataset-driven smoke checks.

## 2) Data Intake Contract (Before Logic Changes)

1. Freeze a baseline dataset snapshot in `data/` for repeatable testing.
1. Verify required parser and results fields.
1. Confirm bets input supports both pipe format and freeform extraction.
1. Confirm results input has `result` and `date` for calibration decay.
1. Record a dataset profile for every run.

Profile metrics:

- Total rows.
- Parseable rows.
- Rejected rows.
- Market-type distribution.
- Odds-format distribution.

## 3) Refinement Workstream

### Phase A: Ingestion and Parser Robustness

1. Run parser on the full dataset and classify failures by pattern.
1. Add targeted parsing rules only for frequent, repeatable real patterns.
1. Preserve backward compatibility with existing `data/bets.txt` format.
1. Expand tests in `tests/test_betlab.py` for each newly supported pattern.

### Phase B: Analysis and Calibration Fundamentals

1. Validate market mapping behavior against dataset market labels.
1. Verify date parse quality in `results.csv`.
1. Verify WIN and LOSS eligibility handling.
1. Verify sample-size threshold behavior.
1. Tune market priors in `config/settings.yaml` only after observing distributions.
1. Keep probability domain constraints strict: $0 < p < 1$.

### Phase C: EV and Kelly Math Fundamentals

1. Validate EV and implied probability calculations on sampled dataset rows.
1. Validate Kelly outputs against confidence caps and unit rounding behavior.
1. Add edge-case tests for near-threshold EV and extreme odds.
1. Confirm no invalid stake assignments under cap pressure.

### Phase D: Parlay and Correlation Behavior

1. Verify hard correlation rejection on same-match and overlap cases.
1. Verify soft-penalty impact using realistic market combinations.
1. Confirm parlay probability explanation fields stay consistent in output.
1. Keep parlay output deterministic for testability.

### Phase E: Risk and Session Controls

1. Validate stop-loss, losing-streak reduction, and daily-cap behavior.
1. Validate optimizer constraints for team, market, and confidence exposure.
1. Confirm rejected-bet reasons are emitted and human-readable.
1. Ensure no scenario exceeds configured daily stake limits.

## 4) Validation Loop (Mandatory Per Iteration)

1. Define one small hypothesis.
1. Add or update focused tests first.
1. Implement the smallest code change.
1. Run focused tests.
1. Run full suite.
1. Run dataset smoke pipeline.
1. Verify generated artifacts.
1. Record metrics delta.
1. Accept or rollback using gates.

Commands:

```bash
python -m pytest tests/test_betlab.py -k parser -v
python -m pytest tests -v
python -m streamlit run src/main.py
```

Artifacts to verify:

- `output/recommendations.md`
- `output/bet_log_template.csv`

## 5) Acceptance Gates (Pass or Fail)

1. Test gate: full test suite passes.
1. Ingestion gate: parse success rate improves or remains stable.
1. Ingestion gate: new parse errors are explainable and non-regressive.
1. Math gate: EV and Kelly outputs remain in expected ranges.
1. Math gate: no invalid probabilities or odds conversions.
1. Risk gate: daily cap and stop-loss invariants always hold.
1. Output gate: markdown and CSV outputs generate and remain coherent.

## 6) Metrics to Track Per Run

1. `parse_success_rate = parsed_rows / total_rows`.
1. `ev_pass_rate = ev_qualified / parsed_rows`.
1. `parlay_build_rate = parlay_options / runs`.
1. `avg_single_ev` (stake-weighted).
1. `total_stake_inr` and `cap_hit` frequency.
1. `rejected_bets_count` by reason.
1. `prior_vs_calibrated_count`.

## 7) Immediate Execution Order

1. Baseline run with current logic on your dataset.
1. Parser fixes for top three real failure patterns.
1. Market mapping and calibration sanity checks.
1. EV and Kelly edge-case and threshold pass.
1. Parlay correlation and output rationale verification.
1. Full regression and documentation update.

## 8) Repo-Specific Notes

1. Existing tests are strong and should stay the primary guardrail.
1. Keep diffs small and phase-specific.
1. Prefer config tuning before major formula changes.
1. Resolve orchestration wiring gaps early in implementation.
1. Pass `ev_robustness` config into analysis flow.
1. Use configured `parlay_max_options` instead of hardcoded value.
