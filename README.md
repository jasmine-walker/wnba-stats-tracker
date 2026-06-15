# WNBA Stats Tracker

A Python and SQL project that pulls live WNBA data from the balldontlie API, stores it in a SQLite database, and generates an HTML dashboard summarizing team and player performance.

## What it does

- Pulls WNBA teams, players, and game results from the balldontlie API
- Stores the data in a local SQLite database
- Runs SQL queries to surface insights (top performers, win streaks, home vs road records)
- Generates a static HTML dashboard for easy viewing

## Tech stack

- Python 3
- SQLite
- balldontlie API
- HTML/CSS for dashboard rendering

## Project structure


## Setup

1. Clone the repo
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
4. Install dependencies: `pip install -r requirements.txt`
5. Sign up at https://app.balldontlie.io and grab a free API key
6. Create a `.env` file with: `BALLDONTLIE_API_KEY=your_key_here`
7. Run the data pull: `python src/fetch_data.py`
8. Generate the dashboard: `python src/dashboard.py`

## Author

Jasmine Walker | [jasminejwalker.com](https://jasminejwalker.com)