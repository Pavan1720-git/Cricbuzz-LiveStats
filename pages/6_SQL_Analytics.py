"""
pages/6_SQL_Analytics.py — 25 predefined SQL analytics queries.

All queries are read-only and predefined. No arbitrary user SQL is executed.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd

from components.header import render_header, render_demo_banner
from components.sidebar import render_sidebar
from database.repositories import query_df
from config import DEMO_MODE

st.set_page_config(page_title="SQL Analytics | Cricbuzz LiveStats", page_icon="🗄️", layout="wide")

render_sidebar()
render_header("SQL Analytics", "25 predefined cricket analytics queries")

if DEMO_MODE:
    render_demo_banner()

# ── Query definitions ─────────────────────────────────────────────────────────
QUERIES = [
    {
        "id": "Q01", "difficulty": "Easy",
        "question": "List all teams",
        "insight": "Shows every team registered in the database.",
        "sql": "SELECT team_id, team_name, country FROM teams ORDER BY team_name",
        "params": {},
    },
    {
        "id": "Q02", "difficulty": "Easy",
        "question": "List all players with their team",
        "insight": "Complete player roster with team and role information.",
        "sql": """SELECT p.player_id, p.full_name, t.team_name, p.role, p.batting_style, p.bowling_style
FROM players p LEFT JOIN teams t ON p.team_id = t.team_id ORDER BY p.full_name""",
        "params": {},
    },
    {
        "id": "Q03", "difficulty": "Easy",
        "question": "Show all completed matches",
        "insight": "All matches with a final result, ordered by date (newest first).",
        "sql": """SELECT m.match_id, m.series_name, m.match_format, m.match_date,
       t1.team_name AS team1, t2.team_name AS team2,
       v.venue_name, m.result_description
FROM matches m
JOIN teams t1 ON m.team1_id = t1.team_id
JOIN teams t2 ON m.team2_id = t2.team_id
LEFT JOIN venues v ON m.venue_id = v.venue_id
WHERE m.match_status = 'Completed'
ORDER BY m.match_date DESC""",
        "params": {},
    },
    {
        "id": "Q04", "difficulty": "Easy",
        "question": "Find the top 10 highest individual batting scores",
        "insight": "Highest scores in a single innings — identifies match-winning performances.",
        "sql": """SELECT p.full_name, t.team_name, pms.runs, pms.balls_faced, m.series_name, m.match_date
FROM player_match_stats pms
JOIN players p ON pms.player_id = p.player_id
JOIN matches m  ON pms.match_id  = m.match_id
LEFT JOIN teams t ON p.team_id = t.team_id
ORDER BY pms.runs DESC LIMIT 10""",
        "params": {},
    },
    {
        "id": "Q05", "difficulty": "Easy",
        "question": "Rank players by total career runs",
        "insight": "All-time run-scorers ranked — the batting Hall of Fame.",
        "sql": """SELECT p.full_name, t.team_name,
       SUM(pms.runs) AS total_runs,
       COUNT(DISTINCT pms.match_id) AS matches_played
FROM player_match_stats pms
JOIN players p ON pms.player_id = p.player_id
LEFT JOIN teams t ON p.team_id = t.team_id
GROUP BY pms.player_id
ORDER BY total_runs DESC""",
        "params": {},
    },
    {
        "id": "Q06", "difficulty": "Easy",
        "question": "Rank bowlers by total wickets",
        "insight": "All-time wicket-takers — bowling Hall of Fame.",
        "sql": """SELECT p.full_name, t.team_name,
       SUM(pms.wickets) AS total_wickets,
       COUNT(DISTINCT pms.match_id) AS matches_played
FROM player_match_stats pms
JOIN players p ON pms.player_id = p.player_id
LEFT JOIN teams t ON p.team_id = t.team_id
WHERE pms.wickets > 0
GROUP BY pms.player_id
ORDER BY total_wickets DESC""",
        "params": {},
    },
    {
        "id": "Q07", "difficulty": "Medium",
        "question": "Calculate batting averages (excluding not-outs from denominator)",
        "insight": "Batting average = total runs ÷ dismissals. Not-outs do not count as dismissals.",
        "sql": """SELECT p.full_name, t.team_name,
       SUM(pms.runs) AS total_runs,
       COUNT(CASE WHEN pms.dismissal_type NOT IN ('not out','') AND pms.dismissal_type IS NOT NULL THEN 1 END) AS dismissals,
       CASE WHEN COUNT(CASE WHEN pms.dismissal_type NOT IN ('not out','') AND pms.dismissal_type IS NOT NULL THEN 1 END) = 0 THEN NULL
            ELSE ROUND(1.0 * SUM(pms.runs) /
                 COUNT(CASE WHEN pms.dismissal_type NOT IN ('not out','') AND pms.dismissal_type IS NOT NULL THEN 1 END), 2)
       END AS batting_average
