# Design Decisions & Rationale

## Overview

This document explains the core architectural and strategic decisions behind BetLab. It's written for engineers who appreciate the reasoning behind design tradeoffs, not just the final implementation. Each section covers a specific choice: why we made it, what alternatives we considered, and what we learned.

---

## 1. Why Half-Kelly Over Full-Kelly?

### The Decision

BetLab uses **Half-Kelly Criterion** for stake sizing, not the theoretically optimal Full-Kelly. This means for every bet where Full-Kelly recommends a 10% bankroll stake, we bet 5%.

### The Math

The Kelly Criterion formula gives the optimal fraction of bankroll to bet:

```text
f* = (b × p - q) / b
```

Where:

- `b` = odds - 1 (decimal odds minus 1)
- `p` = probability of winning
- `q` = 1 - p (probability of losing)

For example, with odds 2.0 (50% implied) and 55% actual win probability:

- Full-Kelly: f* = (1 × 0.55 - 0.45) / 1 = **0.10** (10% of bankroll)
- Half-Kelly: 0.10 × 0.5 = **0.05** (5% of bankroll)

### Why Half-Kelly?

**1. Human Psychology**
Full-Kelly assumes perfect risk tolerance and unwavering discipline. Humans are not rational. A 10% bankroll loss *feels* catastrophic and triggers panic. Half-Kelly reduces the psychological burden while still capturing 95%+ of theoretical gains.

**2. Model Uncertainty**
Our source accuracy estimates (53%, 60%, etc.) aren't ground truth—they're calibrated from observed results. If we're wrong by 2-3%, Full-Kelly can lead to severe bankroll swings. Half-Kelly acts as a safety buffer against model error.

**3. Real-World Variance**
Academic Kelly assumes infinite bet sequences. In practice, you might hit a 5-10 game losing streak. Full-Kelly bankroll could drop 20-30% during this period. Half-Kelly absorbs this variance with less emotional strain.

**4. Empirical Evidence**
Successful professional bettors (Pinnacle, sharp bettors) routinely use fractional Kelly (0.25-0.5) rather than full Kelly. This is not timidity—it's because they value *sustained long-term growth* over theoretical maximum growth.

### What We Didn't Do

We didn't use **Full-Kelly** because the portfolio would be volatile and psychologically grueling for a learning project. We also didn't use **1/4-Kelly** because with an ₹800 bankroll and careful analysis, Half-Kelly still provides meaningful edge capture once the system exits cold-start mode.

---

## 2. Why Correlation Checks in Parlays?

### Correlation Decision

Before assembling multi-leg parlays, BetLab checks whether selected bets are *independent*. If two legs are correlated (e.g., "Man City to win" + "Man City total shots > 8"), we reject the parlay or reassess.

### The Problem: Illusion of Independence

Parlay odds multiply: if you bet Man City @ 2.0 and Arsenal @ 2.0, the combined payout is 4.0, assuming independent outcomes.

**But they're not independent.** Why?

- **Same-match legs:** Man City win + Man City total goals both depend on Man City's performance. If City underperforms, both lose.
- **Correlated sports:** Goal-heavy leagues (Spain, Netherlands) inflate both "over" and "high-scoring team wins" probabilities simultaneously.
- **Market-wide correlation:** Liquidity crunches, surprise injuries, or weather affect multiple betting markets.

### Real-World Example

Imagine:

- **Leg 1:** Man City to beat Arsenal @ 2.0 (55% probability)
- **Leg 2:** Sergio Gómez (City left-back) to score @ 10.0 (assumed 10% independent probability)
- **Parlay odds:** 2.0 × 10.0 = 20.0
- **Independent probability:** 0.55 × 0.10 = 5.5% hit rate
- **Expected payout:** 20.0 × 0.055 = 1.10 (10% edge)

**Reality:** If Gómez only scores when City dominates (which is correlated with their win), his 10% probability *given City loses* is actually 0.1%, not 10%. The true parlay probability is ~3%, not 5.5%. We just bought a -45% EV bet thinking it was +10%.

### How We Check Correlation

BetLab flags potential issues:

1. **Same-match indicator:** Bets from the same game are marked for manual review.
2. **Market family:** Totals + spreads on the same team are tagged as potentially correlated.
3. **Sport/league heuristics:** Football parlays across different matches (different teams, leagues) are safer than same-league legs.

