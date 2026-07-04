"""
Command Center homepage — Music Continue cards and App Directory workstreams.
"""

from __future__ import annotations

import html
from typing import Any
from urllib.parse import parse_qs, urlparse

from activity_store import ActivitySnapshot
from continue_dashboard import ContinueCard
from music_command_center import (
    build_workstream_cards,
    filter_continue_cards_for_workspace,
    summarize_workstreams_from_payloads,
)
from music_resume_payload import (
    build_music_resume_payload,
    decode_payload_b64,
    normalize_workspace_id,
    payload_workspace_matches,
)

__all__ = (
    "active_workspace_id",
    "event_matches_active_workspace",
    "merge_music_continue_cards",
    "music_continue_cards_from_resume_items",
    "music_workstream_cards",
    "payload_from_action_url",
    "render_music_workstreams_section",
    "resolve_music_continue_action_url",
)


def active_workspace_id() -> str:
    try:
        from suite_workspace import get_active_workspace_id

        return normalize_workspace_id(get_active_workspace_id())
    except ImportError:
        return "daniel"


def event_matches_active_workspace(event: dict[str, Any]) -> bool:
    """Drop cross-workspace Music events (coakley11 vs daniel)."""
    ws = active_workspace_id()
    metrics = event.get("metrics") if isinstance(event.get("metrics"), dict) else {}
    event_ws = str(metrics.get("workspace_id") or "").strip()
    if not event_ws:
        try:
            from suite_workspace import DEFAULT_WORKSPACE_ID

            return ws == DEFAULT_WORKSPACE_ID
        except ImportError:
            return True
    return normalize_workspace_id(event_ws) == ws


def payload_from_action_url(action_url: str) -> dict[str, Any]:
    url = str(action_url or "").strip()
    if not url or "suite_resume_payload=" not in url:
        return {}
    try:
        qs = parse_qs(urlparse(url).query)
        raw = str((qs.get("suite_resume_payload") or [""])[0] or "")
        return decode_payload_b64(raw)
    except Exception:
        return {}


def resolve_music_continue_action_url(
    metrics: dict[str, Any],
    *,
    base_url: str,
    stored_action_url: str = "",
) -> str:
    """Prefer stored payload URL; rebuild from resume_payload metrics when needed."""
    stored = str(stored_action_url or "").strip()
    if stored and "suite_entry_mode=continue" in stored and "suite_resume_payload=" in stored:
        payload = payload_from_action_url(stored)
        if payload and payload_workspace_matches(payload, active_workspace_id()):
            return stored
    payload = metrics.get("resume_payload")
    if isinstance(payload, dict) and payload.get("resume_kind"):
        if not payload.get("workspace_id"):
            payload = {**payload, "workspace_id": active_workspace_id()}
        if not payload_workspace_matches(payload, active_workspace_id()):
            return ""
        try:
            from suite_deep_links import build_music_continue_url

            return build_music_continue_url(payload, base_url=base_url)
        except Exception:
            pass
    if stored and "suite_pick_key=" not in stored:
        return stored
    try:
        from suite_deep_links import build_resume_action_url

        return build_resume_action_url(
            "music",
            resume_key=str(metrics.get("resume_key") or ""),
            page=str(metrics.get("studio_page") or metrics.get("page") or ""),
            metrics=metrics,
            base_url=base_url,
        )
    except Exception:
        return stored or base_url


def _resume_item_to_continue_card(item: Any, *, music_url: str, themes: dict[str, str]) -> ContinueCard | None:
    action_url = str(getattr(item, "action_url", "") or "").strip()
    payload = payload_from_action_url(action_url)
    if payload and not payload_workspace_matches(payload, active_workspace_id()):
        return None
    title = str(getattr(item, "title", "") or "").strip()
    subtitle = str(getattr(item, "subtitle", "") or "").strip()
    if not title:
        return None
    metrics: dict[str, Any] = {}
    if payload:
        metrics["resume_payload"] = payload
    url = resolve_music_continue_action_url(
        metrics,
        base_url=music_url,
        stored_action_url=action_url,
    )
    if not url:
        return None
    return ContinueCard(
        app_key="music",
        app_name="Music Practice Coach",
        title=title,
        subtitle=subtitle,
        action_url=url,
        emoji=themes.get("music", "🎵"),
        button_label="Continue",
    )


