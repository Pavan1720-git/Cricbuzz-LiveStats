"""
components/sidebar.py — Shared sidebar for all Streamlit pages.
"""

import streamlit as st
from config import DEMO_MODE
from database.repositories import get_summary_counts


def render_sidebar():
    with st.sidebar:
        st.markdown("## 🏏 Cricbuzz LiveStats")
        st.markdown("---")

        mode = "🟡 Demo Mode" if DEMO_MODE else "🟢 Live Mode"
        st.markdown(f"**Status:** {mode}")

        try:
            counts = get_summary_counts()
            st.markdown("### 📊 Quick Stats")
            col1, col2 = st.columns(2)
            col1.metric("Teams",   counts["teams"])
            col2.metric("Players", counts["players"])
            col1.metric("Matches", counts["matches"])
            col2.metric("Live",    counts["live"])
        except Exception:
            st.info("Database not ready yet.")

        st.markdown("---")
        st.markdown(
            "**Navigation**\n"
            "- 🏠 Home\n"
            "- 📡 Live Matches\n"
            "- 📋 Match Details\n"
            "- 👤 Player Stats\n"
            "- 🏆 Team Analytics\n"
            "- 🗄️ SQL Analytics\n"
            "- ⚙️ Data Management"
        )
        st.markdown("---")
        st.caption("📌 Data is illustrative sample data when in Demo Mode.")
