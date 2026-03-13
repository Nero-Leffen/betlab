# Copilot AI Skills Implementation Plan

**Date:** 2026-03-13  
**Project:** BetLab  
**Goal:** Operationalize AI-assisted development so Copilot can safely speed up delivery across parser, EV model, parlay, bankroll, and reporting modules.

## 1) Skills and Tools Inventory

### Core AI Skills to Apply

1. Requirements breakdown into weekly deliverables.
2. Architecture mapping and dependency tracing.
3. Bug reproduction and root-cause analysis.
4. Test-first feature development for critical logic.
5. Refactoring for readability without behavior regression.
6. Data parsing and normalization strategy design.
7. Probability and risk-model reasoning.
8. Performance and edge-case analysis.
9. Release readiness checks with acceptance criteria.
10. Developer documentation and changelog writing.

### Copilot Capabilities to Use Heavily

1. Agent mode for multi-step implementation and validation.
2. Workspace semantic search for related logic.
3. Symbol usage search for safe cross-file edits.
4. Precise patch-based code edits.
5. Terminal execution for install/test/run/smoke checks.
6. Diagnostics for lint and runtime errors.
7. Test failure triage loops.
8. Notebook support for model experiments.
9. Git diff awareness for incremental safety.
10. Persistent memory for lessons and plans.

### Recommended Development Tooling

1. Python extension.
2. Pylance.
3. Pytest.
4. Ruff.
5. Black.
6. GitHub Pull Requests extension.
7. Markdown linting.
8. Optional Jupyter.

## 2) What Is Already Implemented in Repo

- Project Copilot behavior file: `.github/copilot-instructions.md`
- Recommended VS Code extensions: `.vscode/extensions.json`

## 3) Step-by-Step Implementation (Project + Copilot)

### Step 1: Install and Enable Tooling

1. Open VS Code in the workspace root.
2. Install extension recommendations from `.vscode/extensions.json`.
3. Ensure Python interpreter points to your project environment (`.venv`).

### Step 2: Baseline Environment Validation

- Install dependencies:

```bash
pip install -r requirements.txt
```

- Run baseline tests:

```bash
pytest tests/ -v
```

- Confirm Streamlit app boots:

```bash
streamlit run src/main.py
```

### Step 3: Activate Copilot Project Instructions

1. Keep `.github/copilot-instructions.md` committed and up to date.
2. Start every task by asking Copilot for:

- Acceptance criteria.
- Affected files/symbols.
- Risk level for the change.

### Step 4: Define Weekly Delivery Cadence

1. Week 1: Parser hardening + parser tests.
2. Week 2: EV/calibration correctness + math tests.
3. Week 3: Parlay correlation rules + guardrail tests.
4. Week 4: Bankroll/exposure controls + risk regression tests.
5. Week 5: Explainability output + report consistency checks.
6. Week 6: Refactor/performance/release readiness + docs/changelog pass.

### Step 5: Run Work-Mode-Specific Development Loops

For each task, explicitly request the relevant mode:

1. Parser hardening mode.
2. EV and calibration model mode.
3. Parlay correlation modeling mode.
4. Bankroll optimization and exposure-control mode.
5. Explainability/report-generation mode.
6. Regression guardrail testing mode.

### Step 6: Use Test-First for Critical Logic

1. Write failing tests before changing math/risk logic.
2. Implement minimal changes to pass tests.
3. Run full suite after targeted tests pass.

### Step 7: Enforce Safe Refactoring

1. Use symbol usage search before renames or shared utility extraction.
2. Prefer small patch-based edits.
3. Validate behavior equivalence with tests and smoke output.

### Step 8: Add Performance and Edge-Case Checks

1. Add tests for malformed lines, extreme odds, tiny/large bankroll values.
2. Add timing checks for larger input sets when changing parser/analyser loops.

### Step 9: Add Release Readiness Gate

Before each release candidate:

1. All tests pass.
2. No unresolved diagnostics in changed files.
3. `output/recommendations.md` generation validated on sample input.
4. Config assumptions checked against `config/settings.yaml`.
5. Docs updated for behavior/config/output changes.

### Step 10: Documentation and Changelog Discipline

1. Update relevant docs in `docs/` per feature.
2. Keep implementation plans under `plans/` or `docs/plans/` current.
3. Maintain a simple changelog entry style in PR/commit summaries.

## 4) Daily AI-First Workflow (Reusable)

1. Ask Copilot to restate goal + acceptance criteria.
2. Ask Copilot to find files and impacted symbols.
3. Implement the smallest vertical slice.
4. Run tests and one real-data smoke check.
5. Review diff and update docs/plan.
6. Commit only when behavior and tests are verified.

## 5) Acceptance Criteria for This Rollout

1. Copilot instructions exist and are project-specific.
2. Extension/tool recommendations are versioned in repo.
3. Team (or solo developer) can run the same daily AI workflow repeatedly.
4. Every critical change path has test and release guardrails.
5. Documentation updates are coupled to behavior changes.
