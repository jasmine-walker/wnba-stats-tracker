"""
dashboard.py

Reads from the WNBA SQLite database, runs the documented queries,
and generates a static HTML dashboard at output/dashboard.html.
"""

import os
import sqlite3
from datetime import datetime

DB_PATH = "data/wnba.db"
OUTPUT_PATH = "output/index.html"


# Inline SVG icons. Generic basketball-themed shapes, no branded IP.
# stroke-width is set per-icon since some look better thicker than others.
ICONS = {
    "basketball": '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2v20M4.93 4.93l14.14 14.14M19.07 4.93L4.93 19.07"/></svg>''',
    "trophy": '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/></svg>''',
    "building": '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect width="16" height="20" x="4" y="2" rx="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01M16 6h.01M12 6h.01M12 10h.01M12 14h.01M16 10h.01M16 14h.01M8 10h.01M8 14h.01"/></svg>''',
    "shield": '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>''',
    "lightning": '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>''',
    "target": '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>''',
    "stopwatch": '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="14" r="8"/><path d="M5 3 2 6M22 6l-3-3M6.38 18.7 4 21M17.64 18.67 20 21M12 10v4l2 1M9 2h6"/></svg>''',
    "flame": '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg>''',
    "streak": '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="m22 17-8.5-8.5-5 5L2 7"/><path d="M16 17h6v-6"/></svg>''',
    "users": '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>''',
    "calendar": '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/></svg>''',
    "chart": '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><line x1="12" x2="12" y1="20" y2="10"/><line x1="18" x2="18" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="16"/></svg>''',
    "points": '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>''',
    "github": '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 00-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0020 4.77 5.07 5.07 0 0019.91 1S18.73.65 16 2.48a13.38 13.38 0 00-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 005 4.77a5.44 5.44 0 00-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 009 18.13V22"/></svg>''',
    "linkedin": '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M16 8a6 6 0 016 6v7h-4v-7a2 2 0 00-4 0v7h-4v-7a6 6 0 016-6z"/><rect x="2" y="9" width="4" height="12"/><circle cx="4" cy="4" r="2"/></svg>''',
}


