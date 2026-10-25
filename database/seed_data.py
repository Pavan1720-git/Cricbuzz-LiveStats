"""
database/seed_data.py — Load sample CSV data into the database.

Running this script twice will not create duplicate records.
Run after initialize_db:
    python -m database.seed_data
"""

import logging
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.connection import get_engine
from database.initialize_db import initialize_database
from config import DATA_DIR

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _upsert_team(conn, team_name: str, country: str) -> int:
    """Insert team if not exists; return team_id."""
    row = conn.execute(
        text("SELECT team_id FROM teams WHERE team_name = :n"), {"n": team_name}
    ).fetchone()
    if row:
        return row[0]
    result = conn.execute(
        text("INSERT INTO teams (team_name, country) VALUES (:n, :c)"),
        {"n": team_name, "c": country},
    )
    return result.lastrowid


def _upsert_venue(conn, venue_name: str, city: str, country: str) -> int:
    row = conn.execute(
        text("SELECT venue_id FROM venues WHERE venue_name = :n"), {"n": venue_name}
    ).fetchone()
    if row:
        return row[0]
    result = conn.execute(
        text("INSERT INTO venues (venue_name, city, country) VALUES (:n, :c, :co)"),
        {"n": venue_name, "c": city, "co": country},
    )
    return result.lastrowid


def _get_team_id(conn, team_name: str):
    row = conn.execute(
        text("SELECT team_id FROM teams WHERE team_name = :n"), {"n": team_name}
    ).fetchone()
    return row[0] if row else None


def _get_player_id(conn, full_name: str):
    row = conn.execute(
        text("SELECT player_id FROM players WHERE full_name = :n"), {"n": full_name}
    ).fetchone()
    return row[0] if row else None


# ── Country lookup (basic) ────────────────────────────────────────────────────
_TEAM_COUNTRY = {
    "India": "India",
    "Australia": "Australia",
    "England": "England",
    "South Africa": "South Africa",
    "New Zealand": "New Zealand",
    "Pakistan": "Pakistan",
    "Bangladesh": "Bangladesh",
    "West Indies": "West Indies",
    "Afghanistan": "Afghanistan",
    "Sri Lanka": "Sri Lanka",
    "Oman": "Oman",
    "Ireland": "Ireland",
    "Mumbai Indians": "India",
    "Chennai Super Kings": "India",
    "Royal Challengers Bengaluru": "India",
    "Punjab Kings": "India",
    "Rajasthan Royals": "India",
    "Lucknow Super Giants": "India",
    "Sunrisers Hyderabad": "India",
    "Kolkata Knight Riders": "India",
}


