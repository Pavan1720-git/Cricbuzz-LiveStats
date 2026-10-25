"""
components/scorecards.py — Scorecard table renderers.
"""

import pandas as pd
import streamlit as st


def render_batting_scorecard(df: pd.DataFrame):
    """Render a batting scorecard table."""
    if df.empty:
        st.info("No batting data available.")
        return
    cols = [c for c in ["full_name", "runs", "balls_faced", "fours", "sixes",
                         "strike_rate", "dismissal_type"] if c in df.columns]
    rename = {
        "full_name": "Batsman", "runs": "R", "balls_faced": "B",
        "fours": "4s", "sixes": "6s", "strike_rate": "SR", "dismissal_type": "Dismissal"
    }
    st.dataframe(df[cols].rename(columns=rename), use_container_width=True)


def render_bowling_scorecard(df: pd.DataFrame):
    """Render a bowling scorecard table."""
    if df.empty:
        st.info("No bowling data available.")
        return
    cols = [c for c in ["full_name", "balls_bowled", "maidens", "runs_conceded",
                         "wickets", "economy"] if c in df.columns]
    rename = {
        "full_name": "Bowler", "balls_bowled": "Balls", "maidens": "M",
        "runs_conceded": "Runs", "wickets": "Wkts", "economy": "Econ"
    }
    st.dataframe(df[cols].rename(columns=rename), use_container_width=True)


def render_match_card(match: dict):
    """Render a single match summary card."""
    st.markdown(
        f"""
        <div style='background:#1a3a5c;border-radius:8px;padding:1rem;margin-bottom:0.5rem;
                    border-left:4px solid #00c851;'>
            <b style='color:#00c851;'>{match.get('series_name','')}</b>
            &nbsp;|&nbsp; <span style='color:#8fa8c8;'>{match.get('match_format','')}</span><br/>
            <span style='font-size:1.1rem;color:white;'>
                {match.get('team1','')} vs {match.get('team2','')}
            </span><br/>
            <small style='color:#8fa8c8;'>
                📍 {match.get('venue_name', match.get('venue',''))}
                &nbsp;|&nbsp; 📅 {match.get('match_date','')}
            </small><br/>
            <span style='color:#ffd700;'>
                {match.get('result_description', match.get('match_status',''))}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
