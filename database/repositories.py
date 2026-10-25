"""
database/repositories.py — Data access layer (repository pattern).

All SQL is parameterized.  Never concatenate user input into SQL.
"""

import logging
from typing import Optional
import pandas as pd
from sqlalchemy import text

from database.connection import get_engine

logger = logging.getLogger(__name__)


def _engine():
    return get_engine()


# ── Generic helper ────────────────────────────────────────────────────────────

def query_df(sql: str, params: dict = None) -> pd.DataFrame:
    """Execute a read-only SQL statement and return a DataFrame."""
    with _engine().connect() as conn:
        result = conn.execute(text(sql), params or {})
        rows = result.fetchall()
        cols = list(result.keys())
    return pd.DataFrame(rows, columns=cols)


# ── Teams ─────────────────────────────────────────────────────────────────────

def get_all_teams() -> pd.DataFrame:
    return query_df("SELECT team_id, team_name, country FROM teams ORDER BY team_name")


def get_team_by_id(team_id: int) -> Optional[dict]:
    df = query_df("SELECT * FROM teams WHERE team_id = :id", {"id": team_id})
    return df.iloc[0].to_dict() if not df.empty else None


def create_team(team_name: str, country: str) -> int:
    with _engine().begin() as conn:
        result = conn.execute(
            text("INSERT INTO teams (team_name, country) VALUES (:n, :c)"),
            {"n": team_name, "c": country},
        )
        return result.lastrowid


def update_team(team_id: int, team_name: str, country: str):
    with _engine().begin() as conn:
        conn.execute(
            text("UPDATE teams SET team_name=:n, country=:c WHERE team_id=:id"),
            {"n": team_name, "c": country, "id": team_id},
        )


def delete_team(team_id: int):
    with _engine().begin() as conn:
        conn.execute(text("DELETE FROM teams WHERE team_id = :id"), {"id": team_id})


# ── Players ───────────────────────────────────────────────────────────────────

def get_all_players(team_id: int = None) -> pd.DataFrame:
    if team_id:
        return query_df(
            "SELECT p.player_id, p.full_name, t.team_name, p.role, p.batting_style, p.bowling_style "
            "FROM players p LEFT JOIN teams t ON p.team_id=t.team_id "
            "WHERE p.team_id=:tid ORDER BY p.full_name",
            {"tid": team_id},
        )
    return query_df(
        "SELECT p.player_id, p.full_name, t.team_name, p.role, p.batting_style, p.bowling_style "
        "FROM players p LEFT JOIN teams t ON p.team_id=t.team_id ORDER BY p.full_name"
    )


def get_player_by_id(player_id: int) -> Optional[dict]:
    df = query_df("SELECT * FROM players WHERE player_id = :id", {"id": player_id})
    return df.iloc[0].to_dict() if not df.empty else None


def create_player(full_name: str, team_id: int, role: str, batting_style: str, bowling_style: str) -> int:
    with _engine().begin() as conn:
        result = conn.execute(
            text(
                "INSERT INTO players (full_name, team_id, role, batting_style, bowling_style) "
                "VALUES (:n, :t, :r, :b, :bo)"
            ),
            {"n": full_name, "t": team_id, "r": role, "b": batting_style, "bo": bowling_style},
        )
        return result.lastrowid


def update_player(player_id: int, full_name: str, team_id: int, role: str,
                  batting_style: str, bowling_style: str):
    with _engine().begin() as conn:
        conn.execute(
            text(
                "UPDATE players SET full_name=:n, team_id=:t, role=:r, "
                "batting_style=:b, bowling_style=:bo WHERE player_id=:id"
            ),
            {"n": full_name, "t": team_id, "r": role, "b": batting_style, "bo": bowling_style, "id": player_id},
        )


def delete_player(player_id: int):
    with _engine().begin() as conn:
        conn.execute(text("DELETE FROM players WHERE player_id = :id"), {"id": player_id})


# ── Matches ───────────────────────────────────────────────────────────────────

