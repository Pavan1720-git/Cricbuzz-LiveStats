-- ============================================================
-- schema.sql  - Cricbuzz LiveStats relational schema
-- Compatible with SQLite (dev) and MySQL (production).
-- ============================================================

-- 1. Teams
CREATE TABLE IF NOT EXISTS teams (
    team_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    team_name   TEXT    NOT NULL UNIQUE,
    country     TEXT    NOT NULL,
    created_at  TEXT    DEFAULT (datetime('now'))
);

-- 2. Players
CREATE TABLE IF NOT EXISTS players (
    player_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name       TEXT    NOT NULL,
    team_id         INTEGER REFERENCES teams(team_id) ON DELETE SET NULL,
    role            TEXT    CHECK(role IN ('Batsman','Bowler','All-rounder','Wicket-keeper','Unknown')),
    batting_style   TEXT,
    bowling_style   TEXT,
    created_at      TEXT    DEFAULT (datetime('now'))
);

-- 3. Venues
CREATE TABLE IF NOT EXISTS venues (
    venue_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    venue_name  TEXT    NOT NULL,
    city        TEXT,
    country     TEXT,
    created_at  TEXT    DEFAULT (datetime('now'))
);

-- 4. Matches
CREATE TABLE IF NOT EXISTS matches (
    match_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    series_name         TEXT,
    match_format        TEXT    CHECK(match_format IN ('Test','ODI','T20I','T20','IPL','Other')),
    match_date          TEXT,
    team1_id            INTEGER REFERENCES teams(team_id),
    team2_id            INTEGER REFERENCES teams(team_id),
    venue_id            INTEGER REFERENCES venues(venue_id),
    toss_winner_id      INTEGER REFERENCES teams(team_id),
    toss_decision       TEXT    CHECK(toss_decision IN ('bat','field',NULL)),
    winner_team_id      INTEGER REFERENCES teams(team_id),
    match_status        TEXT    CHECK(match_status IN ('Live','Completed','Upcoming','Abandoned','No Result')),
    result_description  TEXT,
    created_at          TEXT    DEFAULT (datetime('now'))
);

-- 5. Innings
CREATE TABLE IF NOT EXISTS innings (
    innings_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id        INTEGER NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
    innings_number  INTEGER NOT NULL CHECK(innings_number BETWEEN 1 AND 4),
    batting_team_id INTEGER REFERENCES teams(team_id),
    total_runs      INTEGER DEFAULT 0,
    total_wickets   INTEGER DEFAULT 0,
    total_overs     REAL    DEFAULT 0.0,
    extras          INTEGER DEFAULT 0,
    UNIQUE(match_id, innings_number)
);

-- 6. Player Match Statistics
CREATE TABLE IF NOT EXISTS player_match_stats (
    stat_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id        INTEGER NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
    player_id       INTEGER NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    innings_number  INTEGER DEFAULT 1,
    runs            INTEGER DEFAULT 0,
    balls_faced     INTEGER DEFAULT 0,
    fours           INTEGER DEFAULT 0,
    sixes           INTEGER DEFAULT 0,
    dismissal_type  TEXT,
    wickets         INTEGER DEFAULT 0,
    runs_conceded   INTEGER DEFAULT 0,
    balls_bowled    INTEGER DEFAULT 0,
    maidens         INTEGER DEFAULT 0,
    UNIQUE(match_id, player_id, innings_number)
);

-- Indexes (created after tables)
CREATE INDEX IF NOT EXISTS idx_players_team ON players(team_id);
CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date);
CREATE INDEX IF NOT EXISTS idx_matches_format ON matches(match_format);
CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(match_status);
CREATE INDEX IF NOT EXISTS idx_pms_player ON player_match_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_pms_match ON player_match_stats(match_id);
