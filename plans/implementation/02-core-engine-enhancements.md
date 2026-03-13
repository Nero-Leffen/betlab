# Core Engine Enhancements: Step-by-Step Implementation

## Scope

This playbook covers:
1. Multi-market priors.
2. Time-decay learning.
3. Outcome-grade handling.
4. Confidence auto-derivation.
5. Dynamic EV thresholds.

## Step 1: Multi-Market Priors

### Files
- [config/settings.yaml](../../config/settings.yaml)
- [src/analyser.py](../../src/analyser.py)

### Steps
1. Add priors per market family in config.
2. Map parser market labels to canonical families.
3. Select prior by canonical market family during analysis.
4. Fallback to default prior when market family missing.

### Acceptance
1. Same odds in different market families can produce different true probabilities.

## Step 2: Time-Decay Learning

### Files
- [src/output_generator.py](../../src/output_generator.py)
- [src/analyser.py](../../src/analyser.py)

### Steps
1. Load settled history from results file.
2. Compute decayed win rate using recency weights.
3. Blend decayed rate with prior using smoothing weight.
4. Store and expose effective sample weight.

### Acceptance
1. Recent outcomes influence model more than old outcomes.
2. Sparse periods still remain stable due to smoothing.

## Step 3: Outcome-Grade Handling

### Files
- [src/output_generator.py](../../src/output_generator.py)
- [src/bankroll_mgr.py](../../src/bankroll_mgr.py)

### Steps
1. Extend result vocabulary to include HALF_WIN, HALF_LOSS, PUSH, VOID.
2. Update PnL computation and bankroll updates accordingly.
3. Update calibration logic to score partial outcomes proportionally.
4. Add tests for all outcome grades.

### Acceptance
1. Partial outcomes update bankroll and learning correctly.
2. No crash when unknown result appears; it is ignored with warning.

## Step 4: Confidence Auto-Derivation

### Files
- [src/analyser.py](../../src/analyser.py)
- [src/output_generator.py](../../src/output_generator.py)

### Steps
1. Add score combining EV magnitude and uncertainty.
2. Map score bands to high, medium, low confidence.
3. Keep manual confidence as optional override.
4. Emit confidence source in output.

### Acceptance
1. Confidence can be auto-generated without manual tags.
2. Manual confidence still works when explicitly provided.

## Step 5: Dynamic Thresholds

### Files
- [config/settings.yaml](../../config/settings.yaml)
- [src/analyser.py](../../src/analyser.py)
- [src/bankroll_mgr.py](../../src/bankroll_mgr.py)

### Steps
1. Add threshold range config with base, strict, loose values.
2. Define drawdown and calibration quality triggers.
3. Raise threshold during downswings and weak calibration.
4. Lower threshold only when conditions are strong and stable.

### Acceptance
1. Threshold changes are deterministic and logged.
2. Candidates vary with risk state as expected.

## Tests To Add

1. Market-prior selection test.
2. Time-decay weighting monotonicity test.
3. Outcome-grade bankroll update tests.
4. Auto-confidence mapping test.
5. Dynamic threshold trigger tests.

## Completion Criteria

1. Analyzer outputs include probability source, confidence source, and effective threshold.
2. Bankroll and calibration are consistent with partial outcomes.
3. All tests pass with no regressions.
