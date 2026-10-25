-- ============================================================
-- queries.sql  — 25 predefined SQL analytics queries
-- Each query is labelled with its ID, difficulty and question.
-- ============================================================

-- ── EASY ──────────────────────────────────────────────────

-- Q01 [Easy] List all teams
SELECT team_id, team_name, country FROM teams ORDER BY team_name;

-- Q02 [Easy] List all players with their team name
SELECT p.player_id, p.full_name, t.team_name, p.role, p.batting_style, p.bowling_style
FROM players p LEFT JOIN teams t ON p.team_id = t.team_id ORDER BY p.full_name;

-- Q03 [Easy] Show all completed matches
SELECT m.match_id, m.series_name, m.match_format, m.match_date,
       t1.team_name AS team1, t2.team_name AS team2,
       v.venue_name, m.result_description
FROM matches m
JOIN teams t1 ON m.team1_id = t1.team_id
JOIN teams t2 ON m.team2_id = t2.team_id
LEFT JOIN venues v ON m.venue_id = v.venue_id
WHERE m.match_status = 'Completed'
ORDER BY m.match_date DESC;

-- Q04 [Easy] Find the highest individual batting score
SELECT p.full_name, t.team_name, pms.runs, pms.balls_faced, m.series_name, m.match_date
FROM player_match_stats pms
JOIN players p ON pms.player_id = p.player_id
JOIN matches m  ON pms.match_id  = m.match_id
LEFT JOIN teams t ON p.team_id = t.team_id
ORDER BY pms.runs DESC LIMIT 10;

-- Q05 [Easy] Rank players by total runs (career)
SELECT p.full_name, t.team_name,
       SUM(pms.runs)        AS total_runs,
       COUNT(DISTINCT pms.match_id) AS matches_played
FROM player_match_stats pms
JOIN players p ON pms.player_id = p.player_id
LEFT JOIN teams t ON p.team_id = t.team_id
GROUP BY pms.player_id
ORDER BY total_runs DESC;

-- Q06 [Easy] Rank bowlers by total wickets
SELECT p.full_name, t.team_name,
       SUM(pms.wickets) AS total_wickets,
       COUNT(DISTINCT pms.match_id) AS matches_played
FROM player_match_stats pms
JOIN players p ON pms.player_id = p.player_id
LEFT JOIN teams t ON p.team_id = t.team_id
WHERE pms.wickets > 0
GROUP BY pms.player_id
ORDER BY total_wickets DESC;

-- ── MEDIUM ────────────────────────────────────────────────

-- Q07 [Medium] Calculate batting averages (runs / dismissals; excludes not-outs)
SELECT p.full_name, t.team_name,
       SUM(pms.runs) AS total_runs,
       COUNT(CASE WHEN pms.dismissal_type NOT IN ('not out','') AND pms.dismissal_type IS NOT NULL
                  THEN 1 END) AS dismissals,
       CASE WHEN COUNT(CASE WHEN pms.dismissal_type NOT IN ('not out','') AND pms.dismissal_type IS NOT NULL
                            THEN 1 END) = 0
            THEN NULL
            ELSE ROUND(1.0 * SUM(pms.runs) /
                 COUNT(CASE WHEN pms.dismissal_type NOT IN ('not out','') AND pms.dismissal_type IS NOT NULL
                            THEN 1 END), 2)
       END AS batting_average
FROM player_match_stats pms
JOIN players p ON pms.player_id = p.player_id
LEFT JOIN teams t ON p.team_id = t.team_id
GROUP BY pms.player_id
HAVING SUM(pms.runs) > 0
ORDER BY batting_average DESC NULLS LAST;

-- Q08 [Medium] Calculate batting strike rates (runs / balls_faced × 100)
SELECT p.full_name, t.team_name,
       SUM(pms.runs)        AS total_runs,
       SUM(pms.balls_faced) AS total_balls,
       CASE WHEN SUM(pms.balls_faced) = 0 THEN NULL
            ELSE ROUND(100.0 * SUM(pms.runs) / SUM(pms.balls_faced), 2)
       END AS strike_rate
FROM player_match_stats pms
JOIN players p ON pms.player_id = p.player_id
LEFT JOIN teams t ON p.team_id = t.team_id
GROUP BY pms.player_id
HAVING SUM(pms.balls_faced) > 0
ORDER BY strike_rate DESC NULLS LAST;