QUERIES = [
    {
        "title": "Who won the most?",
        "description": "Total wins for each team across the 2026 season so far.",
        "sql": """
            SELECT
                t.full_name AS Team,
                COUNT(*) AS Wins
            FROM games g
            JOIN teams t
                ON t.id = CASE
                    WHEN g.home_score > g.visitor_score THEN g.home_team_id
                    ELSE g.visitor_team_id
                END
            WHERE g.status = 'post'
              AND t.full_name NOT IN ('TEAM COLLIER', 'TEAM CLARK')
            GROUP BY t.full_name
            ORDER BY Wins DESC
        """,
        "bar_column": "Wins",
    },
    {
        "title": "Home vs road",
        "description": "Where teams won and lost. Home court still matters in the W.",
        "sql": """
            SELECT
                t.full_name AS Team,
                SUM(CASE WHEN g.home_team_id = t.id AND g.home_score > g.visitor_score THEN 1 ELSE 0 END) AS "Home W",
                SUM(CASE WHEN g.home_team_id = t.id AND g.home_score < g.visitor_score THEN 1 ELSE 0 END) AS "Home L",
                SUM(CASE WHEN g.visitor_team_id = t.id AND g.visitor_score > g.home_score THEN 1 ELSE 0 END) AS "Road W",
                SUM(CASE WHEN g.visitor_team_id = t.id AND g.visitor_score < g.home_score THEN 1 ELSE 0 END) AS "Road L"
            FROM teams t
            JOIN games g ON t.id IN (g.home_team_id, g.visitor_team_id)
            WHERE g.status = 'post'
              AND t.full_name NOT IN ('TEAM COLLIER', 'TEAM CLARK')
            GROUP BY t.full_name
            HAVING ("Home W" + "Home L" + "Road W" + "Road L") > 5
            ORDER BY ("Home W" + "Road W") DESC
        """,
    },
    {
        "title": "Offense vs defense",
        "description": "Average points scored, allowed, and the differential. Positive means the team outscored opponents on average.",
        "sql": """
            SELECT
                t.full_name AS Team,
                ROUND(AVG(CASE WHEN g.home_team_id = t.id THEN g.home_score ELSE g.visitor_score END), 1) AS Scored,
                ROUND(AVG(CASE WHEN g.home_team_id = t.id THEN g.visitor_score ELSE g.home_score END), 1) AS Allowed,
                ROUND(
                    AVG(CASE WHEN g.home_team_id = t.id THEN g.home_score ELSE g.visitor_score END) -
                    AVG(CASE WHEN g.home_team_id = t.id THEN g.visitor_score ELSE g.home_score END),
                    1
                ) AS Differential
            FROM teams t
            JOIN games g ON t.id IN (g.home_team_id, g.visitor_team_id)
            WHERE g.status = 'post'
              AND t.full_name NOT IN ('TEAM COLLIER', 'TEAM CLARK')
            GROUP BY t.full_name
            HAVING COUNT(*) > 5
            ORDER BY Differential DESC
        """,
        "diff_column": "Differential",
    },
    {
        "title": "Biggest blowouts",
        "description": "The 10 games decided by the largest margins.",
        "sql": """
            SELECT
                SUBSTR(g.date, 1, 10) AS Date,
                home_t.abbreviation AS Home,
                g.home_score AS "Home Score",
                visitor_t.abbreviation AS Away,
                g.visitor_score AS "Away Score",
                ABS(g.home_score - g.visitor_score) AS Margin
            FROM games g
            JOIN teams home_t ON home_t.id = g.home_team_id
            JOIN teams visitor_t ON visitor_t.id = g.visitor_team_id
            WHERE g.status = 'post'
            ORDER BY Margin DESC
            LIMIT 10
        """,
        "bar_column": "Margin",
    },
    {
        "title": "Closest games",
        "description": "The 10 nail-biters that came down to a single possession.",
        "sql": """
            SELECT
                SUBSTR(g.date, 1, 10) AS Date,
                home_t.abbreviation AS Home,
                g.home_score AS "Home Score",
                visitor_t.abbreviation AS Away,
                g.visitor_score AS "Away Score",
                ABS(g.home_score - g.visitor_score) AS Margin
            FROM games g
            JOIN teams home_t ON home_t.id = g.home_team_id
            JOIN teams visitor_t ON visitor_t.id = g.visitor_team_id
            WHERE g.status = 'post'
            ORDER BY Margin ASC, g.date ASC
            LIMIT 10
        """,
    },
    {
        "title": "Regular season vs playoffs",
        "description": "Comparing regular season and playoff scoring patterns. The playoff row will populate once the postseason begins.",
        "sql": """
            SELECT
                CASE WHEN g.postseason = 1 THEN 'Playoffs' ELSE 'Regular Season' END AS Phase,
                COUNT(*) AS Games,
                ROUND(AVG(g.home_score + g.visitor_score), 1) AS "Avg Total",
                ROUND(AVG(ABS(g.home_score - g.visitor_score)), 1) AS "Avg Margin"
            FROM games g
            WHERE g.status = 'post'
            GROUP BY g.postseason
            ORDER BY g.postseason
        """,
    },
    {
        "title": "Highest scoring games",
        "description": "Top 10 games by combined points so far this season.",
        "sql": """
            SELECT
                SUBSTR(g.date, 1, 10) AS Date,
                home_t.abbreviation AS Home,
                g.home_score AS "Home Score",
                visitor_t.abbreviation AS Away,
                g.visitor_score AS "Away Score",
                (g.home_score + g.visitor_score) AS Total
            FROM games g
            JOIN teams home_t ON home_t.id = g.home_team_id
            JOIN teams visitor_t ON visitor_t.id = g.visitor_team_id
            WHERE g.status = 'post'
            ORDER BY Total DESC
            LIMIT 10
        """,
        "bar_column": "Total",
    },
    {
        "title": "Longest win streaks",
        "description": "Each team's longest consecutive run of wins. Uses window functions and the gaps-and-islands pattern.",
        "sql": """
            WITH ordered_results AS (
                SELECT
                    g.date,
                    t.full_name AS team,
                    CASE
                        WHEN (g.home_team_id = t.id AND g.home_score > g.visitor_score)
                          OR (g.visitor_team_id = t.id AND g.visitor_score > g.home_score)
                        THEN 1 ELSE 0
                    END AS won
                FROM teams t
                JOIN games g ON t.id IN (g.home_team_id, g.visitor_team_id)
                WHERE g.status = 'post'
                  AND t.full_name NOT IN ('TEAM COLLIER', 'TEAM CLARK')
            ),
            numbered AS (
                SELECT team, date, won,
                    ROW_NUMBER() OVER (PARTITION BY team ORDER BY date) AS rn_all,
                    ROW_NUMBER() OVER (PARTITION BY team, won ORDER BY date) AS rn_won
                FROM ordered_results
            ),
            streak_groups AS (
                SELECT team, won, (rn_all - rn_won) AS streak_group FROM numbered
            ),
            streak_lengths AS (
                SELECT team, won, streak_group, COUNT(*) AS streak_length
                FROM streak_groups GROUP BY team, won, streak_group
            )
            SELECT team AS Team, MAX(streak_length) AS Streak
            FROM streak_lengths WHERE won = 1
            GROUP BY team
            ORDER BY MAX(streak_length) DESC, team ASC
        """,
        "bar_column": "Streak",
    },
    {
        "title": "Players tracked per franchise",
        "description": "Number of players in the database per active 2026 franchise. Includes historical players, not just the current roster.",
        "sql": """
            WITH active_teams AS (
                SELECT id FROM teams WHERE id IN (
                    SELECT home_team_id FROM games WHERE status = 'post'
                    UNION
                    SELECT visitor_team_id FROM games WHERE status = 'post'
                )
                AND full_name NOT IN ('TEAM COLLIER', 'TEAM CLARK')
            )
            SELECT
                t.full_name AS Team,
                COUNT(p.id) AS "Players"
            FROM teams t
            JOIN active_teams a ON a.id = t.id
            LEFT JOIN players p ON p.team_id = t.id
            GROUP BY t.full_name
            ORDER BY COUNT(p.id) DESC, t.full_name ASC
        """,
        "bar_column": "Players",
    },
]


