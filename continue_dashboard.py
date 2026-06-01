"""
Continue-dashboard helpers for the Daniel AI Command Center homepage.
"""

from __future__ import annotations

from dataclasses import dataclass

from app_registry import APP_DEFINITIONS, get_app_url
from suite_storage import ResumeItem, load_active_resume_items, load_current_states


@dataclass(frozen=True)
class ContinueCard:
    app_key: str
    app_name: str
    title: str
    subtitle: str
    action_url: str
    emoji: str


def _app_meta() -> dict[str, dict[str, str]]:
    return {app.key: {"name": app.name, "url": app.streamlit_url.strip()} for app in APP_DEFINITIONS}


def build_continue_cards(limit: int = 6) -> list[ContinueCard]:
    """Return active resume items only — invalid/deleted items stay out of the dashboard."""
    meta = _app_meta()
    themes = {
        "music": "🎵",
        "investment": "📊",
        "baseball": "⚾",
        "nba": "🏀",
        "applied_intelligence": "🧠",
        "future_lens": "🔮",
    }
    cards: list[ContinueCard] = []

    for item in load_active_resume_items(limit=limit):
        if item.app not in meta:
            continue
        url = item.action_url.strip() or meta[item.app]["url"]
        if not url:
            continue
        cards.append(
            ContinueCard(
                app_key=item.app,
                app_name=meta[item.app]["name"],
                title=item.title,
                subtitle=item.subtitle,
                action_url=url,
                emoji=themes.get(item.app, "▶"),
            )
        )

    if cards:
        return cards[:limit]

    # Fallback: derive lightweight continue cards from current state (no fake history).
    for app_key, state in load_current_states().items():
        if app_key not in meta:
            continue
        summary = str(state.get("summary") or "").strip()
        page = str(state.get("page") or "").strip()
        if not summary and not page:
            continue
        subtitle = summary or page
        title = summary if summary else f"Return to {page}"
        cards.append(
            ContinueCard(
                app_key=app_key,
                app_name=meta[app_key]["name"],
                title=title,
                subtitle=page if page and page != subtitle else "",
                action_url=meta[app_key]["url"],
                emoji=themes.get(app_key, "▶"),
            )
        )
    return cards[:limit]


def recently_used_apps(limit: int = 4) -> list[tuple[str, str, str]]:
    """App keys recently touched, based on current-state timestamps."""
    meta = _app_meta()
    states = load_current_states()
    ordered = sorted(
        ((app, block.get("updated_at", "")) for app, block in states.items() if app in meta),
        key=lambda x: x[1],
        reverse=True,
    )
    out: list[tuple[str, str, str]] = []
    for app_key, _ in ordered[:limit]:
        out.append((app_key, meta[app_key]["name"], get_app_url(app_key)))
    return out