-- Q09 [Medium] Calculate bowling economy rates (runs_conceded / legal_overs)
SELECT p.full_name, t.team_name,
       SUM(pms.wickets)       AS total_wickets,
       SUM(pms.runs_conceded) AS total_runs_conceded,
       SUM(pms.balls_bowled)  AS total_balls_bowled,
       CASE WHEN SUM(pms.balls_bowled) = 0 THEN NULL
            ELSE ROUND(6.0 * SUM(pms.runs_conceded) / SUM(pms.balls_bowled), 2)
       END AS economy_rate
FROM player_match_stats pms
JOIN players p ON pms.player_id = p.player_id
LEFT JOIN teams t ON p.team_id = t.team_id
GROUP BY pms.player_id
HAVING SUM(pms.balls_bowled) > 0
ORDER BY economy_rate ASC NULLS LAST;

-- Q10 [Medium] Find teams with the most wins
SELECT t.team_name, COUNT(*) AS wins
FROM matches m JOIN teams t ON m.winner_team_id = t.team_id
WHERE m.match_status = 'Completed'
GROUP BY t.team_id ORDER BY wins DESC;

-- Q11 [Medium] Show matches played at each venue
SELECT v.venue_name, v.city, v.country, COUNT(m.match_id) AS matches_played
FROM venues v LEFT JOIN matches m ON v.venue_id = m.venue_id
GROUP BY v.venue_id ORDER BY matches_played DESC;

-- Q12 [Medium] Most frequently used venues
SELECT v.venue_name, v.city, COUNT(m.match_id) AS total_matches
FROM venues v LEFT JOIN matches m ON v.venue_id = m.venue_id
GROUP BY v.venue_id ORDER BY total_matches DESC LIMIT 10;

-- Q13 [Medium] Head-to-head results between all team pairs
SELECT
    t1.team_name AS team_a,
    t2.team_name AS team_b,
    COUNT(*)     AS matches_played,
    SUM(CASE WHEN m.winner_team_id = m.team1_id THEN 1 ELSE 0 END) AS team_a_wins,
    SUM(CASE WHEN m.winner_team_id = m.team2_id THEN 1 ELSE 0 END) AS team_b_wins,
    SUM(CASE WHEN m.match_status IN ('Abandoned','No Result') THEN 1 ELSE 0 END) AS no_result
FROM matches m
JOIN teams t1 ON m.team1_id = t1.team_id
JOIN teams t2 ON m.team2_id = t2.team_id
GROUP BY m.team1_id, m.team2_id
ORDER BY matches_played DESC;

-- Q14 [Medium] Toss winners vs match winners
SELECT
    COUNT(*) AS total_matches,
    SUM(CASE WHEN m.toss_winner_id = m.winner_team_id THEN 1 ELSE 0 END) AS toss_winner_won,
    ROUND(100.0 * SUM(CASE WHEN m.toss_winner_id = m.winner_team_id THEN 1 ELSE 0 END) / COUNT(*), 1)
        AS pct_toss_winner_won
FROM matches m
WHERE m.match_status = 'Completed' AND m.toss_winner_id IS NOT NULL;

-- Q15 [Medium] Team performance by match format
SELECT t.team_name, m.match_format,
       COUNT(*) AS played,
       SUM(CASE WHEN m.winner_team_id = t.team_id THEN 1 ELSE 0 END) AS wins
FROM teams t
JOIN matches m ON (m.team1_id = t.team_id OR m.team2_id = t.team_id)
WHERE m.match_status = 'Completed'
GROUP BY t.team_id, m.match_format
ORDER BY t.team_name, m.match_format;

-- ── HARD ──────────────────────────────────────────────────

-- Q16 [Hard] Players with most fours
SELECT p.full_name, t.team_name, SUM(pms.fours) AS total_fours
FROM player_match_stats pms
JOIN players p ON pms.player_id = p.player_id
LEFT JOIN teams t ON p.team_id = t.team_id
GROUP BY pms.player_id ORDER BY total_fours DESC;

-- Q17 [Hard] Players with most sixes
SELECT p.full_name, t.team_name, SUM(pms.sixes) AS total_sixes
FROM player_match_stats pms
JOIN players p ON pms.player_id = p.player_id
LEFT JOIN teams t ON p.team_id = t.team_id
GROUP BY pms.player_id ORDER BY total_sixes DESC;

-- Q18 [Hard] Average team totals per innings by format
SELECT t.team_name, m.match_format,
       ROUND(AVG(i.total_runs), 1) AS avg_team_total,
       COUNT(i.innings_id)         AS innings_count