CSS = """
:root {
    --bg: #0F0F10;
    --bg-elevated: #18181A;
    --bg-row-hover: #1F1F22;
    --text: #F5F2EC;
    --text-muted: #8A8784;
    --text-faint: #555;
    --border: #2A2A2D;
    --accent: #D9580A;
    --accent-soft: rgba(217, 88, 10, 0.15);
    --gold: #D4A24C;
    --negative: #C44A38;
    --rank-shadow: rgba(217, 88, 10, 0.3);
}

* { box-sizing: border-box; margin: 0; padding: 0; }

@font-face {
    font-family: 'system-ui-fallback';
    src: local('Inter'), local('-apple-system'), local('BlinkMacSystemFont');
}

html { scroll-behavior: smooth; }

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
    font-feature-settings: 'cv11', 'ss01';
    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
}

/* STICKY NAV */
.sticky-nav {
    position: sticky;
    top: 0;
    z-index: 100;
    background: rgba(15, 15, 16, 0.85);
    backdrop-filter: saturate(180%) blur(12px);
    -webkit-backdrop-filter: saturate(180%) blur(12px);
    border-bottom: 1px solid var(--border);
    transition: opacity 0.2s ease, transform 0.2s ease;
}

.sticky-nav-inner {
    max-width: 1100px;
    margin: 0 auto;
    padding: 0.75rem 2rem;
    display: flex;
    align-items: center;
    gap: 1.5rem;
}

.sticky-nav .nav-brand {
    font-family: 'JetBrains Mono', 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-muted);
    text-decoration: none;
    flex-shrink: 0;
    transition: color 0.15s ease;
}

.sticky-nav .nav-brand:hover {
    color: var(--text);
}

.sticky-nav .nav-chips {
    display: flex;
    gap: 0.4rem;
    overflow-x: auto;
    scrollbar-width: none;
    -ms-overflow-style: none;
    flex: 1;
    justify-content: flex-end;
}

.sticky-nav .nav-chips::-webkit-scrollbar {
    display: none;
}

.sticky-nav .nav-chip {
    font-family: 'JetBrains Mono', 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.05em;
    padding: 0.35rem 0.6rem;
    border-radius: 3px;
    color: var(--text-muted);
    text-decoration: none;
    border: 1px solid transparent;
    transition: color 0.15s ease, background 0.15s ease, border-color 0.15s ease;
    flex-shrink: 0;
}

.sticky-nav .nav-chip:hover {
    color: var(--text);
    background: var(--bg-elevated);
}

.sticky-nav .nav-chip.active {
    color: var(--accent);
    border-color: var(--accent);
    background: var(--accent-soft);
}

/* NAV ICONS (GitHub, LinkedIn) */
.sticky-nav .nav-icons {
    display: flex;
    gap: 0.4rem;
    flex-shrink: 0;
    padding-left: 0.5rem;
    border-left: 1px solid var(--border);
    margin-left: 0.4rem;
}

.sticky-nav .nav-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    color: var(--text-muted);
    border-radius: 3px;
    transition: color 0.15s ease, background 0.15s ease;
}

.sticky-nav .nav-icon:hover {
    color: var(--accent);
    background: var(--accent-soft);
}

.sticky-nav .nav-icon svg {
    width: 16px;
    height: 16px;
}

@media (max-width: 720px) {
    .sticky-nav-inner {
        padding: 0.6rem 1rem;
        gap: 1rem;
    }
    .sticky-nav .nav-brand { font-size: 0.65rem; }
    .sticky-nav .nav-chip {
        padding: 0.3rem 0.5rem;
        font-size: 0.65rem;
    }
    .sticky-nav .nav-icons {
        padding-left: 0.35rem;
        margin-left: 0.25rem;
    }
    .sticky-nav .nav-icon {
        width: 24px;
        height: 24px;
    }
    .sticky-nav .nav-icon svg {
        width: 14px;
        height: 14px;
    }
}

.container {
    max-width: 1100px;
    margin: 0 auto;
    padding: 3rem 2rem;
}

@media (max-width: 720px) {
    .container { padding: 2rem 1.25rem; }
}

/* HERO */
.hero {
    margin-bottom: 5rem;
    position: relative;
}

.byline {
    font-family: 'JetBrains Mono', 'IBM Plex Mono', 'Menlo', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 0.6rem;
    font-weight: 500;
}

.byline a {
    color: inherit;
    text-decoration: none;
    border-bottom: 1px solid transparent;
    transition: border-color 0.15s ease, color 0.15s ease;
}

.byline a:hover {
    color: var(--text);
    border-bottom-color: var(--text-muted);
}

/* HERO MARK (basketball icon) */
.hero-mark {
    width: 56px;
    height: 56px;
    margin-bottom: 2rem;
    color: var(--accent);
    display: block;
}

.hero-mark svg {
    width: 100%;
    height: 100%;
    display: block;
}

/* STAT ICONS */
.stat-icon {
    width: 18px;
    height: 18px;
    color: var(--text-muted);
    margin-bottom: 0.5rem;
    display: block;
}

.stat-icon svg {
    width: 100%;
    height: 100%;
    display: block;
}

/* SECTION DIVIDER ICON */
.section-mark {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 22px;
    height: 22px;
    color: var(--accent);
    flex-shrink: 0;
}

.section-mark svg {
    width: 100%;
    height: 100%;
    display: block;
}

.eyebrow {
    font-family: 'JetBrains Mono', 'IBM Plex Mono', 'Menlo', monospace;
    font-size: 0.75rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.eyebrow::before {
    content: '';
    width: 24px;
    height: 1px;
    background: var(--accent);
    display: inline-block;
}

.snapshot-note {
    font-family: 'JetBrains Mono', 'IBM Plex Mono', 'Menlo', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-top: 1.5rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 0.6rem;
}

.snapshot-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--accent);
    display: inline-block;
    flex-shrink: 0;
}

.hero h1 {
    font-size: clamp(2.2rem, 5vw, 3.75rem);
    font-weight: 800;
    letter-spacing: -0.025em;
    line-height: 1.05;
    margin-bottom: 1.5rem;
    max-width: 18ch;
}

.hero h1 .accent {
    color: var(--accent);
    font-style: italic;
    font-weight: 700;
}

.hero p {
    font-size: 1.1rem;
    color: var(--text-muted);
    max-width: 55ch;
    line-height: 1.6;
}

/* SUMMARY STRIP */
.summary-strip {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0;
    margin: 3rem 0 5rem;
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
}

@media (max-width: 720px) {
    .summary-strip { grid-template-columns: repeat(2, 1fr); }
}

.summary-strip > div {
    padding: 1.5rem 1rem;
    border-right: 1px solid var(--border);
}

.summary-strip > div:last-child { border-right: 0; }

@media (max-width: 720px) {
    .summary-strip > div:nth-child(2) { border-right: 0; }
    .summary-strip > div:nth-child(1),
    .summary-strip > div:nth-child(2) { border-bottom: 1px solid var(--border); }
}

.summary-strip .number {
    font-family: 'JetBrains Mono', 'IBM Plex Mono', monospace;
    font-size: 2rem;
    font-weight: 600;
    letter-spacing: -0.02em;
    color: var(--text);
    font-variant-numeric: tabular-nums;
}

.summary-strip .label {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--text-muted);
    margin-top: 0.4rem;
}

/* CURATOR NOTE */
.curator-note {
    margin: 0 0 5rem;
    padding: 2.5rem 0;
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
    position: relative;
}

.curator-note::before {
    content: '';
    position: absolute;
    top: -1px;
    left: 0;
    width: 60px;
    height: 2px;
    background: var(--accent);
}

.curator-note-label {
    font-family: 'JetBrains Mono', 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 0.6rem;
}

.curator-note-body {
    max-width: 60ch;
}

.curator-note-body p {
    color: var(--text);
    font-size: 1.02rem;
    line-height: 1.7;
    margin-bottom: 1.1rem;
}

.curator-note-body p:last-of-type {
    margin-bottom: 0;
}

.curator-note-signoff {
    margin-top: 1.75rem;
    padding-top: 1.25rem;
    border-top: 1px dashed var(--border);
    font-family: 'JetBrains Mono', 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-muted);
}

.curator-note-signoff strong {
    color: var(--accent);
    font-weight: 600;
}

/* QUERY SECTIONS */
section.query {
    margin-bottom: 5rem;
    position: relative;
    scroll-margin-top: 4rem;
}

.query-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
    flex-wrap: wrap;
}

.query-num {
    font-family: 'JetBrains Mono', 'IBM Plex Mono', monospace;
    font-size: 0.85rem;
    color: var(--accent);
    font-weight: 500;
    letter-spacing: 0.05em;
}

.query-title {
    font-size: 1.6rem;
    font-weight: 700;
    letter-spacing: -0.015em;
    line-height: 1.2;
}

.query-description {
    color: var(--text-muted);
    margin-bottom: 1.75rem;
    max-width: 60ch;
    font-size: 0.97rem;
    padding-left: 2.5rem;
}

@media (max-width: 720px) {
    .query-description { padding-left: 0; }
}

/* TABLE */
.table-wrap {
    overflow-x: auto;
    border: 1px solid var(--border);
    border-radius: 4px;
    background: var(--bg-elevated);
}

table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.92rem;
}

th, td {
    text-align: left;
    padding: 0.9rem 1.25rem;
    border-bottom: 1px solid var(--border);
    vertical-align: middle;
}

tr:last-child td { border-bottom: 0; }

th {
    background: transparent;
    color: var(--text-muted);
    font-weight: 500;
    text-transform: uppercase;
    font-size: 0.7rem;
    letter-spacing: 0.12em;
    padding-top: 1.1rem;
    padding-bottom: 1.1rem;
    border-bottom: 1px solid var(--border);
}

td {
    font-family: 'Inter', sans-serif;
}

td.numeric, th.numeric {
    text-align: right;
    font-family: 'JetBrains Mono', 'IBM Plex Mono', monospace;
    font-variant-numeric: tabular-nums;
    font-size: 0.88rem;
}

tbody tr {
    transition: background 0.12s ease;
}

tbody tr:hover {
    background: var(--bg-row-hover);
}

/* RANK BADGES */
.rank {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    font-weight: 600;
    margin-right: 0.85rem;
    flex-shrink: 0;
    background: transparent;
    color: var(--text-faint);
    border: 1px solid var(--border);
}

.rank.gold {
    background: var(--accent);
    color: #18181A;
    border-color: var(--accent);
    box-shadow: 0 0 12px var(--rank-shadow);
}

.rank.silver {
    background: rgba(217, 88, 10, 0.4);
    color: var(--text);
    border-color: rgba(217, 88, 10, 0.4);
}

.rank.bronze {
    background: rgba(217, 88, 10, 0.18);
    color: var(--accent);
    border-color: rgba(217, 88, 10, 0.35);
}

/* SPARK BARS */
.bar-cell {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    justify-content: flex-end;
}

.bar-cell .bar {
    flex: 1;
    max-width: 140px;
    min-width: 50px;
    height: 6px;
    background: var(--border);
    border-radius: 1px;
    overflow: hidden;
    position: relative;
}

.bar-cell .bar-fill {
    height: 100%;
    background: var(--accent);
    border-radius: 1px;
    transition: width 0.4s ease;
}

.bar-cell .bar-value {
    font-family: 'JetBrains Mono', 'IBM Plex Mono', monospace;
    font-variant-numeric: tabular-nums;
    font-size: 0.88rem;
    min-width: 2.5rem;
    text-align: right;
}

/* DIFF (positive/negative) */
.diff {
    font-family: 'JetBrains Mono', 'IBM Plex Mono', monospace;
    font-variant-numeric: tabular-nums;
    font-size: 0.88rem;
    font-weight: 500;
}

.diff.positive { color: var(--accent); }
.diff.negative { color: var(--negative); }
.diff.neutral { color: var(--text-muted); }

/* FOOTER */
footer {
    margin-top: 6rem;
    padding-top: 2rem;
    border-top: 1px solid var(--border);
    color: var(--text-muted);
    font-size: 0.85rem;
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 1rem;
}

footer a {
    color: var(--accent);
    text-decoration: none;
    border-bottom: 1px solid transparent;
    transition: border-color 0.15s ease;
}

footer a:hover {
    border-bottom-color: var(--accent);
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
    }
}
"""


