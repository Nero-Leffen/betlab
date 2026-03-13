# BetLab API Reference

Scope: implementation-aligned contracts from `src/` for development use.

## parser.py

### Parser data classes

- `BetInput(match_name, market_type, selection, decimal_odds, confidence, sport='football', raw_odds_str='', line_number=0)`
- `ParseResult(bets: list[BetInput], prebuilt_parlays: list[dict], errors: list[dict])`

### Parser functions

- `parse_line(line: str, line_number: int) -> tuple[BetInput | None, str | None]`
  - Strict pipe format parser.
  - Returns `(None, None)` for blank/comment lines.
- `parse_bets_file(filepath: str | Path) -> ParseResult`
  - Reads full file.
  - Supports strict pipe lines and freeform `Match: Selection @ Odds` lines.
  - Supports `.xlsx` and `.xls` bet workbooks.
  - Extracts prebuilt parlays from worksheet-style `Parlays` sheets when present.
  - Writes parser errors to `data/logs/error_log.txt`.

## math_engine.py

### Odds conversion

- `detect_odds_format(raw: str) -> str`
- `american_to_decimal(american: float) -> float`
- `fractional_to_decimal(fractional: str) -> float`
- `to_decimal_odds(raw: str) -> float`

### Probability and EV

- `get_implied_probability(decimal_odds: float) -> float`
  - Formula: $1 / odds$
- `calculate_ev(decimal_odds: float, true_probability: float) -> float`
  - Formula: $(odds * p) - 1$
- `kelly_criterion(decimal_odds: float, true_probability: float) -> float`
  - Returns half-Kelly fraction, clamped at `>= 0`.

### Parlay math

- `parlay_hit_probability(leg_probabilities: list[float]) -> float`
- `apply_correlation_penalty(independent_probability: float, penalty_factor: float) -> float`
- `parlay_combined_odds(leg_odds: list[float]) -> float`

### Stake helper

- `kelly_stake_inr(decimal_odds, true_probability, bankroll_inr, unit_inr, min_units=1, max_units=2) -> float`

## analyser.py

### Analyser functions

- `get_true_probability(sport: str, accuracy_map: dict) -> float`
- `analyse_bets(bets: list[BetInput], accuracy_map: dict, min_ev_threshold: float, parlay_pool_size: int, market_priors: dict | None = None, results_df = None, calibration_cfg: dict | None = None, robustness_cfg: dict | None = None) -> list[dict]`

Supporting helpers:

- `get_market_prior(market_type: str, market_priors: dict) -> float`
- `compute_calibrated_probability(...) -> dict[str, Any]`
- `dedupe_bets(bets: list[BetInput]) -> tuple[list[BetInput], list[dict]]`
- `filter_conflicts(results: list[dict]) -> tuple[list[dict], list[dict]]`
- `ev_robustness_label(...) -> str`
- `apply_robustness_gate(...) -> list[dict]`
- `is_no_bet_day(results: list[dict]) -> bool`

Output dict keys:

- `match_name, market_type, selection, decimal_odds, confidence, sport`
- `true_probability, implied_probability, ev`
- `tag`: `SINGLE_CANDIDATE` or `PARLAY_CANDIDATE`
- `prob_source`: `prior`, `calibrated`, or `sport`
- `prob_sample_count`: effective calibration sample weight
- `ev_label`: `robust`, `marginal`, or `thin`

## bankroll_mgr.py

### Bankroll data classes

- `BankrollConfig(..., optimizer_cfg: dict = {})`
- `SizedBet(..., prob_source='prior', prob_sample_count=0, ev_label='marginal')`
- `BankrollSession(..., rejected_bets: list[dict] = [])`

### Bankroll functions

- `load_config(config_path='config/settings.yaml') -> BankrollConfig`
- `get_current_bankroll(results_path='data/results.csv') -> float`
- `check_losing_streak(results_path, window_days, threshold) -> tuple[bool, int]`
- `assign_stake(decimal_odds, true_probability, confidence, bankroll_inr, unit_inr, config) -> tuple[float, float]`
- `run_bankroll_session(filtered_bets: list, config: BankrollConfig, results_path='data/results.csv') -> BankrollSession`

Session behavior:

- Stop-loss check first.
- Losing-streak reduction second.
- Optional drawdown governor next.
- Stake sizing and priority sort next.
- Daily cap and optimizer exposure enforcement last.
- Rejected bets carry explicit reason text in `session.rejected_bets`.

## parlay_builder.py

### Parlay data classes

- `ParlayOption(legs, combined_odds, base_hit_probability, hit_probability, penalty_factor, stake_inr, parlay_ev, parlay_id='')`

### Parlay functions

- `build_parlays(sized_bets: list[SizedBet], parlay_stake_inr: float, max_legs=4, max_options=2, correlation_settings: dict | None = None) -> list[ParlayOption]`

Correlation internals used by `build_parlays`:

- `_extract_teams(match_name, selection) -> set[str]`
- `_is_correlated(bet_a, bet_b) -> bool`
- `_validate_parlay_legs(legs) -> bool`

## output_generator.py

### Output functions

- `generate_recommendations(session: BankrollSession, parlays: list[ParlayOption], output_dir='output') -> Path`
- `generate_bet_log_csv(session: BankrollSession, parlays: list[ParlayOption], output_dir='output') -> Path`
- `process_feedback(results_path='data/results.csv', sport='football') -> float | None`

`process_feedback` requires at least 5 completed `WIN/LOSS` rows before returning updated accuracy.

## main.py orchestration

Primary runtime entrypoint:

- `main()`

Pipeline executor:

- `run_analysis(bets_text, uploaded_file, config, accuracy_map, overrides)`

Config writeback helper:

- `_update_accuracy_in_config(new_accuracy: float)`
