"""Classify streamlit.app URLs as public, private, or missing."""
from __future__ import annotations

import requests

NAMES = [
    "baseball-stat-app",
    "ai-music-practice-coach",
    "nba-playoff-companion-ai",
    "applied-mathematical-intelligence",
    "future-lens-ai-transition-simulator",
    "investment-portfolio-analyzer",
    "music-practice-coach",
    "basketball-playoff-companion",
    "ai-homeroom",
    "advanced-math-intelligence",
    "ai-future-lens",
    "future-lens",
    "daniel-cohen-baseball",
    "fantasy-baseball",
    "baseball-stat-app-main",
    "ai-music-practice-coach-dev",
    "nba-playoff-companion-ai-dev",
    "applied-mathematical-intelligence-dev",
    "future-lens-ai-transition-simulator-dev",
    "future-lens-ai-transition-simulator-main",
]

for name in NAMES:
    url = f"https://{name}.streamlit.app"
    try:
        response = requests.get(url, timeout=8, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
        body = response.text[:15000].lower()
        if response.status_code == 404:
            print(name, "404")
        elif "do not have access" in body or "you do not have access" in body:
            print(name, "PRIVATE (exists)", response.url)
        elif "app does not exist" in body or "page not found" in body:
            print(name, "NOT FOUND")
        elif response.status_code == 200:
            print(name, "PUBLIC OK", response.url, "len", len(response.text))
        else:
            print(name, "status", response.status_code)
    except Exception as exc:
        print(name, "ERR", exc)
