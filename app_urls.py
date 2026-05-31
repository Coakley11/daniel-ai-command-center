"""Deployment constants and URL resolution for Daniel AI Command Center."""

from __future__ import annotations

BUILD_VERSION = "2026-05-31-v5"

# GitHub deploy paths (lowercase owner) for Streamlit disambiguate API.
DEPLOY_PATHS: dict[str, str] = {
    "homepage_main": "coakley11/daniel-ai-command-center/main/ai_command_center.py",
    "homepage_dev": "coakley11/daniel-ai-command-center/dev/ai_command_center.py",
    "music": "coakley11/ai-music-practice-coach/dev/streamlit_music_practice_app.py",
    "investment": "coakley11/investment-portfolio-analyzer/dev/streamlit_app.py",
    "baseball": "coakley11/baseball-stat-app/main/streamlit_app.py",
    "nba": "coakley11/nba-playoff-companion-ai/dev/streamlit_app.py",
    "math": "coakley11/applied-mathematical-intelligence/dev/streamlit_app.py",
    "future_lens": "coakley11/future-lens-ai-transition-simulator/main/streamlit_app.py",
}

# Public viewer URLs — verified via share.streamlit.io disambiguate API.
MUSIC_APP_URL = "https://ai-music-practice-coach-6szqxqxqrqxdmryyewk8sq.streamlit.app"
INVESTMENT_APP_URL = "https://investment-portfolio-analyzer-ty2sbzumvxsqwbqhkvf6rz.streamlit.app"
BASEBALL_APP_URL = "https://baseball-stat-app-bwx4bawvayxbsbxqbqmfws.streamlit.app"
NBA_APP_URL = "https://nba-playoff-companion-ai-gd4sx677quejdfkvappv6o.streamlit.app"
MATH_APP_URL = "https://applied-mathematical-intelligence-8l8bqrzpp6fghaj7xuig53.streamlit.app"
FUTURE_LENS_URL = "https://future-lens-ai-transition-simulator-8qfgube5tezjjaxruppnuo.streamlit.app"

HOMEPAGE_PRODUCTION_URL = "https://daniel-ai-command-center-dexxnd7bf8jalxzqbyq55i.streamlit.app"
# Created manually on Streamlit Cloud — see docs/DEPLOYMENTS.md
HOMEPAGE_DEV_URL = ""

MUSIC_GITHUB_URL = "https://github.com/Coakley11/ai-music-practice-coach/tree/dev"
INVESTMENT_GITHUB_URL = "https://github.com/Coakley11/investment-portfolio-analyzer/tree/dev"
BASEBALL_GITHUB_URL = "https://github.com/Coakley11/baseball-stat-app/tree/main"
NBA_GITHUB_URL = "https://github.com/Coakley11/nba-playoff-companion-ai/tree/dev"
MATH_GITHUB_URL = "https://github.com/Coakley11/Applied-mathematical-intelligence/tree/dev"
FUTURE_LENS_GITHUB_URL = "https://github.com/Coakley11/future-lens-ai-transition-simulator/tree/main"

APP_BRANCH: dict[str, str] = {
    "music": "DEV",
    "investment": "DEV",
    "baseball": "MAIN",
    "nba": "DEV",
    "math": "DEV",
    "future_lens": "MAIN",
}

APP_URLS: dict[str, str] = {
    "music": MUSIC_APP_URL,
    "investment": INVESTMENT_APP_URL,
    "baseball": BASEBALL_APP_URL,
    "nba": NBA_APP_URL,
    "math": MATH_APP_URL,
    "future_lens": FUTURE_LENS_URL,
}
