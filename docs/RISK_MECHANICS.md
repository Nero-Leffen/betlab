# Risk Mechanics

## Objective

Protect bankroll first, then optimize growth.

## Core formulas

### Expected Value

$$EV = (odds \times p) - 1$$

### Half-Kelly fraction

$$f_{half} = 0.5 \times \frac{(b \times p - q)}{b}$$
where $b = odds - 1$ and $q = 1 - p$.

### INR stake from Kelly

1. Compute $f_{half}$.
2. Raw stake = $f_{half} \times bankroll$.
3. Round to nearest unit.
4. Clamp by confidence max units.

## Current enforced controls (code)

- Daily cap: `max_daily_stake_inr` (default 200)
- Stop-loss halt: `stop_loss_inr` (default 250)
- Losing streak mode:
  - Window: 7 days
  - Threshold: 5 losses
  - Unit multiplier: 0.5
- Drawdown governor:
  - Optional tiered unit reduction based on bankroll drawdown
  - Default tiers: 10%, 20%, 30%
- Exposure caps:
  - Per-team / selection stake cap
  - Per-market-family stake cap
  - Per-confidence-band stake cap
- Rejected bets are recorded with explicit reason text.
- Priority under cap pressure: highest EV first, confidence as tiebreak.

## Operator target policy (requested)

- Baseline bankroll: INR 800
- Daily risk cap: INR 200
- Max stake per bet: 10% bankroll
- Max open exposure: 20% bankroll
- Session growth objective: +25% to +30%

Implementation note:

- Daily cap is already enforced.
- Team, market, and confidence exposure caps are already enforced in code.
- 10% per-bet and 20% open-exposure are still policy-level rules and are not yet hard-enforced as explicit config keys.

## Practical guardrails

- Never increase stake after a loss.
- If stop-loss is hit, no recommendations should be produced.
- If streak warning is active, keep reduced unit until performance stabilizes.
