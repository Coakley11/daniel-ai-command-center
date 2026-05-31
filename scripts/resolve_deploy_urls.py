"""Resolve public Streamlit viewer URLs from GitHub deploy paths."""
from __future__ import annotations

import requests

DEPLOY_PATHS = {
    "music": "coakley11/ai-music-practice-coach/dev/streamlit_music_practice_app.py",
    "investment": "coakley11/investment-portfolio-analyzer/dev/streamlit_app.py",
    "baseball": "coakley11/baseball-stat-app/main/streamlit_app.py",
    "nba": "coakley11/nba-playoff-companion-ai/dev/streamlit_app.py",
    "math": "coakley11/applied-mathematical-intelligence/dev/streamlit_app.py",
    "future_lens": "coakley11/future-lens-ai-transition-simulator/dev/streamlit_app.py",
}

for name, path in DEPLOY_PATHS.items():
    response = requests.get(
        "https://share.streamlit.io/api/v2/apps/disambiguate",
        params={"path": path},
        timeout=15,
    )
    if response.status_code != 200:
        print(name, "NOT FOUND", response.status_code)
        continue
    payload = response.json()
    print(name, "https://" + payload["host"], payload.get("branch"))
