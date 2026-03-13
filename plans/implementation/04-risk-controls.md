# Risk Controls: Step-by-Step Implementation

## Scope

This playbook covers:
1. Exposure caps by dimension.
2. Drawdown-based governor.
3. Variance-aware stake scaling.
4. No-bet day mode.

## Step 1: Exposure Caps by Dimension

### Files
- [config/settings.yaml](../../config/settings.yaml)
- [src/bankroll_mgr.py](../../src/bankroll_mgr.py)

### Steps
1. Add cap settings for team, league, market, and day.
2. Build exposure tracker for selected candidates in current session.
3. Reject candidates that breach any cap.
4. Log exact rejection reason for each dropped candidate.

### Acceptance
1. Exposure limits are always enforced.
2. Rejection reason is visible in report.

## Step 2: Drawdown-Based Governor

### Files
- [src/bankroll_mgr.py](../../src/bankroll_mgr.py)
- [config/settings.yaml](../../config/settings.yaml)

### Steps
1. Compute rolling peak bankroll and current drawdown.
2. Define drawdown tiers with unit multipliers.
3. Apply multiplier before final stake allocation.
4. Keep stop-loss as hard emergency cut-off.

### Acceptance
1. Stakes reduce progressively as drawdown deepens.
2. Behavior is deterministic for same input state.

## Step 3: Variance-Aware Stake Scaling

### Files
- [src/bankroll_mgr.py](../../src/bankroll_mgr.py)
- [src/parlay_builder.py](../../src/parlay_builder.py)
- [config/settings.yaml](../../config/settings.yaml)

### Steps
1. Add variance class per market and parlay leg count.
2. Map variance class to scaling factors.
3. Apply scaling after base stake calculation and before caps.
4. Log final scaling factor in output rationale.

### Acceptance
1. High-variance candidates receive lower final stake.
2. Scaling is transparent in output.

## Step 4: No-Bet Day Mode

### Files
- [src/analyser.py](../../src/analyser.py)
- [src/bankroll_mgr.py](../../src/bankroll_mgr.py)
- [src/output_generator.py](../../src/output_generator.py)

### Steps
1. Define no-bet triggers:
- low number of robust candidates
- high average correlation score
- calibration quality below floor
- drawdown severity above ceiling
2. Evaluate triggers after candidate scoring.
3. If triggered, return no recommendations and explicit reasons.
4. Surface trigger details in report and UI summary.

### Acceptance
1. System can intentionally return zero bets with clear rationale.
2. No-bet logic is test-covered and reproducible.

## Tests To Add

1. Cap breach tests for each dimension.
2. Drawdown tier transition tests.
3. Variance scaling tests for singles and parlays.
4. No-bet mode trigger matrix tests.

## Completion Criteria

1. Risk controls are enforced before output generation.
2. Every rejection has explicit reason text.
3. Test coverage protects all risk gates.
