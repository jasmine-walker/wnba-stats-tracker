"""
fetch_data.py

Pulls WNBA data (teams, players, games) from the balldontlie API
and stores it in a SQLite database.
"""

import os
import time
import sqlite3
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("BALLDONTLIE_API_KEY")

BASE_URL = "https://api.balldontlie.io/wnba/v1"
HEADERS = {"Authorization": API_KEY}
DB_PATH = "data/wnba.db"
SEASON = 2025

DELAY_BETWEEN_PAGES = 15
DELAY_BETWEEN_ENDPOINTS = 20
RETRY_DELAY = 60
MAX_RETRIES = 3


def create_database():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS teams (id INTEGER PRIMARY KEY, name TEXT, full_name TEXT, abbreviation TEXT, city TEXT, conference TEXT, division TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS players (id INTEGER PRIMARY KEY, first_name TEXT, last_name TEXT, position TEXT, jersey_number TEXT, college TEXT, country TEXT, team_id INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS games (id INTEGER PRIMARY KEY, date TEXT, season INTEGER, status TEXT, postseason INTEGER, home_team_id INTEGER, home_score INTEGER, visitor_team_id INTEGER, visitor_score INTEGER)")
    conn.commit()
    conn.close()
    print(f"Database ready at {DB_PATH}")


def fetch_with_retry(url, params):
    for attempt in range(MAX_RETRIES):
        r = requests.get(url, headers=HEADERS, params=params)
        if r.status_code == 200:
            return r
        if r.status_code == 429:
            w = RETRY_DELAY * (attempt + 1)
            print(f"  Rate limit hit. Waiting {w}s before retry {attempt + 1}/{MAX_RETRIES}...")
            time.sleep(w)
            continue
        print(f"  Error {r.status_code}: {r.text}")
        return None
    return None


def fetch_paginated(endpoint, params=None):
    if params is None:
        params = {}
    all_records = []
    cursor = None
    page = 0
    while True:
        if cursor:
            params["cursor"] = cursor
        params["per_page"] = 100
        r = fetch_with_retry(f"{BASE_URL}/{endpoint}", params)
        if r is None:
            break
        d = r.json()
        all_records.extend(d.get("data", []))
        page += 1
        cursor = d.get("meta", {}).get("next_cursor")
        if not cursor:
            break
        print(f"  Fetched page {page} ({len(all_records)} records so far). Waiting {DELAY_BETWEEN_PAGES}s...")
        time.sleep(DELAY_BETWEEN_PAGES)
    print(f"  Fetched {page} page(s), {len(all_records)} total records")
    return all_records


def store_teams(teams):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for t in teams:
        c.execute("INSERT OR REPLACE INTO teams VALUES (?, ?, ?, ?, ?, ?, ?)", (t.get("id"), t.get("name"), t.get("full_name"), t.get("abbreviation"), t.get("city"), t.get("conference"), t.get("division")))
    conn.commit()
    conn.close()
    print(f"Stored {len(teams)} teams in the database.")


def store_players(players):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for p in players:
        team = p.get("team") or {}
        c.execute("INSERT OR REPLACE INTO players VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (p.get("id"), p.get("first_name"), p.get("last_name"), p.get("position"), p.get("jersey_number"), p.get("college"), p.get("country"), team.get("id")))
    conn.commit()
    conn.close()
    print(f"Stored {len(players)} players in the database.")


def store_games(games):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for g in games:
        h = g.get("home_team") or {}
        v = g.get("visitor_team") or {}
        c.execute("INSERT OR REPLACE INTO games VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (g.get("id"), g.get("date"), g.get("season"), g.get("status"), 1 if g.get("postseason") else 0, h.get("id"), g.get("home_score"), v.get("id"), g.get("away_score")))
    conn.commit()
    conn.close()
    print(f"Stored {len(games)} games in the database.")


def main():
    if not API_KEY:
        print("ERROR: No API key found.")
        return
    create_database()
    print("\nFetching WNBA teams...")
    teams = fetch_paginated("teams")
    if teams:
        store_teams(teams)
    print(f"\nWaiting {DELAY_BETWEEN_ENDPOINTS}s...")
    time.sleep(DELAY_BETWEEN_ENDPOINTS)
    print("\nFetching WNBA players...")
    players = fetch_paginated("players")
    if players:
        store_players(players)
    print(f"\nWaiting {DELAY_BETWEEN_ENDPOINTS}s...")
    time.sleep(DELAY_BETWEEN_ENDPOINTS)
    print(f"\nFetching {SEASON} WNBA games...")
    games = fetch_paginated("games", params={"seasons[]": SEASON})
    if games:
        store_games(games)
    print("\nDone.")


if __name__ == "__main__":
    main()
