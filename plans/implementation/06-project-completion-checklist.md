# Project Completion Checklist

This checklist turns the current roadmap into a practical finish sequence for BetLab from its current state.

## Goal

Complete validation, close remaining wiring gaps, align docs with code, and reach a clean release-ready prototype state.

## Exit Criteria

1. Full test suite passes.
2. Streamlit app starts and runs the end-to-end pipeline.
3. Text and spreadsheet ingestion both succeed on smoke inputs.
4. Output artifacts generate correctly:
   - `output/recommendations.md`
   - `output/bet_log_template.csv`
5. No known config-to-runtime wiring gaps remain.
6. Docs and plan status reflect the actual code behavior.

## Step 1: Lock the Baseline

### Baseline Objective

Create a stable checkpoint before any final completion work.

### Baseline Actions

1. Confirm current branch state and changed files.
2. Keep the current dataset baseline anchored to `data/baselines/bets-2026-03-13.txt`.
3. Record current smoke inputs used for validation:
   - `data/bets.txt`
   - `data/Bets_Dataset.xlsx`
4. Treat `docs/plans/README.md` as the live execution status board.

### Baseline Done When

1. Validation inputs are fixed and repeatable.
2. The team can compare post-change behavior against a known baseline.

## Step 2: Finish EV and Kelly Validation

### EV and Kelly Objective

Complete Phase C from the active validation plan.

### EV and Kelly Actions

1. Add or confirm tests for near-threshold EV cases.
2. Validate Kelly sizing under low odds, high odds, and low-edge cases.
3. Confirm unit rounding and confidence caps behave deterministically.
4. Confirm no invalid stake assignments occur under daily-cap pressure.
5. Run focused tests before running the full suite.

### EV and Kelly Files

1. `src/math_engine.py`
2. `src/bankroll_mgr.py`
3. `src/analyser.py`
4. `tests/test_betlab.py`

### EV and Kelly Done When

1. EV and Kelly edge cases are test-covered.
2. Stake sizing remains mathematically valid across boundary conditions.

## Step 3: Close Main-Flow Wiring Gaps

### Main-Flow Objective

Ensure implemented features are active in the runtime path, not just present in modules.

### Main-Flow Actions

1. Pass `ev_robustness` config into `analyse_bets` from `src/main.py`.
2. Replace hardcoded parlay option count with configured `parlay_max_options`.
3. Verify UI overrides and config-derived values remain consistent.
4. Re-run smoke flow after wiring changes.

### Main-Flow Files

1. `src/main.py`
2. `config/settings.yaml`

### Main-Flow Done When

1. Runtime behavior matches config intent.
2. No known orchestration gaps remain.

## Step 4: Revalidate Ingestion on Real Inputs

### Ingestion Objective

Prove parser stability on both supported input modes.

### Ingestion Actions

1. Run parser smoke tests on `data/bets.txt`.
2. Run spreadsheet ingestion checks on `data/Bets_Dataset.xlsx`.
3. Verify parse counts, error counts, and extracted prebuilt parlays.
4. Confirm no regression in free-form parsing behavior.

### Ingestion Files

1. `src/parser.py`
2. `tests/test_betlab.py`
3. `docs/plans/README.md`

### Ingestion Done When

1. Text and XLSX inputs both parse cleanly.
2. Any remaining parse failures are explainable and intentional.

## Step 5: Validate End-to-End Outputs

### Output Validation Objective

Confirm the pipeline still produces coherent artifacts after final fixes.

### Output Validation Actions

1. Run the full pipeline using the current smoke dataset.
2. Inspect `output/recommendations.md` for:
   - probability source context
   - EV quality labels
   - rejection reasons
   - parlay penalty explanation
3. Inspect `output/bet_log_template.csv` for schema stability.
4. Confirm output generation remains deterministic enough for testing.

### Output Validation Files

1. `src/output_generator.py`
2. `output/recommendations.md`
3. `output/bet_log_template.csv`

### Output Validation Done When

1. Both output artifacts generate without manual intervention.
2. Output content reflects current feature set accurately.

## Step 6: Prepare Live Calibration Readiness

### Calibration Objective

Move calibration from fallback-only behavior toward operational use.

### Calibration Actions

