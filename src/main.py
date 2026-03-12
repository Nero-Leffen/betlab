"""
main.py
=======
BetLab — Streamlit Web UI Entry Point.

Run with:
    streamlit run src/main.py

Pipeline:
    Phase 1 → Parse bets.txt
    Phase 2 → Analyse & filter by EV
    Phase 3 → Size stakes via Half-Kelly + bankroll rules
    Phase 4 → Build parlays with correlation checks
    Phase 5 → Display results + generate output files
"""

from __future__ import annotations
import logging
import sys
from pathlib import Path

import streamlit as st
import yaml

# Ensure project root is on path when running from /src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parser import parse_bets_file
from src.analyser import analyse_bets
from src.bankroll_mgr import load_config, run_bankroll_session
from src.parlay_builder import build_parlays
from src.output_generator import (
    generate_recommendations,
    generate_bet_log_csv,
    process_feedback,
)

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("data/logs/betlab.log", mode="a"),
    ],
)
logger = logging.getLogger(__name__)

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BetLab Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

DISCLAIMER_SHORT = (
    "⚠️ **Educational tool only.** "
    "Betting involves financial risk. Comply with local laws. "
    "Telangana & Andhra Pradesh: online betting is prohibited."
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
def render_sidebar() -> dict:
    """Render sidebar controls. Returns runtime overrides."""
    st.sidebar.title("⚙️ BetLab Settings")
    st.sidebar.caption("Overrides apply to this session only.")

    st.sidebar.markdown("---")
    st.sidebar.subheader("💰 Bankroll")

    bankroll_override = st.sidebar.number_input(
        "Current Bankroll (₹ INR)", min_value=0, max_value=500,
        value=500, step=25,
        help="Set to your actual current bankroll. Max 500 INR per spec."
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("📐 Strategy")

    min_ev = st.sidebar.slider(
        "Min EV Threshold", min_value=0.01, max_value=0.10,
        value=0.02, step=0.01, format="%.2f",
        help="Bets below this edge are filtered out."
    )

    parlay_pool = st.sidebar.slider(
        "Parlay Pool Size (top N by EV)", min_value=2, max_value=4,
        value=4, step=1,
    )

    parlay_max_legs = st.sidebar.slider(
        "Max Parlay Legs", min_value=2, max_value=4,
        value=4, step=1,
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Source Accuracy")
    football_accuracy = st.sidebar.slider(
        "Football Win Rate", min_value=0.40, max_value=0.70,
        value=0.53, step=0.01, format="%.2f",
        help="Your tip source's historical win rate. Default: 0.53"
    )

    st.sidebar.markdown("---")
    st.sidebar.warning(DISCLAIMER_SHORT)

    return {
        "bankroll_override": bankroll_override,
        "min_ev": min_ev,
        "parlay_pool": parlay_pool,
        "parlay_max_legs": parlay_max_legs,
        "football_accuracy": football_accuracy,
    }


# ── Main App ──────────────────────────────────────────────────────────────────
def main():
    st.title("📊 BetLab — Sports Betting Analytics Engine")
    st.caption("Educational tool for systematic bankroll management. v1.0.0")
    st.info(DISCLAIMER_SHORT)

    overrides = render_sidebar()

    # Load base config
    try:
        config = load_config("config/settings.yaml")
    except FileNotFoundError:
        st.error("❌ config/settings.yaml not found. Please run from the /betlab project root.")
        return

    # Apply sidebar overrides
    config.total_inr = overrides["bankroll_override"]
    accuracy_map = {
        "football": overrides["football_accuracy"],
        "default": overrides["football_accuracy"],
    }

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_analyse, tab_results, tab_feedback = st.tabs([
        "🔍 Analyse Bets", "📋 Last Session", "🔄 Update Results"
    ])

    # ── TAB 1: Analyse ────────────────────────────────────────────────────────
    with tab_analyse:
        st.subheader("Step 1 — Upload or Paste Your Bets")

        input_method = st.radio(
            "Input method", ["Upload bets.txt", "Paste directly"],
            horizontal=True
        )

        bets_text = ""

        if input_method == "Upload bets.txt":
            uploaded = st.file_uploader("Upload bets.txt", type=["txt", "csv"])
            if uploaded:
                bets_text = uploaded.read().decode("utf-8")
        else:
            bets_text = st.text_area(
                "Paste your bets (one per line)",
                placeholder="Man City vs Arsenal | 1X2 | Man City | 1.85 | High\nLiverpool vs Chelsea | O/U | Over 2.5 | 1.95 | Medium",
                height=180,
            )

        st.caption("Format: `Match Name | Market | Selection | Odds | [Confidence]`")
        st.caption("Odds accepted: Decimal (1.85), American (+150 / -110), Fractional (5/2)")

        if st.button("🚀 Run Analysis", type="primary", disabled=not bets_text.strip()):
            run_analysis(
                bets_text=bets_text,
                config=config,
                accuracy_map=accuracy_map,
                overrides=overrides,
            )

    # ── TAB 2: Last Session ───────────────────────────────────────────────────
    with tab_results:
        st.subheader("Last Generated Report")
        rec_path = Path("output/recommendations.md")
        if rec_path.exists():
            st.markdown(rec_path.read_text(encoding="utf-8"))
        else:
            st.info("No report generated yet. Run an analysis first.")

    # ── TAB 3: Feedback Loop ──────────────────────────────────────────────────
    with tab_feedback:
        st.subheader("Update Results & Recalibrate Accuracy")
        st.markdown(
            "After your bets settle, fill in the `result` and `pnl_inr` columns "
            "in the downloaded CSV and upload it here."
        )

        results_upload = st.file_uploader("Upload completed results.csv", type=["csv"])
        if results_upload:
            results_path = Path("data/results.csv")
            results_path.parent.mkdir(parents=True, exist_ok=True)

            # Merge with existing if present
            import pandas as pd
            new_df = pd.read_csv(results_upload)

            if results_path.exists():
                existing = pd.read_csv(results_path)
                merged = pd.concat([existing, new_df]).drop_duplicates(subset=["bet_id"])
            else:
                merged = new_df

            merged.to_csv(results_path, index=False)
            st.success(f"✅ Saved {len(new_df)} result(s).")

            new_accuracy = process_feedback(results_path)
            if new_accuracy is not None:
                st.metric("Calculated Win Rate", f"{new_accuracy:.1%}")
                st.markdown(
                    f"Updating football source accuracy from "
                    f"**{overrides['football_accuracy']:.2f}** → **{new_accuracy:.2f}**"
                )
                if st.button("✅ Confirm & Save to Config"):
                    _update_accuracy_in_config(new_accuracy)
                    st.success("Source accuracy updated in config/settings.yaml!")
                    st.balloons()
            else:
                st.info("Need at least 5 WIN/LOSS results to recalibrate accuracy.")


def run_analysis(bets_text, config, accuracy_map, overrides):
    """Execute the full 5-phase pipeline and render results."""

    # Write temp bets file
    temp_path = Path("data/bets.txt")
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    Path("data/logs").mkdir(parents=True, exist_ok=True)
    temp_path.write_text(bets_text, encoding="utf-8")

    with st.spinner("Running analysis pipeline..."):

        # Phase 1: Parse
        parse_result = parse_bets_file(temp_path)

        if parse_result.errors:
            with st.expander(f"⚠️ {len(parse_result.errors)} parse error(s)", expanded=False):
                for err in parse_result.errors:
                    st.warning(f"Line {err['line']}: {err['message']}")

        if not parse_result.bets:
            st.error("❌ No valid bets found. Check your input format.")
            return

        st.success(f"✅ Parsed **{len(parse_result.bets)}** valid bets.")

        # Phase 2: Analyse
        filtered = analyse_bets(
            bets=parse_result.bets,
            accuracy_map=accuracy_map,
            min_ev_threshold=overrides["min_ev"],
            parlay_pool_size=overrides["parlay_pool"],
        )

        if not filtered:
            st.warning("⚠️ No bets passed the EV filter. Try lowering the threshold.")
            return

        st.info(f"📈 **{len(filtered)}** bet(s) passed the EV ≥ {overrides['min_ev']:.0%} filter.")

        # Phase 3: Bankroll
        session = run_bankroll_session(
            filtered_bets=filtered,
            config=config,
        )

        if session.stop_loss_triggered:
            st.error(
                f"🛑 **STOP-LOSS TRIGGERED.** Bankroll ₹{session.bankroll_inr:.0f} INR "
                f"≤ ₹{config.stop_loss_inr:.0f} INR. No bets recommended."
            )
            return

        if session.streak_warning:
            st.warning(
                f"⚠️ **Losing streak: {session.streak_count} losses in 7 days.** "
                f"Unit reduced to ₹{session.effective_unit_inr:.0f} INR."
            )

        # Phase 4: Parlays
        parlays = build_parlays(
            sized_bets=session.sized_bets,
            parlay_stake_inr=session.effective_unit_inr,
            max_legs=overrides["parlay_max_legs"],
            max_options=2,
        )

        # Phase 5: Render + Output
        _render_results(session, parlays)

        rec_path = generate_recommendations(session, parlays)
        csv_path = generate_bet_log_csv(session, parlays)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "📥 Download recommendations.md",
                data=rec_path.read_text(encoding="utf-8"),
                file_name="recommendations.md",
                mime="text/markdown",
            )
        with col2:
            st.download_button(
                "📥 Download bet_log_template.csv",
                data=csv_path.read_text(encoding="utf-8"),
                file_name="bet_log_template.csv",
                mime="text/csv",
            )


def _render_results(session, parlays):
    """Render analysis results in the Streamlit UI."""
    import pandas as pd

    st.markdown("---")
    st.subheader("📊 Session Summary")

    total_parlay_stake = sum(p.stake_inr for p in parlays)
    grand_total = session.total_stake_inr + total_parlay_stake

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Bankroll", f"₹{session.bankroll_inr:.0f}")
    col2.metric("Singles Stake", f"₹{session.total_stake_inr:.0f}")
    col3.metric("Parlay Stake", f"₹{total_parlay_stake:.0f}")
    col4.metric("Total at Risk", f"₹{grand_total:.0f}")

    # Singles table
    st.subheader("🎯 Recommended Singles")
    if session.sized_bets:
        rows = []
        for b in session.sized_bets:
            rows.append({
                "Bet ID": b.bet_id,
                "Match": b.match_name,
                "Selection": b.selection,
                "Odds": f"{b.decimal_odds:.2f}",
                "Confidence": b.confidence.title(),
                "Stake (₹)": f"₹{b.stake_inr:.0f}",
                "EV": f"{b.ev * 100:.2f}%",
                "Kelly%": f"{b.kelly_fraction * 100:.2f}%",
                "Tag": b.tag,
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No singles recommended.")

    # Parlays
    st.subheader("🎲 Parlay Options")
    if parlays:
        for p in parlays:
            with st.expander(
                f"{p.parlay_id} — {p.leg_count} legs @ {p.combined_odds:.2f} "
                f"| Hit: {p.hit_probability * 100:.1f}% | EV: {p.parlay_ev * 100:.2f}% "
                f"| Stake: ₹{p.stake_inr:.0f}"
            ):
                rows = [
                    {"Match": leg.match_name, "Selection": leg.selection, "Odds": f"{leg.decimal_odds:.2f}"}
                    for leg in p.legs
                ]
                st.table(pd.DataFrame(rows))
                st.caption(
                    f"Combined odds: {p.combined_odds:.2f} | "
                    f"Hit probability: {p.hit_probability * 100:.1f}% | "
                    f"Parlay EV: {p.parlay_ev * 100:.2f}%"
                )
    else:
        st.info("No valid parlays constructed (insufficient candidates or correlation conflicts).")


def _update_accuracy_in_config(new_accuracy: float, config_path: str = "config/settings.yaml"):
    """Update football accuracy in settings.yaml after user confirmation."""
    path = Path(config_path)
    with open(path, "r") as f:
        cfg = yaml.safe_load(f)
    cfg["source_accuracy"]["football"] = new_accuracy
    cfg["source_accuracy"]["default"] = new_accuracy
    with open(path, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False)


if __name__ == "__main__":
    main()
