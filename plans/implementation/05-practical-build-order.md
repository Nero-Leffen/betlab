# Practical Build Order: Step-by-Step Delivery Plan

## Purpose

This document gives a precise execution sequence to implement improvements safely in a solo workflow.

## Phase 1: Correlation-Aware Parlay Engine

### Why first
Fastest quality gain with limited blast radius.

### Steps
1. Add penalty config in [config/settings.yaml](../../config/settings.yaml).
2. Implement penalty function in [src/math_engine.py](../../src/math_engine.py).
3. Integrate adjusted probability in [src/parlay_builder.py](../../src/parlay_builder.py).
4. Add tests in [tests/test_betlab.py](../../tests/test_betlab.py).
5. Validate with [Bets.txt](../../Bets.txt).

### Done when
- Parlays still generate when valid.
- Correlated combos show lower adjusted EV.

## Phase 2: Dynamic Probability Calibration

### Why second
Improves all downstream decisions.

### Steps
1. Add priors and calibration settings in [config/settings.yaml](../../config/settings.yaml).
2. Build calibration utility in [src/analyser.py](../../src/analyser.py).
3. Integrate settled result learning from [data/results.csv](../../data/results.csv) handling in [src/output_generator.py](../../src/output_generator.py).
4. Add tests and fallback guards.

### Done when
- Analyzer no longer relies only on fixed default probability.
- Output shows probability source and sample context.

## Phase 3: Session-Level Bankroll Optimizer

### Why third
Converts better signal quality into better capital usage.

### Steps
1. Define optimization constraints in config.
2. Implement allocation pass in [src/bankroll_mgr.py](../../src/bankroll_mgr.py).
3. Keep deterministic tie-breaking.
4. Add exposure and cap tests.

### Done when
- Final stake set obeys all caps and constraints.
- Rejection reasons are logged.

## Phase 4: Dedupe and Conflict Rules

### Why fourth
Reduces input noise and contradictory recommendations.

### Steps
1. Add canonical mappings in [src/parser.py](../../src/parser.py).
2. Add dedupe and conflict policy in [src/analyser.py](../../src/analyser.py).
3. Ensure parlay leg selection uses canonical entities in [src/parlay_builder.py](../../src/parlay_builder.py).
4. Add alias and conflict tests.

### Done when
- Equivalent picks collapse correctly.
- Opposing picks are not both recommended.

## Phase 5: EV Robustness and Uncertainty Display

### Why fifth
Adds final decision quality guardrails and transparency.

### Steps
1. Add robustness gates in [src/analyser.py](../../src/analyser.py).
2. Add display labels in [src/output_generator.py](../../src/output_generator.py).
3. Add optional UI indicators in [src/main.py](../../src/main.py).
4. Add quality-gate tests.

### Done when
- Parlay pool includes only robust candidates.
- Report shows confidence and uncertainty labels.

## Per-Phase Development Loop

1. Update config schema and defaults.
2. Implement logic in smallest vertical slice.
3. Add tests for new behavior.
4. Run full tests.
5. Run smoke flow with [Bets.txt](../../Bets.txt).
6. Review generated outputs.

## Commands

1. Install dependencies:
python -m pip install -r requirements.txt

2. Run tests:
python -m pytest tests -v

3. Run app:
python -m streamlit run src/main.py

## Exit Criteria For Entire Plan

1. All phases complete with passing tests.
2. Daily prototype usage is stable and explainable.
3. No silent parse, risk, or parlay failures in repeated runs.
