"""
Daniel Cohen AI Command Center — personal dashboard for the Daniel AI Suite.

Sections (each with a unique purpose):
  1. Coach Insights — what should I do next? (recommendations only)
  2. Activity Summary — what did I do recently? (facts only)
  3. App Directory — launch apps (navigation only)

Run: streamlit run ai_command_center.py
"""

from __future__ import annotations

import html
from datetime import datetime

import streamlit as st

from activity_feed import build_activity_feed
from activity_store import (
    ActivitySnapshot,
    get_app_directory_card,
    get_weekly_summary,
    load_activity_snapshot,
    load_all_events,
)
from app_registry import APP_DEFINITIONS, AppStatus, get_app_url, verify_connections
from app_urls import BUILD_VERSION, HOMEPAGE_DEV_URL, HOMEPAGE_PRODUCTION_URL
from coach_engine import CoachInsight, generate_coach_insights
from continue_dashboard import ContinueCard, build_continue_cards, recently_used_apps

APP_THEMES: dict[str, dict[str, str]] = {
    "music": {"accent": "#a855f7", "bg": "#faf5ff", "border": "#e9d5ff", "emoji": "🎵"},
    "investment": {"accent": "#0d9488", "bg": "#f0fdfa", "border": "#99f6e4", "emoji": "📊"},
    "baseball": {"accent": "#16a34a", "bg": "#f0fdf4", "border": "#bbf7d0", "emoji": "⚾"},
    "nba": {"accent": "#ea580c", "bg": "#fff7ed", "border": "#fed7aa", "emoji": "🏀"},
    "applied_intelligence": {"accent": "#2563eb", "bg": "#eff6ff", "border": "#bfdbfe", "emoji": "🧠"},
    "future_lens": {"accent": "#7c3aed", "bg": "#f5f3ff", "border": "#ddd6fe", "emoji": "🔮"},
}

STATUS_STYLES: dict[AppStatus, dict[str, str]] = {
    "Active": {"bg": "#dcfce7", "text": "#166534", "border": "#86efac"},
    "Prototype": {"bg": "#dbeafe", "text": "#1e40af", "border": "#93c5fd"},
    "Needs Connection": {"bg": "#fef9c3", "text": "#854d0e", "border": "#fde047"},
    "Coming Soon": {"bg": "#f1f5f9", "text": "#475569", "border": "#cbd5e1"},
}

SECTION_ICONS = {
    "coach": "💡",
    "feed": "🕐",
    "weekly": "📅",
    "apps": "📱",
    "continue": "⏯",
}

