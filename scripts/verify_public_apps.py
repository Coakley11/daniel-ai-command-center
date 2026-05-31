"""Verify public Streamlit app URLs via rendered content."""
from __future__ import annotations

import requests

BLOCKED = (
    "do not have access",
    "you do not have access",
    "sign in to continue",
    "please sign in",
)

CANDIDATES = [
    "investment-portfolio-analyzer",
    "coakley11-investment-portfolio-analyzer",
    "ai-music-practice-coach",
    "coakley11-ai-music-practice-coach",
    "music-practice-coach-dev",
    "baseball-stat-app",
    "coakley11-baseball-stat-app",
    "nba-playoff-companion-ai",
    "coakley11-nba-playoff-companion-ai",
    "applied-mathematical-intelligence",
    "ai-homeroom",
    "future-lens-ai-transition-simulator",
    "future-lens",
    "daniel-ai-command-center",
]

for name in CANDIDATES:
    url = f"https://{name}.streamlit.app"
    try:
        r = requests.get(url, timeout=10, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
        body = r.text.lower()
        if r.status_code == 200 and not any(b in body for b in BLOCKED):
            # Heuristic: real apps have more content than empty shell
            if len(r.text) > 8000 or "streamlit" in body:
                print("OK", url, "len", len(r.text))
    except Exception as exc:
        print("ERR", url, exc)