def run_query(sql):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(sql)
    columns = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    return columns, rows


def get_summary_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM games WHERE status = 'post'")
    games = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM players")
    players = cursor.fetchone()[0]
    cursor.execute("""
        SELECT COUNT(DISTINCT id) FROM teams
        WHERE id IN (
            SELECT home_team_id FROM games WHERE status = 'post'
            UNION
            SELECT visitor_team_id FROM games WHERE status = 'post'
        )
        AND full_name NOT IN ('TEAM COLLIER', 'TEAM CLARK')
    """)
    teams = cursor.fetchone()[0]
    cursor.execute("SELECT ROUND(AVG(home_score + visitor_score), 1) FROM games WHERE status = 'post'")
    avg_points = cursor.fetchone()[0]
    conn.close()
    return {"games": games, "players": players, "teams": teams, "avg_points": avg_points}


def is_numeric(value):
    if value is None:
        return False
    return isinstance(value, (int, float))


def detect_numeric_columns(rows, columns):
    numeric = set(range(len(columns)))
    for row in rows:
        for i, value in enumerate(row):
            if value is not None and not is_numeric(value):
                numeric.discard(i)
    return numeric


def render_rank_badge(rank):
    if rank == 1:
        return '<span class="rank gold">1</span>'
    elif rank == 2:
        return '<span class="rank silver">2</span>'
    elif rank == 3:
        return '<span class="rank bronze">3</span>'
    else:
        return f'<span class="rank">{rank}</span>'


