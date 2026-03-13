# BetLab Setup

## Goal

Get a fresh machine to first successful run in under 10 minutes.

## Baseline

- OS: Windows (PowerShell examples below)
- Python: 3.11
- Package manager: pip

## 1. Create virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

## 2. Install dependencies

```powershell
pip install -r requirements.txt
pip install ruff
```

## 3. Verify project paths

Required folders:

- `config/`
- `data/`
- `data/logs/`
- `output/`

If missing, create:

```powershell
New-Item -ItemType Directory -Force data\logs, output | Out-Null
```

## 4. Run checks (lint + tests)

```powershell
ruff check src tests
pytest tests -v
```

## 5. Start the app

```powershell
streamlit run src/main.py
```

Open `http://localhost:8501`.

## 6. Quick smoke input

Paste into app:

```text
Man City vs Arsenal | 1X2 | Man City | 1.85 | High
Liverpool vs Chelsea | Over/Under | Over 2.5 | 1.95 | Medium
```

Expected outcome:

- At least one parsed bet
- `output/recommendations.md` generated
- `output/bet_log_template.csv` generated

## Recommended operator preset (your target)

These are policy targets for your sessions:

- Default bankroll: INR 800
- Daily risk cap: INR 200
- Max stake per bet: 10% bankroll
- Max open exposure: 20% bankroll
- Session growth target: +25% to +30%

Current code defaults in `config/settings.yaml` use the 800 INR prototype baseline and cold-start fixed-stake mode for first-run sessions.

## Common failures

- `ModuleNotFoundError`: activate `.venv` before running commands.
- `streamlit: command not found`: reinstall with `pip install -r requirements.txt`.
- Tests fail after config edits: restore valid YAML indentation in `config/settings.yaml`.
