"""
queries.py

A collection of SQL queries against the WNBA database.
Each query answers a specific question about the 2025 WNBA season.

Run this script to see all queries executed against the database.
"""

import sqlite3

DB_PATH = "data/wnba.db"


def run_query(title, description, sql, params=None):
    """Run a query and print results in a readable format."""
    print("\n" + "=" * 70)
    print(f"{title}")
    print("-" * 70)
    print(f"{description}")
    print("=" * 70)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(sql, params or [])
    columns = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    conn.close()

    print(" | ".join(columns))
    print("-" * 70)
    for row in rows:
        print(" | ".join(str(c) if c is not None else "-" for c in row))


QUERY_1 = """
SELECT
    t.full_name AS team,
    COUNT(*) AS wins
FROM games g
JOIN teams t
    ON t.id = CASE
        WHEN g.home_score > g.visitor_score THEN g.home_team_id
        ELSE g.visitor_team_id
    END
WHERE g.home_score IS NOT NULL
GROUP BY t.full_name
ORDER BY wins DESC
"""

QUERY_2 = """
SELECT
    t.full_name AS team,
    SUM(CASE WHEN g.home_team_id = t.id AND g.home_score > g.visitor_score THEN 1 ELSE 0 END) AS home_wins,
    SUM(CASE WHEN g.home_team_id = t.id AND g.home_score < g.visitor_score THEN 1 ELSE 0 END) AS home_losses,
    SUM(CASE WHEN g.visitor_team_id = t.id AND g.visitor_score > g.home_score THEN 1 ELSE 0 END) AS road_wins,
    SUM(CASE WHEN g.visitor_team_id = t.id AND g.visitor_score < g.home_score THEN 1 ELSE 0 END) AS road_losses
FROM teams t
JOIN games g
    ON t.id IN (g.home_team_id, g.visitor_team_id)
WHERE g.home_score IS NOT NULL
GROUP BY t.full_name
HAVING home_wins + home_losses + road_wins + road_losses > 0
ORDER BY (home_wins + road_wins) DESC
"""

QUERY_3 = """
SELECT
    t.full_name AS team,
    ROUND(AVG(CASE WHEN g.home_team_id = t.id THEN g.home_score ELSE g.visitor_score END), 1) AS avg_pts_scored,
    ROUND(AVG(CASE WHEN g.home_team_id = t.id THEN g.visitor_score ELSE g.home_score END), 1) AS avg_pts_allowed,
    ROUND(
        AVG(CASE WHEN g.home_team_id = t.id THEN g.home_score ELSE g.visitor_score END) -
        AVG(CASE WHEN g.home_team_id = t.id THEN g.visitor_score ELSE g.home_score END),
        1
    ) AS point_differential
FROM teams t
JOIN games g
    ON t.id IN (g.home_team_id, g.visitor_team_id)
WHERE g.home_score IS NOT NULL
GROUP BY t.full_name
HAVING COUNT(*) > 5
ORDER BY point_differential DESC
"""

QUERY_4 = """
SELECT
    g.date,
    home_t.abbreviation AS home,
    g.home_score,
    visitor_t.abbreviation AS away,
    g.visitor_score,
    ABS(g.home_score - g.visitor_score) AS margin
FROM games g
JOIN teams home_t ON home_t.id = g.home_team_id
JOIN teams visitor_t ON visitor_t.id = g.visitor_team_id
WHERE g.home_score IS NOT NULL
ORDER BY margin DESC
LIMIT 10
"""

QUERY_5 = """
SELECT
    g.date,
    home_t.abbreviation AS home,
    g.home_score,
    visitor_t.abbreviation AS away,
    g.visitor_score,
    ABS(g.home_score - g.visitor_score) AS margin
FROM games g
JOIN teams home_t ON home_t.id = g.home_team_id
JOIN teams visitor_t ON visitor_t.id = g.visitor_team_id
WHERE g.home_score IS NOT NULL
ORDER BY margin ASC, g.date ASC
LIMIT 10
"""

QUERY_6 = """
SELECT
    CASE WHEN g.postseason = 1 THEN 'Playoffs' ELSE 'Regular Season' END AS phase,
    COUNT(*) AS games,
    ROUND(AVG(g.home_score + g.visitor_score), 1) AS avg_total_points,
    ROUND(AVG(ABS(g.home_score - g.visitor_score)), 1) AS avg_margin
FROM games g
WHERE g.home_score IS NOT NULL
GROUP BY g.postseason
ORDER BY g.postseason
"""

