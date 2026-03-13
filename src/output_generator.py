"""
output_generator.py
===================
Phase 5: Generate all BetLab output files.

Outputs:
  - output/recommendations.md   — Human-readable analysis report
  - output/bet_log_template.csv — Blank tracking CSV for the user
  - Feedback loop: read results.csv, recalculate accuracy, prompt confirmation
"""

from __future__ import annotations
import csv
import logging
from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd

from src.bankroll_mgr import SizedBet, BankrollSession
from src.parlay_builder import ParlayOption

logger = logging.getLogger(__name__)

DISCLAIMER = """
---
> ⚠️ **WARNING:** Sports betting involves financial risk. This system is for **educational purposes only**.
> Past performance does not guarantee future results. Only bet what you can afford to lose.
> Ensure compliance with local laws — including the **Indian Public Gambling Act** and
> state-specific restrictions in **Telangana** and **Andhra Pradesh** where online betting is prohibited.
> This tool does not recommend bookmakers or facilitate any transactions.
---
"""


def _ev_pct(ev: float) -> str:
    return f"{ev * 100:.2f}%"


def _prob_pct(p: float) -> str:
    return f"{p * 100:.1f}%"


def generate_recommendations(
    session: BankrollSession,
    parlays: list[ParlayOption],
    output_dir: str | Path = "output",
) -> Path:
    """
    Write the full recommendations.md report.
    Returns the path to the generated file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "recommendations.md"

    today = date.today().strftime("%A, %d %B %Y")
    singles = session.sized_bets
    total_parlay_stake = sum(p.stake_inr for p in parlays)
    grand_total = session.total_stake_inr + total_parlay_stake

    # Expected ROI (weighted average EV of singles)
    if singles:
        avg_ev = sum(b.ev * b.stake_inr for b in singles) / session.total_stake_inr
    else:
        avg_ev = 0.0

    lines = []

    # ── Header ──────────────────────────────────────────────────────────────
    lines += [
        f"# 📊 BetLab Recommendations",
        f"**Date:** {today}  ",
        f"**Bankroll:** ₹{session.bankroll_inr:.0f} INR  ",
        f"**Effective Unit:** ₹{session.effective_unit_inr:.0f} INR  ",
        "",
    ]

    # ── Warnings ────────────────────────────────────────────────────────────
    if session.stop_loss_triggered:
        lines += [
            "## 🛑 STOP-LOSS TRIGGERED",
            f"> Bankroll has dropped to ₹{session.bankroll_inr:.0f} INR.",
            "> **No bets recommended.** Please pause, review your strategy, and only resume when ready.",
            "",
            DISCLAIMER,
        ]
        _write_file(out_path, lines)
        return out_path

    if session.streak_warning:
        lines += [
            f"## ⚠️ Losing Streak Warning",
            f"> **{session.streak_count} losses** detected in the last 7 days.",
            f"> Unit size has been **reduced to ₹{session.effective_unit_inr:.0f} INR** for this session.",
            "> Do NOT increase stakes to chase losses.",
            "",
        ]

    if session.cold_start_active:
        lines += [
            "## 🧪 Cold-Start Bankroll Mode",
            f"> Only **{session.completed_results_count} completed results** are available, so BetLab is using flat ₹{session.effective_unit_inr:.0f} stakes.",
            "> Kelly is still shown for reference, but first-run bankroll management remains fixed-stake and capped.",
            "",
        ]

    if session.cap_hit:
        lines += [
            "## ℹ️ Daily Cap Note",
            f"> Some bets were dropped to keep total stake within the ₹200 INR daily limit.",
            "",
        ]

    # ── Session Summary ──────────────────────────────────────────────────────
    lines += [
        "## 📋 Session Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Singles Recommended | {len(singles)} |",
        f"| Parlay Options | {len(parlays)} |",
        f"| Total Singles Stake | ₹{session.total_stake_inr:.0f} INR |",
        f"| Total Parlay Stake | ₹{total_parlay_stake:.0f} INR |",
        f"| **Grand Total at Risk** | **₹{grand_total:.0f} INR** |",
        f"| Expected Edge (Singles) | {_ev_pct(avg_ev)} |",
        "",
    ]

    # ── Singles ──────────────────────────────────────────────────────────────
    lines += [
        "## 🎯 Singles",
        "",
        "| # | Match | Selection | Odds | Confidence | Stake (₹) | EV% | Kelly% |",
        "|---|-------|-----------|------|------------|-----------|-----|--------|",
    ]

    if not singles:
        lines.append("| — | No bets passed the EV filter today. | | | | | | |")
    else:
        for i, b in enumerate(singles, start=1):
            lines.append(
                f"| {i} | {b.match_name} | {b.selection} | {b.decimal_odds:.2f} "
                f"| {b.confidence.title()} | ₹{b.stake_inr:.0f} "
                f"| {_ev_pct(b.ev)} | {_ev_pct(b.kelly_fraction)} |"
            )

    lines.append("")

    # ── Singles Rationale ────────────────────────────────────────────────────
    if singles:
        lines += ["### 📝 Rationale", ""]
        for b in singles:
            lines += [
                f"**{b.bet_id} — {b.selection} @ {b.decimal_odds:.2f}**",
                f"- **Match:** {b.match_name} ({b.market_type})",
                f"- **EV:** {_ev_pct(b.ev)} — Passes the 2% minimum edge threshold.",
                f"- **True Probability Used:** {_prob_pct(b.true_probability)} "
                  f"(source: {b.prob_source}"
                  + (f", n≈{b.prob_sample_count}" if b.prob_source == "calibrated" else "")
                  + ")",
                f"- **Implied Probability:** {_prob_pct(b.implied_probability)} "
                  f"(bookmaker's break-even)",
                                f"- **Kelly Fraction:** {_ev_pct(b.kelly_fraction)} of bankroll"
                                    + (" (reference only in cold-start mode)" if session.cold_start_active else "")
                                    + f" → rounded to ₹{b.stake_inr:.0f} INR ({int(b.stake_inr / session.effective_unit_inr)} unit(s))",
                f"- **Risk Level:** {b.confidence.title()} confidence",
                f"- **EV Quality:** {b.ev_label.upper()}",
                "",
            ]

    # ── Parlays ───────────────────────────────────────────────────────────────
    lines += ["## 🎲 Parlay Options", ""]

    if not parlays:
        lines.append("_No valid parlays could be constructed from today's candidates._")
    else:
        for p in parlays:
            lines += [
                f"### {p.parlay_id}",
                "",
                f"| Leg | Selection | Odds |",
                f"|-----|-----------|------|",
            ]
            for leg in p.legs:
                lines.append(f"| {leg.match_name} | {leg.selection} | {leg.decimal_odds:.2f} |")

            lines += [
                "",
                f"| Metric | Value |",
                f"|--------|-------|",
                f"| Combined Odds | {p.combined_odds:.2f} |",
                                f"| Base Hit Probability | {_prob_pct(p.base_hit_probability)} |",
                                f"| Correlation Penalty Factor | {p.penalty_factor:.3f} |",
                f"| Hit Probability | {_prob_pct(p.hit_probability)} |",
                f"| Parlay EV | {_ev_pct(p.parlay_ev)} |",
                f"| Stake | ₹{p.stake_inr:.0f} INR (1 unit) |",
                "",
                                f"> 💡 Base hit probability {_prob_pct(p.base_hit_probability)} adjusted by "
                                    f"penalty factor {p.penalty_factor:.3f} gives final hit probability "
                                    f"{_prob_pct(p.hit_probability)}. "
                  f"At combined odds of {p.combined_odds:.2f}, this is a high-variance play.",
                "",
            ]

    # ── Disclaimer ───────────────────────────────────────────────────────────
    lines += ["", DISCLAIMER]

    _write_file(out_path, lines)
    logger.info("Recommendations written to %s", out_path)
    return out_path


def generate_bet_log_csv(
    session: BankrollSession,
    parlays: list[ParlayOption],
    output_dir: str | Path = "output",
) -> Path:
    """
    Write bet_log_template.csv — blank tracking file for the user.
    Pre-fills today's bets; user fills in result and pnl_inr after the event.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "bet_log_template.csv"

    today = date.today().isoformat()
    rows = []

    for b in session.sized_bets:
        rows.append({
            "date": today,
            "bet_id": b.bet_id,
            "type": "single",
            "match": b.match_name,
            "selection": b.selection,
            "odds": b.decimal_odds,
            "stake_inr": b.stake_inr,
            "result": "",       # WIN / LOSS / VOID — user fills in
            "pnl_inr": "",      # user fills in after result
            "notes": "",
        })

    for p in parlays:
        rows.append({
            "date": today,
            "bet_id": p.parlay_id,
            "type": "parlay",
            "match": " + ".join(b.match_name for b in p.legs),
            "selection": p.leg_summary,
            "odds": p.combined_odds,
            "stake_inr": p.stake_inr,
            "result": "",
            "pnl_inr": "",
            "notes": f"{len(p.legs)}-leg parlay",
        })

    fieldnames = ["date", "bet_id", "type", "match", "selection",
                  "odds", "stake_inr", "result", "pnl_inr", "notes"]

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    logger.info("Bet log template written to %s", out_path)
    return out_path


def process_feedback(
    results_path: str | Path = "data/results.csv",
    sport: str = "football",
) -> Optional[float]:
    """
    Read completed results.csv and calculate updated source accuracy.

    Returns the new win rate, or None if insufficient data.
    Does NOT save automatically — caller prompts user for confirmation.
    """
    results_path = Path(results_path)
    if not results_path.exists():
        logger.info("No results.csv found. Nothing to process.")
        return None

    try:
        df = pd.read_csv(results_path)
        if "result" not in df.columns:
            logger.warning("results.csv missing 'result' column.")
            return None

        completed = df[df["result"].str.upper().isin(["WIN", "LOSS"])]
        if len(completed) < 5:
            logger.info("Need at least 5 completed bets to update accuracy. Have %d.", len(completed))
            return None

        wins = (completed["result"].str.upper() == "WIN").sum()
        new_accuracy = round(wins / len(completed), 4)
        return new_accuracy

    except Exception as e:
        logger.warning("Feedback processing failed: %s", e)
        return None


def _write_file(path: Path, lines: list[str]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