def seed(engine=None):
    """Seed all sample data.  Idempotent."""
    if engine is None:
        engine = get_engine()

    initialize_database(engine)

    matches_csv  = DATA_DIR / "sample_matches.csv"
    players_csv  = DATA_DIR / "sample_players.csv"
    stats_csv    = DATA_DIR / "sample_player_stats.csv"

    matches_df = pd.read_csv(matches_csv)
    players_df = pd.read_csv(players_csv)
    stats_df   = pd.read_csv(stats_csv)

    with engine.begin() as conn:
        # ── Teams ─────────────────────────────────────────
        all_teams = set(matches_df["team1"].tolist() + matches_df["team2"].tolist())
        for t in all_teams:
            _upsert_team(conn, t, _TEAM_COUNTRY.get(t, "Unknown"))

        logger.info("Teams seeded: %d", len(all_teams))

        # ── Players ───────────────────────────────────────
        player_id_map = {}
        for _, row in players_df.iterrows():
            team_id = _get_team_id(conn, row["team"])
            if team_id is None:
                _upsert_team(conn, row["team"], _TEAM_COUNTRY.get(row["team"], "India"))
                team_id = _get_team_id(conn, row["team"])

            existing = conn.execute(
                text("SELECT player_id FROM players WHERE full_name = :n"),
                {"n": row["full_name"]},
            ).fetchone()
            if existing:
                player_id_map[row["player_id"]] = existing[0]
                continue

            result = conn.execute(
                text(
                    "INSERT INTO players (full_name, team_id, role, batting_style, bowling_style) "
                    "VALUES (:n, :t, :r, :b, :bo)"
                ),
                {
                    "n":  row["full_name"],
                    "t":  team_id,
                    "r":  row["role"],
                    "b":  row["batting_style"],
                    "bo": row["bowling_style"],
                },
            )
            player_id_map[row["player_id"]] = result.lastrowid

        logger.info("Players seeded: %d", len(player_id_map))

        # ── Venues & Matches ──────────────────────────────
        match_id_map = {}
        for _, row in matches_df.iterrows():
            venue_id     = _upsert_venue(conn, row["venue"], row["city"], row.get("city", "Unknown"))
            team1_id     = _get_team_id(conn, row["team1"])
            team2_id     = _get_team_id(conn, row["team2"])
            toss_id      = _get_team_id(conn, row["toss_winner"])
            winner_id    = _get_team_id(conn, row["winner"]) if pd.notna(row.get("winner")) else None

            # Skip duplicates
            existing = conn.execute(
                text(
                    "SELECT match_id FROM matches "
                    "WHERE series_name=:s AND match_date=:d AND team1_id=:t1 AND team2_id=:t2"
                ),
                {"s": row["series_name"], "d": row["match_date"], "t1": team1_id, "t2": team2_id},
            ).fetchone()
            if existing:
                match_id_map[row["match_id"]] = existing[0]
                continue

            toss_decision = row.get("toss_decision", None)
            if pd.isna(toss_decision) or toss_decision == "":
                toss_decision = None

            result = conn.execute(
                text(
                    "INSERT INTO matches "
                    "(series_name, match_format, match_date, team1_id, team2_id, venue_id, "
                    " toss_winner_id, toss_decision, winner_team_id, match_status, result_description) "
                    "VALUES (:s, :f, :d, :t1, :t2, :v, :tw, :td, :w, :ms, :rd)"
                ),
                {
                    "s":  row["series_name"],
                    "f":  row["match_format"],
                    "d":  row["match_date"],
                    "t1": team1_id,
                    "t2": team2_id,
                    "v":  venue_id,
                    "tw": toss_id,
                    "td": toss_decision,
                    "w":  winner_id,
                    "ms": row["match_status"],
                    "rd": row["result_description"],
                },
            )
            match_id_map[row["match_id"]] = result.lastrowid

        logger.info("Matches seeded: %d", len(match_id_map))

        # ── Player Match Stats ────────────────────────────
        stats_inserted = 0
        for _, row in stats_df.iterrows():
            db_match_id  = match_id_map.get(row["match_id"])
            db_player_id = player_id_map.get(row["player_id"])
            if db_match_id is None or db_player_id is None:
                continue

            innings_num = int(row.get("innings_number", 1))
            existing = conn.execute(
                text(
                    "SELECT stat_id FROM player_match_stats "
                    "WHERE match_id=:m AND player_id=:p AND innings_number=:i"
                ),
                {"m": db_match_id, "p": db_player_id, "i": innings_num},
            ).fetchone()
            if existing:
                continue

            conn.execute(
                text(
                    "INSERT INTO player_match_stats "
                    "(match_id, player_id, innings_number, runs, balls_faced, fours, sixes, "
                    " dismissal_type, wickets, runs_conceded, balls_bowled, maidens) "
                    "VALUES (:m, :p, :i, :r, :bf, :fo, :si, :dt, :w, :rc, :bb, :ma)"
                ),
                {
                    "m":  db_match_id,
                    "p":  db_player_id,
                    "i":  innings_num,
                    "r":  int(row.get("runs", 0)),
                    "bf": int(row.get("balls_faced", 0)),
                    "fo": int(row.get("fours", 0)),
                    "si": int(row.get("sixes", 0)),
                    "dt": row.get("dismissal_type", None),
                    "w":  int(row.get("wickets", 0)),
                    "rc": int(row.get("runs_conceded", 0)),
                    "bb": int(row.get("balls_bowled", 0)),
                    "ma": int(row.get("maidens", 0)),
                },
            )
            stats_inserted += 1

        logger.info("Player stats seeded: %d rows", stats_inserted)

    logger.info("[OK] Seeding complete.")


if __name__ == "__main__":
    seed()
    print("[OK] Sample data seeded.")