def render_bar_cell(value, max_value):
    if value is None or max_value == 0:
        return f'<span>{value if value is not None else "—"}</span>'
    pct = (value / max_value) * 100
    return f'''
        <div class="bar-cell">
            <div class="bar"><div class="bar-fill" style="width: {pct}%"></div></div>
            <div class="bar-value">{value}</div>
        </div>
    '''


def render_diff_cell(value):
    if value is None:
        return '<span class="diff neutral">—</span>'
    if value > 0:
        return f'<span class="diff positive">+{value}</span>'
    elif value < 0:
        return f'<span class="diff negative">{value}</span>'
    else:
        return f'<span class="diff neutral">{value}</span>'


def render_table(columns, rows, bar_column=None, diff_column=None):
    numeric_cols = detect_numeric_columns(rows, columns)

    bar_col_idx = None
    if bar_column and bar_column in columns:
        bar_col_idx = columns.index(bar_column)

    diff_col_idx = None
    if diff_column and diff_column in columns:
        diff_col_idx = columns.index(diff_column)

    # Compute max for bar normalization
    max_bar = 0
    if bar_col_idx is not None:
        max_bar = max((r[bar_col_idx] for r in rows if r[bar_col_idx] is not None), default=0)

    # Detect if this table should show ranks (first column is team-like and we have a bar)
    show_rank = bar_col_idx is not None and bar_col_idx == len(columns) - 1

    # Header
    header_cells = []
    if show_rank:
        header_cells.append('<th></th>')
    for i, col in enumerate(columns):
        cls = ' class="numeric"' if i in numeric_cols else ''
        header_cells.append(f'<th{cls}>{col}</th>')
    header_html = '<tr>' + ''.join(header_cells) + '</tr>'

    # Body
    body_rows = []
    for rank, row in enumerate(rows, start=1):
        cells = []
        if show_rank:
            cells.append(f'<td>{render_rank_badge(rank)}</td>')
        for i, value in enumerate(row):
            cls = ' class="numeric"' if i in numeric_cols else ''
            if i == bar_col_idx:
                cells.append(f'<td{cls}>{render_bar_cell(value, max_bar)}</td>')
            elif i == diff_col_idx:
                cells.append(f'<td{cls}>{render_diff_cell(value)}</td>')
            else:
                display = '—' if value is None else str(value)
                cells.append(f'<td{cls}>{display}</td>')
        body_rows.append('<tr>' + ''.join(cells) + '</tr>')
    body_html = ''.join(body_rows)

    return f'<div class="table-wrap"><table><thead>{header_html}</thead><tbody>{body_html}</tbody></table></div>'


