# BetLab Implementation Playbooks

This folder contains step-by-step implementation documents for each roadmap section.

## Documents

1. [Highest Impact Improvements](01-highest-impact-improvements.md)
2. [Core Engine Enhancements](02-core-engine-enhancements.md)
3. [Data and Parsing Upgrades](03-data-parsing-upgrades.md)
4. [Risk Controls](04-risk-controls.md)
5. [Practical Build Order](05-practical-build-order.md)
6. [Project Completion Checklist](06-project-completion-checklist.md)

## How to Use

1. Start with [Practical Build Order](05-practical-build-order.md).
2. Use [Project Completion Checklist](06-project-completion-checklist.md) to close the remaining validation and release-readiness work.
3. Execute one phase at a time.
4. For each phase, follow the corresponding detailed playbook.
5. Run tests before and after each phase.
6. Update [plans/improvement/betlab-core-improvements-plan.md](../improvement/betlab-core-improvements-plan.md) with progress notes.

## Mandatory Validation Loop

1. Run parser and analysis smoke test with [Bets.txt](../../Bets.txt).
2. Run all tests in [tests/test_betlab.py](../../tests/test_betlab.py).
3. Run end-to-end pipeline and verify outputs in [output/recommendations.md](../../output/recommendations.md) and [output/bet_log_template.csv](../../output/bet_log_template.csv).