We don't have true correlation matrices (that would require historical data), but we use domain knowledge to avoid obvious pitfalls.

### Correlation Tradeoff

We didn't use **naive parlay assembly** (just multiply probabilities without checks). We also didn't implement **copula modeling** or fetch correlation from Pinnacle APIs—that's Phase 2 scope. For a learning project, heuristics suffice.

---

## 3. Why Local-First Architecture?

### Local-First Decision

BetLab stores everything locally: bets, results, odds, configuration. No cloud sync, no API calls (except Streamlit UI). Data never leaves your machine.

### Why This Approach?

**1. No External Dependencies**
If an odds API goes down, BetLab still works. You input odds manually (or copy from screenshots), and the engine analyzes them. This resilience is essential for a learning tool—no vendor lock-in, no surprise outages.

**2. Privacy & Autonomy**
Betting analytics are sensitive. Sending your bets to a cloud service means:

- Your betting patterns are profiled
- Someone could sell aggregated data to bookmakers
- Your strategy leaks if the service is compromised

Local-first means *you* own your data. Period.

**3. Simplicity for MVP**
Building a real-time odds API integration requires:

- Account setup (Pinnacle, CoinDrop, etc.)
- API credential management
- Rate limiting, caching, fallbacks
- Documentation of API quirks

For a portfolio project, this is overhead that doesn't showcase core logic. Local-first lets us focus on the math and risk management, which are the hard problems.

**4. Reproducibility**
Every recommendation is deterministic given fixed inputs. No randomness from API latency or market microstructure. You can audit every decision by reading the input file and config.

### Tradeoff: Manual Odds Entry

The cost is manual entry. You copy odds from your bookmaker into `bets.txt`. This is:

- **Slow:** ~2 minutes for 20 bets vs. 5 seconds with API
- **Error-prone:** Typos in odds or match names

But for a learning tool, this is acceptable. You engage with each bet consciously—no fire-and-forget.

### Local-First Tradeoff

We didn't build a **live odds ingestion engine** (Phase 1 scope). We didn't integrate with Betfair, DafaBet, or Pinnacle APIs. Those are listed as Phase 2 expansion points.

---

## 4. Why Modular Python Architecture?

### Modularity Decision

BetLab separates concerns into distinct modules:

- `parser.py` — Input parsing
- `math_engine.py` — Pure calculations
- `analyser.py` — Filtering and tagging
- `bankroll_mgr.py` — Risk management
- `parlay_builder.py` — Multi-leg construction
- `output_generator.py` — Report generation

Each module is testable in isolation.

### Why Modularity?

**1. Testability**
Each module has a clear interface. `math_engine` doesn't know about files; `parser` doesn't know about Kelly fractions. We test:

```python
# math_engine_test.py
assert half_kelly(odds=2.0, prob=0.55) == 0.05  # Deterministic math

# parser_test.py
assert parse_odds("1.85") == 1.85  # Format conversion
assert parse_odds("American: -110") == 1.909  # Format variety
```

Without modularity, testing "does the system output correct stakes?" requires setting up files, configs, and fixtures. Modularity lets us test the mathematical kernel separately.

**2. Maintainability**
If we discover a bug in stake sizing, it's in `bankroll_mgr.py`. If odds parsing is broken, it's `parser.py`. Bugs don't cascade through a monolithic script.

**3. Reusability**
The `math_engine` (odds conversion, Kelly, EV) is poker-table agnostic. We could plug it into:

