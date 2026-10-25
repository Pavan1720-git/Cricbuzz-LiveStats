"""
pages/7_Data_Management.py — CRUD operations for teams and players.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd

from components.header import render_header, render_demo_banner
from components.sidebar import render_sidebar
from database import repositories as repo
from config import DEMO_MODE

st.set_page_config(page_title="Data Management | Cricbuzz LiveStats", page_icon="⚙️", layout="wide")

render_sidebar()
render_header("Data Management", "Create, read, update and delete teams and players")

if DEMO_MODE:
    render_demo_banner()

st.info(
    "ℹ️ You can add, edit or remove **manually entered** records here. "
    "Original sample data records can also be managed but changes persist only in this session's database."
)

tab_teams, tab_players = st.tabs(["🏆 Teams", "👤 Players"])

# ── TEAMS ─────────────────────────────────────────────────────────────────────
with tab_teams:
    crud_teams = st.selectbox("Operation", ["View All", "Add New Team", "Edit Team", "Delete Team"],
                              key="team_op")

    if crud_teams == "View All":
        teams_df = repo.get_all_teams()
        st.dataframe(teams_df, use_container_width=True)

    elif crud_teams == "Add New Team":
        with st.form("add_team_form"):
            new_name    = st.text_input("Team Name *")
            new_country = st.text_input("Country *")
            submitted   = st.form_submit_button("➕ Add Team")
            if submitted:
                if not new_name.strip() or not new_country.strip():
                    st.error("Team name and country are required.")
                else:
                    # Check duplicate
                    existing = repo.get_all_teams()
                    if new_name.strip() in existing["team_name"].values:
                        st.error(f"Team '{new_name}' already exists.")
                    else:
                        try:
                            tid = repo.create_team(new_name.strip(), new_country.strip())
                            st.success(f"✅ Team '{new_name}' added with ID {tid}.")
                        except Exception as e:
                            st.error(f"Error: {e}")

    elif crud_teams == "Edit Team":
        teams_df = repo.get_all_teams()
        if teams_df.empty:
            st.info("No teams to edit.")
        else:
            sel = st.selectbox("Select team to edit", teams_df["team_name"].tolist(), key="edit_team_sel")
            row = teams_df[teams_df["team_name"] == sel].iloc[0]
            with st.form("edit_team_form"):
                upd_name    = st.text_input("Team Name", value=row["team_name"])
                upd_country = st.text_input("Country",   value=row["country"])
                submitted   = st.form_submit_button("💾 Save Changes")
                if submitted:
                    if not upd_name.strip() or not upd_country.strip():
                        st.error("Both fields are required.")
                    else:
                        try:
                            repo.update_team(int(row["team_id"]), upd_name.strip(), upd_country.strip())
                            st.success("✅ Team updated.")
                        except Exception as e:
                            st.error(f"Error: {e}")

    elif crud_teams == "Delete Team":
        teams_df = repo.get_all_teams()
        if teams_df.empty:
            st.info("No teams to delete.")
        else:
            sel = st.selectbox("Select team to delete", teams_df["team_name"].tolist(), key="del_team_sel")
            row = teams_df[teams_df["team_name"] == sel].iloc[0]
            st.warning(f"⚠️ This will delete team **{sel}** and may affect related records.")
            confirm = st.checkbox("I understand the impact and want to proceed")
            if confirm and st.button("🗑️ Delete Team", type="primary"):
                try:
                    repo.delete_team(int(row["team_id"]))
                    st.success(f"✅ Team '{sel}' deleted.")
                except Exception as e:
                    st.error(f"Error (related records may exist): {e}")

# ── PLAYERS ───────────────────────────────────────────────────────────────────
with tab_players:
    ROLES = ["Batsman", "Bowler", "All-rounder", "Wicket-keeper", "Unknown"]
    BAT_STYLES = ["Right-hand bat", "Left-hand bat"]
    BOWL_STYLES = [
        "Right-arm fast", "Right-arm fast-medium", "Right-arm medium",
        "Right-arm off-break", "Right-arm leg-break",
        "Left-arm fast", "Left-arm fast-medium", "Left-arm medium",
        "Left-arm orthodox", "Left-arm wrist-spin", "N/A"
    ]

    crud_players = st.selectbox(
        "Operation", ["View All", "Search", "Add New Player", "Edit Player", "Delete Player"],
        key="player_op"
    )

    teams_df = repo.get_all_teams()
    team_map = dict(zip(teams_df["team_name"], teams_df["team_id"]))

    if crud_players == "View All":
        players_df = repo.get_all_players()
        st.dataframe(players_df, use_container_width=True)

    elif crud_players == "Search":
        q = st.text_input("Search by name", placeholder="e.g. Kohli")
        if q:
            all_p = repo.get_all_players()
            filtered = all_p[all_p["full_name"].str.contains(q, case=False, na=False)]
            st.dataframe(filtered, use_container_width=True)

    elif crud_players == "Add New Player":
        with st.form("add_player_form"):
            pname    = st.text_input("Full Name *")
            pteam    = st.selectbox("Team", ["(no team)"] + list(team_map.keys()))
            prole    = st.selectbox("Role", ROLES)
            pbat     = st.selectbox("Batting Style", BAT_STYLES)
            pbowl    = st.selectbox("Bowling Style", BOWL_STYLES)
            sub      = st.form_submit_button("➕ Add Player")
            if sub:
                if not pname.strip():
                    st.error("Player name is required.")
                else:
                    team_id = team_map.get(pteam) if pteam != "(no team)" else None
                    try:
                        pid = repo.create_player(pname.strip(), team_id, prole, pbat, pbowl)
                        st.success(f"✅ Player '{pname}' added with ID {pid}.")
                    except Exception as e:
                        st.error(f"Error: {e}")

    elif crud_players == "Edit Player":
        players_df = repo.get_all_players()
        if players_df.empty:
            st.info("No players to edit.")
        else:
            sel = st.selectbox("Select player", players_df["full_name"].tolist(), key="edit_p_sel")
            row = players_df[players_df["full_name"] == sel].iloc[0]
            with st.form("edit_player_form"):
                upd_name  = st.text_input("Full Name", value=row["full_name"])
                upd_team  = st.selectbox("Team",
                                         ["(no team)"] + list(team_map.keys()),
                                         index=list(team_map.keys()).index(row["team_name"])
                                               if row["team_name"] in team_map else 0)
                upd_role  = st.selectbox("Role",  ROLES,
                                         index=ROLES.index(row["role"]) if row["role"] in ROLES else 0)
                upd_bat   = st.selectbox("Batting Style", BAT_STYLES)
                upd_bowl  = st.selectbox("Bowling Style", BOWL_STYLES)
                sub       = st.form_submit_button("💾 Save")
                if sub:
                    team_id = team_map.get(upd_team) if upd_team != "(no team)" else None
                    try:
                        repo.update_player(int(row["player_id"]), upd_name.strip(), team_id,
                                           upd_role, upd_bat, upd_bowl)
                        st.success("✅ Player updated.")
                    except Exception as e:
                        st.error(f"Error: {e}")

    elif crud_players == "Delete Player":
        players_df = repo.get_all_players()
        if players_df.empty:
            st.info("No players to delete.")
        else:
            sel = st.selectbox("Select player to delete", players_df["full_name"].tolist(), key="del_p_sel")
            row = players_df[players_df["full_name"] == sel].iloc[0]
            st.warning(f"⚠️ Deleting **{sel}** will also remove their match statistics.")
            confirm = st.checkbox("I confirm deletion", key="del_p_confirm")
            if confirm and st.button("🗑️ Delete Player", type="primary"):
                try:
                    repo.delete_player(int(row["player_id"]))
                    st.success(f"✅ Player '{sel}' deleted.")
                except Exception as e:
                    st.error(f"Error: {e}")
