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
    parlay_hit_probability,
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

def _make_sized_bet(match, selection, odds=2.0, confidence="medium", tag="PARLAY_CANDIDATE"):
    return SizedBet(
        match_name=match,
        market_type="1X2",
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
