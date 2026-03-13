# Data Formats

This file defines the technical contracts used by parser, outputs, and feedback loop.

## 1. Input: bets file

Primary format (pipe-delimited):

```text
Match Name | Market Type | Selection | Odds | [Confidence]
```

Fields:

- `Match Name` required
- `Market Type` required
- `Selection` required
- `Odds` required
- `Confidence` optional (`high`, `medium`, `low`; default `medium`)

Accepted odds syntax:

- Decimal: `1.85`
- American: `+150`, `-110`
- Fractional: `5/2`

Freeform fallback format also supported:

```text
Match Name: Selection @ Odds
Match Name: Pick A @ 2.10 OR Pick B @ 1.70
```

## 2. Parser error log

File: `data/logs/error_log.txt`

Behavior:

- Written each parse run.
- Includes line number and parser failure message.
- Blank/comment/noise lines are skipped silently.

## 3. Output: recommendations markdown

File: `output/recommendations.md`

Contains:

- Session header (date, bankroll, effective unit)
- Stop-loss/streak/cap warnings
- Singles table
- Per-bet rationale
- Parlay options with combined odds, hit probability, EV

## 4. Output: bet log CSV template

File: `output/bet_log_template.csv`

Schema:

| Column | Type | Required | Notes |
| --- | --- | --- | --- |
| `date` | date string | yes | `YYYY-MM-DD` |
| `bet_id` | string | yes | `BL-YYYYMMDD-###` or `PARLAY-#` |
| `type` | enum | yes | `single` or `parlay` |
| `match` | string | yes | Match or combined leg matches |
| `selection` | string | yes | Bet pick or leg summary |
| `odds` | float | yes | Decimal odds |
| `stake_inr` | float | yes | Stake amount in INR |
| `result` | enum | no | `WIN`, `LOSS`, `VOID` (user fill) |
| `pnl_inr` | float | no | User fill after settlement |
| `notes` | string | no | Optional metadata |

## 5. Feedback input

File: `data/results.csv`

Minimum columns required for recalibration:

- `result`

Recommended columns:

- full `bet_log_template.csv` schema

Recalibration rule:

- At least 5 completed rows where `result in {WIN, LOSS}`.
