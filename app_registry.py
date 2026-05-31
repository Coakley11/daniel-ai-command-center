"""
App registry and URL discovery for the Daniel AI Command Center.

Auto-discovered from local GitHub repos and Streamlit Cloud deployments.
Replace verification logic later with shared activity DB + deployment API.
"""

from __future__ import annotations

import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

AppStatus = Literal["Active", "Prototype", "Needs Connection", "Coming Soon"]

# ── Discovered deployment URLs (Streamlit Cloud) ──────────────────────────────
# Canonical *.streamlit.app used when verified; otherwise share.streamlit.io link.

MUSIC_STREAMLIT_URL = (
    "https://share.streamlit.io/Coakley11/ai-music-practice-coach/dev/streamlit_music_practice_app.py"
)
INVESTMENT_STREAMLIT_URL = "https://investment-portfolio-analyzer.streamlit.app"
BASEBALL_STREAMLIT_URL = (
    "https://share.streamlit.io/Coakley11/baseball-stat-app/main/streamlit_app.py"
)
NBA_STREAMLIT_URL = (
    "https://share.streamlit.io/Coakley11/nba-playoff-companion-ai/dev/streamlit_app.py"
)
MATH_STREAMLIT_URL = (
    "https://share.streamlit.io/Coakley11/Applied-mathematical-intelligence/dev/streamlit_app.py"
)
FUTURE_LENS_STREAMLIT_URL = ""

# ── GitHub repository URLs ────────────────────────────────────────────────────

MUSIC_GITHUB_URL = "https://github.com/Coakley11/ai-music-practice-coach/tree/dev"
INVESTMENT_GITHUB_URL = "https://github.com/Coakley11/investment-portfolio-analyzer/tree/dev"
BASEBALL_GITHUB_URL = "https://github.com/Coakley11/baseball-stat-app/tree/main"
NBA_GITHUB_URL = "https://github.com/Coakley11/nba-playoff-companion-ai/tree/dev"
MATH_GITHUB_URL = "https://github.com/Coakley11/Applied-mathematical-intelligence/tree/dev"
FUTURE_LENS_GITHUB_URL = ""

# Resolved app URLs — Streamlit when available, else GitHub repo link
MUSIC_APP_URL = MUSIC_STREAMLIT_URL or MUSIC_GITHUB_URL
INVESTMENT_APP_URL = INVESTMENT_STREAMLIT_URL or INVESTMENT_GITHUB_URL
BASEBALL_APP_URL = BASEBALL_STREAMLIT_URL or BASEBALL_GITHUB_URL
NBA_APP_URL = NBA_STREAMLIT_URL or NBA_GITHUB_URL
MATH_APP_URL = MATH_STREAMLIT_URL or MATH_GITHUB_URL
FUTURE_LENS_APP_URL = FUTURE_LENS_STREAMLIT_URL or FUTURE_LENS_GITHUB_URL


@dataclass(frozen=True)
class AppDefinition:
    key: str
    name: str
    icon: str
    status: AppStatus
    branch: str
    github_url: str
    streamlit_url: str
    main_file: str
    description: str
    why_it_matters: str
    button_label: str


