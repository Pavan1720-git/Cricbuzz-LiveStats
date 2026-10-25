"""
components/header.py — Shared page header for all Streamlit pages.
"""

import streamlit as st


def render_header(title: str, subtitle: str = ""):
    st.markdown(
        """
        <style>
        .main-header {
            background: linear-gradient(135deg, #0d1b2a 0%, #1a3a5c 100%);
            padding: 1.2rem 1.5rem;
            border-radius: 10px;
            border-left: 5px solid #00c851;
            margin-bottom: 1rem;
        }
        .main-header h1 {
            color: #00c851;
            margin: 0;
            font-size: 1.8rem;
            font-weight: 700;
        }
        .main-header p {
            color: #8fa8c8;
            margin: 0.2rem 0 0;
            font-size: 0.95rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    sub_html = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f'<div class="main-header"><h1>🏏 {title}</h1>{sub_html}</div>',
        unsafe_allow_html=True,
    )


def render_demo_banner():
    st.warning(
        "⚠️ **Demo Mode** — Showing illustrative sample data. "
        "Add your API key to `.env` to enable live Cricbuzz data."
    )
