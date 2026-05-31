"""
App registry for the Daniel AI Command Center.

Replace verification logic later with shared activity DB + deployment API.
"""

from __future__ import annotations

import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

from app_urls import (
    APP_BRANCH,
    APPLIED_INTELLIGENCE_GITHUB_URL,
    APPLIED_INTELLIGENCE_URL,
    BASEBALL_APP_URL,
    BASEBALL_GITHUB_URL,
    FUTURE_LENS_GITHUB_URL,
    FUTURE_LENS_URL,
    INVESTMENT_APP_URL,
    INVESTMENT_GITHUB_URL,
    MUSIC_APP_URL,
    MUSIC_GITHUB_URL,
    NBA_APP_URL,
    NBA_GITHUB_URL,
)

AppStatus = Literal["Active", "Prototype", "Needs Connection", "Coming Soon"]

ACCESS_BLOCKED_PHRASES = (
    "do not have access",
    "you do not have access",
    "sign in to continue",
    "please sign in",
    "app does not exist",
)


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
        branch=APP_BRANCH["music"],
        github_url=MUSIC_GITHUB_URL,
        streamlit_url=MUSIC_APP_URL,
        main_file="streamlit_music_practice_app.py",
        description="Your AI practice buddy — songs, chords, and progress tracking.",
        why_it_matters="Keeps your creative skills sharp and makes practice fun.",
        button_label="Go to App",
    ),
    AppDefinition(
        key="investment",
        name="Investment Analytics",
        icon="📊",
        status="Active",
        branch=APP_BRANCH["investment"],
        github_url=INVESTMENT_GITHUB_URL,
        streamlit_url=INVESTMENT_APP_URL,
        main_file="streamlit_app.py",
        description="See how your money is doing — risk, allocation, and smart next steps.",
        why_it_matters="Stay confident about financial decisions without overthinking.",
        button_label="Go to App",
    ),
    AppDefinition(
        key="baseball",
        name="Baseball Analytics",
        icon="⚾",
        status="Active",
        branch=APP_BRANCH["baseball"],
        github_url=BASEBALL_GITHUB_URL,
        streamlit_url=BASEBALL_APP_URL,
        main_file="streamlit_app.py",
        description="Lineups, start/sit picks, and stats when you need an edge.",
        why_it_matters="Win more fantasy weeks with data-backed lineup calls.",
        button_label="Go to App",
    ),
    AppDefinition(
        key="nba",
        name="Basketball Companion",
        icon="🏀",
        status="Active",
        branch=APP_BRANCH["nba"],
        github_url=NBA_GITHUB_URL,
        streamlit_url=NBA_APP_URL,
        main_file="streamlit_app.py",
        description="Matchups, injuries, and live game insights for basketball fans.",
        why_it_matters="Walk into game day knowing who's playing and who to watch.",
        button_label="Go to App",
    ),
    AppDefinition(
        key="applied_intelligence",
        name="Applied Intelligence",
        icon="🧠",
        status="Active",
        branch=APP_BRANCH["applied_intelligence"],
        github_url=APPLIED_INTELLIGENCE_GITHUB_URL,
        streamlit_url=APPLIED_INTELLIGENCE_URL,
        main_file="streamlit_app.py",
        description=(
            "Explore applied mathematics, quantitative reasoning, problem solving, modeling, "
            "decision-making, and AI-assisted analytical thinking."
        ),
        why_it_matters="Build sharper analytical instincts for school, work, and everyday decisions.",
        button_label="Go to App",
    ),
    AppDefinition(
        key="future_lens",
        name="AI Future Simulator",
        icon="🔮",
        status="Active",
        branch=APP_BRANCH["future_lens"],
        github_url=FUTURE_LENS_GITHUB_URL,
        streamlit_url=FUTURE_LENS_URL,
        main_file="streamlit_app.py",
        description="Explore how AI might reshape music, money, sports, and teaching.",
        why_it_matters="Helps you adapt early instead of reacting late.",
        button_label="Go to App",
    ),
)


@dataclass(frozen=True)
class ConnectionStatus:
    key: str
    name: str
    branch: str
    open_url: str
    streamlit_url: str
    github_url: str
    streamlit_live: bool
    url_connected: bool
    button_works: bool
    last_verified: str


def _is_viewer_url(url: str) -> bool:
    cleaned = url.strip().lower()
    if not cleaned.startswith("https://"):
        return False
    if "share.streamlit.io" in cleaned:
        return False
    return ".streamlit.app" in cleaned


def _url_is_live(url: str) -> bool:
    if not _is_viewer_url(url):
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
        return not any(phrase in body for phrase in ACCESS_BLOCKED_PHRASES)
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return False


def get_app_url(key: str, connections: list[ConnectionStatus] | None = None) -> str:
    """Return the public Streamlit viewer URL for navigation buttons."""
    for app in APP_DEFINITIONS:
        if app.key == key:
            return app.streamlit_url.strip()
    return ""


def verify_connections() -> list[ConnectionStatus]:
    """Check deployment URLs for the Connected Apps Status panel only."""
    verified_at = datetime.now().strftime("%b %d, %Y · %I:%M %p")
    rows: list[ConnectionStatus] = []

    for app in APP_DEFINITIONS:
        streamlit_url = app.streamlit_url.strip()
        streamlit_live = _url_is_live(streamlit_url) if streamlit_url else False
        url_connected = bool(streamlit_url) and _is_viewer_url(streamlit_url)
        button_works = url_connected and streamlit_live

        rows.append(
            ConnectionStatus(
                key=app.key,
                name=app.name,
                branch=app.branch,
                open_url=streamlit_url,
                streamlit_url=streamlit_url,
                github_url=app.github_url,
                streamlit_live=streamlit_live,
                url_connected=url_connected,
                button_works=button_works,
                last_verified=verified_at,
            )
        )
    return rows