APP_DEFINITIONS: tuple[AppDefinition, ...] = (
    AppDefinition(
        key="music",
        name="Music Practice Coach",
        icon="🎵",
        status="Active",
        branch="dev",
        github_url=MUSIC_GITHUB_URL,
        streamlit_url=MUSIC_STREAMLIT_URL,
        main_file="streamlit_music_practice_app.py",
        description="Your AI practice buddy — songs, chords, and progress tracking.",
        why_it_matters="Keeps your creative skills sharp and makes practice fun.",
        button_label="Go to Music App",
    ),
    AppDefinition(
        key="investment",
        name="Investment Portfolio Analyzer",
        icon="📊",
        status="Active",
        branch="dev",
        github_url=INVESTMENT_GITHUB_URL,
        streamlit_url=INVESTMENT_STREAMLIT_URL,
        main_file="streamlit_app.py",
        description="See how your money is doing — risk, allocation, and smart next steps.",
        why_it_matters="Stay confident about financial decisions without overthinking.",
        button_label="Go to Investment App",
    ),
    AppDefinition(
        key="baseball",
        name="Fantasy Baseball",
        icon="⚾",
        status="Active",
        branch="main",
        github_url=BASEBALL_GITHUB_URL,
        streamlit_url=BASEBALL_STREAMLIT_URL,
        main_file="streamlit_app.py",
        description="Lineups, start/sit picks, and stats when you need an edge.",
        why_it_matters="Win more fantasy weeks with data-backed lineup calls.",
        button_label="Go to Baseball App",
    ),
    AppDefinition(
        key="nba",
        name="NBA Playoff Companion",
        icon="🏀",
        status="Active",
        branch="dev",
        github_url=NBA_GITHUB_URL,
        streamlit_url=NBA_STREAMLIT_URL,
        main_file="streamlit_app.py",
        description="Matchups, injuries, and live game insights for basketball fans.",
        why_it_matters="Walk into game day knowing who's playing and who to watch.",
        button_label="Go to NBA App",
    ),
    AppDefinition(
        key="math",
        name="Advanced Math Intelligence",
        icon="🧮",
        status="Prototype",
        branch="dev",
        github_url=MATH_GITHUB_URL,
        streamlit_url=MATH_STREAMLIT_URL,
        main_file="streamlit_app.py",
        description="Build and test applied math ideas — simulations, puzzles, and reasoning.",
        why_it_matters="Strengthens how you think through real-world quantitative problems.",
        button_label="Go to Math App",
    ),
    AppDefinition(
        key="future_lens",
        name="Future Lens",
        icon="🔮",
        status="Coming Soon",
        branch="dev",
        github_url=FUTURE_LENS_GITHUB_URL,
        streamlit_url=FUTURE_LENS_STREAMLIT_URL,
        main_file="",
        description="Explore how AI might reshape music, money, sports, and teaching.",
        why_it_matters="Helps you adapt early instead of reacting late.",
        button_label="Go to Future Lens",
    ),
)


@dataclass(frozen=True)
class ConnectionStatus:
    key: str
    name: str
    connected: bool
    streamlit_found: bool
    github_found: bool
    open_url: str
    streamlit_url: str
    github_url: str
    last_verified: str


def resolve_app_url(app: AppDefinition) -> str:
    """Prefer verified Streamlit deployment; fall back to GitHub repo URL."""
    if app.streamlit_url.strip():
        return app.streamlit_url.strip()
    if app.github_url.strip():
        return app.github_url.strip()
    return ""


def _url_is_live(url: str) -> bool:
    if not url.strip():
        return False
    headers = {"User-Agent": "DanielAICommandCenter/1.0"}
    try:
        if requests is not None:
            response = requests.get(url, timeout=8, allow_redirects=True, headers=headers)
            if response.status_code != 200:
                return False
            body = response.text[:12000].lower()
        else:
            req = urllib.request.Request(url, method="GET", headers=headers)
            with urllib.request.urlopen(req, timeout=8) as response:
                if response.status != 200:
                    return False
                body = response.read(12000).decode("utf-8", errors="ignore").lower()
        blocked = any(
            phrase in body
            for phrase in ("do not have access", "you do not have access", "app does not exist")
        )
        return not blocked
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return False


def verify_connections() -> list[ConnectionStatus]:
    """Check Streamlit and GitHub links. Cache in Streamlit via st.cache_data in caller."""
    verified_at = datetime.now().strftime("%b %d, %Y · %I:%M %p")
    rows: list[ConnectionStatus] = []

    for app in APP_DEFINITIONS:
        streamlit_live = _url_is_live(app.streamlit_url) if app.streamlit_url else False
        github_live = bool(re.match(r"https://github\.com/Coakley11/\S+", app.github_url or ""))
        open_url = app.streamlit_url if streamlit_live else (app.github_url if github_live else "")
        connected = bool(open_url) and app.status != "Coming Soon"

        rows.append(
            ConnectionStatus(
                key=app.key,
                name=app.name,
                connected=connected,
                streamlit_found=streamlit_live,
                github_found=github_live,
                open_url=open_url,
                streamlit_url=app.streamlit_url,
                github_url=app.github_url,
                last_verified=verified_at,
            )
        )
    return rows


def get_app_url(key: str, connections: list[ConnectionStatus] | None = None) -> str:
    if connections:
        for row in connections:
            if row.key == key and row.open_url:
                return row.open_url
    for app in APP_DEFINITIONS:
        if app.key == key:
            return resolve_app_url(app)
    return ""
