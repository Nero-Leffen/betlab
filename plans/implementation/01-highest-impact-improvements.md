# Highest Impact Improvements: Step-by-Step Implementation

## Scope

This playbook covers:
1. Dynamic calibrated probability model.
2. Correlation-aware parlay probability.
3. Session-level bankroll optimization.
4. Duplicate and conflict resolution.
5. EV robustness quality gates.

## Preconditions

1. Baseline tests pass in [tests/test_betlab.py](../../tests/test_betlab.py).
2. Current settings are documented in [config/settings.yaml](../../config/settings.yaml).
3. A baseline output is captured using [Bets.txt](../../Bets.txt).

## Step 1: Dynamic Calibrated Probability Model

### Goal
Replace single fixed accuracy with dynamic probability by market type, odds band, and source.

### Files
- [src/analyser.py](../../src/analyser.py)
- [src/output_generator.py](../../src/output_generator.py)
- [config/settings.yaml](../../config/settings.yaml)

### Steps
1. Add config block for market priors and odds bands.
2. Add calibration utility in analyzer to compute blended true probability.
3. Blend formula should combine base prior and recent realized win rate.
4. Add fallback path when sample count is below minimum.
5. Add output fields showing chosen probability source and sample size.

### Acceptance
1. Analyzer returns true probability with source metadata.
2. Sparse data always falls back to priors.
3. Existing flow remains backward compatible.

## Step 2: Correlation-Aware Parlay Probability

### Goal
Lower over-optimistic parlay estimates with a transparent penalty factor.

### Files
- [src/parlay_builder.py](../../src/parlay_builder.py)
- [src/math_engine.py](../../src/math_engine.py)
- [config/settings.yaml](../../config/settings.yaml)

### Steps
1. Add penalty weights in config for league overlap, market overlap, kickoff proximity, and team overlap.
2. Add helper in math engine to apply penalty factor c where 0 < c <= 1.
3. In parlay builder, compute pairwise overlap score for each leg pair.
4. Convert overlap score to penalty factor.
5. Apply adjusted probability before parlay EV calculation.
6. Add rationale fields to parlay output showing penalty reason.

### Acceptance
1. Same-structure parlays get lower adjusted hit probability than independent product.
2. Non-overlapping parlays remain near baseline.
3. At least one test validates penalty application.

## Step 3: Session-Level Bankroll Optimization

### Goal
Allocate stake portfolio-wide under constraints instead of isolated per-bet rounding.

### Files
- [src/bankroll_mgr.py](../../src/bankroll_mgr.py)
- [config/settings.yaml](../../config/settings.yaml)

### Steps
1. Add exposure constraints in config by league, team, market, confidence band.
2. Build candidate stake table from analyzer outputs.
3. Implement greedy or bounded optimizer maximizing adjusted utility under cap.
4. Enforce hard constraints in deterministic order.
5. Keep current stop-loss as hard override.
6. Emit rejection reasons for dropped candidates.

### Acceptance
1. Daily cap is never exceeded.
2. Exposure caps always hold.
3. Tie-breaking is deterministic and testable.

## Step 4: Duplicate and Conflict Resolution

### Goal
Prevent semantic duplicates and mutually conflicting picks in same event.

### Files
- [src/parser.py](../../src/parser.py)
- [src/analyser.py](../../src/analyser.py)
- [src/parlay_builder.py](../../src/parlay_builder.py)

### Steps
1. Define canonical mapping for markets and selections.
2. Normalize equivalent labels before analysis.
3. Build duplicate key using match ID, market canonical, selection canonical.
4. Keep best version by odds quality and parse confidence.
5. Detect direct conflicts and mark both for review or drop lower score.

### Acceptance
1. Duplicate picks collapse to one canonical candidate.
2. Conflicting picks are never both promoted to final bet list.

## Step 5: EV Robustness Quality Gates

### Goal
Promote only robust edges, not fragile near-threshold values.

### Files
- [src/analyser.py](../../src/analyser.py)
- [config/settings.yaml](../../config/settings.yaml)

### Steps
1. Add minimum sample gate for calibration-based EV.
2. Add uncertainty margin around EV and probability.
3. Add quality tier labels: robust, marginal, reject.
4. Restrict parlay pool to robust candidates only.
5. Add quality tier to output and UI summary.

### Acceptance
1. Marginal EV picks can appear in singles but are excluded from parlay pool.
2. Robustness tier appears in outputs.

## Validation Commands

1. Run tests: python -m pytest tests -v
2. Run smoke parse: python -m pytest tests/test_betlab.py -k parser -v
3. Run app: python -m streamlit run src/main.py

## Deliverable Checklist

1. Config updated with defaults and comments.
2. New tests added for each feature block.
3. No regression in existing tests.
4. Output report contains new rationale fields.
