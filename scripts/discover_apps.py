"""One-off discovery script for Streamlit deployment URLs."""
from __future__ import annotations

import re

import requests

URLS = [
    "https://investment-portfolio-analyzer.streamlit.app",
    "https://share.streamlit.io/Coakley11/baseball-stat-app/main/streamlit_app.py",
    "https://share.streamlit.io/Coakley11/ai-music-practice-coach/dev/streamlit_music_practice_app.py",
    "https://share.streamlit.io/Coakley11/investment-portfolio-analyzer/main/streamlit_app.py",
    "https://share.streamlit.io/Coakley11/investment-portfolio-analyzer/dev/streamlit_app.py",
    "https://share.streamlit.io/Coakley11/nba-playoff-companion-ai/dev/streamlit_app.py",
    "https://share.streamlit.io/Coakley11/Applied-mathematical-intelligence/dev/streamlit_app.py",
]

CANDIDATES = [
    "baseball-stat-app",
    "ai-music-practice-coach",
    "nba-playoff-companion-ai",
    "applied-mathematical-intelligence",
    "daniel-ai-command-center",
    "music-practice-coach",
    "future-lens",
]

for url in URLS:
    r = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
    apps = set(re.findall(r"https://[a-zA-Z0-9-]+\.streamlit\.app/?", r.text))
    blocked = any(x in r.text.lower() for x in ("not found", "do not have access"))
    print(url, r.status_code, "blocked=", blocked, "apps=", apps)

print("\n--- candidate probe ---")
for name in CANDIDATES:
    url = f"https://{name}.streamlit.app"
    try:
        r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        blocked = "not found" in r.text.lower() or r.status_code == 404
        live = r.status_code == 200 and not blocked
        print(name, "live=", live, "status=", r.status_code)
    except Exception as exc:
        print(name, "err", exc)
