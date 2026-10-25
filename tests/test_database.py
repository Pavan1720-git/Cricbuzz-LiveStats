"""
tests/test_database.py — Database initialization, seeding and CRUD tests.

Uses an in-memory SQLite database so tests run without a persistent file.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, text
from database.connection import reset_engine
from database.initialize_db import initialize_database
from database.seed_data import seed
from database import repositories as repo


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def engine():
    """In-memory SQLite engine for the test suite."""
    eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    from sqlalchemy import event

    @event.listens_for(eng, "connect")
    def set_pragmas(conn, _):
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    initialize_database(eng)
    seed(eng)
    return eng


@pytest.fixture(autouse=True)
def _patch_engine(engine, monkeypatch):
    """Make all repository functions use the test engine."""
    import database.repositories as _repo
    import database.connection as _conn

    monkeypatch.setattr(_conn, "_engine", engine)
    monkeypatch.setattr(_conn, "_SessionLocal", None)

    def _mock_engine(*args, **kwargs):
        return engine

    monkeypatch.setattr(_conn, "get_engine", _mock_engine)
    monkeypatch.setattr(_repo, "_engine", lambda: engine)


# ── Initialization ────────────────────────────────────────────────────────────

class TestDatabaseInit:
    def test_tables_created(self, engine):
        with engine.connect() as conn:
            tables = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            ).fetchall()
        table_names = [t[0] for t in tables]
        for expected in ("teams", "players", "venues", "matches", "player_match_stats"):
            assert expected in table_names, f"Table '{expected}' not found"

    def test_idempotent_initialization(self, engine):
        """Running initialize_database twice should not raise or duplicate tables."""
        initialize_database(engine)  # second call
        with engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM teams")).scalar()
        assert count > 0


# ── Seeding ───────────────────────────────────────────────────────────────────

class TestSeeding:
    def test_teams_seeded(self, engine):
        with engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM teams")).scalar()
        assert count > 0

    def test_players_seeded(self, engine):
        with engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM players")).scalar()
        assert count > 0

    def test_matches_seeded(self, engine):
        with engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM matches")).scalar()
        assert count > 0

    def test_player_stats_seeded(self, engine):
        with engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM player_match_stats")).scalar()
        assert count > 0

    def test_idempotent_seeding(self, engine):
        """Running seed twice should not create duplicates."""
        with engine.connect() as conn:
            count_before = conn.execute(text("SELECT COUNT(*) FROM teams")).scalar()
        seed(engine)
        with engine.connect() as conn:
            count_after = conn.execute(text("SELECT COUNT(*) FROM teams")).scalar()
        assert count_before == count_after


# ── Repository CRUD ───────────────────────────────────────────────────────────

class TestTeamRepository:
    def test_get_all_teams(self):
        df = repo.get_all_teams()
        assert not df.empty
        assert "team_name" in df.columns

    def test_create_and_delete_team(self, engine):
        with engine.begin() as conn:
            count_before = conn.execute(text("SELECT COUNT(*) FROM teams")).scalar()

        new_id = repo.create_team("Test Team XYZ", "Testland")

        with engine.connect() as conn:
            count_after = conn.execute(text("SELECT COUNT(*) FROM teams")).scalar()
        assert count_after == count_before + 1

        repo.delete_team(new_id)

        with engine.connect() as conn:
            count_final = conn.execute(text("SELECT COUNT(*) FROM teams")).scalar()
        assert count_final == count_before

    def test_update_team(self, engine):
        tid = repo.create_team("UpdateMe", "OldCountry")
        repo.update_team(tid, "Updated Team", "NewCountry")
        team = repo.get_team_by_id(tid)
        assert team["team_name"] == "Updated Team"
        assert team["country"] == "NewCountry"
        repo.delete_team(tid)


class TestPlayerRepository:
    def test_get_all_players(self):
        df = repo.get_all_players()
        assert not df.empty
        assert "full_name" in df.columns

    def test_create_player(self, engine):
        teams = repo.get_all_teams()
        tid = int(teams["team_id"].iloc[0])
        pid = repo.create_player("Test Player", tid, "Batsman", "Right-hand bat", "N/A")
        player = repo.get_player_by_id(pid)
        assert player is not None
        assert player["full_name"] == "Test Player"
        repo.delete_player(pid)


# ── Match and Stat Queries ────────────────────────────────────────────────────

class TestMatchRepository:
    def test_get_all_matches(self):
        df = repo.get_all_matches()
        assert not df.empty
        assert "team1" in df.columns
        assert "team2" in df.columns

    def test_filter_by_status(self):
        df = repo.get_all_matches(status="Completed")
        assert not df.empty
        assert all(df["match_status"] == "Completed")

    def test_filter_by_format(self):
        df = repo.get_all_matches(fmt="ODI")
        assert not df.empty
        assert all(df["match_format"] == "ODI")

    def test_get_player_stats(self):
        df = repo.get_player_stats()
        assert not df.empty

    def test_summary_counts(self):
        counts = repo.get_summary_counts()
        assert "teams" in counts
        assert "players" in counts
        assert "matches" in counts
        assert counts["teams"] > 0
        assert counts["players"] > 0
        assert counts["matches"] > 0

    def test_top_run_scorers(self):
        df = repo.get_top_run_scorers(5)
        assert not df.empty
        assert "total_runs" in df.columns

    def test_top_wicket_takers(self):
        df = repo.get_top_wicket_takers(5)
        assert not df.empty
