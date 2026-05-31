"""Probe likely custom Streamlit subdomains."""
from __future__ import annotations

import requests

CANDIDATES = [
    # baseball
    "fantasy-baseball",
    "baseball-stats",
    "baseball-stat",
    "daniel-baseball",
    "coakley-baseball",
    # music
    "music-practice-coach",
    "music-practice",
    "ai-music-coach",
    "music-coach",
    "practice-coach",
    # nba / basketball
    "nba-playoffs",
    "nba-playoff",
    "basketball-playoff",
    "basketball-companion",
    "nba-companion",
    "knicks-companion",
    # math / homeroom
    "ai-homeroom",
    "math-intelligence",
    "applied-math",
    "applied-mathematics",
    "mathematical-intelligence",
    # future lens
    "future-lens",
    "ai-future-lens",
    "future-simulator",
    "ai-transition",
    "transition-simulator",
    # investment variants
    "investment-analyzer",
    "portfolio-analyzer",
    # command center
    "daniel-ai-command-center",
    "ai-command-center",
    "daniel-ai-suite",
]

for name in CANDIDATES:
    url = f"https://{name}.streamlit.app"
    try:
        response = requests.get(url, timeout=8, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 404:
            continue
        body = response.text[:20000].lower()
        if "do not have access" in body or "you do not have access" in body:
            print("PRIVATE", name, response.url)
        elif response.status_code == 200:
            print("LIVE", name, response.url, "len", len(response.text))
    except Exception:
        pass
