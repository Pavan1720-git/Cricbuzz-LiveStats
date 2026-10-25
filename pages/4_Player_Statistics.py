"""
pages/4_Player_Statistics.py — Player batting and bowling leaderboards.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd

from components.header import render_header, render_demo_banner
from components.sidebar import render_sidebar
from components.charts import bar_chart, scatter_chart
from services.cricket_service import get_player_batting_summary, get_player_bowling_summary
from database.repositories import get_all_players, get_all_teams
from config import DEMO_MODE

st.set_page_config(page_title="Player Stats | Cricbuzz LiveStats", page_icon="👤", layout="wide")

render_sidebar()
render_header("Player Statistics", "Batting & bowling leaderboards and comparisons")

if DEMO_MODE:
    render_demo_banner()

# ── Filters ───────────────────────────────────────────────────────────────────
teams = get_all_teams()
team_options = ["All Teams"] + teams["team_name"].tolist()
sel_team = st.selectbox("Filter by team", team_options)

search_name = st.text_input("Search player by name", placeholder="e.g. Kohli")

# ── Batting Stats ─────────────────────────────────────────────────────────────
tab_bat, tab_bowl, tab_compare = st.tabs(["🏏 Batting", "⚾ Bowling", "📊 Compare"])

with tab_bat:
    bat_df = get_player_batting_summary()

    if not bat_df.empty:
        if sel_team != "All Teams":
            bat_df = bat_df[bat_df["team_name"] == sel_team]
        if search_name:
            bat_df = bat_df[bat_df["full_name"].str.contains(search_name, case=False, na=False)]

        display_cols = ["full_name", "team_name", "innings", "total_runs", "highest_score",
                        "total_balls", "total_fours", "total_sixes", "dismissals",
                        "batting_average", "strike_rate"]
        display_cols = [c for c in display_cols if c in bat_df.columns]
        rename_map = {
            "full_name": "Player", "team_name": "Team", "innings": "Inn",
            "total_runs": "Runs", "highest_score": "HS", "total_balls": "Balls",
            "total_fours": "4s", "total_sixes": "6s", "dismissals": "Dismissals",
            "batting_average": "Avg", "strike_rate": "SR"
        }
        st.dataframe(bat_df[display_cols].rename(columns=rename_map), use_container_width=True)

        csv = bat_df.to_csv(index=False)
        st.download_button("⬇️ Download Batting Stats CSV", csv,
                           file_name="batting_stats.csv", mime="text/csv")

        # Chart
        top10 = bat_df.nlargest(10, "total_runs")
        if not top10.empty:
            st.plotly_chart(
                bar_chart(top10, x="full_name", y="total_runs",
                          title="Top 10 Run Scorers", orientation="v"),
                use_container_width=True,
            )
    else:
        st.info("No batting data found.")

with tab_bowl:
    bowl_df = get_player_bowling_summary()

    if not bowl_df.empty:
        if sel_team != "All Teams":
            bowl_df = bowl_df[bowl_df["team_name"] == sel_team]
        if search_name:
            bowl_df = bowl_df[bowl_df["full_name"].str.contains(search_name, case=False, na=False)]

        display_cols = ["full_name", "team_name", "matches", "total_wickets",
                        "total_runs_conceded", "total_balls_bowled", "total_maidens",
                        "bowling_average", "economy", "bowling_sr"]
        display_cols = [c for c in display_cols if c in bowl_df.columns]
        rename_map = {
            "full_name": "Bowler", "team_name": "Team", "matches": "M",
            "total_wickets": "Wkts", "total_runs_conceded": "Runs",
            "total_balls_bowled": "Balls", "total_maidens": "Maidens",
            "bowling_average": "Avg", "economy": "Econ", "bowling_sr": "SR"
        }
        st.dataframe(bowl_df[display_cols].rename(columns=rename_map), use_container_width=True)

        csv = bowl_df.to_csv(index=False)
        st.download_button("⬇️ Download Bowling Stats CSV", csv,
                           file_name="bowling_stats.csv", mime="text/csv")

        top_bowl = bowl_df.nlargest(10, "total_wickets")
        if not top_bowl.empty:
            st.plotly_chart(
                bar_chart(top_bowl, x="full_name", y="total_wickets",
                          title="Top 10 Wicket Takers"),
                use_container_width=True,
            )
    else:
        st.info("No bowling data found.")

with tab_compare:
    st.subheader("📊 Batting: Runs vs Strike Rate")
    bat_all = get_player_batting_summary()
    if not bat_all.empty:
        bat_all_filt = bat_all.dropna(subset=["strike_rate"])
        fig = scatter_chart(
            bat_all_filt, x="total_runs", y="strike_rate",
            title="Runs vs Strike Rate", color="team_name",
            hover_data=["full_name"]
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data for comparison chart.")