FROM player_match_stats pms
JOIN players p ON pms.player_id = p.player_id
LEFT JOIN teams t ON p.team_id = t.team_id
GROUP BY pms.player_id
HAVING SUM(pms.runs) > 0
ORDER BY batting_average DESC""",
        "params": {},
    },
    {
        "id": "Q08", "difficulty": "Medium",
        "question": "Calculate batting strike rates",
        "insight": "Strike rate = (runs ÷ balls faced) × 100. Higher = more aggressive batsman.",
        "sql": """SELECT p.full_name, t.team_name,
       SUM(pms.runs) AS total_runs,
       SUM(pms.balls_faced) AS total_balls,
       CASE WHEN SUM(pms.balls_faced) = 0 THEN NULL
            ELSE ROUND(100.0 * SUM(pms.runs) / SUM(pms.balls_faced), 2)
       END AS strike_rate
FROM player_match_stats pms
JOIN players p ON pms.player_id = p.player_id
LEFT JOIN teams t ON p.team_id = t.team_id
GROUP BY pms.player_id
HAVING SUM(pms.balls_faced) > 0
ORDER BY strike_rate DESC""",
        "params": {},
    },
    {
        "id": "Q09", "difficulty": "Medium",
        "question": "Calculate bowling economy rates",
        "insight": "Economy = runs conceded per over. Lower is better for a bowler.",
        "sql": """SELECT p.full_name, t.team_name,
       SUM(pms.wickets) AS total_wickets,
       SUM(pms.runs_conceded) AS total_runs_conceded,
       ROUND(6.0 * SUM(pms.runs_conceded) / NULLIF(SUM(pms.balls_bowled), 0), 2) AS economy_rate
FROM player_match_stats pms
JOIN players p ON pms.player_id = p.player_id
LEFT JOIN teams t ON p.team_id = t.team_id
GROUP BY pms.player_id
HAVING SUM(pms.balls_bowled) > 0
ORDER BY economy_rate ASC""",
        "params": {},
    },
    {
        "id": "Q10", "difficulty": "Medium",
        "question": "Teams with the most wins",
        "insight": "Which team has won the most matches in this dataset?",
        "sql": """SELECT t.team_name, COUNT(*) AS wins
FROM matches m JOIN teams t ON m.winner_team_id = t.team_id
WHERE m.match_status = 'Completed'
GROUP BY t.team_id ORDER BY wins DESC""",
        "params": {},
    },
    {
        "id": "Q11", "difficulty": "Medium",
        "question": "Matches played at each venue",
        "insight": "Reveals which grounds host the most international cricket.",
        "sql": """SELECT v.venue_name, v.city, v.country, COUNT(m.match_id) AS matches_played
FROM venues v LEFT JOIN matches m ON v.venue_id = m.venue_id
GROUP BY v.venue_id ORDER BY matches_played DESC""",
        "params": {},
    },
    {
        "id": "Q12", "difficulty": "Medium",
        "question": "Top 10 most frequently used venues",
        "insight": "The busiest cricket grounds — popular for their capacity and pitch conditions.",
        "sql": """SELECT v.venue_name, v.city, COUNT(m.match_id) AS total_matches
FROM venues v LEFT JOIN matches m ON v.venue_id = m.venue_id
GROUP BY v.venue_id ORDER BY total_matches DESC LIMIT 10""",
        "params": {},
    },
    {
        "id": "Q13", "difficulty": "Medium",
        "question": "Head-to-head results between all team pairs",
        "insight": "A rivalry matrix — which team dominates each head-to-head record.",
        "sql": """SELECT t1.team_name AS team_a, t2.team_name AS team_b,
    COUNT(*) AS matches_played,
    SUM(CASE WHEN m.winner_team_id = m.team1_id THEN 1 ELSE 0 END) AS team_a_wins,
    SUM(CASE WHEN m.winner_team_id = m.team2_id THEN 1 ELSE 0 END) AS team_b_wins,
    SUM(CASE WHEN m.match_status IN ('Abandoned','No Result') THEN 1 ELSE 0 END) AS no_result
