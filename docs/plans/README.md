# Plans Index

Last updated: 2026-03-13

## Priority Order

1. `2026-03-13-data-ingestion-analysis-math-validation-plan.md`
2. `2026-03-13-copilot-ai-skills-implementation.md`
3. `2026-03-13-portfolio-documentation-design.md`
4. `2026-03-13-portfolio-documentation.md` (lowest priority)

## Status Snapshot

| Plan | Priority | Status | Notes |
| --- | ---: | --- | --- |
| `2026-03-13-data-ingestion-analysis-math-validation-plan.md` | P1 | Active | Phases A-E validated in current prototype flow: EV/Kelly checks, runtime wiring, ingestion smoke, output generation, and calibration fallback/threshold behavior all verified. |
| `2026-03-13-copilot-ai-skills-implementation.md` | P2 | Active | Workflow and release-guardrail discipline. |
| `2026-03-13-portfolio-documentation-design.md` | P3 | Planned | Documentation architecture and presentation strategy. |
| `2026-03-13-portfolio-documentation.md` | P4 | Deferred | Keep as reference only; trim or replace later. |

## Working Rule

Execute P1 and P2 before any P3 or P4 documentation expansion. If P4 is used, first align symbols and examples with current `src/` implementations.

## Immediate Next Actions

1. Use the cold-start bankroll mode for first-run sessions while `data/results.csv` remains absent.
1. Collect settled outcomes into `data/results.csv` to unlock calibration and adaptive sizing after the first 20 completed bets.
1. Decide whether policy-level `10%` per-bet and `20%` open-exposure targets should become hard-enforced runtime rules.
1. Keep the release gate green after any new change: `python -m pytest tests -v` and Streamlit smoke startup.

## Current Baseline Metrics

- Dataset: `data/bets.txt`
- Frozen snapshot: `data/baselines/bets-2026-03-13.txt`
- Total rows: 31
- Parseable rows: 31
- Rejected rows: 0
- Parse success rate: 100.00%
- Market-type distribution: `freeform=31`
- Odds-format distribution: `decimal=31`

### XLSX Dataset Metrics

- Dataset: `data/Bets_Dataset.xlsx`
- Sheets detected: `Individual Bets`, `Parlays`
- Singles parsed: 29
- Prebuilt parlays parsed: 4
- Parse errors: 0

### Phase B Calibration Checks

- `data/results.csv` is currently absent in workspace, so live calibration fallback path is active by default.
- Fallback sanity check (no results/calibration config): `prob_source=sport`, `prob_sample_count=0`.
- Eligibility sanity check with synthetic mixed results (WIN/LOSS/VOID + invalid dates): only valid WIN/LOSS rows with parseable dates contribute.
- Threshold sanity check:
  - with `min_sample_size=5`, effective sample `~7` produced `prob_source=calibrated`.
  - with `min_sample_size=20`, same sample produced fallback `prob_source=prior`.

### Phase C-E Validation Checks

- EV and Kelly edge-case coverage expanded; invalid probability, odds, bankroll, and unit-bound inputs are now guarded explicitly.
- Main runtime wiring validated: `ev_robustness` is passed into analysis and parlay max options now follow config.
- End-to-end smoke output validated on `data/bets.txt`: output artifacts generate successfully and include rationale fields.
- First-run bankroll policy validated: cold-start mode uses flat `₹25` stakes, `₹75` total singles exposure, and suppresses parlays when exposure would be breached.

### Current First-Run Profile

- Bankroll baseline: `₹800`
- Stop-loss threshold: `₹400`
- Cold-start mode: active until `20` completed results exist
- Cold-start singles stake: `₹25`
- Cold-start max total exposure: `₹75`
- Cold-start parlay limit: `1`, further reduced to `0` if exposure would be exceeded

## Change Log

| Date | Change | Reason |
| --- | --- | --- |
| 2026-03-13 | Created plans index with priority and status snapshot. | Establish single planning entry point and execution order. |
| 2026-03-13 | Marked `2026-03-13-portfolio-documentation.md` as deferred (P4). | Reduce low-impact documentation churn during core engine refinement. |
| 2026-03-13 | Captured P1 baseline test state: parser-focused `13 passed`, full suite `117 passed`. | Lock a known-good checkpoint before ingestion/parser hardening changes. |
| 2026-03-13 | Added ingestion profile baseline from `data/bets.txt` (31/31 parse success). | Establish measurable parser baseline before introducing new real-data patterns. |
| 2026-03-13 | Created baseline dataset snapshot at `data/baselines/bets-2026-03-13.txt`. | Enable reproducible comparisons as parsing logic evolves. |
| 2026-03-13 | Implemented direct `.xlsx` ingestion path and Streamlit upload support; parser/full tests now `119 passed`. | Accept structured worksheet input while preserving `bets.txt` compatibility and regression safety. |
| 2026-03-13 | Upgraded XLSX ingestion to multi-sheet mode: parse all bet-like sheets and skip non-bet sheets (e.g., `Parlays`); tests now `120 passed`. | Properly ingest structured workbook layouts without false schema failures on auxiliary sheets. |
| 2026-03-13 | Added explicit `Parlays` sheet extraction as prebuilt parlay entries and surfaced them in Streamlit analysis view. | Ingest workbook parlay content instead of dropping it silently. |
| 2026-03-13 | Updated `data/Bets_Dataset.xlsx` `Individual Bets!E14` to `1.40`. | Resolve remaining missing-odds row and complete clean ingest. |
| 2026-03-13 | Re-validated XLSX ingest: `29` singles, `4` prebuilt parlays, `0` errors. | Confirm workbook is now fully ingestible with current parser logic. |
| 2026-03-13 | Completed Phase B calibration sanity checks (fallback path, WIN/LOSS eligibility, date parsing, sample threshold gating). | Validate analysis calibration fundamentals before EV/Kelly refinement work. |
| 2026-03-13 | Completed Phase C EV/Kelly validation and tightened bankroll math guards; full suite now `130 passed`. | Verify math correctness before further runtime wiring and first-run policy changes. |
| 2026-03-13 | Closed main-flow wiring gaps in `src/main.py` for `ev_robustness` and config-driven parlay max options. | Ensure implemented features are active in the Streamlit runtime path. |
| 2026-03-13 | Re-validated parser smoke on live text and XLSX inputs. | Confirm dataset baseline still matches documented ingest counts. |
| 2026-03-13 | Validated end-to-end output generation for markdown and CSV artifacts. | Confirm report and tracking outputs remain coherent after recent changes. |
| 2026-03-13 | Switched runtime baseline to `₹800` bankroll and `₹400` stop-loss, removing hardcoded `₹500` fallback behavior. | Align the prototype with the intended bankroll profile. |
| 2026-03-13 | Implemented cold-start bankroll mode for first-run sessions; full suite now `135 passed`. | Use flat-stake, capped exposure until enough settled results exist for adaptive sizing. |
| 2026-03-13 | Cleaned secondary documentation and aligned architecture/design docs to cold-start first-run behavior. | Keep docs consistent with the verified runtime profile. |
