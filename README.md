# 🏏 Cricbuzz LiveStats — Real-Time Cricket Insights & SQL-Based Analytics

A comprehensive, production-grade cricket analytics dashboard built for sports analysts, coaches, and cricket enthusiasts. Integrates real-time cricket data APIs with a normalized relational database (MySQL/SQLite), offering interactive visualizations, SQL-based statistical querying, and controlled CRUD operations.

---

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Problem Statement & Objectives](#problem-statement--objectives)
3. [System Architecture & Data Flow](#system-architecture--data-flow)
4. [Technology Stack](#technology-stack)
5. [Database Schema & Entity Relationships](#database-schema--entity-relationships)
6. [Windows Setup & Installation](#windows-setup--installation)
7. [API Configuration & Demo Mode](#api-configuration--demo-mode)
8. [Database Initialization & Seeding](#database-initialization--seeding)
9. [Running the Application](#running-the-application)
10. [Automated Testing](#automated-testing)
11. [Dashboard Pages Walkthrough](#dashboard-pages-walkthrough)
12. [SQL Analytics Queries (25 Predefined Queries)](#sql-analytics-queries)
13. [Cricket Formulas & Validation Rules](#cricket-formulas--validation-rules)
14. [Troubleshooting & FAQs](#troubleshooting--faqs)
15. [Limitations & Attribution](#limitations--attribution)
16. [Deployment Guide](#deployment-guide)

---

## 1. Project Overview

**Cricbuzz LiveStats** bridges the gap between live streaming data and relational analytics. It provides:
- Live match tracking with live scorecard displays.
- Historical match statistics across international formats (ODI, T20I, Test) and franchise leagues (IPL).
- Career batting and bowling performance metrics calculated using standard ICC-compliant cricket formulas.
- Head-to-head records and venue analysis.
- 25 categorized SQL analytics queries with live execution and instant CSV export.
- Full Data Management (CRUD) for teams and players with foreign-key enforcement.
- Seamless demo mode fallback with deterministic sample data when external API credentials are not provided.

---

## 2. Problem Statement & Objectives

Cricket generates high-volume, multi-dimensional statistics: ball-by-ball events, strike rates, economy rates, partnerships, venue biases, and toss correlations. Most casual dashboards only show high-level score updates without relational depth or analytical querying capabilities.

### Objectives:
- **Normalized Persistence:** Store match entities, innings, and player performances in a 3NF relational schema.
- **Dual Engine Support:** Run out of the box using SQLite for local development/offline grading, with plug-and-play MySQL support for production.
- **Accurate Cricket Mathematics:** Implement strict non-zero division safety, ball-to-over conversions, and exclusion of not-outs in batting averages.
- **Interactive Visualizations:** Render responsive charts using Plotly and Streamlit in a dark navy and cricket-green sports aesthetic.
- **Security & Integrity:** Prevent SQL injection using parameterized queries, store secrets strictly in `.env`, and provide input validation for all CRUD actions.

---

## 3. System Architecture & Data Flow

```mermaid
flowchart TD
    subgraph Data Sources
        API[Cricbuzz / RapidAPI]
        SampleCSV[Deterministic CSVs in data/]
    end

    subgraph Service Layer
        ApiSvc[services/cricket_api.py - TTL Cache & Rate Limit]
        CricketSvc[services/cricket_service.py - Orchestrator]
        AnalyticsSvc[services/analytics_service.py - Cricket Math & Validation]
    end

    subgraph Database Layer
        Conn[database/connection.py - SQLAlchemy Pool]
        Repo[database/repositories.py - Parameterized Queries]
        DB[(MySQL / SQLite cricbuzz.db)]
    end

    subgraph Presentation Layer - Streamlit
        App[app.py - Main Entry]
        P1[1_Home.py - Overview & KPIs]
        P2[2_Live_Matches.py - Live Feeds]
        P3[3_Match_Details.py - Scorecards]
        P4[4_Player_Statistics.py - Bat/Bowl Tables]
        P5[5_Team_Analytics.py - H2H & Venues]
        P6[6_SQL_Analytics.py - 25 Predefined Queries]
        P7[7_Data_Management.py - CRUD Forms]
    end

    API -->|Authorized REST| ApiSvc
    SampleCSV -->|Seed| DB
    ApiSvc --> CricketSvc
    DB --> Repo
    Repo --> CricketSvc
    AnalyticsSvc --> CricketSvc
    CricketSvc --> Presentation Layer
```

---

## 4. Technology Stack

- **Language:** Python 3.11+
- **Frontend / Dashboard:** Streamlit 1.32+
- **Visualizations:** Plotly Express & Plotly Graph Objects
- **Data Manipulation:** Pandas 2.0+
- **Database:** SQLite (default/zero-config fallback) or MySQL 8.0+
- **ORM & Query Engine:** SQLAlchemy 2.0+ & PyMySQL
- **HTTP Client:** Requests with custom TTL cache and retry/timeout handlers
- **Configuration:** Python-Dotenv
- **Testing:** Pytest & Pytest-Mock

---

## 5. Database Schema & Entity Relationships

The schema is defined in `schema.sql` and includes appropriate primary keys, foreign keys, index structures, and check constraints:

```mermaid
erDiagram
    teams ||--o{ players : "rosters"
    teams ||--o{ matches : "team1"
    teams ||--o{ matches : "team2"
    teams ||--o{ matches : "winner"
    venues ||--o{ matches : "hosts"
    matches ||--o{ innings : "has"
    matches ||--o{ player_match_stats : "records"
    players ||--o{ player_match_stats : "scores"

    teams {
        int team_id PK
        string team_name UK
        string country
        string created_at
    }

    players {
        int player_id PK
        string full_name
        int team_id FK
        string role
        string batting_style
        string bowling_style
    }

    venues {
        int venue_id PK
        string venue_name
        string city
        string country
    }

    matches {
        int match_id PK
        string series_name
        string match_format
        string match_date
        int team1_id FK
        int team2_id FK
        int venue_id FK
        int toss_winner_id FK
        string toss_decision
        int winner_team_id FK
        string match_status
        string result_description
    }

    innings {
        int innings_id PK
        int match_id FK
        int innings_number
        int batting_team_id FK
        int total_runs
        int total_wickets
        real total_overs
        int extras
    }

    player_match_stats {
        int stat_id PK
        int match_id FK
        int player_id FK
        int innings_number
        int runs
        int balls_faced
        int fours
        int sixes
        string dismissal_type
        int wickets
        int runs_conceded
        int balls_bowled
        int maidens
    }
```

---

## 6. Windows Setup & Installation

Follow these steps in PowerShell or CMD on Windows:

```powershell
# 1. Navigate to the project directory
cd Cricbuzz-LiveStats

# 2. Create a virtual environment (recommended)
python -m venv .venv

# 3. Activate the virtual environment
.venv\Scripts\activate

# 4. Install all dependencies
pip install -r requirements.txt
```

---

## 7. API Configuration & Demo Mode

### Demo Mode (Default, Zero-Config)
If you don't have a RapidAPI Cricbuzz key, **the system automatically operates in Demo Mode**. All features, charts, leaderboards, and 25 SQL queries run against the comprehensive sample dataset located in `data/`.

### Live Mode Setup
To connect to live Cricbuzz data:
1. Copy `.env.example` to `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```
2. Edit `.env` and fill in your RapidAPI credentials:
   ```env
   CRICKET_API_KEY=your_rapidapi_key_here
   CRICKET_API_HOST=cricbuzz-cricket.p.rapidapi.com
   CRICKET_API_BASE_URL=https://cricbuzz-cricket.p.rapidapi.com
   DATABASE_URL=sqlite:///cricbuzz.db
   DEMO_MODE=false
   ```
3. To switch to MySQL, update `DATABASE_URL`:
   ```env
   DATABASE_URL=mysql+pymysql://username:password@localhost:3306/cricbuzz_db
   ```

---

## 8. Database Initialization & Seeding

Run these scripts from the project root:

```powershell
# Initialize tables and indexes
python -m database.initialize_db

# Seed sample teams, players, matches, and stats (idempotent; safe to repeat)
python -m database.seed_data
```

---

## 9. Running the Application

Launch the Streamlit web dashboard:

```powershell
streamlit run app.py
```

Open your browser at: **`http://localhost:8501`**

---

## 10. Automated Testing

The project contains unit and integration tests covering cricket formulas, database CRUD, SQL queries, and API error handling:

```powershell
pytest
```

---

## 11. Dashboard Pages Walkthrough

- **🏠 1_Home.py:** Top KPIs (Total Matches, Live Matches, Teams, Players), interactive top 10 run scorers and wicket takers charts, format breakdown pie chart, and recent match cards.
- **📡 2_Live_Matches.py:** Real-time match feed tabs (Live/Upcoming vs Recent Completed), format filters, and a manual cache-refresh button.
- **📋 3_Match_Details.py:** Deep-dive into any selected match with venue metadata, toss details, formatted batting scorecards with strike rates, bowling figures with economy rates, and instant CSV scorecard export.
- **👤 4_Player_Statistics.py:** Batting and bowling leaderboards, team and name search filters, and a scatter chart comparing Career Runs vs Batting Strike Rate.
- **🏆 5_Team_Analytics.py:** Win percentage tables, head-to-head match comparison selector, venue utilization rankings, and format-wise team win distributions.
- **🗄️ 6_SQL_Analytics.py:** 25 structured analytical questions organized by difficulty (Easy, Medium, Hard). Displays the SQL code, dynamic result table, business insight explanation, and downloadable CSV export for each query.
- **⚙️ 7_Data_Management.py:** Full CRUD interface for adding, searching, modifying, and safely deleting teams and players with foreign-key referential integrity checks and confirmation prompts.

---

## 12. SQL Analytics Queries

The application implements 25 curated analytical queries defined in `queries.sql` and accessible via Page 6:

| ID | Difficulty | Title | Business Insight |
|:---|:---|:---|:---|
| **Q01** | Easy | List all teams | Master team directory |
| **Q02** | Easy | List all players with their team | Player roster with playing roles |
| **Q03** | Easy | Show completed matches | Chronological list of concluded fixtures |
| **Q04** | Easy | Highest individual batting scores | Match-winning single innings knocks |
| **Q05** | Easy | Rank players by career runs | Batting aggregate leaderboard |
| **Q06** | Easy | Rank bowlers by total wickets | Bowling aggregate leaderboard |
| **Q07** | Medium | Batting averages (excluding not-outs) | Accurate metric: $\text{Runs} / \text{Dismissals}$ |
| **Q08** | Medium | Batting strike rates | Scoring pace: $(\text{Runs} / \text{Balls}) \times 100$ |
| **Q09** | Medium | Bowling economy rates | Run containment: $\text{Runs Conceded} / \text{Overs Bowled}$ |
| **Q10** | Medium | Teams with most wins | Most successful teams across all fixtures |
| **Q11** | Medium | Matches played by venue | Match distribution per cricket ground |
| **Q12** | Medium | Most frequently used venues | Ground popularity and hosting density |
| **Q13** | Medium | Head-to-head records | Rivalry matrix with win/loss/no-result breakdown |
| **Q14** | Medium | Toss winners vs match winners | Toss advantage hypothesis testing |
| **Q15** | Medium | Team performance by match format | Format specialization (Tests vs T20s vs ODIs) |
| **Q16** | Hard | Players with most fours | Boundary accumulation through precision |
| **Q17** | Hard | Players with most sixes | Power hitting leaderboard |
| **Q18** | Hard | Average team totals per innings | Expected team totals across formats |
| **Q19** | Hard | Batting first vs chasing win rate | Pitch deterioration vs chase pressure |
| **Q20** | Hard | 10 most recent completed matches | Current form and recency tracking |
| **Q21** | Hard | Players meeting 200+ run threshold | High-contribution core performers |
| **Q22** | Hard | Bowlers ranked by wickets & economy | Multi-attribute ranking: strike power + stinginess |
| **Q23** | Hard | Team win percentages (decided matches) | Standardized winning efficiency percentage |
| **Q24** | Hard | Format-specific player rankings | SQL Window function (`RANK() OVER PARTITION BY`) |
| **Q25** | Hard | Player scoring trends over time | Yearly progression and longevity tracking |

---

## 13. Cricket Formulas & Validation Rules

1. **Batting Strike Rate:**
   $$\text{SR} = \frac{\text{Runs}}{\text{Balls Faced}} \times 100 \quad (\text{if Balls} > 0)$$
2. **Batting Average:**
   $$\text{Avg} = \frac{\text{Total Runs}}{\text{Dismissals}} \quad (\text{Not Outs are excluded from denominator})$$
3. **Bowling Economy Rate:**
   $$\text{Economy} = \frac{\text{Runs Conceded}}{\text{Legal Overs Bowled}} = \frac{6 \times \text{Runs Conceded}}{\text{Balls Bowled}}$$
4. **Cricket Overs Notation:**
   In cricket, $19.5$ overs means $19$ completed overs and $5$ legal deliveries ($119$ balls), **not** $19.5$ decimal ($117$ balls). The application rigorously enforces:
   $$\text{Balls} = \lfloor\text{Overs}\rfloor \times 6 + \text{fraction} \times 10$$
   Deliveries component must be between $0$ and $5$.

---

## 14. Troubleshooting & FAQs

- **Q: `ModuleNotFoundError: No module named 'database'`**  
  *A:* Make sure you run commands from the project root (`Cricbuzz-LiveStats`), or use `python -m database.initialize_db`. Streamlit automatically injects the project directory into `sys.path`.
- **Q: UnicodeEncodeError on Windows PowerShell**  
  *A:* The application and CLI scripts strictly output ASCII indicators (`[OK]`, `[INFO]`) to avoid CP1252 Windows console encoding errors.
- **Q: How do I reset the sample data?**  
  *A:* Delete `cricbuzz.db` and re-run `python -m database.initialize_db` and `python -m database.seed_data`.

---

## 15. Limitations & Attribution

- **Live Data Quota:** Live cricket APIs often enforce strict rate limits on free tiers. The application implements an in-memory TTL cache (`API_CACHE_SECONDS=60`) to respect API limits.
- **Data Attribution:** In Demo Mode, all data represents synthetic/illustrative samples created for academic and internship demonstration purposes. In Live Mode, match records are consumed from the configured Cricbuzz API via RapidAPI.

---

## 16. Deployment Guide

To deploy to **Streamlit Community Cloud**:
1. Push this repository to GitHub.
2. Log in to [share.streamlit.io](https://share.streamlit.io).
3. Connect your repository and select `app.py` as the main entry point.
4. Under **Settings > Secrets**, add your environment variables from `.env.example`.
5. Deploy! The application will automatically boot the database schema and seed deterministic data on first load.
