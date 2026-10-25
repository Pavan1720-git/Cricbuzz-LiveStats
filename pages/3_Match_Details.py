"""
pages/3_Match_Details.py — Detailed scorecard for a selected match.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd

from components.header import render_header, render_demo_banner
from components.sidebar import render_sidebar
from components.scorecards import render_batting_scorecard, render_bowling_scorecard
from database.repositories import get_all_matches, get_player_stats
from services.analytics_service import batting_strike_rate, bowling_economy
from config import DEMO_MODE

st.set_page_config(page_title="Match Details | Cricbuzz LiveStats", page_icon="📋", layout="wide")

render_sidebar()
render_header("Match Details", "Batting and bowling scorecards")

if DEMO_MODE:
    render_demo_banner()

# ── Match selector ────────────────────────────────────────────────────────────
matches = get_all_matches()
if matches.empty:
    st.warning("No matches in the database. Run the seeder first.")
    st.stop()

matches["label"] = matches["team1"] + " vs " + matches["team2"] + " (" + matches["match_date"].astype(str) + ")"
selected_label = st.selectbox("Select a match", matches["label"].tolist())
sel_row = matches[matches["label"] == selected_label].iloc[0]
match_id = int(sel_row["match_id"])

# ── Match metadata ────────────────────────────────────────────────────────────
st.markdown(f"### {sel_row['team1']} vs {sel_row['team2']}")
info_cols = st.columns(4)
info_cols[0].info(f"📅 Date: {sel_row['match_date']}")
info_cols[1].info(f"🏟️ Venue: {sel_row.get('venue_name', 'N/A')}")
info_cols[2].info(f"🏏 Format: {sel_row['match_format']}")
info_cols[3].info(f"📊 Status: {sel_row['match_status']}")

if pd.notna(sel_row.get("result_description")):
    st.success(f"🏆 Result: {sel_row['result_description']}")

if pd.notna(sel_row.get("toss_winner")):
    st.caption(f"🪙 Toss: {sel_row['toss_winner']} won and chose to {sel_row.get('toss_decision','N/A')}")

st.markdown("---")

# ── Player stats for this match ───────────────────────────────────────────────
stats = get_player_stats()
match_stats = stats[stats["match_id"] == match_id].copy()

if match_stats.empty:
    st.info("No detailed scorecard data available for this match.")
else:
    # Batting scorecard
    st.subheader("🏏 Batting Scorecard")
    bat = match_stats[match_stats["balls_faced"] > 0].copy()
    if not bat.empty:
        bat["strike_rate"] = bat.apply(
            lambda r: batting_strike_rate(r["runs"], r["balls_faced"]), axis=1
        )
        render_batting_scorecard(bat)
    else:
        st.info("No batting statistics recorded for this match.")

    st.markdown("---")

    # Bowling scorecard
    st.subheader("⚾ Bowling Figures")
    bowl = match_stats[match_stats["balls_bowled"] > 0].copy()
    if not bowl.empty:
        bowl["economy"] = bowl.apply(
            lambda r: bowling_economy(r["runs_conceded"], r["balls_bowled"]), axis=1
        )
        render_bowling_scorecard(bowl)
    else:
        st.info("No bowling statistics recorded for this match.")

    # CSV export
    st.markdown("---")
    csv = match_stats.to_csv(index=False)
    st.download_button("⬇️ Download Scorecard CSV", csv,
                       file_name=f"match_{match_id}_scorecard.csv", mime="text/csv")
