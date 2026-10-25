"""
app.py — Cricbuzz LiveStats: entry point.

Run with:
    streamlit run app.py
"""

import sys
from pathlib import Path

# Ensure the project root is always on sys.path when Streamlit runs pages/
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Cricbuzz LiveStats",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Auto-initialize database on first launch ──────────────────────────────────
@st.cache_resource(show_spinner="Initializing database…")
def _boot():
    from database.initialize_db import initialize_database
    from database.seed_data import seed
    initialize_database()
    seed()
    return True

_boot()

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Dark navy background */
    .stApp { background-color: #0d1b2a; color: #e8f4f8; }
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #0f2035; }
    /* Metric cards */
    [data-testid="metric-container"] {
        background: #1a3a5c;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        border: 1px solid #2a5a8c;
    }
    /* Dataframes */
    .stDataFrame { border-radius: 6px; }
    /* Buttons */
    .stButton > button {
        background: #00c851;
        color: #0d1b2a;
        font-weight: 700;
        border: none;
        border-radius: 6px;
    }
    .stButton > button:hover { background: #00a040; }
    /* Tabs */
    .stTabs [data-baseweb="tab"] { color: #8fa8c8; }
    .stTabs [aria-selected="true"] { color: #00c851 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Home page content (redirect notice) ──────────────────────────────────────
from components.header import render_header, render_demo_banner
from components.sidebar import render_sidebar
from config import DEMO_MODE

render_sidebar()
render_header("Cricbuzz LiveStats", "Real-Time Cricket Insights & SQL-Based Analytics")

if DEMO_MODE:
    render_demo_banner()

st.markdown(
    """
    Welcome to **Cricbuzz LiveStats** — your cricket analytics dashboard.

    Use the **sidebar** to navigate between pages:

    | Page | Description |
    |------|-------------|
    | 🏠 Home | Dashboard overview with KPIs and charts |
    | 📡 Live Matches | Live, upcoming and recent matches |
    | 📋 Match Details | Detailed scorecards |
    | 👤 Player Statistics | Batting & bowling leaderboards |
    | 🏆 Team Analytics | Win rates, head-to-head, venues |
    | 🗄️ SQL Analytics | 25 predefined SQL insights |
    | ⚙️ Data Management | CRUD operations |

    > **Note:** All data shown is sample/illustrative data in Demo Mode.
    """
)

# Show quick summary metrics
try:
    from database.repositories import get_summary_counts, get_top_run_scorers, get_top_wicket_takers
    from components.charts import top_scorers_chart, top_wicket_chart

    counts = get_summary_counts()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🏏 Matches", counts["matches"])
    c2.metric("📡 Live Now", counts["live"])
    c3.metric("🏆 Teams",   counts["teams"])
    c4.metric("👤 Players", counts["players"])

    st.markdown("---")
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("🏏 Top Run Scorers")
        scorers = get_top_run_scorers(8)
        if not scorers.empty:
            st.plotly_chart(top_scorers_chart(scorers, 8), use_container_width=True)

    with col_r:
        st.subheader("⚾ Top Wicket Takers")
        wickers = get_top_wicket_takers(8)
        if not wickers.empty:
            st.plotly_chart(top_wicket_chart(wickers, 8), use_container_width=True)

except Exception as e:
    st.error(f"Could not load dashboard data: {e}")