FROM matches m
JOIN teams t1 ON m.team1_id = t1.team_id
JOIN teams t2 ON m.team2_id = t2.team_id
GROUP BY m.team1_id, m.team2_id ORDER BY matches_played DESC""",
        "params": {},
    },
    {
        "id": "Q14", "difficulty": "Medium",
        "question": "Do toss winners also win the match?",
        "insight": "Tests the 'toss advantage' hypothesis in cricket.",
        "sql": """SELECT COUNT(*) AS total_matches,
    SUM(CASE WHEN m.toss_winner_id = m.winner_team_id THEN 1 ELSE 0 END) AS toss_winner_won,
    ROUND(100.0 * SUM(CASE WHEN m.toss_winner_id = m.winner_team_id THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_toss_winner_won
FROM matches m
WHERE m.match_status = 'Completed' AND m.toss_winner_id IS NOT NULL""",
        "params": {},
    },
    {
        "id": "Q15", "difficulty": "Medium",
        "question": "Team performance by match format",
        "insight": "Some teams excel in Tests but struggle in T20s. This reveals those patterns.",
        "sql": """SELECT t.team_name, m.match_format,
       COUNT(*) AS played,
       SUM(CASE WHEN m.winner_team_id = t.team_id THEN 1 ELSE 0 END) AS wins
FROM teams t
JOIN matches m ON (m.team1_id = t.team_id OR m.team2_id = t.team_id)
WHERE m.match_status = 'Completed'
GROUP BY t.team_id, m.match_format
ORDER BY t.team_name, m.match_format""",
        "params": {},
    },
    {
        "id": "Q16", "difficulty": "Hard",
        "question": "Players with the most fours",
        "insight": "Boundary hitters — players who score quickly through the off side.",
        "sql": """SELECT p.full_name, t.team_name, SUM(pms.fours) AS total_fours
FROM player_match_stats pms
JOIN players p ON pms.player_id = p.player_id
LEFT JOIN teams t ON p.team_id = t.team_id
GROUP BY pms.player_id ORDER BY total_fours DESC""",
        "params": {},
    },
    {
        "id": "Q17", "difficulty": "Hard",
        "question": "Players with the most sixes",
        "insight": "Power hitters who can clear the boundary — especially important in T20s.",
        "sql": """SELECT p.full_name, t.team_name, SUM(pms.sixes) AS total_sixes
FROM player_match_stats pms
JOIN players p ON pms.player_id = p.player_id
LEFT JOIN teams t ON p.team_id = t.team_id
GROUP BY pms.player_id ORDER BY total_sixes DESC""",
        "params": {},
    },
    {
        "id": "Q18", "difficulty": "Hard",
        "question": "Average team totals per innings by format",
        "insight": "Helps understand expected team scores in ODIs vs T20s vs Tests.",
        "sql": """SELECT t.team_name, m.match_format,
       ROUND(AVG(i.total_runs), 1) AS avg_team_total,
       COUNT(i.innings_id) AS innings_count
FROM innings i
JOIN matches m ON i.match_id = m.match_id
JOIN teams   t ON i.batting_team_id = t.team_id
GROUP BY t.team_id, m.match_format
ORDER BY avg_team_total DESC""",
        "params": {},
    },
    {
        "id": "Q19", "difficulty": "Hard",
        "question": "First-innings vs second-innings win rate",
        "insight": "Does batting first or chasing give a better chance of winning?",
        "sql": """SELECT
    SUM(CASE WHEN i1.batting_team_id = m.winner_team_id THEN 1 ELSE 0 END) AS batting_first_won,
    SUM(CASE WHEN i1.batting_team_id != m.winner_team_id THEN 1 ELSE 0 END) AS chasing_won,
    COUNT(*) AS matches_with_innings_data
FROM matches m
JOIN innings i1 ON i1.match_id = m.match_id AND i1.innings_number = 1
WHERE m.match_status = 'Completed' AND m.winner_team_id IS NOT NULL""",
        "params": {},
    },
    {
        "id": "Q20", "difficulty": "Hard",
        "question": "10 most recent completed matches",
        "insight": "Latest results — useful for tracking current team form.",
        "sql": """SELECT m.match_id, m.series_name, m.match_format, m.match_date,
       t1.team_name AS team1, t2.team_name AS team2,
       wt.team_name AS winner, m.result_description
FROM matches m
JOIN teams t1 ON m.team1_id = t1.team_id
JOIN teams t2 ON m.team2_id = t2.team_id
LEFT JOIN teams wt ON m.winner_team_id = wt.team_id
WHERE m.match_status = 'Completed'
ORDER BY m.match_date DESC LIMIT 10""",
        "params": {},
    },
    {
        "id": "Q21", "difficulty": "Hard",
        "question": "Players with 200+ total runs (minimum threshold)",
        "insight": "Identifies consistent performers who make significant contributions.",
        "sql": """SELECT p.full_name, t.team_name,
       SUM(pms.runs) AS total_runs,
       COUNT(DISTINCT pms.match_id) AS matches_played
FROM player_match_stats pms
JOIN players p ON pms.player_id = p.player_id
LEFT JOIN teams t ON p.team_id = t.team_id
GROUP BY pms.player_id
HAVING total_runs >= 200
ORDER BY total_runs DESC""",
        "params": {},
    },
    {
        "id": "Q22", "difficulty": "Hard",
        "question": "Top bowlers ranked by wickets then economy",
        "insight": "Best all-round bowlers — takes wickets cheaply.",
        "sql": """SELECT p.full_name, t.team_name,
       SUM(pms.wickets) AS total_wickets,
       SUM(pms.runs_conceded) AS runs_conceded,
       ROUND(6.0 * SUM(pms.runs_conceded) / NULLIF(SUM(pms.balls_bowled), 0), 2) AS economy
FROM player_match_stats pms
JOIN players p ON pms.player_id = p.player_id
LEFT JOIN teams t ON p.team_id = t.team_id
GROUP BY pms.player_id
HAVING total_wickets > 0
ORDER BY total_wickets DESC, economy ASC""",
        "params": {},
    },
    {
        "id": "Q23", "difficulty": "Hard",
        "question": "Team win percentages (matches with a result only)",
        "insight": "Win % = wins ÷ decided matches × 100. Excludes no-results and abandoned.",
        "sql": """SELECT t.team_name,
       COUNT(*) AS matches_with_result,
       SUM(CASE WHEN m.winner_team_id = t.team_id THEN 1 ELSE 0 END) AS wins,
       ROUND(100.0 * SUM(CASE WHEN m.winner_team_id = t.team_id THEN 1 ELSE 0 END) / COUNT(*), 1) AS win_pct
FROM teams t
JOIN matches m ON (m.team1_id = t.team_id OR m.team2_id = t.team_id)
WHERE m.match_status = 'Completed' AND m.winner_team_id IS NOT NULL
GROUP BY t.team_id
ORDER BY win_pct DESC""",
        "params": {},
    },
    {
        "id": "Q24", "difficulty": "Hard",
        "question": "Player ranking within each format by runs",
        "insight": "Format-specific rankings — a player might rank #1 in T20s but lower in Tests.",
        "sql": """SELECT p.full_name, t.team_name, m.match_format,
       SUM(pms.runs) AS total_runs,
       RANK() OVER (PARTITION BY m.match_format ORDER BY SUM(pms.runs) DESC) AS format_rank
FROM player_match_stats pms
JOIN players p ON pms.player_id = p.player_id
JOIN matches m  ON pms.match_id  = m.match_id
LEFT JOIN teams t ON p.team_id = t.team_id
GROUP BY pms.player_id, m.match_format
ORDER BY m.match_format, format_rank""",
        "params": {},
    },
    {
        "id": "Q25", "difficulty": "Hard",
        "question": "Player run-scoring trend by year",
        "insight": "Shows whether a player's form is improving, declining, or consistent over time.",
        "sql": """SELECT p.full_name,
       SUBSTR(m.match_date, 1, 4) AS year,
       SUM(pms.runs) AS runs_that_year,
       COUNT(DISTINCT pms.match_id) AS matches
FROM player_match_stats pms
JOIN players p ON pms.player_id = p.player_id
JOIN matches m  ON pms.match_id  = m.match_id
GROUP BY pms.player_id, year
ORDER BY p.full_name, year""",
        "params": {},
    },
]

# ── Filter controls ────────────────────────────────────────────────────────────
difficulty_filter = st.selectbox(
    "Filter by difficulty", ["All", "Easy", "Medium", "Hard"], key="sql_diff"
)
search_q = st.text_input("Search questions", placeholder="e.g. toss, economy")

filtered = QUERIES
if difficulty_filter != "All":
    filtered = [q for q in filtered if q["difficulty"] == difficulty_filter]
if search_q:
    filtered = [q for q in filtered if search_q.lower() in q["question"].lower()]

st.markdown(f"Showing **{len(filtered)}** of {len(QUERIES)} queries")
st.markdown("---")

# ── Render each query ─────────────────────────────────────────────────────────
DIFF_COLOR = {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴"}

for q in filtered:
    with st.expander(f"{DIFF_COLOR.get(q['difficulty'],'⚪')} [{q['id']}] {q['question']}"):
        col_l, col_r = st.columns([2, 1])
        with col_l:
            st.markdown(f"**Difficulty:** {q['difficulty']}")
            st.markdown(f"**Insight:** {q['insight']}")
        with col_r:
            st.markdown(f"**Query ID:** `{q['id']}`")

        st.code(q["sql"], language="sql")

        try:
            result_df = query_df(q["sql"], q["params"])
            if result_df.empty:
                st.info("ℹ️ No rows returned — this is normal if the relevant data is not in the sample set.")
            else:
                st.dataframe(result_df, use_container_width=True)
                csv = result_df.to_csv(index=False)
                st.download_button(
                    f"⬇️ Export {q['id']} CSV",
                    csv,
                    file_name=f"{q['id']}_results.csv",
                    mime="text/csv",
                    key=f"dl_{q['id']}",
                )
        except Exception as exc:
            st.error(f"Query error: {exc}")
