# Configuration Reference

Source of truth: `config/settings.yaml`.

## Sections

- `bankroll`
- `bankroll_policy`
- `strategy`
- `market_priors`
- `calibration`
- `source_accuracy`
- `risk`
- `optimizer`
- `ev_robustness`
- `confidence_stake_map`

## bankroll

| Key | Current Default | Meaning | Valid Range | Restart Needed |
| --- | ---: | --- | --- | --- |
| `total_inr` | 800 | Base bankroll used for session sizing | `> 0` | No (UI override exists) |
| `unit_inr` | 25 | 1 unit in INR | `> 0` | Yes |
| `max_daily_stake_inr` | 200 | Hard daily stake cap | `> 0` | Yes |
| `stop_loss_inr` | 400 | Halt betting when bankroll is at or below this | `>= 0` | Yes |

## bankroll_policy

| Key | Current Default | Meaning |
| --- | ---: | --- |
| `mode` | `cold_start` | Uses flat stakes until enough settled history exists |
| `cold_start_min_settled_bets` | `20` | Number of completed results required before leaving cold-start mode |
| `cold_start_flat_stake_inr` | `25` | Flat stake applied to singles during cold-start mode |
| `cold_start_max_total_exposure_inr` | `75` | Max total singles exposure allowed during cold-start mode |
| `cold_start_max_parlay_options` | `1` | Max parlay options allowed during cold-start mode |

## strategy

| Key | Current Default | Meaning | Valid Range |
| --- | ---: | --- | --- |
| `min_ev_threshold` | 0.02 | Minimum EV to keep a bet | `0.0` to `1.0` |
| `kelly_enabled` | `true` | Intended toggle (currently sizing still uses Kelly path) | `true/false` |
| `parlay_max_legs` | 4 | Maximum legs attempted per parlay | `2+` |
| `parlay_pool_size` | 4 | Top N EV bets eligible for parlay pool | `2+` |
| `parlay_max_options` | 2 | Max parlay suggestions returned | `1+` |

`parlay_correlation` subkeys:

| Key | Current Default | Meaning |
| --- | ---: | --- |
| `enabled` | `true` | Enables soft probability penalty for correlated parlays |
| `min_factor` | `0.85` | Floor for final parlay hit-probability multiplier |
| `same_market_weight` | `0.10` | Penalty added for same market family |
| `shared_token_weight` | `0.10` | Penalty scaled by token overlap between legs |
| `shared_sport_weight` | `0.00` | Optional broad same-sport penalty |

## market_priors

| Key | Current Default | Meaning |
| --- | ---: | --- |
| `moneyline` | `0.53` | Base true probability for 1X2 / moneyline markets |
| `btts` | `0.52` | Base true probability for BTTS markets |
| `totals` | `0.54` | Base true probability for totals / over-under markets |
| `handicap` | `0.51` | Base true probability for handicap markets |
| `freeform` | `0.53` | Base true probability for freeform parsed markets |
| `default` | `0.53` | Fallback when no family match exists |

## calibration

| Key | Current Default | Meaning |
| --- | ---: | --- |
| `min_sample_size` | `10` | Minimum effective settled sample before calibration is used |
| `time_decay_halflife_days` | `30` | Recency half-life for result weighting |
| `smoothing_weight` | `0.30` | Prior weight in the prior/live blend |

## source_accuracy

| Key | Current Default | Meaning |
| --- | ---: | --- |
| `football` | 0.53 | Win-rate estimate for football bets |
| `default` | 0.53 | Fallback when sport key is unknown |

Guideline:

- Keep values in `(0, 1)`.
- Update after enough settled results.

## risk

| Key | Current Default | Meaning |
| --- | ---: | --- |
| `stop_loss_percentage` | 50 | Informational safety threshold (secondary to `stop_loss_inr`) |
| `losing_streak_window_days` | 7 | Rolling streak window |
| `losing_streak_threshold` | 5 | Loss count that triggers warning mode |
| `reduced_unit_multiplier` | 0.5 | Unit shrink factor during streak warning |

## optimizer

| Key | Current Default | Meaning |
| --- | ---: | --- |
| `enabled` | `true` | Enables exposure-based portfolio filtering |
| `max_exposure_per_team_inr` | `75` | Max total stake allocated to one team/selection |
| `max_exposure_per_market_inr` | `100` | Max total stake allocated to one market family |

`max_exposure_per_confidence` subkeys:

| Key | Current Default | Meaning |
| --- | ---: | --- |
| `high` | `100` | Max stake for high-confidence bets |
| `medium` | `100` | Max stake for medium-confidence bets |
| `low` | `50` | Max stake for low-confidence bets |

`drawdown_governor` subkeys:

| Key | Current Default | Meaning |
| --- | ---: | --- |
| `enabled` | `true` | Enables unit-size reduction during drawdowns |
| `tiers[].drawdown_pct` | `10, 20, 30` | Drawdown thresholds in percent |
| `tiers[].unit_multiplier` | `0.75, 0.50, 0.25` | Applied unit multiplier once threshold is hit |

## ev_robustness

| Key | Current Default | Meaning |
| --- | ---: | --- |
| `enabled` | `false` | Enables EV quality labeling and parlay gating |
| `margin_pct` | `0.02` | Extra EV margin above threshold required to avoid `thin` label |
| `parlay_require_robust` | `true` | Keeps `thin` bets out of the parlay pool when enabled |

## confidence_stake_map

| Key | Current Default | Meaning |
| --- | ---: | --- |
| `high` | 2 | Max units allowed for high confidence |
| `medium` | 1 | Max units for medium confidence |
| `low` | 1 | Max units for low confidence |

## Operator policy target profile (requested)

This is your target policy profile for documentation and operations:

- Bankroll baseline: INR 800
- Daily risk cap: INR 200
- Max stake per bet: 10% bankroll
- Max open exposure: 20% bankroll
- Session growth target: +25% to +30%

Important:

- `max stake 10%` and `max exposure 20%` are policy targets.
- They are not yet enforced as explicit per-bet/open-exposure config keys.
- Current code does enforce daily cap plus team, market, and confidence exposure caps.

## Example profile snippet

```yaml
bankroll:
  total_inr: 800
  unit_inr: 25
  max_daily_stake_inr: 200
  stop_loss_inr: 400
```