- A different sport (cricket, tennis, esports)
- A different UI (CLI, API, Slack bot)
- Different risk rules (Thorp's Criterion, growth-optimal strategies)

Modularity enables experimentation without rewriting the core.

**4. Team Scalability**
If we added a team member, they can own `parlay_builder` without touching `parser`. Clear boundaries reduce merge conflicts and communication overhead.

### The Cost: Indirection

Reading code requires jumping between files. A monolithic script is simpler to grep through. But the tradeoff favors modularity for a project we'll maintain and extend.

---

## 5. Tradeoffs & What We Didn't Do

### Live Odds API Integration

**Why we didn't:** Phase 1 scope. Building real-time odds ingestion requires:

- Vendor account management (Pinnacle, CoinDrop, Betfair)
- API credential rotation, rate limiting
- Handling sports data quirks (different naming conventions, event IDs)
- Fallback strategies when APIs are slow

This adds 500+ lines of code and infrastructure that doesn't teach us anything new about risk management or EV analysis.

**Why it matters:** Phase 2 will add live odds. Once done, you can feed tips without copying odds manually, and BetLab auto-constructs parlays in real-time.

### Machine Learning for Accuracy

**Why we didn't:** Our source accuracy (53%, 60%) is simple Bayesian updating from historical wins/losses. This is transparent and testable.

ML models (logistic regression, gradient boosting) would predict win probability given features (odds, time-to-match, league). But they require:

- 1000+ historical tips (we have ~50)
- Feature engineering (what's predictive?)
- Overfitting risk (memorizing noise in 50 samples)

For a portfolio project, this is premature optimization. Once we have 500+ results, retraining on historical accuracy makes sense.

### Multi-Sport Support (Phase 1)

**Why we didn't:** BetLab is currently football-only. Adding cricket, tennis, esports requires:

- Different event structures (T20 has different dynamics than test cricket)
- Sport-specific accuracy profiles (10% edge in football ≠ 10% edge in tennis)
- Separate bankroll tracking or unified?

Monolithic design would handle this, but modular design makes it easier. We've stubbed `source_accuracy` in config for future sports.

### Loss-Chasing Prevention

**Why we didn't add it:** BetLab has stop-loss (halt if 50% bankroll loss) and losing-streak detection (reduce stakes after 5 losses in 7 days). We didn't add aggressive loss-chasing blockers like:

- "If down 20%, no bets today" (too rigid)
- "Ban same bet type after 2 consecutive losses" (ignores EV)

The philosophy: **trust the math**. If a bet has +2% EV and we size correctly, chasing it isn't irrational. Preventing all loss-induced bets assumes the human can't distinguish good variance from bad reasoning.

---

## 6. Lessons Learned & Reflection

### What We Got Right

**1. Transparency First**
Showing all calculations in the output (EV, Kelly %, hit probability) builds trust. You understand *why* each bet is recommended. This is underrated—most betting tools are black boxes.

**2. Consensus on Half-Kelly**
Research and industry practice (sharp bettors use fractional Kelly) aligned with what intuition suggested. Half-Kelly is a sweet spot: conservative enough to survive losing streaks, aggressive enough to capture edge.

**3. Local-First Enabled Rapid Iteration**
Without API complexity, we shipped Phase 1 (parsing, filtering, stake sizing) in two weeks. This gave us time to refine the UX and risk rules instead of debugging API latency.

### What We'd Do Differently

**1. Earlier Backtesting**
We should have implemented a backtesting harness *before* deploying. The spec sheet (53% accuracy) is theoretical. Real results might show 48% or 58%. Early backtesting would calibrate assumptions.

**2. Correlation Matrix from Day One**
Right now, correlation checks are heuristics. We hardcode "same match → potential issue." With 50+ historical bets, we could compute actual correlation matrix. This would eliminate false positives.

**3. Stakeholder Input Sooner**
The system now uses an ₹800 bankroll baseline and ₹200 daily cap, but we still need to keep asking: what's right for *your* bankroll? Configurable profiles (conservative, moderate, aggressive) would surface this earlier.

### Open Questions for Phase 2

1. **Does Half-Kelly hold up empirically?** After 200+ results, does 5% Kelly oscillation feel right, or does 2.5% feel better?
2. **How strong is source accuracy signal?** Is 53% real, or regression to 51%?
3. **Which correlation checks matter most?** Same-match correlation is obvious. Inter-league correlation is rare. What's the middle ground?

---

## Conclusion

BetLab embodies three principles:

1. **Transparency:** Every number is auditable. The edge is real, not marketing.
2. **Modularity:** Each phase is testable and swappable. You can replace the bankroll rules without rewriting the parser.
3. **Conservatism:** Half-Kelly, daily caps, and stop-loss favor sustained growth over maximum payout.

These decisions reflect a belief that betting is *skill*—mathematical, psychological, disciplined. BetLab is built for practitioners who want to understand their edge, not gamblers who want to feel lucky.

The project is a learning tool, not production-grade. It succeeds if it teaches engineering rigor and betting mathematics. It fails silently if overconfidence leads to real-money losses on untested strategies.

Use wisely. Bet small. Audit often.

---

**Built with intention. Documented with care.**