1. Prepare or add a valid `data/results.csv` workflow.
2. Validate date parsing, WIN/LOSS eligibility, and fallback behavior.
3. Verify sample-size thresholds trigger `prior` vs `calibrated` correctly.
4. Confirm results handling does not break when history is sparse or partially malformed.

### Calibration Files

1. `src/analyser.py`
2. `src/output_generator.py`
3. `data/results.csv`
4. `tests/test_betlab.py`

### Calibration Done When

1. Calibration can run on real results data.
2. Sparse or invalid data still degrades safely to prior-based behavior.

## Step 7: Finish Risk Policy Enforcement

### Risk Enforcement Objective

Ensure documented risk rules are fully enforced in code.

### Risk Enforcement Actions

1. Compare documented policy targets against actual enforcement.
2. Confirm daily cap, stop-loss, streak logic, and exposure caps are fully covered.
3. Implement any still-missing hard controls such as per-bet or open-exposure limits if required.
4. Add tests for every enforced rule.

### Risk Enforcement Files

1. `src/bankroll_mgr.py`
2. `config/settings.yaml`
3. `docs/RISK_MECHANICS.md`
4. `docs/CONFIGURATION_REFERENCE.md`

### Risk Enforcement Done When

1. Documented critical risk controls are true in runtime behavior.
2. Risk invariants are covered by tests.

## Step 8: Sync Documentation to Implementation

### Documentation Sync Objective

Remove doc drift now that core features are mostly implemented.

### Documentation Sync Actions

1. Update project overview docs to match current runtime behavior.
2. Update API and configuration references for added fields and config blocks.
3. Update correlation and risk docs where behavior changed from roadmap to implementation.
4. Ensure plan statuses match real completion state.

### Documentation Sync Files

1. `README.md`
2. `docs/API_REFERENCE.md`
3. `docs/CONFIGURATION_REFERENCE.md`
4. `docs/PARLAY_CORRELATION.md`
5. `docs/RISK_MECHANICS.md`
6. `docs/plans/README.md`

### Documentation Sync Done When

1. Readers can rely on docs without checking the source code to resolve contradictions.
2. No major feature is documented incorrectly.

## Step 9: Clean Repository Quality Issues

### Repo Quality Objective

Resolve preventable repo hygiene problems before calling the project complete.

### Repo Quality Actions

1. Fix markdown lint issues in active documentation files.
2. Remove or justify local-only helper artifacts that should not ship.
3. Check generated files and auxiliary config files for repo fit.
4. Review the diff for unrelated noise.

### Repo Quality Done When

1. The repository is clean and reviewable.
2. Remaining issues are known and intentionally deferred.

## Step 10: Run Final Release Gate

### Release Gate Objective

Perform one explicit completion pass before closing the plan.

### Release Gate Actions

1. Run the full test suite.
2. Run text-input smoke validation.
3. Run spreadsheet-input smoke validation.
4. Start the Streamlit app successfully.
5. Verify both generated output artifacts.
6. Review changed files for unintended behavior changes.

### Release Gate Done When

1. All gates pass in one end-to-end pass.
2. The project is stable enough for daily prototype use.

## Step 11: Mark Plans Complete

### Plan Closure Objective

Close the loop in planning artifacts after validation succeeds.

### Plan Closure Actions

1. Update `docs/plans/README.md` status notes.
2. Update `plans/improvement/betlab-core-improvements-plan.md` if any status wording changed.
3. Record what was verified in the final pass.
4. List any intentionally deferred work as post-plan items.

### Plan Closure Done When

1. Plan files show the real project state.
2. Future work is clearly separated from core completion work.

## Suggested Execution Order

1. Step 2: Finish EV and Kelly validation.
2. Step 3: Close main-flow wiring gaps.
3. Step 4: Revalidate ingestion on real inputs.
4. Step 5: Validate end-to-end outputs.
5. Step 6: Prepare live calibration readiness.
6. Step 7: Finish risk policy enforcement.
7. Step 8: Sync documentation to implementation.
8. Step 9: Clean repository quality issues.
9. Step 10: Run final release gate.
10. Step 11: Mark plans complete.

## Validation Commands

```bash
python -m pytest tests/test_betlab.py -k parser -v
python -m pytest tests -v
python -m streamlit run src/main.py
```
