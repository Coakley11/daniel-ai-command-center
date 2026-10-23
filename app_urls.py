"""Deployment constants and URL resolution for Daniel AI Command Center."""

from __future__ import annotations

import os

BUILD_VERSION = "2026-06-03-v31"


def _deployment_url(app_key: str, default: str) -> str:
    """A staging deployment points the suite at its own app: SUITE_APP_URL_<APP> (environment, or a root-level
    Streamlit secret) replaces the default. Unset in production, so these stay the verified URLs below."""
    return os.environ.get(f"SUITE_APP_URL_{app_key.upper()}", "").strip().rstrip("/") or default

# GitHub deploy paths (lowercase owner) for Streamlit disambiguate API.
DEPLOY_PATHS: dict[str, str] = {
    "homepage_main": "coakley11/daniel-ai-command-center/main/ai_command_center.py",
    "homepage_dev": "coakley11/daniel-ai-command-center/dev/ai_command_center.py",
    "music": "coakley11/ai-music-practice-coach/dev/streamlit_music_practice_app.py",
    "investment": "coakley11/investment-portfolio-analyzer/dev/streamlit_app.py",
    "baseball": "coakley11/baseball-stat-app/dev/streamlit_app.py",
    "nba": "coakley11/nba-playoff-companion-ai/dev/streamlit_app.py",
    "applied_intelligence": "coakley11/applied-mathematical-intelligence/dev/streamlit_app.py",
    "future_lens": "coakley11/future-lens-ai-transition-simulator/dev/streamlit_app.py",
}

# Public viewer URLs — verified via share.streamlit.io disambiguate API.
MUSIC_APP_URL = _deployment_url("music", "https://ai-music-practice-coach-6szqxqxqrqxdmryyewk8sq.streamlit.app")
INVESTMENT_APP_URL = _deployment_url(
    "investment", "https://investment-portfolio-analyzer-ty2sbzumvxsqwbqhkvf6rz.streamlit.app"
)
BASEBALL_PRODUCTION_URL = "https://baseball-stat-app-bwx4bawvayxbsbxqbqmfws.streamlit.app"
BASEBALL_DEV_URL = "https://baseball-stat-app-d4jlymjc4iptaadc3kquwx.streamlit.app"
BASEBALL_APP_URL = _deployment_url("baseball", BASEBALL_DEV_URL or BASEBALL_PRODUCTION_URL)
NBA_APP_URL = _deployment_url("nba", "https://nba-playoff-companion-ai-gd4sx677quejdfkvappv6o.streamlit.app")
APPLIED_INTELLIGENCE_URL = _deployment_url(
    "applied_intelligence", "https://applied-mathematical-intelligence-8l8bqrzpp6fghaj7xuig53.streamlit.app"
)
FUTURE_LENS_URL = _deployment_url(
    "future_lens", "https://future-lens-ai-transition-simulator-m6n4kaku28ztzlxfts2xt6.streamlit.app"
)
FUTURE_LENS_PRODUCTION_URL = "https://future-lens-ai-transition-simulator-8qfgube5tezjjaxruppnuo.streamlit.app"

HOMEPAGE_PRODUCTION_URL = "https://daniel-ai-command-center-dexxnd7bf8jalxzqbyq55i.streamlit.app"
# Created manually on Streamlit Cloud — see docs/DEPLOYMENTS.md
HOMEPAGE_DEV_URL = "https://daniel-ai-command-center-ion4vh2cvo7bgdnkuktrb3.streamlit.app"

MUSIC_GITHUB_URL = "https://github.com/Coakley11/ai-music-practice-coach/tree/dev"
INVESTMENT_GITHUB_URL = "https://github.com/Coakley11/investment-portfolio-analyzer/tree/dev"
BASEBALL_GITHUB_URL = "https://github.com/Coakley11/baseball-stat-app/tree/dev"
NBA_GITHUB_URL = "https://github.com/Coakley11/nba-playoff-companion-ai/tree/dev"
APPLIED_INTELLIGENCE_GITHUB_URL = "https://github.com/Coakley11/Applied-mathematical-intelligence/tree/dev"
FUTURE_LENS_GITHUB_URL = "https://github.com/Coakley11/future-lens-ai-transition-simulator/tree/dev"

APP_BRANCH: dict[str, str] = {
    "music": "DEV",
    "investment": "DEV",
    "baseball": "DEV",
    "nba": "DEV",
    "applied_intelligence": "DEV",
    "future_lens": "DEV",
}

APP_URLS: dict[str, str] = {
    "music": MUSIC_APP_URL,
    "investment": INVESTMENT_APP_URL,
    "baseball": BASEBALL_APP_URL,
    "nba": NBA_APP_URL,
    "applied_intelligence": APPLIED_INTELLIGENCE_URL,
    "future_lens": FUTURE_LENS_URL,
}


def command_center_home_url() -> str:
    """Suite homepage URL for sibling-app sidebar return links."""
    base = (HOMEPAGE_DEV_URL or HOMEPAGE_PRODUCTION_URL or "").strip()
    return base.rstrip("/")
