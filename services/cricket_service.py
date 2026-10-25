"""
services/cricket_service.py — Business logic layer.

Combines live API data with database records.
Switches transparently between demo mode and live API mode.
"""

import logging
from datetime import datetime
from typing import Optional
import pandas as pd

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DEMO_MODE
from database import repositories as repo
from services import cricket_api as api

logger = logging.getLogger(__name__)


def is_demo_mode() -> bool:
    return DEMO_MODE


def demo_notice() -> str:
    return (
        "⚠️ **Demo Mode** — This dashboard is using illustrative sample data, "
        "not live Cricbuzz data. To enable live data, add your API key to the `.env` file."
    )


# ── Match data ────────────────────────────────────────────────────────────────

def get_live_matches_display() -> tuple[pd.DataFrame, str]:
    """Return (dataframe, source_label)."""
    if DEMO_MODE:
        df = repo.get_all_matches(status="Live")
        if df.empty:
            df = repo.get_all_matches(status="Completed").head(3)
        return df, "demo"

    raw = api.get_live_matches()
    if raw is None:
        df = repo.get_all_matches(status="Live")
        return df, "db_fallback"

    # Transform API response → flat DataFrame
    matches = raw.get("typeMatches", [])
    rows = []
    for t in matches:
        for sm in t.get("seriesMatches", []):
            for m in sm.get("seriesAdWrapper", {}).get("matches", []):
                mi = m.get("matchInfo", {})
                ms = m.get("matchScore", {})
                rows.append({
                    "match_id":    mi.get("matchId"),
                    "series_name": mi.get("seriesName"),
                    "match_format":mi.get("matchFormat"),
                    "match_date":  mi.get("startDate"),
                    "team1":       mi.get("team1", {}).get("teamName"),
                    "team2":       mi.get("team2", {}).get("teamName"),
                    "venue_name":  mi.get("venueInfo", {}).get("ground"),
                    "match_status":mi.get("state"),
                    "score":       _format_score(ms),
                })
    return pd.DataFrame(rows), "api"


def _format_score(ms: dict) -> str:
    parts = []
    for team_key in ("team1Score", "team2Score"):
        ts = ms.get(team_key, {})
        for inn in ["inngs1", "inngs2"]:
            i = ts.get(inn, {})
            if i:
                r = i.get("runs", "")
                w = i.get("wickets", "")
                o = i.get("overs", "")
                parts.append(f"{r}/{w} ({o})")
    return " | ".join(parts)


def get_recent_matches_display() -> pd.DataFrame:
    if DEMO_MODE:
        return repo.get_all_matches(status="Completed")

    raw = api.get_recent_matches()
    if raw is None:
        return repo.get_all_matches(status="Completed")

    # Simplified parse — return DB data as fallback if transform fails
    try:
        rows = []
        for t in raw.get("typeMatches", []):
            for sm in t.get("seriesMatches", []):
                for m in sm.get("seriesAdWrapper", {}).get("matches", []):
                    mi = m.get("matchInfo", {})
                    rows.append({
                        "match_id":    mi.get("matchId"),
                        "series_name": mi.get("seriesName"),
                        "team1":       mi.get("team1", {}).get("teamName"),
                        "team2":       mi.get("team2", {}).get("teamName"),
                        "match_status":mi.get("state"),
                    })
        return pd.DataFrame(rows) if rows else repo.get_all_matches(status="Completed")
    except Exception as exc:
        logger.warning("API parse failed: %s", exc)
        return repo.get_all_matches(status="Completed")


# ── Player stats ──────────────────────────────────────────────────────────────

def get_player_batting_summary(player_id: int = None) -> pd.DataFrame:
    from services.analytics_service import compute_batting_stats
    df = repo.get_player_stats(player_id)
    return compute_batting_stats(df)


def get_player_bowling_summary(player_id: int = None) -> pd.DataFrame:
    from services.analytics_service import compute_bowling_stats
    df = repo.get_player_stats(player_id)
    return compute_bowling_stats(df)


# ── Team analytics ────────────────────────────────────────────────────────────

def get_team_win_stats() -> pd.DataFrame:
    from database.repositories import query_df
    return query_df("""
        SELECT t.team_name,
               COUNT(DISTINCT m.match_id) AS matches_played,
               SUM(CASE WHEN m.winner_team_id = t.team_id THEN 1 ELSE 0 END) AS wins,
               SUM(CASE WHEN m.winner_team_id != t.team_id
                         AND m.match_status = 'Completed'
                         AND m.winner_team_id IS NOT NULL THEN 1 ELSE 0 END) AS losses
        FROM teams t
        JOIN matches m ON (m.team1_id = t.team_id OR m.team2_id = t.team_id)
        GROUP BY t.team_id
        ORDER BY wins DESC
    """)


def get_head_to_head(team_a_id: int, team_b_id: int) -> pd.DataFrame:
    from database.repositories import query_df
    return query_df("""
        SELECT m.match_id, m.series_name, m.match_format, m.match_date,
               wt.team_name AS winner, m.result_description
        FROM matches m
        LEFT JOIN teams wt ON m.winner_team_id = wt.team_id
        WHERE (m.team1_id=:a AND m.team2_id=:b)
           OR (m.team1_id=:b AND m.team2_id=:a)
        ORDER BY m.match_date DESC
    """, {"a": team_a_id, "b": team_b_id})


def get_venue_stats() -> pd.DataFrame:
    from database.repositories import query_df
    return query_df("""
        SELECT v.venue_name, v.city, v.country,
               COUNT(m.match_id) AS matches_played,
               SUM(CASE WHEN m.match_status='Completed' THEN 1 ELSE 0 END) AS completed
        FROM venues v
        LEFT JOIN matches m ON v.venue_id = m.venue_id
        GROUP BY v.venue_id
        ORDER BY matches_played DESC
    """)
