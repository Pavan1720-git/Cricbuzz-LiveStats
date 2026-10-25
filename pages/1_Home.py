"""
pages/1_Home.py — Home Dashboard.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from components.header import render_header, render_demo_banner
from components.sidebar import render_sidebar
from components.charts import top_scorers_chart, top_wicket_chart, bar_chart, pie_chart
from database.repositories import (
    get_summary_counts, get_top_run_scorers, get_top_wicket_takers, get_all_matches
)
from config import DEMO_MODE

st.set_page_config(page_title="Home | Cricbuzz LiveStats", page_icon="🏠", layout="wide")

render_sidebar()
render_header("Home Dashboard", "Overview of cricket statistics and recent results")

if DEMO_MODE:
    render_demo_banner()

# ── KPI Metrics ───────────────────────────────────────────────────────────────
try:
    counts = get_summary_counts()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🏏 Total Matches", counts["matches"])
    c2.metric("📡 Live Matches",  counts["live"],  help="Matches currently in progress")
    c3.metric("🏆 Teams",         counts["teams"])
    c4.metric("👤 Players",       counts["players"])
except Exception as e:
    st.error(f"Database error: {e}")
    st.stop()

st.markdown("---")

# ── Charts ────────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏏 Top 10 Run Scorers")
    scorers = get_top_run_scorers(10)
    if not scorers.empty:
        st.plotly_chart(top_scorers_chart(scorers, 10), use_container_width=True)
    else:
        st.info("No batting data available.")

with col2:
    st.subheader("⚾ Top 10 Wicket Takers")
    wickets = get_top_wicket_takers(10)
    if not wickets.empty:
        st.plotly_chart(top_wicket_chart(wickets, 10), use_container_width=True)
    else:
        st.info("No bowling data available.")

# ── Match format distribution ─────────────────────────────────────────────────
st.markdown("---")
col3, col4 = st.columns(2)

with col3:
    st.subheader("📊 Matches by Format")
    matches_df = get_all_matches()
    if not matches_df.empty:
        fmt_count = matches_df.groupby("match_format").size().reset_index(name="count")
        st.plotly_chart(pie_chart(fmt_count, "match_format", "count", "Matches by Format"),
                        use_container_width=True)

with col4:
    st.subheader("📋 Recent Completed Matches")
    recent = get_all_matches(status="Completed").head(5)
    if not recent.empty:
        for _, row in recent.iterrows():
            st.markdown(
                f"**{row['team1']} vs {row['team2']}** — {row['result_description'] or row['match_status']}"
                f"  \n*{row.get('series_name','')} | {row.get('match_date','')}*"
            )
            st.markdown("---")
    else:
        st.info("No recent matches found.")

st.caption("📌 Data shown is sample/illustrative data in Demo Mode.")
