"""Probe Streamlit public URLs."""
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

CANDIDATES = [
    "ai-music-practice-coach",
    "ai-music-practice-coach-dev",
    "music-practice-coach",
    "investment-portfolio-analyzer",
    "investment-portfolio-analyzer-dev",
    "baseball-stat-app",
    "baseball-stat-app-main",
    "nba-playoff-companion-ai",
    "nba-playoff-companion-ai-dev",
    "applied-mathematical-intelligence",
    "applied-mathematical-intelligence-dev",
    "ai-homeroom",
    "advanced-math-intelligence",
    "future-lens-ai-transition-simulator",
    "future-lens",
    "ai-future-lens",
    "daniel-cohen-baseball",
    "daniel-cohen-music",
    "daniel-cohen-nba",
]

BLOCKED = (
    "do not have access",
    "you do not have access",
    "sign in to continue",
    "please sign in",
)


def is_public(url: str) -> tuple[bool, int, str]:
    try:
        r = requests.get(url, timeout=12, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
        body = r.text[:25000].lower()
        blocked = any(p in body for p in BLOCKED)
        return r.status_code == 200 and not blocked, r.status_code, r.url
    except Exception as exc:
        return False, 0, str(exc)


print("=== share.streamlit.io ===")
for name, url in SHARE.items():
    ok, status, final = is_public(url)
    print(name, ok, status, final[:80])

print("\n=== streamlit.app candidates ===")
for name in CANDIDATES:
    url = f"https://{name}.streamlit.app"
    ok, status, final = is_public(url)
    if ok:
        print("PUBLIC", name, final)

print("\n=== extract from share HTML ===")
for name, url in SHARE.items():
    r = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
    apps = set(re.findall(r"https://[a-zA-Z0-9-]+\.streamlit\.app/?", r.text))
    print(name, apps)
