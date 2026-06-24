# WNBA Stats Tracker

A SQL-driven look at the 2025 WNBA season, built with Python, SQLite, and the balldontlie API.

**Live dashboard:** [wnba.jasminejwalker.com](https://wnba.jasminejwalker.com)

---

## About this project

This project pulls live WNBA data from the balldontlie API, stores it in a local SQLite database, runs nine documented SQL queries against it, and generates a polished static HTML dashboard. The dashboard refreshes automatically every day via GitHub Actions.

The project answers nine specific questions about the 2025 WNBA season, including team win totals, home vs road performance, point differentials, biggest blowouts, closest games, and longest win streaks. Each query is documented, each table is interactive, and the design is intentional.

## How it works

The data flow is straightforward: API → SQLite → SQL queries → HTML dashboard → Vercel.

1. `fetch_data.py` pulls teams, players, and games from the balldontlie API with rate limiting and automatic retry on 429 errors.
2. The data lands in a local SQLite database at `data/wnba.db`, with normalized tables for teams, players, and games.
3. `queries.py` contains nine SQL queries that answer specific questions about the season, including one that uses window functions and the gaps-and-islands pattern to compute win streaks.
4. `dashboard.py` runs the queries and generates a single static HTML file at `output/index.html`, with inline SVG icons, sparkbar visualizations, ranking badges, and a sticky navigation bar.
5. GitHub Actions runs the pipeline daily and commits the refreshed data and dashboard back to the repo.
6. Vercel auto-deploys on every commit.

## Tech stack

- **Python 3** for the data pipeline and HTML generation
- **SQLite** for local storage and querying
- **balldontlie API** as the data source
- **HTML and CSS** for the static dashboard (Inter and JetBrains Mono fonts, inline SVG icons)
- **GitHub Actions** for daily automated refresh
- **Vercel** for hosting

## The nine queries

1. Win totals by team
2. Home vs road performance
3. Offensive and defensive averages with point differential
4. Biggest blowouts of the season
5. Closest games of the season
6. Regular season vs playoffs comparison
7. Highest-scoring games of the season
8. Longest winning streak per team (uses window functions)
9. Players tracked per active franchise

## Project structure

```
wnba-stats-tracker/
├── data/
│   └── wnba.db              SQLite database, refreshed daily
├── output/
│   └── index.html           The generated dashboard, served by Vercel
├── src/
│   ├── fetch_data.py        Pulls from the balldontlie API and stores in SQLite
│   ├── queries.py           The nine documented SQL queries
│   └── dashboard.py         Generates the static HTML dashboard
├── .github/
│   └── workflows/
│       └── refresh.yml      GitHub Actions workflow for daily refresh
├── .env                     API key, gitignored
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

## Run it yourself

1. Clone the repo
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
4. Install dependencies: `pip install -r requirements.txt`
5. Sign up at [balldontlie.io](https://app.balldontlie.io) and grab a free API key
6. Create a `.env` file at the project root with: `BALLDONTLIE_API_KEY=your_key_here`
7. Run the data pull: `python src/fetch_data.py` (takes about 10 minutes due to rate limiting)
8. Generate the dashboard: `python src/dashboard.py`
9. Open `output/index.html` in your browser

## Notes on data

- The 2025 WNBA season ran from May through October 2025
- All 312 regular season and playoff games are included
- balldontlie's free tier is limited to 5 requests per minute, which is why the data pull is slow
- The free tier does not return player country or biographical details, only names and team affiliations

## Author

Built by Jasmine Walker as part of a personal portfolio.

- Portfolio: [jasminejwalker.com](https://jasminejwalker.com)
- GitHub: [jasmine-walker](https://github.com/jasmine-walker)
