"""
pages/5_Team_Analytics.py — Team win rates, head-to-head and venue analysis.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd

from components.header import render_header, render_demo_banner
from components.sidebar import render_sidebar
from components.charts import bar_chart, pie_chart
from services.cricket_service import get_team_win_stats, get_head_to_head, get_venue_stats
from database.repositories import get_all_teams, query_df
from services.analytics_service import win_percentage
from config import DEMO_MODE

st.set_page_config(page_title="Team Analytics | Cricbuzz LiveStats", page_icon="🏆", layout="wide")

render_sidebar()
render_header("Team Analytics", "Win rates, head-to-head records and venue performance")

if DEMO_MODE:
    render_demo_banner()

tab_overview, tab_h2h, tab_venue, tab_format = st.tabs(
    ["📊 Overview", "⚔️ Head-to-Head", "🏟️ Venues", "📋 By Format"]
)

# ── Overview ──────────────────────────────────────────────────────────────────
with tab_overview:
    teams_stats = get_team_win_stats()
    if teams_stats.empty:
        st.info("No team statistics available.")
    else:
        teams_stats["win_pct"] = teams_stats.apply(
            lambda r: win_percentage(r["wins"], r["matches_played"]), axis=1
        )
        st.dataframe(
            teams_stats.rename(columns={
                "team_name": "Team", "matches_played": "Played",
                "wins": "Wins", "losses": "Losses", "win_pct": "Win %"
            }),
            use_container_width=True,
        )
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(
                bar_chart(teams_stats.sort_values("wins", ascending=False),
                          x="team_name", y="wins", title="Team Wins"),
                use_container_width=True,
            )
        with col2:
            teams_stats["losses"] = teams_stats["losses"].fillna(0)
            st.plotly_chart(
                bar_chart(teams_stats.sort_values("win_pct", ascending=False).dropna(subset=["win_pct"]),
                          x="team_name", y="win_pct", title="Win Percentage (%)"),
                use_container_width=True,
            )

# ── Head-to-Head ──────────────────────────────────────────────────────────────
with tab_h2h:
    teams_df = get_all_teams()
    if teams_df.empty:
        st.info("No teams found.")
    else:
        team_names = teams_df["team_name"].tolist()
        col_a, col_b = st.columns(2)
        team_a = col_a.selectbox("Team A", team_names, key="h2h_a")
        team_b = col_b.selectbox("Team B", [t for t in team_names if t != team_a], key="h2h_b")

        team_a_id = int(teams_df[teams_df["team_name"] == team_a]["team_id"].iloc[0])
        team_b_id = int(teams_df[teams_df["team_name"] == team_b]["team_id"].iloc[0])

        h2h = get_head_to_head(team_a_id, team_b_id)
        if h2h.empty:
            st.info(f"No head-to-head matches found between {team_a} and {team_b}.")
        else:
            a_wins = (h2h["winner"] == team_a).sum()
            b_wins = (h2h["winner"] == team_b).sum()
            no_result = h2h["winner"].isna().sum()

            mc1, mc2, mc3 = st.columns(3)
            mc1.metric(f"{team_a} Wins", a_wins)
            mc2.metric(f"{team_b} Wins", b_wins)
            mc3.metric("No Result", no_result)

            st.dataframe(h2h.rename(columns={
                "match_id": "ID", "series_name": "Series", "match_format": "Format",
                "match_date": "Date", "winner": "Winner", "result_description": "Result"
            }), use_container_width=True)

# ── Venues ────────────────────────────────────────────────────────────────────
with tab_venue:
    venue_df = get_venue_stats()
    if venue_df.empty:
        st.info("No venue data available.")
    else:
        st.dataframe(venue_df.rename(columns={
            "venue_name": "Venue", "city": "City", "country": "Country",
            "matches_played": "Matches", "completed": "Completed"
        }), use_container_width=True)

        top10 = venue_df.nlargest(10, "matches_played")
        st.plotly_chart(
            bar_chart(top10, x="venue_name", y="matches_played",
                      title="Top 10 Venues by Matches Played"),
            use_container_width=True,
        )

# ── Performance by Format ─────────────────────────────────────────────────────
with tab_format:
    fmt_df = query_df("""
        SELECT t.team_name, m.match_format,
               COUNT(*) AS played,
               SUM(CASE WHEN m.winner_team_id = t.team_id THEN 1 ELSE 0 END) AS wins
        FROM teams t
        JOIN matches m ON (m.team1_id = t.team_id OR m.team2_id = t.team_id)
        WHERE m.match_status = 'Completed'
        GROUP BY t.team_id, m.match_format
        ORDER BY t.team_name, m.match_format
    """)
    if fmt_df.empty:
        st.info("No format data available.")
    else:
        formats = sorted(fmt_df["match_format"].dropna().unique())
        sel_fmt = st.selectbox("Select Format", formats, key="team_fmt")
        filt = fmt_df[fmt_df["match_format"] == sel_fmt]
        st.dataframe(filt.rename(columns={
            "team_name": "Team", "match_format": "Format",
            "played": "Played", "wins": "Wins"
        }), use_container_width=True)
        st.plotly_chart(
            bar_chart(filt.sort_values("wins", ascending=False),
                      x="team_name", y="wins", title=f"Wins in {sel_fmt}"),
            use_container_width=True,
        )
