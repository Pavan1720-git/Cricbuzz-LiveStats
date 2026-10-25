"""
tests/test_analytics.py — Unit tests for cricket formula calculations.
"""

import pytest
from services.analytics_service import (
    batting_strike_rate,
    batting_average,
    bowling_economy,
    bowling_average,
    bowling_strike_rate,
    win_percentage,
    overs_to_balls,
    balls_to_overs,
    validate_player_stat,
    validate_match_date,
    validate_overs,
    compute_batting_stats,
    compute_bowling_stats,
)
import pandas as pd


# ── Batting Strike Rate ────────────────────────────────────────────────────────

class TestBattingStrikeRate:
    def test_normal(self):
        assert batting_strike_rate(50, 40) == 125.0

    def test_zero_balls(self):
        assert batting_strike_rate(0, 0) is None

    def test_none_balls(self):
        assert batting_strike_rate(10, None) is None

    def test_hundred_off_hundred(self):
        assert batting_strike_rate(100, 100) == 100.0

    def test_rounding(self):
        result = batting_strike_rate(33, 50)
        assert result == 66.0


# ── Batting Average ───────────────────────────────────────────────────────────

class TestBattingAverage:
    def test_normal(self):
        assert batting_average(500, 10) == 50.0

    def test_zero_dismissals(self):
        assert batting_average(500, 0) is None

    def test_none_dismissals(self):
        assert batting_average(100, None) is None

    def test_single_dismissal(self):
        assert batting_average(85, 1) == 85.0


# ── Bowling Economy ───────────────────────────────────────────────────────────

class TestBowlingEconomy:
    def test_normal(self):
        # 24 runs in 24 balls (4 overs) → economy = 24/4 = 6.0
        assert bowling_economy(24, 24) == 6.0

    def test_zero_balls(self):
        assert bowling_economy(10, 0) is None

    def test_none_balls(self):
        assert bowling_economy(10, None) is None

    def test_tight_bowling(self):
        # 18 runs in 36 balls (6 overs) → economy = 18/6 = 3.0
        assert bowling_economy(18, 36) == 3.0

    def test_partial_over(self):
        # 5 runs in 5 balls → economy = 5 / (5/6) = 6.0
        result = bowling_economy(5, 5)
        assert result == round(5 / (5 / 6.0), 2)


# ── Win Percentage ────────────────────────────────────────────────────────────

class TestWinPercentage:
    def test_normal(self):
        assert win_percentage(7, 10) == 70.0

    def test_zero_matches(self):
        assert win_percentage(0, 0) is None

    def test_none_matches(self):
        assert win_percentage(5, None) is None

    def test_perfect(self):
        assert win_percentage(10, 10) == 100.0

    def test_no_wins(self):
        assert win_percentage(0, 5) == 0.0


# ── Overs / Balls conversion ──────────────────────────────────────────────────

class TestOversConversion:
    def test_full_overs_to_balls(self):
        assert overs_to_balls(20.0) == 120

    def test_partial_overs_to_balls(self):
        # 19.5 → 19 overs (114) + 5 balls = 119
        assert overs_to_balls(19.5) == 119

    def test_zero(self):
        assert overs_to_balls(0.0) == 0

    def test_balls_to_overs(self):
        assert balls_to_overs(119) == "19.5"
        assert balls_to_overs(120) == "20.0"
        assert balls_to_overs(0)   == "0.0"


# ── Validation ────────────────────────────────────────────────────────────────

class TestValidation:
    def test_valid_stat(self):
        stat = {"runs": 50, "balls_faced": 40, "fours": 5, "sixes": 2,
                "wickets": 0, "runs_conceded": 0, "balls_bowled": 0, "maidens": 0}
        assert validate_player_stat(stat) == []

    def test_negative_runs(self):
        stat = {"runs": -1, "balls_faced": 10, "fours": 0, "sixes": 0,
                "wickets": 0, "runs_conceded": 0, "balls_bowled": 0, "maidens": 0}
        errors = validate_player_stat(stat)
        assert any("runs" in e for e in errors)

    def test_boundary_exceeds_runs(self):
        # 2 sixes (12 runs) but only 10 runs scored — impossible
        stat = {"runs": 10, "balls_faced": 5, "fours": 0, "sixes": 2,
                "wickets": 0, "runs_conceded": 0, "balls_bowled": 0, "maidens": 0}
        errors = validate_player_stat(stat)
        assert any("boundary" in e.lower() or "runs" in e.lower() for e in errors)

    def test_valid_match_date(self):
        assert validate_match_date("2024-06-01") is True

    def test_invalid_match_date(self):
        assert validate_match_date("01-06-2024") is False
        assert validate_match_date("not-a-date") is False

    def test_valid_overs(self):
        assert validate_overs("19.5") is True
        assert validate_overs("20")   is True
        assert validate_overs("0.0")  is True

    def test_invalid_overs(self):
        assert validate_overs("19.6") is False   # 6 balls in an over is invalid
        assert validate_overs("abc")  is False


# ── Aggregation Helpers ───────────────────────────────────────────────────────

class TestAggregation:
    @pytest.fixture
    def sample_batting_df(self):
        return pd.DataFrame([
            {"player_id": 1, "full_name": "Player A", "team_name": "India",
             "match_id": 1, "runs": 85, "balls_faced": 70, "fours": 8, "sixes": 2, "dismissal_type": "caught"},
            {"player_id": 1, "full_name": "Player A", "team_name": "India",
             "match_id": 2, "runs": 45, "balls_faced": 40, "fours": 4, "sixes": 1, "dismissal_type": "not out"},
            {"player_id": 2, "full_name": "Player B", "team_name": "Australia",
             "match_id": 1, "runs": 0, "balls_faced": 3, "fours": 0, "sixes": 0, "dismissal_type": "bowled"},
        ])

    def test_batting_aggregation(self, sample_batting_df):
        result = compute_batting_stats(sample_batting_df)
        a = result[result["full_name"] == "Player A"].iloc[0]
        assert a["total_runs"] == 130
        assert a["dismissals"] == 1        # only 'caught'; not-out excluded
        assert a["batting_average"] == 130.0

    def test_batting_empty(self):
        result = compute_batting_stats(pd.DataFrame())
        assert result.empty

    @pytest.fixture
    def sample_bowling_df(self):
        return pd.DataFrame([
            {"player_id": 3, "full_name": "Bowler X", "team_name": "India",
             "match_id": 1, "wickets": 3, "runs_conceded": 27, "balls_bowled": 24, "maidens": 1},
            {"player_id": 3, "full_name": "Bowler X", "team_name": "India",
             "match_id": 2, "wickets": 2, "runs_conceded": 18, "balls_bowled": 18, "maidens": 0},
        ])

    def test_bowling_aggregation(self, sample_bowling_df):
        result = compute_bowling_stats(sample_bowling_df)
        x = result[result["full_name"] == "Bowler X"].iloc[0]
        assert x["total_wickets"] == 5
        assert x["total_balls_bowled"] == 42
        # Economy = (27+18) / (42/6) = 45 / 7 = 6.43
        assert x["economy"] == round(6.0 * 45 / 42, 2)

    def test_bowling_empty(self):
        result = compute_bowling_stats(pd.DataFrame())
        assert result.empty
