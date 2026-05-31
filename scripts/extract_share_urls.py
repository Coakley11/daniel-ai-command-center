"""Extract viewer URLs from share.streamlit.io pages."""
from __future__ import annotations

import re

import requests

SHARE = {
    "music": "https://share.streamlit.io/Coakley11/ai-music-practice-coach/dev/streamlit_music_practice_app.py",
    "investment": "https://share.streamlit.io/Coakley11/investment-portfolio-analyzer/dev/streamlit_app.py",
    "baseball": "https://share.streamlit.io/Coakley11/baseball-stat-app/main/streamlit_app.py",
    "nba": "https://share.streamlit.io/Coakley11/nba-playoff-companion-ai/dev/streamlit_app.py",
    "math": "https://share.streamlit.io/Coakley11/Applied-mathematical-intelligence/dev/streamlit_app.py",
    "future": "https://share.streamlit.io/Coakley11/future-lens-ai-transition-simulator/main/streamlit_app.py",
}

PATTERNS = [
    r"https://[a-zA-Z0-9-]+\.streamlit\.app/?[^\"'\s<>]*",
    r'"appUrl":"([^"]+)"',
    r'"embedUrl":"([^"]+)"',
    r'"url":"(https://[^"]+\.streamlit\.app[^"]*)"',
]

for name, url in SHARE.items():
    response = requests.get(url, timeout=15, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
    print("===", name, "status", response.status_code, "final", response.url)
    found: set[str] = set()
    for pattern in PATTERNS:
        found.update(re.findall(pattern, response.text))
    print("  urls", found)
    body = response.text.lower()
    for phrase in ("do not have access", "you do not have access", "sign in", "app does not exist"):
        if phrase in body:
            print("  blocked:", phrase)