def render_dashboard():
    stats = get_summary_stats()
    now = datetime.now().strftime("%B %d, %Y")

    sections_html = []
    for i, q in enumerate(QUERIES, start=1):
        columns, rows = run_query(q["sql"])
        table_html = render_table(
            columns,
            rows,
            bar_column=q.get("bar_column"),
            diff_column=q.get("diff_column"),
        )
        icon_svg = ICONS.get(q.get("icon", ""), "")
        icon_html = f'<span class="section-mark">{icon_svg}</span>' if icon_svg else ''
        sections_html.append(f'''
            <section class="query" id="q{i:02d}">
                <div class="query-header">
                    {icon_html}
                    <span class="query-num">Q{i:02d}</span>
                    <h2 class="query-title">{q['title']}</h2>
                </div>
                <p class="query-description">{q['description']}</p>
                {table_html}
            </section>
        ''')

    sections_combined = "\n".join(sections_html)

    # Build the sticky nav chips
    nav_chips = "\n".join([
        f'<a href="#q{i:02d}" class="nav-chip" data-target="q{i:02d}">Q{i:02d}</a>'
        for i in range(1, len(QUERIES) + 1)
    ])

    # Small JS to highlight active chip based on scroll position
    nav_js = '''
    <script>
    (function() {
        const chips = document.querySelectorAll('.nav-chip');
        const sections = Array.from(document.querySelectorAll('section.query'));
        if (!chips.length || !sections.length) return;

        const setActive = (id) => {
            chips.forEach(c => c.classList.toggle('active', c.dataset.target === id));
        };

        const observer = new IntersectionObserver((entries) => {
            // Find the entry closest to the top that is intersecting
            const visible = entries
                .filter(e => e.isIntersecting)
                .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
            if (visible.length > 0) {
                setActive(visible[0].target.id);
            }
        }, { rootMargin: '-20% 0px -60% 0px', threshold: 0 });

        sections.forEach(s => observer.observe(s));
    })();
    </script>
    '''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WNBA 2026 Season in Nine Questions</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>{CSS}</style>
