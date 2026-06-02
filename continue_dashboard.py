"""
Continue-dashboard helpers for the Daniel AI Command Center homepage.
"""

from __future__ import annotations

from dataclasses import dataclass

from app_registry import APP_DEFINITIONS, get_app_url
from activity_store import ActivitySnapshot, load_activity_snapshot
from project_intelligence import build_project_continue_cards
from suite_storage import load_current_states


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


def build_continue_cards(limit: int = 6, snapshot: ActivitySnapshot | None = None) -> list[ContinueCard]:
    """Active projects derived from events + resume — not raw last-click titles."""
    meta = _app_meta()
    snap = snapshot if snapshot is not None else load_activity_snapshot()
    cards = build_project_continue_cards(snap, limit=limit, meta=meta)
    if cards:
        return cards

    themes = {
        "music": "🎵",
        "investment": "📊",
        "baseball": "⚾",
        "nba": "🏀",
        "applied_intelligence": "🧠",
        "future_lens": "🔮",
    }
    for app_key, state in load_current_states().items():
        if app_key not in meta or not meta[app_key]["url"]:
            continue
        summary = str(state.get("summary") or "").strip()
        page = str(state.get("page") or "").strip()
        if not summary and not page:
            continue
        cards.append(
            ContinueCard(
                app_key=app_key,
                app_name=meta[app_key]["name"],
                title=summary or f"Continue work in {meta[app_key]['name']}",
                subtitle=page if page and page != summary else "",
                action_url=meta[app_key]["url"],
                emoji=themes.get(app_key, "▶"),
            )
        )
        if len(cards) >= limit:
            break
    return cards[:limit]


def recently_used_apps(limit: int = 4) -> list[tuple[str, str, str]]:
    """App keys recently touched, based on meaningful week activity."""
    meta = _app_meta()
    snapshot = load_activity_snapshot()
    ordered = sorted(
        ((app, count) for app, count in snapshot.week_activity_by_app.items() if app in meta and count > 0),
        key=lambda x: x[1],
        reverse=True,
    )
    if not ordered:
        states = load_current_states()
        ordered = sorted(
            ((app, 1) for app, block in states.items() if app in meta and block.get("updated_at")),
            key=lambda x: str(states[x[0]].get("updated_at") or ""),
            reverse=True,
        )
    out: list[tuple[str, str, str]] = []
    for app_key, _ in ordered[:limit]:
        out.append((app_key, meta[app_key]["name"], get_app_url(app_key)))
    return out