st.set_page_config(
    page_title="Daniel Cohen AI Command Center",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    :root { --cc-text: #1e293b; --cc-muted: #64748b; }
    .stApp {
        background: linear-gradient(180deg, #fff7ed 0%, #f8fafc 18%, #f0f9ff 100%);
    }
    .block-container { padding-top: 1rem; padding-bottom: 2.5rem; max-width: 1200px; }
    #MainMenu, footer { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent; }

    .cc-hero {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 45%, #ec4899 100%);
        border-radius: 24px; padding: 2rem 2.2rem; margin-bottom: 1.5rem; color: white;
        box-shadow: 0 16px 40px rgba(99, 102, 241, 0.25);
    }
    .cc-hero-tag {
        display: inline-block; background: rgba(255,255,255,0.2);
        border: 1px solid rgba(255,255,255,0.35); border-radius: 999px;
        padding: 0.25rem 0.75rem; font-size: 0.78rem; font-weight: 600; margin-bottom: 0.75rem;
    }
    .cc-hero h1 { margin: 0 0 0.35rem 0; font-size: 2.1rem; font-weight: 800; letter-spacing: -0.02em; }
    .cc-hero p { margin: 0; font-size: 1rem; line-height: 1.55; opacity: 0.95; max-width: 720px; }

    .cc-section-title {
        font-size: 1.35rem; font-weight: 800; color: #1e293b;
        margin: 1.75rem 0 0.35rem 0;
    }
    .cc-section-sub { color: #64748b; font-size: 0.92rem; margin-bottom: 1rem; line-height: 1.5; }

    .cc-insight-card {
        background: white; border-radius: 16px; padding: 1rem 1.1rem;
        margin-bottom: 0.65rem; border-left: 5px solid;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
    }
    .cc-insight-icon { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .cc-insight-text { color: #1e293b; font-size: 0.95rem; line-height: 1.5; margin: 0; }

    .cc-activity-card {
        border-radius: 16px; padding: 1rem 1.1rem; height: 100%;
        border: 1px solid; box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
    }
    .cc-activity-icon { font-size: 1.75rem; margin-bottom: 0.35rem; }
    .cc-activity-name { font-size: 0.95rem; font-weight: 800; color: #1e293b; margin-bottom: 0.25rem; }
    .cc-activity-when { font-size: 0.82rem; font-weight: 600; margin-bottom: 0.35rem; }
    .cc-activity-detail { font-size: 0.84rem; color: #64748b; line-height: 1.45; margin: 0; }

    .cc-app-card {
        background: white; border-radius: 20px; padding: 1.25rem 1.3rem 0.35rem;
        height: 100%; min-height: 0; box-shadow: 0 8px 28px rgba(15, 23, 42, 0.08);
        border: 1px solid #e2e8f0; border-top-width: 4px;
        transition: box-shadow 0.15s ease, transform 0.15s ease;
    }
    .cc-app-card:hover {
        box-shadow: 0 12px 32px rgba(15, 23, 42, 0.12);
        transform: translateY(-2px);
    }
    .cc-app-top {
        display: flex; justify-content: space-between; align-items: flex-start;
        gap: 0.75rem; margin-bottom: 0.85rem;
    }
    .cc-app-icon-wrap {
        width: 4.25rem; height: 4.25rem; border-radius: 18px;
        display: flex; align-items: center; justify-content: center;
        font-size: 2.35rem; line-height: 1; flex-shrink: 0;
    }
    .cc-app-when {
        font-size: 0.72rem; font-weight: 600; color: #94a3b8;
        text-align: right; padding-top: 0.15rem; white-space: nowrap;
    }
    .cc-status-badge {
        font-size: 0.65rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.04em; border-radius: 999px; padding: 0.2rem 0.55rem;
        border: 1px solid; white-space: nowrap;
    }
    .cc-app-name {
        font-size: 1.12rem; font-weight: 800; color: #0f172a;
        margin-bottom: 0.65rem; letter-spacing: -0.02em; line-height: 1.25;
    }
    .cc-app-highlights { display: flex; flex-direction: column; gap: 0.35rem; min-height: 3.2rem; }
    .cc-app-highlight {
        font-size: 0.88rem; font-weight: 600; color: #334155; line-height: 1.35;
        padding-left: 0.65rem; border-left: 3px solid;
    }
    .cc-app-highlight-label {
        font-weight: 600; color: #64748b;
    }
    .cc-app-ready {
        font-size: 0.88rem; font-weight: 500; color: #94a3b8; font-style: italic;
        padding-left: 0; border: none;
    }
    .cc-empty-box {
        background: white; border: 1px dashed #cbd5e1; border-radius: 16px;
        padding: 1.25rem 1.5rem; color: #64748b; font-size: 0.92rem; line-height: 1.5;
    }
    .cc-continue-card {
        background: white; border-radius: 16px; padding: 1rem 1.1rem; height: 100%;
        border: 1px solid #e2e8f0; box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
    }
    .cc-continue-app { font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.05em; color: #64748b; margin-bottom: 0.25rem; }
    .cc-continue-title { font-size: 0.98rem; font-weight: 800; color: #1e293b; margin-bottom: 0.2rem; }
    .cc-continue-sub { font-size: 0.84rem; color: #64748b; line-height: 1.45; margin: 0 0 0.65rem 0; }
    .cc-feed-list { list-style: none; padding: 0; margin: 0; }
    .cc-feed-item {
        background: white; border-radius: 12px; padding: 0.75rem 1rem; margin-bottom: 0.5rem;
        border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
        font-size: 0.9rem; color: #334155; line-height: 1.4;
    }
    .cc-feed-meta { font-size: 0.72rem; font-weight: 700; color: #94a3b8; text-transform: uppercase;
        letter-spacing: 0.04em; margin-bottom: 0.2rem; }
    .cc-weekly-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 0.65rem; }
    .cc-weekly-stat {
        background: white; border-radius: 14px; padding: 0.85rem 1rem; border: 1px solid #e2e8f0;
        box-shadow: 0 2px 10px rgba(15, 23, 42, 0.05);
    }
    .cc-weekly-value { font-size: 1.35rem; font-weight: 800; color: #0f172a; line-height: 1.1; }
    .cc-weekly-label { font-size: 0.78rem; color: #64748b; margin-top: 0.15rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


def _status_badge_html(status: AppStatus) -> str:
    style = STATUS_STYLES[status]
    return (
        f'<span class="cc-status-badge" style="background:{style["bg"]};'
        f'color:{style["text"]};border-color:{style["border"]};">{status}</span>'
    )


def _render_go_button(label: str, url: str, key: str) -> None:
    cleaned = url.strip()
    if cleaned:
        st.link_button(label, cleaned, use_container_width=True, key=key)
    else:
        st.button(label, disabled=True, use_container_width=True, key=key)
        st.caption("Not connected")


def _render_unsafe_html(block: str) -> None:
    """Render HTML as one block (no newlines inside tags — Streamlit markdown-safe)."""
    st.markdown(block.strip(), unsafe_allow_html=True)


def _render_hero(snapshot: ActivitySnapshot) -> None:
    activity_tag = "Live activity" if snapshot.has_real_data else "Waiting for activity data"
    st.markdown(
        f"""
        <div class="cc-hero">
            <div class="cc-hero-tag">👋 Welcome back</div>
            <h1>🏠 Daniel Cohen AI Command Center</h1>
            <p>Your cross-app activity dashboard — continue work, coach insights, and app launchers.
            Build {BUILD_VERSION} · {activity_tag}.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_continue_section(snapshot: ActivitySnapshot, cards: list[ContinueCard]) -> None:
    st.markdown(
        f'<div class="cc-section-title">{SECTION_ICONS["continue"]} Continue where you left off</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="cc-section-sub">Active projects and recent work pulled from saved app state — no placeholder data.</div>',
        unsafe_allow_html=True,
    )

    if snapshot.last_opened_app:
        app_name = next(
            (a.name for a in APP_DEFINITIONS if a.key == snapshot.last_opened_app),
            snapshot.last_opened_app,
        )
        page_bit = f" · {snapshot.last_opened_page}" if snapshot.last_opened_page else ""
        st.caption(f"Last opened: **{app_name}**{page_bit}")

    recent = recently_used_apps(limit=4)
    if recent:
        chips = " · ".join(name for _, name, _ in recent)
        st.caption(f"Recently used: {chips}")

    if not cards:
        st.markdown(
            '<div class="cc-empty-box">No saved continue items yet. As you use the suite apps, '
            "your current songs, analyses, and simulations will appear here.</div>",
            unsafe_allow_html=True,
        )
        return

    for group_start in (0, 3):
        chunk = cards[group_start : group_start + 3]
        if not chunk:
            break
        cols = st.columns(3, gap="medium")
        for idx, card in enumerate(chunk):
            theme = APP_THEMES.get(card.app_key, {"accent": "#6366f1", "emoji": card.emoji})
            with cols[idx]:
                sub = (
                    f'<p class="cc-continue-sub">{html.escape(card.subtitle)}</p>'
                    if card.subtitle
                    else ""
                )
                _render_unsafe_html(
                    f'<div class="cc-continue-card" style="border-left:4px solid {theme["accent"]};">'
                    f'<div class="cc-continue-app">{html.escape(card.app_name)}</div>'
                    f'<div class="cc-continue-title">{theme.get("emoji", card.emoji)} '
                    f"{html.escape(card.title)}</div>{sub}</div>"
                )
                _render_go_button("Continue", card.action_url, f"continue_{card.app_key}_{idx}_{group_start}")


def _render_coach_insights(insights: list[CoachInsight]) -> None:
    st.markdown(
        f'<div class="cc-section-title">{SECTION_ICONS["coach"]} Coach Insights</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="cc-section-sub">Personalized next steps based on your real activity — recommendations only.</div>',
        unsafe_allow_html=True,
    )
    if not insights:
        st.markdown(
            '<div class="cc-empty-box">No coach insights right now. '
            "As you use your apps, recommendations will appear here based on what you actually do.</div>",
            unsafe_allow_html=True,
        )
        return

    cols = st.columns(min(len(insights), 2), gap="medium")
    for col, insight in zip(cols, insights[:2]):
        with col:
            theme = APP_THEMES.get(insight.key, {"accent": "#6366f1", "emoji": insight.icon})
            st.markdown(
                f"""
                <div class="cc-insight-card" style="border-left-color:{theme['accent']};">
                    <div class="cc-insight-icon">{theme.get('emoji', insight.icon)}</div>
                    <p class="cc-insight-text">{html.escape(insight.message)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    for insight in insights[2:]:
        theme = APP_THEMES.get(insight.key, {"accent": "#6366f1", "emoji": insight.icon})
        st.markdown(
            f"""
            <div class="cc-insight-card" style="border-left-color:{theme['accent']};">
                <div class="cc-insight-icon">{theme.get('emoji', insight.icon)}</div>
                <p class="cc-insight-text">{html.escape(insight.message)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_recent_activity_feed() -> None:
    st.markdown(
        f'<div class="cc-section-title">{SECTION_ICONS["feed"]} Recent Activity</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="cc-section-sub">Meaningful actions across your suite — newest first. '
        "Music chart/lyrics saves appear after <strong>Save as user verified</strong> when repos run side-by-side locally.</div>",
        unsafe_allow_html=True,
    )

    feed = build_activity_feed(load_all_events(), limit=20)
    if not feed:
        st.markdown(
            '<div class="cc-empty-box">No meaningful actions logged yet. Use your apps locally (sibling repos '
            "side-by-side) or add a cloud activity backend for Streamlit Cloud sync.</div>",
            unsafe_allow_html=True,
        )
        return

    items_html = []
    for item in feed:
        when = ""
        if item.timestamp:
            try:
                when = datetime.fromisoformat(item.timestamp).strftime("%b %d · %I:%M %p")
            except ValueError:
                when = item.timestamp[:16]
        items_html.append(
            f'<li class="cc-feed-item"><div class="cc-feed-meta">{html.escape(item.app_label)}'
            f'{f" · {html.escape(when)}" if when else ""}</div>{html.escape(item.message)}</li>'
        )
    _render_unsafe_html(f'<ul class="cc-feed-list">{"".join(items_html)}</ul>')


def _render_weekly_summary(snapshot: ActivitySnapshot) -> None:
    st.markdown(
        f'<div class="cc-section-title">{SECTION_ICONS["weekly"]} Weekly Summary</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="cc-section-sub">This week only — counts appear when real activity exists.</div>',
        unsafe_allow_html=True,
    )

    summary = get_weekly_summary(snapshot)
    if not summary.has_any:
        st.markdown(
            '<div class="cc-empty-box">No weekly activity totals yet. Practice, review, or run an analysis '
            "in any suite app to populate this section.</div>",
            unsafe_allow_html=True,
        )
        return

    stats: list[tuple[str, str]] = []
    if summary.music_minutes > 0:
        stats.append((f"{summary.music_minutes:.0f}", "Music practice min"))
    if summary.songs_practiced > 0:
        stats.append((str(summary.songs_practiced), "Songs practiced"))
    if summary.baseball_reviews > 0:
        stats.append((str(summary.baseball_reviews), "Baseball actions"))
    if summary.portfolio_checks > 0:
        stats.append((str(summary.portfolio_checks), "Portfolio checks"))
    if summary.nba_sessions > 0:
        stats.append((str(summary.nba_sessions), "Basketball sessions"))
    if summary.applied_intelligence_sessions > 0:
        stats.append((str(summary.applied_intelligence_sessions), "Applied Intelligence"))
    if summary.future_simulations > 0:
        stats.append((str(summary.future_simulations), "Simulations"))

    cells = "".join(
        f'<div class="cc-weekly-stat"><div class="cc-weekly-value">{html.escape(val)}</div>'
        f'<div class="cc-weekly-label">{html.escape(label)}</div></div>'
        for val, label in stats
    )
    _render_unsafe_html(f'<div class="cc-weekly-grid">{cells}</div>')


def _app_highlight_line_html(line: str, accent: str) -> str:
    if line == "Ready to start.":
        return f'<div class="cc-app-ready">{html.escape(line)}</div>'
    if ": " in line:
        label, value = line.split(": ", 1)
        return (
            f'<div class="cc-app-highlight" style="border-color:{accent};">'
            f'<span class="cc-app-highlight-label">{html.escape(label)}:</span> '
            f"{html.escape(value)}</div>"
        )
    return (
        f'<div class="cc-app-highlight" style="border-color:{accent};">{html.escape(line)}</div>'
    )


def _app_highlights_html(card_highlights: tuple[str, ...], accent: str) -> str:
    parts = [_app_highlight_line_html(line, accent) for line in card_highlights]
    return f'<div class="cc-app-highlights">{"".join(parts)}</div>'


def _build_app_card_html(app_key: str, snapshot: ActivitySnapshot) -> str:
    """Single-line HTML tree — avoids st.markdown newline/div parsing bugs."""
    app = next(a for a in APP_DEFINITIONS if a.key == app_key)
    theme = APP_THEMES[app.key]
    accent = theme["accent"]
    card = get_app_directory_card(snapshot, app.key)

    if card.when:
        top_right = f'<div class="cc-app-when" style="color:{accent};">{html.escape(card.when)}</div>'
    elif app.status != "Active":
        top_right = _status_badge_html(app.status)
    else:
        top_right = ""

    return (
        f'<div class="cc-app-card" style="border-top-color:{accent};">'
        f'<div class="cc-app-top">'
        f'<div class="cc-app-icon-wrap" style="background:{theme["bg"]};border:1px solid {theme["border"]};">'
        f"{theme['emoji']}</div>"
        f"{top_right}</div>"
        f'<div class="cc-app-name">{html.escape(app.name)}</div>'
        f"{_app_highlights_html(card.highlights, accent)}"
        f"</div>"
    )


def _render_app_card(app_key: str, snapshot: ActivitySnapshot) -> None:
    app = next(a for a in APP_DEFINITIONS if a.key == app_key)
    url = get_app_url(app.key)
    _render_unsafe_html(_build_app_card_html(app_key, snapshot))
    _render_go_button("Open", url, f"app_{app.key}")


def _render_app_directory(snapshot: ActivitySnapshot) -> None:
    st.markdown(
        f'<div class="cc-section-title">{SECTION_ICONS["apps"]} App Directory</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="cc-section-sub">Your apps at a glance — pick up where you left off or start fresh.</div>',
        unsafe_allow_html=True,
    )

    app_keys = [app.key for app in APP_DEFINITIONS]
    for row_keys in (app_keys[:3], app_keys[3:]):
        cols = st.columns(3, gap="medium")
        for col, key in zip(cols, row_keys):
            with col:
                _render_app_card(key, snapshot)


@st.cache_data(ttl=300, show_spinner=False)
def _cached_connections():
    return verify_connections()


snapshot = load_activity_snapshot()
insights = generate_coach_insights(snapshot)
continue_cards = build_continue_cards()
connections = _cached_connections()

_render_hero(snapshot)
_render_continue_section(snapshot, continue_cards)
_render_coach_insights(insights)
_render_recent_activity_feed()
_render_weekly_summary(snapshot)
_render_app_directory(snapshot)

with st.expander("Deployment & link audit (admin)"):
    from activity_diagnostics import run_activity_diagnostics

    diag = run_activity_diagnostics()
    st.markdown("#### Cross-app activity trace (Music → Command Center)")
    st.markdown(
        f"| Check | Result |\n|---|---|\n"
        f"| Deployment mode | `{diag.deployment_mode}` |\n"
        f"| Supabase configured | {diag.cloud_storage_configured} |\n"
        f"| Supabase reachable | {diag.cloud_storage_reachable} |\n"
        f"| Failing step | **{diag.failure_step}** |\n"
        f"| CC SQLite exists | {diag.command_center_db_exists} |\n"
        f"| Music events in CC DB | {diag.sqlite_music_event_count} "
        f"(verified: {diag.sqlite_verified_count}, lyrics: {diag.sqlite_lyrics_count}) |\n"
        f"| Last music event in CC DB | {diag.last_music_event} |\n"
        f"| Last verified/lyrics in CC DB | {diag.last_verified_event} |\n"
        f"| Music fallback file found | {diag.music_fallback_found or '—'} |\n"
        f"| Verified/lyrics in fallback | {diag.music_fallback_verified_count} |\n"
        f"| Sibling repos on disk | {diag.sibling_repos_reachable} |\n"
        f"| CC can see verified saves | {diag.can_command_center_see_music_verified} |"
    )
    st.info(diag.recommendation)
    with st.expander("Fallback paths checked"):
        for p in diag.music_fallback_paths_checked:
            st.code(p)
    st.divider()
    st.markdown(f"**Homepage Production:** {HOMEPAGE_PRODUCTION_URL} · branch `main`")
    dev_line = HOMEPAGE_DEV_URL or "Not deployed yet — create on Streamlit Cloud from branch `dev`"
    st.markdown(f"**Homepage Dev:** {dev_line}")
    st.divider()
    st.markdown("| App | Branch | Button URL | Live |")
    st.markdown("|---|---|---|---|")
    for conn in connections:
        live = "Yes" if conn.streamlit_live else "No"
        st.markdown(f"| {conn.name} | {conn.branch} | `{conn.open_url}` | {live} |")

st.caption(
    f"Daniel Cohen AI Command Center · {datetime.now().strftime('%B %d, %Y')} · build {BUILD_VERSION}"
)
