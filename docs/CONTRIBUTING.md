# Contributing (Lightweight Solo Workflow)

## Workflow

1. Create a focused branch.
2. Make small changes.
3. Run lint + tests.
4. Merge only when both pass.

## Branch naming

- `feat/<short-topic>`
- `fix/<short-topic>`
- `docs/<short-topic>`

## Local quality gate

```powershell
ruff check src tests
pytest tests -v
```

## Commit style

Use short, explicit messages:

- `feat: add bankroll session summary`
- `fix: enforce cap after sorting`
- `docs: add configuration reference`

## PR checklist (even if solo)

- [ ] Change scope is small and clear
- [ ] No secrets/credentials added
- [ ] Lint passes
- [ ] Tests pass
- [ ] Docs updated for behavior/config changes

## Testing expectation

- Add/adjust tests for any logic change in:
  - `src/math_engine.py`
  - `src/analyser.py`
  - `src/bankroll_mgr.py`
  - `src/parlay_builder.py`

## CI target

Preferred CI profile: lint + tests.

Minimal GitHub Actions steps:

1. Setup Python 3.11
2. Install `requirements.txt` + `ruff`
3. `ruff check src tests`
4. `pytest tests -v`