def get_all_matches(status: str = None, fmt: str = None) -> pd.DataFrame:
    where = []
    params = {}
    if status:
        where.append("m.match_status = :status")
        params["status"] = status
    if fmt:
        where.append("m.match_format = :fmt")
        params["fmt"] = fmt
    where_clause = "WHERE " + " AND ".join(where) if where else ""
    sql = f"""
        SELECT m.match_id, m.series_name, m.match_format, m.match_date,
               t1.team_name AS team1, t2.team_name AS team2,
               v.venue_name, v.city,
               tw.team_name AS toss_winner, m.toss_decision,
               wt.team_name AS winner, m.match_status, m.result_description
        FROM matches m
        JOIN teams t1 ON m.team1_id = t1.team_id
        JOIN teams t2 ON m.team2_id = t2.team_id
        LEFT JOIN venues v  ON m.venue_id = v.venue_id
        LEFT JOIN teams tw  ON m.toss_winner_id = tw.team_id
        LEFT JOIN teams wt  ON m.winner_team_id  = wt.team_id
        {where_clause}
        ORDER BY m.match_date DESC
    """
    return query_df(sql, params)


def get_match_by_id(match_id: int) -> Optional[dict]:
    df = get_all_matches()
    row = df[df["match_id"] == match_id]
    return row.iloc[0].to_dict() if not row.empty else None


# ── Player Stats ──────────────────────────────────────────────────────────────

def get_player_stats(player_id: int = None) -> pd.DataFrame:
    params = {}
    where = ""
    if player_id:
        where = "WHERE pms.player_id = :pid"
        params["pid"] = player_id
    sql = f"""
        SELECT pms.stat_id, pms.match_id, pms.player_id,
               p.full_name, t.team_name, m.match_format, m.match_date,
               pms.innings_number, pms.runs, pms.balls_faced, pms.fours, pms.sixes,
               pms.dismissal_type, pms.wickets, pms.runs_conceded, pms.balls_bowled, pms.maidens
        FROM player_match_stats pms
        JOIN players p ON pms.player_id = p.player_id
        JOIN matches  m ON pms.match_id  = m.match_id
        LEFT JOIN teams t ON p.team_id = t.team_id
        {where}
        ORDER BY m.match_date DESC
    """
    return query_df(sql, params)


# ── Dashboard summary helpers ─────────────────────────────────────────────────

def get_summary_counts() -> dict:
    teams   = query_df("SELECT COUNT(*) AS n FROM teams").iloc[0]["n"]
    players = query_df("SELECT COUNT(*) AS n FROM players").iloc[0]["n"]
    matches = query_df("SELECT COUNT(*) AS n FROM matches").iloc[0]["n"]
    live    = query_df("SELECT COUNT(*) AS n FROM matches WHERE match_status='Live'").iloc[0]["n"]
    return {"teams": int(teams), "players": int(players), "matches": int(matches), "live": int(live)}


def get_top_run_scorers(limit: int = 10) -> pd.DataFrame:
    return query_df(
        "SELECT p.full_name, t.team_name, SUM(pms.runs) AS total_runs "
        "FROM player_match_stats pms "
        "JOIN players p ON pms.player_id=p.player_id "
        "LEFT JOIN teams t ON p.team_id=t.team_id "
        "GROUP BY pms.player_id ORDER BY total_runs DESC LIMIT :lim",
        {"lim": limit},
    )


def get_top_wicket_takers(limit: int = 10) -> pd.DataFrame:
    return query_df(
        "SELECT p.full_name, t.team_name, SUM(pms.wickets) AS total_wickets "
        "FROM player_match_stats pms "
        "JOIN players p ON pms.player_id=p.player_id "
        "LEFT JOIN teams t ON p.team_id=t.team_id "
        "WHERE pms.wickets > 0 "
        "GROUP BY pms.player_id ORDER BY total_wickets DESC LIMIT :lim",
        {"lim": limit},
    )