def music_continue_cards_from_resume_items(*, limit: int = 6) -> list[ContinueCard]:
    """Top Continue section — Music tasks from workspace-scoped resume items."""
    from app_branding import suite_app_icons
    from app_registry import APP_DEFINITIONS
    from suite_storage import load_active_resume_items

    try:
        from suite_workspace import get_active_workspace_id

        ws = normalize_workspace_id(get_active_workspace_id())
    except ImportError:
        ws = active_workspace_id()

    music_url = ""
    for app in APP_DEFINITIONS:
        if app.key == "music":
            music_url = app.streamlit_url.strip()
            break
    if not music_url:
        return []

    themes = suite_app_icons()
    cards: list[ContinueCard] = []
    seen: set[str] = set()
    for item in load_active_resume_items(limit=40, app="music"):
        if str(getattr(item, "app", "") or "") != "music":
            continue
        key = str(getattr(item, "item_key", "") or "").strip()
        if not key or key in seen:
            continue
        card = _resume_item_to_continue_card(item, music_url=music_url, themes=themes)
        if card is None:
            continue
        seen.add(key)
        cards.append(card)
        if len(cards) >= limit:
            break

    dict_cards = [
        {
            "workspace_id": ws,
            "payload": payload_from_action_url(c.action_url),
            **c.__dict__,
        }
        for c in cards
    ]
    filtered = filter_continue_cards_for_workspace(dict_cards, ws)
    allowed_urls = {str(c.get("action_url") or "") for c in filtered}
    return [c for c in cards if c.action_url in allowed_urls][:limit]


def merge_music_continue_cards(
    existing: list[ContinueCard],
    *,
    limit: int = 6,
) -> list[ContinueCard]:
    """Merge Music resume Continue cards ahead of inferred project cards."""
    music_cards = music_continue_cards_from_resume_items(limit=limit)
    if not music_cards:
        return existing[:limit]
    music_keys = {c.title.lower() for c in music_cards}
    rest = [c for c in existing if c.title.lower() not in music_keys]
    merged = music_cards + rest
    return merged[:limit]


def _payloads_from_snapshot(snapshot: ActivitySnapshot) -> list[dict[str, Any]]:
    from activity_store import load_all_events

    ws = active_workspace_id()
    payloads: list[dict[str, Any]] = []
    for event in sorted(load_all_events(limit=200), key=lambda e: str(e.get("timestamp") or ""), reverse=True):
        if str(event.get("app") or "") != "music":
            continue
        if not event_matches_active_workspace(event):
            continue
        metrics = event.get("metrics") if isinstance(event.get("metrics"), dict) else {}
        payload = metrics.get("resume_payload")
        if isinstance(payload, dict) and payload.get("resume_kind"):
            payloads.append(payload)
            continue
        session = {
            "_suite_active_workspace_id": ws,
            "studio_page": str(metrics.get("studio_page") or event.get("page") or "practice"),
            "active_catalog_pick_key": str(metrics.get("pick_key") or ""),
            "song": str(metrics.get("song") or ""),
            "artist": str(metrics.get("artist") or ""),
            "instrument": str(metrics.get("instrument") or ""),
            "display_key": str(metrics.get("display_key") or ""),
            "practice_focus_section": str(metrics.get("practice_focus_section") or ""),
            "bpm": metrics.get("bpm"),
            "backing_track_scope": metrics.get("backing_track_scope"),
            "backing_track_multi_sections": metrics.get("backing_track_multi_sections"),
            "backing_groove_style": metrics.get("backing_groove_style"),
        }
        payloads.append(build_music_resume_payload(session, workspace_id=ws))
        if len(payloads) >= 12:
            break
    return payloads


def music_workstream_cards(snapshot: ActivitySnapshot) -> list[dict[str, Any]]:
    """App Directory — Music workstream entry cards (soft open, no stale song)."""
    from app_registry import APP_DEFINITIONS

    ws = active_workspace_id()
    music_url = next((a.streamlit_url.strip() for a in APP_DEFINITIONS if a.key == "music"), "")
    summaries = summarize_workstreams_from_payloads(_payloads_from_snapshot(snapshot), workspace_id=ws)
    if snapshot.last_song and "song_practice" not in summaries:
        summaries.setdefault("song_practice", f"Recent: {snapshot.last_song}")
    return build_workstream_cards(workspace_id=ws, summaries=summaries, base_url=music_url)


def render_music_workstreams_section(st: Any, snapshot: ActivitySnapshot) -> None:
    """Bottom App Directory — Music workstream row."""
    cards = music_workstream_cards(snapshot)
    if not cards:
        return
    st.markdown(
        '<div class="cc-section-sub" style="margin-top:1.25rem;">Music workstreams — open your workspace without forcing an old song.</div>',
        unsafe_allow_html=True,
    )
    row_a, row_b = cards[:3], cards[3:6]
    for row in (row_a, row_b):
        if not row:
            continue
        cols = st.columns(len(row), gap="medium")
        for col, card in zip(cols, row):
            with col:
                title = html.escape(str(card.get("title") or ""))
                subtitle = html.escape(str(card.get("subtitle") or ""))
                st.markdown(
                    f'<div class="cc-continue-card" style="border-left:4px solid #6366f1;">'
                    f'<div class="cc-continue-app">Music</div>'
                    f'<div class="cc-continue-title">🎵 {title}</div>'
                    f'<p class="cc-continue-sub">{subtitle}</p></div>',
                    unsafe_allow_html=True,
                )
                url = str(card.get("action_url") or "")
                if url:
                    st.link_button("Open", url, use_container_width=True)
