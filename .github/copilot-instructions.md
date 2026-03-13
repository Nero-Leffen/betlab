# BetLab Copilot Operating Instructions

## Mission

Help implement small, high-impact improvements to BetLab with measurable safety:

- No behavior regressions in core math and bankroll logic.
- Every non-trivial change has tests or smoke validation.
- Docs and plans are updated with implementation changes.

## Project Context

- Language: Python 3.11+
- Core folders: `src/`, `tests/`, `config/`, `data/`, `docs/`, `plans/`
- Entry point: `src/main.py`
- Test command: `pytest tests/ -v`

## Copilot Default Workflow

1. Restate goal and acceptance criteria in 3-5 bullets.
2. Find impacted files and symbols before editing.
3. Implement the smallest vertical slice.
4. Run tests and a smoke check with realistic data.
5. Review diff for unintended behavior changes.
6. Update docs or plans for any user-visible or architectural change.

## Required Safety Checks

Before coding:

- Identify all impacted modules and dependencies.
- Call out risk level for bankroll, EV, and parlay logic.

After coding:

- Run `pytest tests/ -v`.
- For parser/math changes, run focused tests first, then full tests.
- Validate output files still generate (`output/recommendations.md`, `output/bet_log_template.csv`).

## Project AI Work Modes

### 1) Parser Hardening Mode

Use when changing `src/parser.py` or input handling.

- Add/expand table-driven tests in `tests/test_betlab.py`.
- Cover decimal, American, fractional odds and malformed lines.
- Preserve backward compatibility for existing `data/bets.txt` format.

### 2) EV and Calibration Model Mode

Use when changing `src/math_engine.py` or EV thresholds.

- Validate EV formula assumptions explicitly.
- Keep units and probability domains clear (`0-1` probability).
- Add edge-case tests for near-zero and high-odds scenarios.

### 3) Parlay Correlation Mode

Use when changing `src/parlay_builder.py`.

- Explain correlation assumptions in PR/summary notes.
- Add regression tests for correlated markets and duplicate match exposure.

### 4) Bankroll and Exposure Control Mode

Use when changing `src/bankroll_mgr.py`.

- Treat risk controls as critical-path logic.
- Verify caps, streak logic, and stop-loss behavior with tests.

### 5) Explainability and Report Generation Mode

Use when changing `src/output_generator.py` and docs.

- Ensure recommendations include rationale fields (EV, implied probability, stake basis).
- Keep markdown output deterministic for testability.

### 6) Regression Guardrail Testing Mode

Use for cross-module refactors.

- Run full test suite.
- Add at least one integration-style test path.
- Confirm no output schema drift unless intentionally versioned.

## Copilot Capability Mapping

- Agent mode: multi-step changes with verification loops.
- Semantic search: locate call chains and side effects quickly.
- Symbol usage search: safe cross-file edits and renames.
- Patch-based edits: minimal and reviewable diffs.
- Terminal runs: tests, smoke checks, and linting.
- Diagnostics: catch and resolve lint/typing/runtime issues.
- Diff awareness: verify only intended behavior changed.
- Persistent memory: store plans, constraints, and lessons learned.

## Definition of Done

A task is done only when:

- Acceptance criteria are met.
- Tests pass for impacted logic.
- Any changed behavior is reflected in docs.
- Diff is small, intentional, and explained.
