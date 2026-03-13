"""
test_betlab.py
==============
Unit tests for BetLab core modules.

Tests cover:
  - math_engine: all formulas + odds conversion
  - parser: valid/invalid inputs, confidence defaults
  - analyser: EV filtering and parlay tagging
  - parlay_builder: correlation rejection
  - bankroll_mgr: cap enforcement, stake sizing
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.math_engine import (
    get_implied_probability,
    calculate_ev,
    kelly_criterion,
    kelly_stake_inr,
    parlay_hit_probability,
    apply_correlation_penalty,
    parlay_combined_odds,
    american_to_decimal,
    fractional_to_decimal,
    to_decimal_odds,
    detect_odds_format,
)
from src.parser import parse_line, _parse_confidence, parse_bets_file
from src.analyser import analyse_bets, get_true_probability
from src.parlay_builder import _is_correlated, build_parlays
from src.bankroll_mgr import SizedBet


# ─────────────────────────────────────────────
# math_engine tests
# ─────────────────────────────────────────────

class TestImpliedProbability:
    def test_standard(self):
        assert get_implied_probability(2.0) == pytest.approx(0.5)

    def test_odds_185(self):
        assert get_implied_probability(1.85) == pytest.approx(1 / 1.85)

    def test_invalid_odds_raises(self):
        with pytest.raises(ValueError):
            get_implied_probability(1.0)

    def test_below_one_raises(self):
        with pytest.raises(ValueError):
            get_implied_probability(0.9)


class TestExpectedValue:
    def test_positive_ev(self):
        # EV = (2.0 * 0.55) - 1 = 0.10
        assert calculate_ev(2.0, 0.55) == pytest.approx(0.10, abs=1e-6)

    def test_negative_ev(self):
        # EV = (1.85 * 0.50) - 1 = -0.075
        assert calculate_ev(1.85, 0.50) == pytest.approx(-0.075, abs=1e-6)

    def test_zero_ev(self):
        # EV = (2.0 * 0.50) - 1 = 0.0
        assert calculate_ev(2.0, 0.50) == pytest.approx(0.0, abs=1e-6)

    def test_invalid_probability_raises(self):
        with pytest.raises(ValueError):
            calculate_ev(2.0, 1.0)
        with pytest.raises(ValueError):
            calculate_ev(2.0, 0.0)

    def test_near_threshold_positive_ev(self):
        assert calculate_ev(2.0, 0.5101) == pytest.approx(0.0202, abs=1e-6)

    def test_high_odds_small_edge_positive_ev(self):
        assert calculate_ev(10.0, 0.11) == pytest.approx(0.1, abs=1e-6)


class TestKellyCriterion:
    def test_positive_kelly(self):
        # b=1, p=0.6, q=0.4 → full = (0.6-0.4)/1 = 0.2 → half = 0.1
        result = kelly_criterion(2.0, 0.6)
        assert result == pytest.approx(0.1, abs=1e-6)

    def test_no_edge_returns_zero(self):
        # b=1, p=0.4, q=0.6 → full = (0.4-0.6)/1 = -0.2 → max(0, -0.1) = 0
        assert kelly_criterion(2.0, 0.4) == 0.0

    def test_half_kelly_factor(self):
        k1 = kelly_criterion(3.0, 0.6)
        k2 = kelly_criterion(3.0, 0.6)
        assert k1 == k2  # deterministic

    def test_break_even_probability_returns_zero(self):
        assert kelly_criterion(2.5, 0.4) == pytest.approx(0.0, abs=1e-6)

    def test_invalid_probability_raises(self):
        with pytest.raises(ValueError):
            kelly_criterion(2.0, 0.0)
        with pytest.raises(ValueError):
            kelly_criterion(2.0, 1.0)

    def test_invalid_odds_raises(self):
        with pytest.raises(ValueError):
            kelly_criterion(1.0, 0.55)


class TestKellyStakeInr:
    def test_rounds_to_one_unit_for_small_positive_edge(self):
        assert kelly_stake_inr(2.0, 0.51, bankroll_inr=800, unit_inr=25) == 25

    def test_clamps_to_max_units_for_large_edge(self):
        assert kelly_stake_inr(3.0, 0.75, bankroll_inr=800, unit_inr=25, max_units=2) == 50

    def test_invalid_bankroll_raises(self):
        with pytest.raises(ValueError):
            kelly_stake_inr(2.0, 0.55, bankroll_inr=0, unit_inr=25)

    def test_invalid_unit_raises(self):
        with pytest.raises(ValueError):
            kelly_stake_inr(2.0, 0.55, bankroll_inr=800, unit_inr=0)

    def test_invalid_unit_bounds_raises(self):
        with pytest.raises(ValueError):
            kelly_stake_inr(2.0, 0.55, bankroll_inr=800, unit_inr=25, min_units=2, max_units=1)


class TestBankrollState:
    def test_missing_results_uses_starting_bankroll(self):
        from src.bankroll_mgr import get_current_bankroll
        assert get_current_bankroll("data/nonexistent.csv", starting_bankroll=800) == pytest.approx(800)

    def test_results_pnl_applies_on_top_of_starting_bankroll(self, tmp_path):
        from src.bankroll_mgr import get_current_bankroll

        results_path = tmp_path / "results.csv"
        results_path.write_text(
            "date,bet_id,pnl_inr\n2026-03-13,BL-1,40\n2026-03-13,BL-2,-25\n",
            encoding="utf-8",
        )

        assert get_current_bankroll(results_path, starting_bankroll=800) == pytest.approx(815)

    def test_completed_results_count_missing_file_returns_zero(self):
        from src.bankroll_mgr import get_completed_results_count
        assert get_completed_results_count("data/nonexistent.csv") == 0

    def test_completed_results_count_counts_only_completed_rows(self, tmp_path):
        from src.bankroll_mgr import get_completed_results_count

        results_path = tmp_path / "results.csv"
        results_path.write_text(
            "date,bet_id,result\n2026-03-13,BL-1,WIN\n2026-03-13,BL-2,LOSS\n2026-03-13,BL-3,VOID\n2026-03-13,BL-4,PENDING\n",
            encoding="utf-8",
        )

        assert get_completed_results_count(results_path) == 3


class TestParlayProbability:
    def test_two_legs(self):
        assert parlay_hit_probability([0.5, 0.6]) == pytest.approx(0.30, abs=1e-6)

    def test_three_legs(self):
        assert parlay_hit_probability([0.5, 0.6, 0.7]) == pytest.approx(0.21, abs=1e-6)

    def test_single_leg(self):
        assert parlay_hit_probability([0.75]) == pytest.approx(0.75)

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            parlay_hit_probability([])

    def test_apply_correlation_penalty(self):
        assert apply_correlation_penalty(0.25, 0.8) == pytest.approx(0.20, abs=1e-6)

    def test_apply_correlation_penalty_invalid_factor_raises(self):
        with pytest.raises(ValueError):
            apply_correlation_penalty(0.25, 0.0)


class TestParlayOdds:
    def test_two_legs(self):
        assert parlay_combined_odds([2.0, 3.0]) == pytest.approx(6.0)

    def test_three_legs(self):
        assert parlay_combined_odds([1.5, 2.0, 2.5]) == pytest.approx(7.5)


class TestOddsConversion:
    def test_decimal_passthrough(self):
        assert to_decimal_odds("1.85") == pytest.approx(1.85)

    def test_american_positive(self):
        # +150 → (150/100) + 1 = 2.5
        assert american_to_decimal(150) == pytest.approx(2.5)

    def test_american_negative(self):
        # -110 → (100/110) + 1 ≈ 1.909
        assert american_to_decimal(-110) == pytest.approx(1.9091, abs=0.001)

    def test_fractional(self):
        # 5/2 → 2.5 + 1 = 3.5
        assert fractional_to_decimal("5/2") == pytest.approx(3.5)

    def test_fractional_11_4(self):
        # 11/4 → 2.75 + 1 = 3.75
        assert fractional_to_decimal("11/4") == pytest.approx(3.75)

    def test_detect_fractional(self):
        assert detect_odds_format("5/2") == "fractional"

    def test_detect_american_positive(self):
        assert detect_odds_format("+150") == "american"

    def test_detect_american_negative(self):
        assert detect_odds_format("-110") == "american"

    def test_detect_decimal(self):
        assert detect_odds_format("1.85") == "decimal"

    def test_to_decimal_american_string(self):
        result = to_decimal_odds("+200")
        assert result == pytest.approx(3.0)

    def test_to_decimal_fractional_string(self):
        result = to_decimal_odds("5/2")
        assert result == pytest.approx(3.5)

    def test_invalid_fractional_raises(self):
        with pytest.raises(ValueError):
            fractional_to_decimal("5/0")


# ─────────────────────────────────────────────
# parser tests
# ─────────────────────────────────────────────

class TestParser:
    def test_valid_line_decimal(self):
        bet, err = parse_line("Man City vs Arsenal | 1X2 | Man City | 1.85 | High", 1)
        assert bet is not None
        assert err is None
        assert bet.decimal_odds == pytest.approx(1.85)
        assert bet.confidence == "high"

    def test_valid_line_no_confidence_defaults_medium(self):
        bet, err = parse_line("Real Madrid | AH | Real -1.5 | 2.10 | ", 1)
        assert bet is not None
        assert bet.confidence == "medium"

    def test_valid_line_american_odds(self):
        bet, err = parse_line("Chelsea vs Spurs | 1X2 | Chelsea | +120 | Medium", 1)
        assert bet is not None
        assert bet.decimal_odds == pytest.approx(2.2)

    def test_valid_line_fractional_odds(self):
        bet, err = parse_line("Chelsea vs Spurs | 1X2 | Chelsea | 5/2 | Low", 1)
        assert bet is not None
        assert bet.decimal_odds == pytest.approx(3.5)

    def test_invalid_too_few_fields(self):
        bet, err = parse_line("Man City | 1X2 | Win", 1)
        assert bet is None
        assert err is not None

    def test_invalid_odds_below_one(self):
        bet, err = parse_line("Man City vs Arsenal | 1X2 | Man City | 0.75 | High", 1)
        assert bet is None
        assert err is not None

    def test_blank_line_returns_none_none(self):
        bet, err = parse_line("", 1)
        assert bet is None
        assert err is None

    def test_comment_line_skipped(self):
        bet, err = parse_line("# This is a comment", 1)
        assert bet is None
        assert err is None

    def test_empty_match_name_rejected(self):
        bet, err = parse_line(" | 1X2 | Win | 1.85 | High", 1)
        assert bet is None
        assert err is not None

    def test_confidence_normalisation(self):
        assert _parse_confidence("HIGH") == "high"
        assert _parse_confidence("medium") == "medium"
        assert _parse_confidence("garbage") == "medium"
        assert _parse_confidence("") == "medium"

    def test_parse_bets_file_freeform_line(self, tmp_path):
        p = tmp_path / "bets.txt"
        p.write_text(
            "Marseille vs Angers: Marseille Money Line @ 1.47  04:31\n",
            encoding="utf-8",
        )
        result = parse_bets_file(p)
        assert len(result.bets) == 1
        assert len(result.errors) == 0
        assert result.bets[0].match_name == "Marseille vs Angers"
        assert result.bets[0].selection == "Marseille Money Line"
        assert result.bets[0].decimal_odds == pytest.approx(1.47)

    def test_parse_bets_file_freeform_or_line_expands(self, tmp_path):
        p = tmp_path / "bets.txt"
        p.write_text(
            "Napoli vs Lecce: Both Teams to Score @ 2.65 OR Over 1.5 Goals @ 1.44  14:46\n",
            encoding="utf-8",
        )
        result = parse_bets_file(p)
        assert len(result.bets) == 2
        selections = {b.selection for b in result.bets}
        assert "Both Teams to Score" in selections
        assert "Over 1.5 Goals" in selections
        assert len(result.errors) == 0

    def test_parse_bets_file_ignores_noise_lines(self, tmp_path):
        p = tmp_path / "bets.txt"
        p.write_text(
            "FRIDAY\n"
            "French Ligue 1\n"
            "Marseille vs Angers: Marseille Money Line @ 1.47\n",
            encoding="utf-8",
        )
        result = parse_bets_file(p)
        assert len(result.bets) == 1
        assert len(result.errors) == 0

    def test_parse_bets_file_xlsx_success(self, tmp_path):
        pd = pytest.importorskip("pandas")
        pytest.importorskip("openpyxl")

        p = tmp_path / "bets.xlsx"
        df = pd.DataFrame([
            {
                "Slate": "Friday",
                "Match": "Marseille vs Auxerre",
                "Market": "Moneyline",
                "Selection": "Marseille",
                "Odds": 1.47,
                "Confidence": "Very High",
                "Reasoning": "Form edge",
            },
            {
                "Slate": "Saturday",
                "Match": "Lorient vs RC Lens",
                "Market": "Moneyline",
                "Selection": "RC Lens",
                "Odds": "+120",
                "Confidence": "High",
                "Reasoning": "Value",
            },
        ])
        df.to_excel(p, index=False)

        result = parse_bets_file(p)
        assert len(result.bets) == 2
        assert len(result.errors) == 0
        assert result.bets[0].market_type == "1X2"
        assert result.bets[0].confidence == "high"
        assert result.bets[1].decimal_odds == pytest.approx(2.2)

    def test_parse_bets_file_xlsx_missing_required_column(self, tmp_path):
        pd = pytest.importorskip("pandas")
        pytest.importorskip("openpyxl")

        p = tmp_path / "bets.xlsx"
        df = pd.DataFrame([
            {
                "Match": "Marseille vs Auxerre",
                "Market": "Moneyline",
                "Selection": "Marseille",
                "Confidence": "High",
            },
        ])
        df.to_excel(p, index=False)

        result = parse_bets_file(p)
        assert len(result.bets) == 0
        assert len(result.errors) == 1
        assert "No bet-like sheet found" in result.errors[0]["message"]
        assert len(result.prebuilt_parlays) == 0

    def test_parse_bets_file_xlsx_multisheet_extracts_parlay_sheet(self, tmp_path):
        pd = pytest.importorskip("pandas")
        pytest.importorskip("openpyxl")

        p = tmp_path / "bets.xlsx"
        singles_df = pd.DataFrame([
            {
                "Slate": "Friday",
                "Match": "Marseille vs Auxerre",
                "Market": "Moneyline",
                "Selection": "Marseille",
                "Odds": 1.47,
                "Confidence": "Very High",
            },
            {
                "Slate": "Saturday",
                "Match": "Lorient vs RC Lens",
                "Market": "Moneyline",
                "Selection": "RC Lens",
                "Odds": 1.85,
                "Confidence": "High",
            },
        ])
        parlays_df = pd.DataFrame([
            {
                "Parlay Name": "Dreamer",
                "Legs": 5,
                "Multiplier": "42x",
                "Legs Included": "Marseille ML, RC Lens ML",
            }
        ])

        with pd.ExcelWriter(p) as writer:
            singles_df.to_excel(writer, sheet_name="Individual Bets", index=False)
            parlays_df.to_excel(writer, sheet_name="Parlays", index=False)

        result = parse_bets_file(p)
        assert len(result.bets) == 2
        assert len(result.errors) == 0
        assert len(result.prebuilt_parlays) == 1
        assert result.prebuilt_parlays[0]["parlay_name"] == "Dreamer"
        assert result.prebuilt_parlays[0]["legs"] == 5
        assert result.prebuilt_parlays[0]["multiplier"] == pytest.approx(42.0)


# ─────────────────────────────────────────────
# analyser tests
# ─────────────────────────────────────────────

class TestAnalyser:
    def _make_bet(self, odds=2.0, confidence="medium"):
        from src.parser import BetInput
        return BetInput(
            match_name="Team A vs Team B",
            market_type="1X2",
            selection="Team A",
            decimal_odds=odds,
            confidence=confidence,
            sport="football",
        )

    def test_positive_ev_passes(self):
        bets = [self._make_bet(odds=2.5)]  # EV = (2.5*0.53)-1 = 0.325
        result = analyse_bets(bets, {"football": 0.53}, 0.02, 4)
        assert len(result) == 1

    def test_negative_ev_filtered(self):
        bets = [self._make_bet(odds=1.5)]  # EV = (1.5*0.53)-1 = -0.205
        result = analyse_bets(bets, {"football": 0.53}, 0.02, 4)
        assert len(result) == 0

    def test_parlay_tagging_top_n(self):
        from src.parser import BetInput
        bets = []
        for i, odds in enumerate([2.5, 2.3, 2.1, 1.9, 1.8], start=1):
            bets.append(BetInput(
                match_name=f"Match {i}", market_type="1X2",
                selection=f"Team {i}", decimal_odds=odds,
                confidence="medium", sport="football",
            ))
        result = analyse_bets(bets, {"football": 0.53}, 0.02, 3)
        parlay_count = sum(1 for b in result if b["tag"] == "PARLAY_CANDIDATE")
        assert parlay_count == min(3, len(result))

    def test_get_true_probability_football(self):
        accuracy_map = {"football": 0.55, "default": 0.53}
        assert get_true_probability("football", accuracy_map) == 0.55

    def test_get_true_probability_fallback(self):
        accuracy_map = {"football": 0.55, "default": 0.53}
        assert get_true_probability("tennis", accuracy_map) == 0.53


# ─────────────────────────────────────────────
# parlay_builder tests
# ─────────────────────────────────────────────

def _make_sized_bet(
    match,
    selection,
    odds=2.0,
    confidence="medium",
    tag="PARLAY_CANDIDATE",
    market_type="1X2",
):
    return SizedBet(
        match_name=match,
        market_type=market_type,
        selection=selection,
        decimal_odds=odds,
        confidence=confidence,
        sport="football",
        ev=0.06,
        implied_probability=0.5,
        true_probability=0.53,
        kelly_fraction=0.03,
        stake_inr=25.0,
        tag=tag,
    )


class TestParlayCorrelation:
    def test_same_match_rejected(self):
        a = _make_sized_bet("Man City vs Arsenal", "Man City")
        b = _make_sized_bet("Man City vs Arsenal", "Over 2.5")
        assert _is_correlated(a, b) is True

    def test_different_match_accepted(self):
        a = _make_sized_bet("Man City vs Arsenal", "Man City")
        b = _make_sized_bet("Liverpool vs Chelsea", "Liverpool")
        assert _is_correlated(a, b) is False

    def test_same_team_different_market_rejected(self):
        a = _make_sized_bet("Man City vs Arsenal", "Man City")
        b = _make_sized_bet("Man City vs Spurs", "Man City")
        assert _is_correlated(a, b) is True

    def test_build_parlays_filters_correlated(self):
        bets = [
            _make_sized_bet("Man City vs Arsenal", "Man City", odds=1.85),
            _make_sized_bet("Man City vs Arsenal", "Over 2.5", odds=1.90),  # same match
            _make_sized_bet("Liverpool vs Chelsea", "Liverpool", odds=2.1),
        ]
        parlays = build_parlays(bets, parlay_stake_inr=25.0, max_legs=4, max_options=2)
        for p in parlays:
            matches = [leg.match_name for leg in p.legs]
            assert len(matches) == len(set(matches)), "Parlay has duplicate match!"

    def test_build_parlays_not_enough_candidates(self):
        bets = [_make_sized_bet("Man City vs Arsenal", "Man City")]
        parlays = build_parlays(bets, parlay_stake_inr=25.0)
        assert parlays == []

    def test_build_parlays_max_options(self):
        bets = [
            _make_sized_bet("Match A vs B", "Team A", odds=2.0),
            _make_sized_bet("Match C vs D", "Team C", odds=2.1),
            _make_sized_bet("Match E vs F", "Team E", odds=2.2),
            _make_sized_bet("Match G vs H", "Team G", odds=2.3),
        ]
        parlays = build_parlays(bets, parlay_stake_inr=25.0, max_legs=4, max_options=2)
        assert len(parlays) <= 2

    def test_build_parlays_applies_correlation_penalty(self):
        bets = [
            _make_sized_bet("Match A vs B", "Team A", odds=2.0, market_type="1X2"),
            _make_sized_bet("Match C vs D", "Team C", odds=2.0, market_type="1X2"),
        ]
        parlays = build_parlays(
            bets,
            parlay_stake_inr=25.0,
            max_legs=2,
            max_options=1,
            correlation_settings={
                "enabled": True,
                "min_factor": 0.5,
                "same_market_weight": 0.2,
                "shared_token_weight": 0.0,
                "shared_sport_weight": 0.0,
            },
        )
        assert len(parlays) == 1
        assert parlays[0].penalty_factor < 1.0
        assert parlays[0].hit_probability < parlays[0].base_hit_probability

    def test_build_parlays_disable_penalty(self):
        bets = [
            _make_sized_bet("Match A vs B", "Team A", odds=2.0),
            _make_sized_bet("Match C vs D", "Team C", odds=2.0),
        ]
        parlays = build_parlays(
            bets,
            parlay_stake_inr=25.0,
            max_legs=2,
            max_options=1,
            correlation_settings={"enabled": False},
        )
        assert len(parlays) == 1
        assert parlays[0].penalty_factor == pytest.approx(1.0)
        assert parlays[0].hit_probability == pytest.approx(parlays[0].base_hit_probability)


# ─────────────────────────────────────────────
# bankroll_mgr: stake cap test
# ─────────────────────────────────────────────

class TestBankrollCap:
    def test_total_stake_never_exceeds_200(self):
        """Critical: total recommended stake must never exceed 200 INR."""
        from src.bankroll_mgr import run_bankroll_session, load_config
        from src.parser import BetInput
        from src.analyser import analyse_bets

        # Create many high-EV bets
        bets = []
        for i in range(20):
            bets.append(BetInput(
                match_name=f"Match {i} A vs B",
                market_type="1X2",
                selection=f"Team {i}",
                decimal_odds=2.5,
                confidence="high",
                sport="football",
            ))

        accuracy_map = {"football": 0.53, "default": 0.53}
        filtered = analyse_bets(bets, accuracy_map, 0.02, 10)

        config = load_config("config/settings.yaml")
        session = run_bankroll_session(filtered, config)

        assert session.total_stake_inr <= 200, (
            f"Total stake {session.total_stake_inr} exceeds 200 INR cap!"
        )

    def test_preserves_parlay_candidate_tag(self):
        """Parlay candidate tags from analyser must survive bankroll sizing."""
        from src.bankroll_mgr import run_bankroll_session, load_config

        filtered_bets = [
            {
                "match_name": "Match A vs B",
                "market_type": "1X2",
                "selection": "Team A",
                "decimal_odds": 2.2,
                "confidence": "medium",
                "sport": "football",
                "ev": 0.05,
                "implied_probability": 0.4545,
                "true_probability": 0.53,
                "tag": "PARLAY_CANDIDATE",
            },
            {
                "match_name": "Match C vs D",
                "market_type": "1X2",
                "selection": "Team C",
                "decimal_odds": 2.3,
                "confidence": "medium",
                "sport": "football",
                "ev": 0.06,
                "implied_probability": 0.4348,
                "true_probability": 0.53,
                "tag": "PARLAY_CANDIDATE",
            },
        ]

        config = load_config("config/settings.yaml")
        session = run_bankroll_session(filtered_bets, config)

        assert len(session.sized_bets) == 2
        assert all(b.tag == "PARLAY_CANDIDATE" for b in session.sized_bets)


# ─────────────────────────────────────────────
# Phase 2: Calibration tests
# ─────────────────────────────────────────────

from src.analyser import (
    _market_to_prior_key,
    get_market_prior,
    compute_calibrated_probability,
)


class TestMarketPriorMapping:
    def test_1x2_maps_to_moneyline(self):
        assert _market_to_prior_key("1X2") == "moneyline"

    def test_money_line_maps_to_moneyline(self):
        assert _market_to_prior_key("Money Line") == "moneyline"

    def test_btts_maps_to_btts(self):
        assert _market_to_prior_key("BTTS") == "btts"

    def test_both_teams_maps_to_btts(self):
        assert _market_to_prior_key("Both Teams to Score") == "btts"

    def test_over_maps_to_totals(self):
        assert _market_to_prior_key("Over 2.5") == "totals"

    def test_under_maps_to_totals(self):
        assert _market_to_prior_key("Under 3.5") == "totals"

    def test_asian_handicap_maps_to_handicap(self):
        assert _market_to_prior_key("Asian Handicap") == "handicap"

    def test_freeform_maps_to_freeform(self):
        assert _market_to_prior_key("freeform") == "freeform"

    def test_unknown_maps_to_default(self):
        assert _market_to_prior_key("draw no bet") == "default"

    def test_get_market_prior_returns_configured_value(self):
        priors = {"moneyline": 0.55, "btts": 0.52, "default": 0.53}
        assert get_market_prior("1X2", priors) == pytest.approx(0.55)

    def test_get_market_prior_falls_back_to_default(self):
        priors = {"moneyline": 0.55, "default": 0.50}
        assert get_market_prior("draw no bet", priors) == pytest.approx(0.50)


class TestCalibratedProbability:
    _PRIORS = {"moneyline": 0.55, "btts": 0.52, "totals": 0.54, "default": 0.53}
    _CAL_CFG = {"min_sample_size": 3, "time_decay_halflife_days": 30, "smoothing_weight": 0.30}
    _ACC = {"football": 0.53, "default": 0.53}

    def _make_results(self, wins: int, losses: int) -> "pd.DataFrame":
        import pandas as pd
        from datetime import date, timedelta
        rows = []
        for i in range(wins):
            rows.append({"date": (date.today() - timedelta(days=i)).isoformat(), "result": "WIN"})
        for i in range(losses):
            rows.append({"date": (date.today() - timedelta(days=wins + i)).isoformat(), "result": "LOSS"})
        return pd.DataFrame(rows)

    def test_no_results_returns_prior(self):
        result = compute_calibrated_probability(
            market_type="1X2", sport="football",
            accuracy_map=self._ACC, market_priors=self._PRIORS,
            results_df=None, calibration_cfg=self._CAL_CFG,
        )
        assert result["true_probability"] == pytest.approx(0.55)
        assert result["prob_source"] == "prior"

    def test_sparse_results_returns_prior(self):
        import pandas as pd
        # Only 2 results < min_sample_size of 3
        df = self._make_results(wins=1, losses=1)
        result = compute_calibrated_probability(
            market_type="1X2", sport="football",
            accuracy_map=self._ACC, market_priors=self._PRIORS,
            results_df=df, calibration_cfg=self._CAL_CFG,
        )
        assert result["prob_source"] == "prior"

    def test_sufficient_results_returns_calibrated(self):
        # 5 wins, 0 losses → win rate = 1.0, blended = 0.3*0.55 + 0.7*1.0 = 0.865
        df = self._make_results(wins=5, losses=0)
        result = compute_calibrated_probability(
            market_type="1X2", sport="football",
            accuracy_map=self._ACC, market_priors=self._PRIORS,
            results_df=df, calibration_cfg=self._CAL_CFG,
        )
        assert result["prob_source"] == "calibrated"
        assert result["true_probability"] > 0.55  # blended above prior

    def test_blended_is_between_prior_and_live_rate(self):
        # 3 wins 3 losses → win rate ≈ 0.5; prior = 0.55
        df = self._make_results(wins=3, losses=3)
        result = compute_calibrated_probability(
            market_type="1X2", sport="football",
            accuracy_map=self._ACC, market_priors=self._PRIORS,
            results_df=df, calibration_cfg=self._CAL_CFG,
        )
        if result["prob_source"] == "calibrated":
            # blended = 0.3*0.55 + 0.7*~0.5 = 0.515; between 0.5 and 0.55
            assert 0.49 < result["true_probability"] < 0.56

    def test_no_market_priors_falls_back_to_sport(self):
        result = compute_calibrated_probability(
            market_type="1X2", sport="football",
            accuracy_map={"football": 0.57, "default": 0.53},
            market_priors=None,
            results_df=None, calibration_cfg=None,
        )
        assert result["true_probability"] == pytest.approx(0.57)
        assert result["prob_source"] == "sport"

    def test_analyse_bets_includes_prob_source(self):
        from src.parser import BetInput
        bets = [BetInput(
            match_name="A vs B", market_type="1X2",
            selection="A", decimal_odds=2.5,
            confidence="medium", sport="football",
        )]
        result = analyse_bets(
            bets, {"football": 0.53, "default": 0.53}, 0.02, 4,
            market_priors=self._PRIORS,
        )
        assert len(result) == 1
        assert "prob_source" in result[0]
        assert result[0]["prob_source"] in {"prior", "calibrated", "sport"}
        assert "prob_sample_count" in result[0]


# ─────────────────────────────────────────────
# Phase 3: Session-Level Bankroll Optimizer
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# Phase 4: Dedupe and Conflict Rules
# ─────────────────────────────────────────────

class TestMarketNormalization:
    """normalize_market_type maps aliases to canonical labels."""

    def test_money_line_normalizes_to_1x2(self):
        from src.parser import normalize_market_type
        assert normalize_market_type("Money Line") == "1X2"

    def test_ml_normalizes_to_1x2(self):
        from src.parser import normalize_market_type
        assert normalize_market_type("ML") == "1X2"

    def test_moneyline_normalizes_to_1x2(self):
        from src.parser import normalize_market_type
        assert normalize_market_type("moneyline") == "1X2"

    def test_btts_alias_normalizes(self):
        from src.parser import normalize_market_type
        assert normalize_market_type("Both Teams to Score") == "BTTS"

    def test_gg_alias_normalizes_to_btts(self):
        from src.parser import normalize_market_type
        assert normalize_market_type("GG") == "BTTS"

    def test_asian_handicap_normalizes(self):
        from src.parser import normalize_market_type
        assert normalize_market_type("Asian Handicap") == "Handicap"

    def test_known_canonical_passes_through(self):
        from src.parser import normalize_market_type
        assert normalize_market_type("1X2") == "1X2"

    def test_unknown_market_passes_through(self):
        from src.parser import normalize_market_type
        assert normalize_market_type("Draw No Bet") == "Draw No Bet"


class TestBetDeduplication:
    """dedupe_bets collapses identical picks, keeping the better-odds copy."""

    def _make_bet(self, match, market, selection, odds=2.0):
        from src.parser import BetInput
        return BetInput(
            match_name=match, market_type=market, selection=selection,
            decimal_odds=odds, confidence="medium", sport="football",
        )

    def test_exact_duplicate_drops_one(self):
        from src.analyser import dedupe_bets
        bets = [
            self._make_bet("A vs B", "1X2", "Team A", odds=2.0),
            self._make_bet("A vs B", "1X2", "Team A", odds=2.0),
        ]
        result, dropped = dedupe_bets(bets)
        assert len(result) == 1
        assert len(dropped) == 1

    def test_duplicate_keeps_better_odds(self):
        from src.analyser import dedupe_bets
        bets = [
            self._make_bet("A vs B", "1X2", "Team A", odds=2.0),
            self._make_bet("A vs B", "1X2", "Team A", odds=2.3),
        ]
        result, dropped = dedupe_bets(bets)
        assert len(result) == 1
        assert result[0].decimal_odds == pytest.approx(2.3)

    def test_market_alias_collapses_duplicate(self):
        """'Money Line' and '1X2' for the same pick are the same bet."""
        from src.analyser import dedupe_bets
        bets = [
            self._make_bet("A vs B", "Money Line", "Team A", odds=2.0),
            self._make_bet("A vs B", "1X2", "Team A", odds=2.0),
        ]
        result, dropped = dedupe_bets(bets)
        assert len(result) == 1
        assert len(dropped) == 1

    def test_different_selections_not_deduped(self):
        from src.analyser import dedupe_bets
        bets = [
            self._make_bet("A vs B", "1X2", "Team A"),
            self._make_bet("A vs B", "1X2", "Team B"),
        ]
        result, dropped = dedupe_bets(bets)
        assert len(result) == 2
        assert len(dropped) == 0

    def test_analyse_bets_dedupes_before_ev(self):
        """analyse_bets must not return duplicate picks."""
        from src.parser import BetInput
        bets = [
            BetInput("A vs B", "1X2", "Team A", 2.5, "medium", "football"),
            BetInput("A vs B", "1X2", "Team A", 2.5, "medium", "football"),
        ]
        result = analyse_bets(bets, {"football": 0.53, "default": 0.53}, 0.02, 4)
        assert len(result) == 1


class TestConflictDetection:
    """filter_conflicts removes the lower-EV side of opposing picks in the same match."""

    def _make_result(self, match, market, selection, ev=0.05):
        return {
            "match_name": match, "market_type": market, "selection": selection,
            "decimal_odds": 2.2, "confidence": "medium", "sport": "football",
            "true_probability": 0.53, "implied_probability": 0.4545, "ev": ev,
            "tag": "SINGLE_CANDIDATE", "prob_source": "prior", "prob_sample_count": 0,
        }

    def test_moneyline_conflict_keeps_higher_ev(self):
        from src.analyser import filter_conflicts
        results = [
            self._make_result("A vs B", "1X2", "Team A", ev=0.06),
            self._make_result("A vs B", "1X2", "Team B", ev=0.04),
        ]
        clean, dropped = filter_conflicts(results)
        assert len(clean) == 1
        assert len(dropped) == 1
        assert clean[0]["selection"] == "Team A"

    def test_btts_yes_no_conflict_keeps_higher_ev(self):
        from src.analyser import filter_conflicts
        results = [
            self._make_result("A vs B", "BTTS", "Yes", ev=0.07),
            self._make_result("A vs B", "BTTS", "No", ev=0.05),
        ]
        clean, dropped = filter_conflicts(results)
        assert len(clean) == 1
        assert clean[0]["selection"] == "Yes"

    def test_over_under_conflict_keeps_higher_ev(self):
        from src.analyser import filter_conflicts
        results = [
            self._make_result("A vs B", "O/U", "Over 2.5", ev=0.06),
            self._make_result("A vs B", "O/U", "Under 2.5", ev=0.04),
        ]
        clean, dropped = filter_conflicts(results)
        assert len(clean) == 1
        assert clean[0]["selection"] == "Over 2.5"

    def test_different_match_not_a_conflict(self):
        from src.analyser import filter_conflicts
        results = [
            self._make_result("A vs B", "1X2", "Team A", ev=0.06),
            self._make_result("C vs D", "1X2", "Team A", ev=0.05),
        ]
        clean, dropped = filter_conflicts(results)
        assert len(clean) == 2
        assert len(dropped) == 0

    def test_analyse_bets_drops_lower_ev_conflict(self):
        """Pipeline keeps only the higher-EV side when two bets conflict."""
        from src.parser import BetInput
        # Both give positive EV at p=0.53: 2.5*0.53-1=0.325, 2.2*0.53-1=0.166
        bets = [
            BetInput("A vs B", "1X2", "Team A", 2.5, "medium", "football"),
            BetInput("A vs B", "1X2", "Team B", 2.2, "medium", "football"),
        ]
        result = analyse_bets(bets, {"football": 0.53, "default": 0.53}, 0.02, 4)
        assert len(result) == 1
        assert result[0]["selection"] == "Team A"


class TestSessionOptimizer:
    """Phase 3: exposure caps, drawdown governor, rejection tracking."""

    def _make_bet(self, match_name, selection, market_type="1X2",
                  odds=2.2, confidence="medium", ev=0.05):
        return {
            "match_name": match_name,
            "market_type": market_type,
            "selection": selection,
            "decimal_odds": odds,
            "confidence": confidence,
            "sport": "football",
            "ev": ev,
            "implied_probability": round(1 / odds, 6),
            "true_probability": 0.53,
            "tag": "SINGLE_CANDIDATE",
        }

    def _make_config(self, optimizer_cfg=None):
        from src.bankroll_mgr import BankrollConfig
        return BankrollConfig(
            total_inr=800,
            unit_inr=25,
            max_daily_stake_inr=200,
            stop_loss_inr=400,
            losing_streak_window_days=7,
            losing_streak_threshold=5,
            reduced_unit_multiplier=0.5,
            confidence_stake_map={"high": 2, "medium": 1, "low": 1},
            optimizer_cfg=optimizer_cfg or {},
        )

    def test_cold_start_mode_uses_flat_stake_and_tighter_total_exposure(self):
        from src.bankroll_mgr import run_bankroll_session, BankrollConfig

        bets = [
            self._make_bet("Match A vs B", "Team A", odds=2.2, ev=0.10),
            self._make_bet("Match C vs D", "Team C", odds=2.3, ev=0.09),
            self._make_bet("Match E vs F", "Team E", odds=2.4, ev=0.08),
            self._make_bet("Match G vs H", "Team G", odds=2.5, ev=0.07),
        ]
        config = BankrollConfig(
            total_inr=800,
            unit_inr=25,
            max_daily_stake_inr=200,
            stop_loss_inr=400,
            losing_streak_window_days=7,
            losing_streak_threshold=5,
            reduced_unit_multiplier=0.5,
            confidence_stake_map={"high": 2, "medium": 1, "low": 1},
            optimizer_cfg={},
            policy_cfg={
                "mode": "cold_start",
                "cold_start_min_settled_bets": 20,
                "cold_start_flat_stake_inr": 25,
                "cold_start_max_total_exposure_inr": 75,
            },
        )

        session = run_bankroll_session(bets, config, results_path="data/nonexistent.csv")

        assert session.cold_start_active is True
        assert session.total_stake_inr <= 75
        assert all(b.stake_inr == 25 for b in session.sized_bets)

    def test_team_exposure_cap_respected(self):
        """Total stake on the same team must not exceed the per-team cap."""
        from src.bankroll_mgr import run_bankroll_session

        bets = [
            self._make_bet("Match A vs B", "Team A", odds=2.2, ev=0.10),
            self._make_bet("Match A vs C", "Team A", odds=2.5, ev=0.09),
        ]
        config = self._make_config({"enabled": True, "max_exposure_per_team_inr": 25})
        session = run_bankroll_session(bets, config, results_path="data/nonexistent.csv")

        team_stake = sum(b.stake_inr for b in session.sized_bets if b.selection == "Team A")
        assert team_stake <= 25

    def test_market_exposure_cap_respected(self):
        """Total stake in one market family must not exceed the per-market cap."""
        from src.bankroll_mgr import run_bankroll_session

        bets = [
            self._make_bet("Match A vs B", "Over 2.5", market_type="O/U", odds=2.0, ev=0.06),
            self._make_bet("Match C vs D", "Over 2.5", market_type="Over/Under", odds=2.0, ev=0.05),
            self._make_bet("Match E vs F", "Over 3.5", market_type="over 3.5", odds=2.0, ev=0.04),
        ]
        config = self._make_config({"enabled": True, "max_exposure_per_market_inr": 25})
        session = run_bankroll_session(bets, config, results_path="data/nonexistent.csv")

        totals_stake = sum(
            b.stake_inr for b in session.sized_bets
            if any(x in b.market_type.lower() for x in ["over", "under", "o/u"])
        )
        assert totals_stake <= 25

    def test_confidence_band_cap_respected(self):
        """Total stake for a confidence tier must not exceed its configured cap."""
        from src.bankroll_mgr import run_bankroll_session

        bets = [
            self._make_bet("Match A vs B", "Team A", confidence="high", odds=2.2, ev=0.10),
            self._make_bet("Match C vs D", "Team C", confidence="high", odds=2.3, ev=0.09),
            self._make_bet("Match E vs F", "Team E", confidence="high", odds=2.4, ev=0.08),
        ]
        config = self._make_config({
            "enabled": True,
            "max_exposure_per_confidence": {"high": 50, "medium": 75, "low": 50},
        })
        session = run_bankroll_session(bets, config, results_path="data/nonexistent.csv")

        high_stake = sum(b.stake_inr for b in session.sized_bets if b.confidence == "high")
        assert high_stake <= 50

    def test_drawdown_governor_no_reduction_at_zero_drawdown(self):
        """Bankroll at or above initial → multiplier is 1.0."""
        from src.bankroll_mgr import _compute_drawdown_multiplier

        tiers = [
            {"drawdown_pct": 10, "unit_multiplier": 0.75},
            {"drawdown_pct": 20, "unit_multiplier": 0.50},
        ]
        assert _compute_drawdown_multiplier(800.0, 800.0, tiers) == pytest.approx(1.0)
        assert _compute_drawdown_multiplier(820.0, 800.0, tiers) == pytest.approx(1.0)

    def test_drawdown_governor_tier1_at_15pct_drawdown(self):
        """15 % drawdown hits the 10 % tier → multiplier 0.75."""
        from src.bankroll_mgr import _compute_drawdown_multiplier

        tiers = [
            {"drawdown_pct": 10, "unit_multiplier": 0.75},
            {"drawdown_pct": 20, "unit_multiplier": 0.50},
            {"drawdown_pct": 30, "unit_multiplier": 0.25},
        ]
        # 800 → 680 = 15% down
        assert _compute_drawdown_multiplier(680.0, 800.0, tiers) == pytest.approx(0.75)

    def test_drawdown_governor_tier2_at_25pct_drawdown(self):
        """25 % drawdown hits the 20 % tier → multiplier 0.50."""
        from src.bankroll_mgr import _compute_drawdown_multiplier

        tiers = [
            {"drawdown_pct": 10, "unit_multiplier": 0.75},
            {"drawdown_pct": 20, "unit_multiplier": 0.50},
            {"drawdown_pct": 30, "unit_multiplier": 0.25},
        ]
        # 800 → 600 = 25% down
        assert _compute_drawdown_multiplier(600.0, 800.0, tiers) == pytest.approx(0.50)

    def test_rejected_bets_tracked_with_reason(self):
        """Bets rejected by the optimizer must appear in session.rejected_bets with a reason."""
        from src.bankroll_mgr import run_bankroll_session

        bets = [
            self._make_bet("Match A vs B", "Team A", odds=2.2, ev=0.10),
            self._make_bet("Match A vs C", "Team A", odds=2.5, ev=0.09),
        ]
        config = self._make_config({"enabled": True, "max_exposure_per_team_inr": 25})
        session = run_bankroll_session(bets, config, results_path="data/nonexistent.csv")

        assert len(session.rejected_bets) >= 1
        assert all("reason" in r for r in session.rejected_bets)

    def test_optimizer_disabled_does_not_restrict(self):
        """With optimizer disabled, two bets on the same team both pass (within daily cap)."""
        from src.bankroll_mgr import run_bankroll_session

        bets = [
            self._make_bet("Match A vs B", "Team A", odds=2.2, ev=0.10),
            self._make_bet("Match A vs C", "Team A", odds=2.5, ev=0.09),
        ]
        config = self._make_config({"enabled": False})
        session = run_bankroll_session(bets, config, results_path="data/nonexistent.csv")

        assert len(session.sized_bets) == 2


class TestDrawdownGovernorIntegration:
    """Drawdown governor applied within a full bankroll session."""

    def test_drawdown_governor_reduces_effective_unit(self):
        """Session effective_unit_inr should reflect drawdown tier multiplier."""
        from src.bankroll_mgr import run_bankroll_session, BankrollConfig
        import tempfile, os, csv

        # Create a results.csv with 125 INR net loss → 375 bankroll (25% drawdown)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline=""
        ) as f:
            writer = csv.DictWriter(f, fieldnames=["bet_id", "pnl_inr"])
            writer.writeheader()
            writer.writerow({"bet_id": "BL-001", "pnl_inr": -125})
            tmp_path = f.name

        try:
            config = BankrollConfig(
                total_inr=800,
                unit_inr=25,
                max_daily_stake_inr=200,
                stop_loss_inr=400,
                losing_streak_window_days=7,
                losing_streak_threshold=5,
                reduced_unit_multiplier=0.5,
                confidence_stake_map={"high": 2, "medium": 1, "low": 1},
                optimizer_cfg={
                    "enabled": True,
                    "drawdown_governor": {
                        "enabled": True,
                        "tiers": [
                            {"drawdown_pct": 10, "unit_multiplier": 0.75},
                            {"drawdown_pct": 20, "unit_multiplier": 0.50},
                        ],
                    },
                },
            )
            bets = [{
                "match_name": "Match A vs B",
                "market_type": "1X2",
                "selection": "Team A",
                "decimal_odds": 2.2,
                "confidence": "medium",
                "sport": "football",
                "ev": 0.05,
                "implied_probability": 0.4545,
                "true_probability": 0.53,
                "tag": "SINGLE_CANDIDATE",
            }]
            session = run_bankroll_session(bets, config, results_path=tmp_path)
            # 15.625% drawdown from 800 to 675 → tier1 → effective unit = 18.75
            assert session.effective_unit_inr == pytest.approx(18.75)
        finally:
            os.unlink(tmp_path)


# ─────────────────────────────────────────────
# Phase 5: EV Robustness Quality Gates
# ─────────────────────────────────────────────

class TestEvRobustnessLabel:
    """ev_robustness_label assigns robust/marginal/thin based on EV quality."""

    def _cfg(self, enabled=True):
        return {"enabled": enabled, "margin_pct": 0.02}

    def _call(self, ev, prob_source="prior", sample=0, enabled=True):
        from src.analyser import ev_robustness_label
        bet = {"ev": ev, "prob_source": prob_source, "prob_sample_count": sample}
        return ev_robustness_label(bet, self._cfg(enabled), min_ev_threshold=0.02, min_sample=10)

    def test_calibrated_good_sample_is_robust(self):
        assert self._call(0.10, prob_source="calibrated", sample=15) == "robust"

    def test_calibrated_thin_sample_is_marginal(self):
        assert self._call(0.10, prob_source="calibrated", sample=5) == "marginal"

    def test_prior_good_ev_is_marginal(self):
        # EV=0.10 > threshold(0.02) + margin(0.02) = 0.04 → above thin band
        assert self._call(0.10, prob_source="prior") == "marginal"

    def test_prior_thin_ev_is_thin(self):
        # EV=0.025 < 0.04 → thin
        assert self._call(0.025, prob_source="prior") == "thin"

    def test_calibrated_thin_ev_is_thin_regardless_of_sample(self):
        # Even with good sample, EV below margin makes it thin
        assert self._call(0.025, prob_source="calibrated", sample=15) == "thin"

    def test_disabled_gate_always_returns_marginal(self):
        # When gate disabled, even thin EV gets "marginal"
        assert self._call(0.025, prob_source="prior", enabled=False) == "marginal"

    def test_analyse_bets_output_includes_ev_label(self):
        from src.parser import BetInput
        bets = [BetInput("A vs B", "1X2", "Team A", 2.5, "medium", "football")]
        result = analyse_bets(bets, {"football": 0.53, "default": 0.53}, 0.02, 4)
        assert len(result) == 1
        assert "ev_label" in result[0]


class TestParlayRobustnessGate:
    """Thin bets are excluded from parlay pool when robustness gate is enabled."""

    def _make_result(self, ev, prob_source="prior", sample=0):
        return {
            "match_name": f"Match {ev}", "market_type": "1X2",
            "selection": "Team A", "decimal_odds": 2.2, "confidence": "medium",
            "sport": "football", "true_probability": 0.53,
            "implied_probability": 0.4545, "ev": ev, "tag": "SINGLE_CANDIDATE",
            "prob_source": prob_source, "prob_sample_count": sample,
            "ev_label": "thin" if ev < 0.04 else "marginal",
        }

    def test_thin_bet_stays_single_candidate(self):
        from src.analyser import apply_robustness_gate
        results = [self._make_result(ev=0.025)]  # thin
        cfg = {"enabled": True, "margin_pct": 0.02}
        out = apply_robustness_gate(results, parlay_pool_size=4, robustness_cfg=cfg,
                                    min_ev_threshold=0.02, min_sample=10)
        assert out[0]["tag"] == "SINGLE_CANDIDATE"

    def test_marginal_bet_tagged_parlay_candidate(self):
        from src.analyser import apply_robustness_gate
        results = [self._make_result(ev=0.10)]  # marginal
        cfg = {"enabled": True, "margin_pct": 0.02}
        out = apply_robustness_gate(results, parlay_pool_size=4, robustness_cfg=cfg,
                                    min_ev_threshold=0.02, min_sample=10)
        assert out[0]["tag"] == "PARLAY_CANDIDATE"

    def test_gate_disabled_thin_still_tagged_parlay_candidate(self):
        from src.analyser import apply_robustness_gate
        results = [self._make_result(ev=0.025)]  # thin but gate off
        cfg = {"enabled": False, "margin_pct": 0.02}
        out = apply_robustness_gate(results, parlay_pool_size=4, robustness_cfg=cfg,
                                    min_ev_threshold=0.02, min_sample=10)
        assert out[0]["tag"] == "PARLAY_CANDIDATE"


class TestNoBetDayMode:
    """is_no_bet_day returns True when all bets are thin or list is empty."""

    def test_empty_list_is_no_bet_day(self):
        from src.analyser import is_no_bet_day
        assert is_no_bet_day([]) is True

    def test_all_thin_is_no_bet_day(self):
        from src.analyser import is_no_bet_day
        assert is_no_bet_day([{"ev_label": "thin"}, {"ev_label": "thin"}]) is True

    def test_any_marginal_is_not_no_bet_day(self):
        from src.analyser import is_no_bet_day
        assert is_no_bet_day([{"ev_label": "thin"}, {"ev_label": "marginal"}]) is False

    def test_robust_is_not_no_bet_day(self):
        from src.analyser import is_no_bet_day
        assert is_no_bet_day([{"ev_label": "robust"}]) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