FROM innings i
JOIN matches m ON i.match_id = m.match_id
JOIN teams   t ON i.batting_team_id = t.team_id
GROUP BY t.team_id, m.match_format
ORDER BY avg_team_total DESC;

-- Q19 [Hard] First-innings vs second-innings win rate
SELECT
    SUM(CASE WHEN i1.batting_team_id = m.winner_team_id THEN 1 ELSE 0 END) AS first_innings_batting_won,
    SUM(CASE WHEN i1.batting_team_id != m.winner_team_id THEN 1 ELSE 0 END) AS chased_successfully,
    COUNT(*) AS completed_with_innings_data
FROM matches m
JOIN innings i1 ON i1.match_id = m.match_id AND i1.innings_number = 1
WHERE m.match_status = 'Completed' AND m.winner_team_id IS NOT NULL;

-- Q20 [Hard] 10 most recent completed matches
SELECT m.match_id, m.series_name, m.match_format, m.match_date,
       t1.team_name AS team1, t2.team_name AS team2,
       wt.team_name AS winner, m.result_description
FROM matches m
JOIN teams t1 ON m.team1_id = t1.team_id
JOIN teams t2 ON m.team2_id = t2.team_id
LEFT JOIN teams wt ON m.winner_team_id = wt.team_id
WHERE m.match_status = 'Completed'
ORDER BY m.match_date DESC LIMIT 10;

-- Q21 [Hard] Players who scored above a minimum run threshold (>= 200 runs)
SELECT p.full_name, t.team_name,
       SUM(pms.runs) AS total_runs,
       COUNT(DISTINCT pms.match_id) AS matches_played
FROM player_match_stats pms
JOIN players p ON pms.player_id = p.player_id
LEFT JOIN teams t ON p.team_id = t.team_id
GROUP BY pms.player_id
HAVING total_runs >= 200
ORDER BY total_runs DESC;

-- Q22 [Hard] Top bowlers ranked by wickets then economy
SELECT p.full_name, t.team_name,
       SUM(pms.wickets)                                                    AS total_wickets,
       SUM(pms.runs_conceded)                                              AS runs_conceded,
       ROUND(6.0 * SUM(pms.runs_conceded) / NULLIF(SUM(pms.balls_bowled),0), 2) AS economy
FROM player_match_stats pms
JOIN players p ON pms.player_id = p.player_id
LEFT JOIN teams t ON p.team_id = t.team_id
GROUP BY pms.player_id
HAVING total_wickets > 0
ORDER BY total_wickets DESC, economy ASC;

-- Q23 [Hard] Team win percentages (excluding abandoned / no-result)
SELECT t.team_name,
       COUNT(*) AS matches_with_result,
       SUM(CASE WHEN m.winner_team_id = t.team_id THEN 1 ELSE 0 END) AS wins,
       ROUND(100.0 * SUM(CASE WHEN m.winner_team_id = t.team_id THEN 1 ELSE 0 END) / COUNT(*), 1) AS win_pct
FROM teams t
JOIN matches m ON (m.team1_id = t.team_id OR m.team2_id = t.team_id)
WHERE m.match_status = 'Completed' AND m.winner_team_id IS NOT NULL
GROUP BY t.team_id
ORDER BY win_pct DESC;

-- Q24 [Hard] Player ranking within their format by runs
SELECT p.full_name, t.team_name, m.match_format,
       SUM(pms.runs) AS total_runs,
       RANK() OVER (PARTITION BY m.match_format ORDER BY SUM(pms.runs) DESC) AS format_rank
FROM player_match_stats pms
JOIN players p ON pms.player_id = p.player_id
JOIN matches m  ON pms.match_id  = m.match_id
LEFT JOIN teams t ON p.team_id = t.team_id
GROUP BY pms.player_id, m.match_format
ORDER BY m.match_format, format_rank;

-- Q25 [Hard] Player run-scoring trend by year
SELECT p.full_name,
       SUBSTR(m.match_date, 1, 4) AS year,
       SUM(pms.runs)              AS runs_that_year,
       COUNT(DISTINCT pms.match_id) AS matches
FROM player_match_stats pms
JOIN players p ON pms.player_id = p.player_id
JOIN matches m  ON pms.match_id  = m.match_id
GROUP BY pms.player_id, year
ORDER BY p.full_name, year;
