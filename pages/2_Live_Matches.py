"""
pages/2_Live_Matches.py — Live, upcoming and recent matches.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from datetime import datetime

from components.header import render_header, render_demo_banner
from components.sidebar import render_sidebar
from components.scorecards import render_match_card
from services.cricket_service import get_live_matches_display, get_recent_matches_display
from services.cricket_api import clear_cache, last_refresh_time
from config import DEMO_MODE

st.set_page_config(page_title="Live Matches | Cricbuzz LiveStats", page_icon="📡", layout="wide")

render_sidebar()
render_header("Live Matches", "Live, upcoming and recently completed matches")

if DEMO_MODE:
    render_demo_banner()

# ── Refresh controls ──────────────────────────────────────────────────────────
col_r1, col_r2 = st.columns([3, 1])
with col_r2:
    if st.button("🔄 Refresh Now"):
        clear_cache()
        st.rerun()

last = last_refresh_time()
if last:
    st.caption(f"Last refreshed: {last.strftime('%Y-%m-%d %H:%M:%S')}")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_live, tab_recent = st.tabs(["📡 Live / Upcoming", "✅ Recent Completed"])

with tab_live:
    with st.spinner("Loading live matches…"):
        df, source = get_live_matches_display()

    if source == "api":
        st.success("✅ Live data from Cricbuzz API")
    elif source == "db_fallback":
        st.warning("⚠️ API unavailable — showing database records")
    else:
        st.info("ℹ️ Demo mode — showing sample data")

    if df.empty:
        st.info("🏏 No live matches are currently in progress.")
    else:
        for _, row in df.iterrows():
            render_match_card(row.to_dict())

with tab_recent:
    with st.spinner("Loading recent matches…"):
        recent_df = get_recent_matches_display()

    if recent_df.empty:
        st.info("No completed matches found.")
    else:
        # Filters
        formats = ["All"] + sorted(recent_df["match_format"].dropna().unique().tolist()) \
            if "match_format" in recent_df.columns else ["All"]
        sel_fmt = st.selectbox("Filter by format", formats, key="live_fmt_filter")
        show_df = recent_df if sel_fmt == "All" else recent_df[recent_df["match_format"] == sel_fmt]

        for _, row in show_df.head(20).iterrows():
            render_match_card(row.to_dict())
