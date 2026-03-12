# Portfolio Documentation Design for BetLab
**Date:** 2026-03-13
**Project:** BetLab — Sports Betting Analytics Engine
**Audience:** Hiring managers, senior engineers, fellow developers
**Format:** Modern portfolio style with Mermaid diagrams

---

## Executive Summary

Create a tiered documentation structure that showcases BetLab as a professional, well-designed portfolio project. The documentation will serve three audiences:
- **Hiring managers:** High-level architecture story (10 min read)
- **Senior engineers:** Design decisions and engineering rationale
- **Fellow developers:** Modular API reference with code examples

---

## Approved Design: Tiered Portfolio Approach

### 1. High-Level Architecture Doc (`docs/ARCHITECTURE.md`)

**Purpose:** First impression. The "story" of the system.

**Content:**
- Problem & Context — Why built, what problem solved
- System Overview — 2-3 sentence pitch + architecture diagram
- Key Design Principles — Simplicity, transparency, risk management
- Pipeline Architecture — 5-phase workflow with visual data flow
- Technology Stack — Python, Streamlit, pandas, pytest
- Links to deeper documentation

**Visual:** System architecture diagram (Mermaid flowchart showing parser → math_engine → analyser → bankroll_mgr → parlay_builder → output_generator)

---

### 2. Design Decisions Doc (`docs/DESIGN_DECISIONS.md`)

**Purpose:** Demonstrate engineering thinking and rationale.

**Content:**
- Why Half-Kelly Over Full-Kelly? — Risk mitigation philosophy
- Why Correlation Checks in Parlays? — Edge cases, real scenarios
- Why Local-First Architecture? — No API dependency, user data control
- Why Modular Python? — Separation of concerns, testability
- Tradeoffs Made — What wasn't done and why
- Lessons Learned — Self-awareness, what you'd do differently

---

### 3. Module Reference Docs (`docs/MODULES/`)

**6 files, one per module:**

#### `parser.md`
- Purpose: Parse bets in multiple odds formats
- Key functions: parse_decimal, parse_american, parse_fractional, validate_odds
- Dependencies: Standard library
- Code example: Parsing "1.85", "+115", "5/2"

#### `math_engine.md`
- Purpose: Core betting math (EV, Kelly, probability)
- Key functions: calculate_ev, calculate_kelly_fraction, calculate_parlay_probability
- Dependencies: None
- Code example: Calculate EV for a single bet

#### `analyser.md`
- Purpose: Filter bets by EV, apply confidence tagging
- Key functions: filter_by_ev, tag_candidates
- Dependencies: math_engine
- Code example: Tag bets as SINGLE_CANDIDATE or PARLAY_CANDIDATE

#### `bankroll_mgr.md`
- Purpose: Stake sizing using Half-Kelly, enforce daily caps
- Key functions: calculate_stake, apply_daily_cap, detect_losing_streak
- Dependencies: math_engine
- Code example: Size a stake for a bet with given confidence

#### `parlay_builder.md`
- Purpose: Construct parlays with correlation checks
- Key functions: check_correlation, build_parlay_combinations
- Dependencies: analyser, math_engine
- Code example: Build valid parlay from candidates

#### `output_generator.md`
- Purpose: Generate recommendations.md and CSV templates
- Key functions: generate_report, export_csv
- Dependencies: All others (reads results of pipeline)
- Code example: Generate markdown report

---

### 4. Diagrams (`docs/diagrams/`)

**Mermaid diagrams (GitHub-native rendering):**

1. **data_flow.mmd** — Input → Parse → EV Analysis → Kelly Sizing → Parlay → Output
2. **module_dependencies.mmd** — Module import graph
3. **pipeline_walkthrough.mmd** — Single bet through all 5 phases with example values
4. **README.md** — How to view diagrams locally

---

### 5. Enhanced README.md

Update root `README.md`:
- Add "Architecture & Design" section linking to `docs/ARCHITECTURE.md`
- Add "API Reference" section linking to `docs/MODULES/`
- Keep existing quick-start and configuration sections

---

## Directory Structure

```
betlab/
├── README.md (enhanced with doc links)
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DESIGN_DECISIONS.md
│   ├── MODULES/
│   │   ├── parser.md
│   │   ├── math_engine.md
│   │   ├── analyser.md
│   │   ├── bankroll_mgr.md
│   │   ├── parlay_builder.md
│   │   └── output_generator.md
│   ├── diagrams/
│   │   ├── data_flow.mmd
│   │   ├── module_dependencies.mmd
│   │   ├── pipeline_walkthrough.mmd
│   │   └── README.md
│   └── plans/
│       └── 2026-03-13-portfolio-documentation-design.md (this file)
├── config/
├── data/
├── src/
├── tests/
└── output/
```

---

## Rationale

**Why tiered?**
- Hiring managers see narrative (ARCHITECTURE.md) first
- Engineers can navigate to specific MODULES as needed
- Shows understanding of audience-driven documentation

**Why Mermaid?**
- Native GitHub rendering (no external tools needed)
- Version controlled, easy to update
- Professional appearance
- Diagrams embedded in README for easy discovery

**Why DESIGN_DECISIONS.md?**
- Shows engineering judgment, not just code
- Demonstrates you think about tradeoffs
- Attractive to senior engineers

---

## Success Criteria

✅ Portfolio reviewers can understand BetLab's architecture in <10 minutes
✅ Code reference is comprehensive (all modules, all key functions documented)
✅ Diagrams are clear and contribute to understanding, not clutter
✅ Documentation demonstrates professional software engineering practices
✅ Easy to update — modular structure means changes don't require overhaul
