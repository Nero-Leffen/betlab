# Parlay Correlation

## Why this exists

Parlay probability multiplication assumes independent legs. Correlated legs inflate perceived EV and can create false-positive parlays.

## Current implemented logic

Used in `src/parlay_builder.py`:

1. Candidate pool:

- Only bets tagged `PARLAY_CANDIDATE` are used.

1. Correlation rejection rules:

- Reject if two legs are from the same match.
- Reject if extracted team tokens overlap.

1. Construction:

- Try combinations from `max_legs` down to 2.
- Keep only non-correlated combinations.
- Compute:
  - Combined odds via product of leg odds
  - Hit probability via product of leg probabilities
  - Parlay EV: $(combined\_odds \times hit\_probability) - 1$
- Return top `max_options` by parlay EV.

## Heuristic limitations

- Team extraction is string-based and can miss aliases.
- No historical covariance matrix.
- League-level or market-family dependence is not explicitly modeled.

## Scoring roadmap (next iteration)

Use a lightweight additive penalty score:

- Same match: +1.00 (auto reject)
- Same team token: +0.70
- Same league and kickoff window: +0.30
- Same market family (totals/spreads): +0.25

Decision:

- Reject if score >= 1.00
- Warn if score in [0.50, 0.99]
- Accept if score < 0.50

This keeps behavior interpretable while improving beyond binary overlap checks.
