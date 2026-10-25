"""
tests/test_data_validation.py — Tests for data validation and API error handling.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from unittest.mock import patch, MagicMock
from services.analytics_service import validate_player_stat, validate_match_date, validate_overs
import requests


# ── Player Stat Validation ─────────────────────────────────────────────────────

class TestPlayerStatValidation:
    def test_all_valid_zeros(self):
        stat = {"runs": 0, "balls_faced": 1, "fours": 0, "sixes": 0,
                "wickets": 0, "runs_conceded": 0, "balls_bowled": 0, "maidens": 0}
        assert validate_player_stat(stat) == []

    def test_valid_boundary_contribution(self):
        # 1 four (4 runs) + 1 six (6 runs) = 10 boundary runs, total runs 15 (ok)
        stat = {"runs": 15, "balls_faced": 10, "fours": 1, "sixes": 1,
                "wickets": 0, "runs_conceded": 0, "balls_bowled": 0, "maidens": 0}
        assert validate_player_stat(stat) == []

    def test_impossible_boundary_contribution(self):
        # 3 sixes = 18 runs minimum but only 10 runs
        stat = {"runs": 10, "balls_faced": 5, "fours": 0, "sixes": 3,
                "wickets": 0, "runs_conceded": 0, "balls_bowled": 0, "maidens": 0}
        errors = validate_player_stat(stat)
        assert len(errors) > 0

    def test_negative_wickets(self):
        stat = {"runs": 0, "balls_faced": 0, "fours": 0, "sixes": 0,
                "wickets": -1, "runs_conceded": 0, "balls_bowled": 0, "maidens": 0}
        errors = validate_player_stat(stat)
        assert any("wickets" in e for e in errors)

    def test_missing_optional_fields(self):
        """Partial stat (batting only) should not raise errors."""
        stat = {"runs": 50, "balls_faced": 40}
        errors = validate_player_stat(stat)
        assert isinstance(errors, list)


# ── Match Date Validation ─────────────────────────────────────────────────────

class TestMatchDateValidation:
    @pytest.mark.parametrize("date,expected", [
        ("2024-06-01", True),
        ("2023-10-05", True),
        ("2024-02-29", True),   # Leap year valid
        ("01-06-2024", False),  # Wrong format
        ("2024/06/01", False),  # Wrong separator
        ("not-a-date", False),
        ("",           False),
    ])
    def test_dates(self, date, expected):
        assert validate_match_date(date) == expected


# ── Overs Validation ──────────────────────────────────────────────────────────

class TestOversValidation:
    @pytest.mark.parametrize("overs,expected", [
        ("0.0",  True),
        ("19.5", True),
        ("20",   True),
        ("10.3", True),
        ("19.6", False),  # 6 balls in an over is not valid
        ("19.7", False),
        ("abc",  False),
        ("-1",   False),
    ])
    def test_overs(self, overs, expected):
        assert validate_overs(overs) == expected


# ── API Error Handling ────────────────────────────────────────────────────────

class TestAPIErrorHandling:
    """These tests mock HTTP calls — no real network requests are made."""

    def test_api_timeout_returns_none(self):
        with patch("services.cricket_api.CRICKET_API_KEY", "fake-key"), \
             patch("services.cricket_api.requests.get", side_effect=requests.exceptions.Timeout):
            from services.cricket_api import _cached_get, _cache
            _cache.clear()
            result = _cached_get("matches/v1/live")
            assert result is None

    def test_api_http_error_returns_none(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_resp)
        with patch("services.cricket_api.CRICKET_API_KEY", "fake-key"), \
             patch("services.cricket_api.requests.get", return_value=mock_resp):
            from services.cricket_api import _cached_get, _cache
            _cache.clear()
            result = _cached_get("matches/v1/live")
            assert result is None

    def test_invalid_json_returns_none(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.side_effect = ValueError("No JSON")
        with patch("services.cricket_api.CRICKET_API_KEY", "fake-key"), \
             patch("services.cricket_api.requests.get", return_value=mock_resp):
            from services.cricket_api import _cached_get, _cache
            _cache.clear()
            result = _cached_get("matches/v1/live")
            assert result is None

    def test_no_api_key_returns_none(self):
        with patch("services.cricket_api.CRICKET_API_KEY", ""):
            from services.cricket_api import _cached_get, _cache
            _cache.clear()
            result = _cached_get("matches/v1/live")
            assert result is None

    def test_demo_mode_fallback(self):
        """In demo mode, get_live_matches_display must not crash even with no API."""
        with patch("services.cricket_service.DEMO_MODE", True):
            from services.cricket_service import get_live_matches_display
            # Patch the DB call to return empty DataFrame
            with patch("services.cricket_service.repo.get_all_matches", return_value=__import__("pandas").DataFrame()):
                df, source = get_live_matches_display()
                assert source == "demo"


# ── Duplicate Ingestion ───────────────────────────────────────────────────────

class TestDuplicateIngestion:
    def test_seeding_twice_no_duplicates(self):
        """Seed idempotency is tested in test_database.py — reference here."""
        # This is an integration test stub; see TestSeeding.test_idempotent_seeding
        assert True


# ── Empty Dataset Edge Cases ──────────────────────────────────────────────────

class TestEmptyDatasets:
    def test_batting_stats_on_empty_df(self):
        import pandas as pd
        from services.analytics_service import compute_batting_stats
        result = compute_batting_stats(pd.DataFrame())
        assert result.empty

    def test_bowling_stats_on_empty_df(self):
        import pandas as pd
        from services.analytics_service import compute_bowling_stats
        result = compute_bowling_stats(pd.DataFrame())
        assert result.empty

    def test_win_percentage_zero_matches(self):
        from services.analytics_service import win_percentage
        assert win_percentage(0, 0) is None