</head>
<body>
    <nav class="sticky-nav">
        <div class="sticky-nav-inner">
            <a href="#top" class="nav-brand">Jasmine Walker · WNBA 2026</a>
            <div class="nav-chips">
                {nav_chips}
            </div>
            <div class="nav-icons">
                <a href="https://github.com/jasmine-walker/wnba-stats-tracker" target="_blank" rel="noopener" class="nav-icon" title="GitHub">{ICONS["github"]}</a>
                <a href="https://www.linkedin.com/in/jasminejwalker/" target="_blank" rel="noopener" class="nav-icon" title="LinkedIn">{ICONS["linkedin"]}</a>
            </div>
        </div>
    </nav>
    <div class="container" id="top">
        <header class="hero">
            <div class="byline">By <a href="https://jasminejwalker.com">Jasmine Walker</a></div>
            <div class="hero-mark">{ICONS["basketball"]}</div>
            <div class="eyebrow">2026 Season · 9 Questions · Live</div>
            <h1>The 2026 WNBA season, <span class="accent">in data.</span></h1>
            <p>A SQL-driven look at every game of the 2026 season, refreshed daily while it's in progress. Built with Python, SQLite, and the balldontlie API. Each section answers one question with one query.</p>
            <div class="snapshot-note">
                <span class="snapshot-dot"></span>
                Season in progress · Updates daily · As of {now}
            </div>
        </header>

        <div class="summary-strip">
            <div>
                <div class="stat-icon">{ICONS["calendar"]}</div>
                <div class="number">{stats['games']}</div>
                <div class="label">Games</div>
            </div>
            <div>
                <div class="stat-icon">{ICONS["building"]}</div>
                <div class="number">{stats['teams']}</div>
                <div class="label">Active Teams</div>
            </div>
            <div>
                <div class="stat-icon">{ICONS["users"]}</div>
                <div class="number">{stats['players']}</div>
                <div class="label">Players Tracked</div>
            </div>
            <div>
                <div class="stat-icon">{ICONS["chart"]}</div>
                <div class="number">{stats['avg_points']}</div>
                <div class="label">Avg Total Points</div>
            </div>
        </div>

        <section class="curator-note" id="curator-note">
            <div class="curator-note-label">A Note From the Curator</div>
            <div class="curator-note-body">
                <p>Two things are true at the same time: I love women's basketball, and I am a technologist looking for my next role. This project lives at the intersection of both.</p>
                <p>The WNBA does not get enough good data work done about it. The same fifteen storylines get recycled every season. I wanted to ask my own questions and let the data answer them.</p>
                <p>So I built one. Nine SQL queries, one dashboard, the entire 2026 season behind it. I taught myself SQL on a dataset I already had opinions about, because window functions and CTEs are easier to learn when you are using them to settle real arguments about real teams. No editorial filter. No narrative I was trying to push. Just the questions I cared about and the answers SQL gave back.</p>
                <p>Some answers confirmed what I already thought. A couple genuinely surprised me. That is what good data work is supposed to do.</p>
            </div>
            <div class="curator-note-signoff">— <strong>Jasmine Walker</strong></div>
        </section>

        {sections_combined}

        <footer>
            <div>Jasmine Walker · <a href="https://jasminejwalker.com">jasminejwalker.com</a></div>
            <div>Data: <a href="https://balldontlie.io">balldontlie API</a></div>
        </footer>
    </div>
    {nav_js}
</body>
</html>
'''

    os.makedirs("output", exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Dashboard written to {OUTPUT_PATH}")


if __name__ == "__main__":
    render_dashboard()