QUERY_7 = """
SELECT
    g.date,
    home_t.abbreviation AS home,
    g.home_score,
    visitor_t.abbreviation AS away,
    g.visitor_score,
    (g.home_score + g.visitor_score) AS total_points
FROM games g
JOIN teams home_t ON home_t.id = g.home_team_id
JOIN teams visitor_t ON visitor_t.id = g.visitor_team_id
WHERE g.home_score IS NOT NULL
ORDER BY total_points DESC
LIMIT 10
"""

QUERY_11 = """
WITH ordered_results AS (
    SELECT
        g.date,
        g.id AS game_id,
        t.id AS team_id,
        t.full_name AS team,
        CASE
            WHEN (g.home_team_id = t.id AND g.home_score > g.visitor_score)
              OR (g.visitor_team_id = t.id AND g.visitor_score > g.home_score)
            THEN 1
            ELSE 0
        END AS won
    FROM teams t
    JOIN games g ON t.id IN (g.home_team_id, g.visitor_team_id)
    WHERE g.home_score IS NOT NULL
),
numbered AS (
    SELECT
        team,
        date,
        won,
        ROW_NUMBER() OVER (PARTITION BY team ORDER BY date) AS rn_all,
        ROW_NUMBER() OVER (PARTITION BY team, won ORDER BY date) AS rn_won
    FROM ordered_results
),
streak_groups AS (
    SELECT
        team,
        date,
        won,
        (rn_all - rn_won) AS streak_group
    FROM numbered
),
streak_lengths AS (
    SELECT
        team,
        won,
        streak_group,
        COUNT(*) AS streak_length
    FROM streak_groups
    GROUP BY team, won, streak_group
)
SELECT
    team,
    MAX(streak_length) AS longest_win_streak
FROM streak_lengths
WHERE won = 1
GROUP BY team
ORDER BY longest_win_streak DESC, team ASC
"""

# QUERY 12: Roster size for current active WNBA teams only.
# We filter using the team IDs that appear as either home or visitor
# in regular season or playoff games, which excludes all-star teams,
# historical teams, and international/exhibition teams.
QUERY_12 = """
WITH active_teams AS (
    SELECT id FROM teams WHERE id IN (
        SELECT home_team_id FROM games WHERE home_score IS NOT NULL
        UNION
        SELECT visitor_team_id FROM games WHERE home_score IS NOT NULL
    )
    AND full_name NOT IN ('TEAM COLLIER', 'TEAM CLARK')
)
SELECT
    t.full_name AS team,
    COUNT(p.id) AS roster_size
FROM teams t
JOIN active_teams a ON a.id = t.id
LEFT JOIN players p ON p.team_id = t.id
GROUP BY t.full_name
ORDER BY roster_size DESC, t.full_name ASC
"""


def main():
    run_query(
        "QUERY 1: Win totals by team",
        "Which teams won the most games in 2025?",
        QUERY_1,
    )
    run_query(
        "QUERY 2: Home vs road performance",
        "How do teams perform at home versus on the road?",
        QUERY_2,
    )
    run_query(
        "QUERY 3: Offensive and defensive averages",
        "Average points scored and allowed per team, plus point differential.",
        QUERY_3,
    )
    run_query(
        "QUERY 4: Biggest blowouts of the season",
        "The 10 games with the largest margins of victory.",
        QUERY_4,
    )
    run_query(
        "QUERY 5: Closest games of the season",
        "The 10 nail-biters with the smallest margins.",
        QUERY_5,
    )
    run_query(
        "QUERY 6: Regular season vs playoffs",
        "Are playoff games higher-scoring and closer than regular season games?",
        QUERY_6,
    )
    run_query(
        "QUERY 7: Highest-scoring games of the season",
        "The 10 games with the most combined points.",
        QUERY_7,
    )
    run_query(
        "QUERY 11: Longest winning streak per team",
        "Each team's longest consecutive run of wins. Uses window functions and the gaps-and-islands pattern.",
        QUERY_11,
    )
    run_query(
        "QUERY 12: Roster size by active WNBA team",
        "Number of players associated with each active 2025 WNBA team.",
        QUERY_12,
    )


if __name__ == "__main__":
    main()
