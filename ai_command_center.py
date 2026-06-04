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

from activity_models import ActivityFeedItem
from activity_feed import build_activity_dashboard
from activity_time import format_activity_display_time
from activity_store import (
    ActivitySnapshot,
    get_app_directory_card,
    get_weekly_summary,
    load_activity_snapshot,
    load_all_events,
)
from app_branding import build_app_themes
from app_registry import APP_DEFINITIONS, AppStatus, get_app_url, verify_connections
from app_urls import BUILD_VERSION, HOMEPAGE_DEV_URL, HOMEPAGE_PRODUCTION_URL
from coach_engine import CoachInsight, generate_coach_insights
from continue_dashboard import ContinueCard, continue_cards_for_snapshot, recently_used_apps
from project_intelligence import generate_cross_app_insights, weekly_accomplishment_lines

APP_THEMES: dict[str, dict[str, str]] = build_app_themes()

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
    .cc-feed-item-highlight {
        border-left: 4px solid #6366f1;
        background: linear-gradient(90deg, #eef2ff 0%, #ffffff 40%);
    }
    .cc-feed-item-rollup { font-style: normal; color: #475569; }
    .cc-today-work {
        background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 50%, #ffffff 100%);
        border: 1px solid #bbf7d0; border-radius: 14px; padding: 0.85rem 1.1rem;
        margin-bottom: 1rem;
    }
    .cc-today-work-title {
        font-size: 0.72rem; font-weight: 800; text-transform: uppercase;
        letter-spacing: 0.06em; color: #15803d; margin-bottom: 0.45rem;
    }
    .cc-today-work-item {
        font-size: 0.92rem; color: #166534; font-weight: 600; line-height: 1.45;
        margin: 0.15rem 0;
    }
    .cc-feed-section-label {
        font-size: 0.78rem; font-weight: 800; text-transform: uppercase;
        letter-spacing: 0.05em; color: #64748b; margin: 1rem 0 0.45rem 0;
    }
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
        try:
            st.link_button(label, cleaned, use_container_width=True, key=key)
        except TypeError:
            # Older Streamlit: link_button has no key= parameter
            st.link_button(label, cleaned, use_container_width=True)
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
        '<div class="cc-section-sub">Active projects inferred from your work — edits, reviews, and analyses waiting for the next step.</div>',
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


def _render_feed_items(items: tuple[ActivityFeedItem, ...] | list[ActivityFeedItem], *, highlight: bool = False) -> str:
    if not items:
        return ""
    items_html = []
    for item in items:
        when = format_activity_display_time(item.timestamp)
        css_class = "cc-feed-item"
        if highlight or item.is_highlight:
            css_class += " cc-feed-item-highlight"
        if item.is_rollup:
            css_class += " cc-feed-item-rollup"
        items_html.append(
            f'<li class="{css_class}"><div class="cc-feed-meta">{html.escape(item.app_label)}'
            f'{f" · {html.escape(when)}" if when else ""}</div>{html.escape(item.message)}</li>'
        )
    return f'<ul class="cc-feed-list">{"".join(items_html)}</ul>'


def _render_recent_activity_feed() -> None:
    st.markdown(
        f'<div class="cc-section-title">{SECTION_ICONS["feed"]} Activity</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="cc-section-sub">What you accomplished across the suite — milestones first, '
        "then a chronological feed with rollups for repeated work.</div>",
        unsafe_allow_html=True,
    )

    dashboard = build_activity_dashboard(load_all_events())
    if not dashboard.today_summaries and not dashboard.highlights and not dashboard.recent:
        st.markdown(
            '<div class="cc-empty-box">No meaningful actions logged yet. Use your apps locally (sibling repos '
            "side-by-side) or add a cloud activity backend for Streamlit Cloud sync.</div>",
            unsafe_allow_html=True,
        )
        return

    blocks: list[str] = []
    if dashboard.today_summaries:
        summary_lines = "".join(
            f'<div class="cc-today-work-item">· {html.escape(line)}</div>'
            for line in dashboard.today_summaries
        )
        blocks.append(
            f'<div class="cc-today-work"><div class="cc-today-work-title">Today\'s Work</div>{summary_lines}</div>'
        )

    if dashboard.highlights:
        blocks.append('<div class="cc-feed-section-label">Highlights</div>')
        blocks.append(_render_feed_items(dashboard.highlights, highlight=True))

    if dashboard.recent:
        blocks.append('<div class="cc-feed-section-label">Recent Activity</div>')
        blocks.append(_render_feed_items(dashboard.recent))

    _render_unsafe_html("".join(blocks))


def _render_cross_app_section(snapshot: ActivitySnapshot) -> None:
    """Suite-wide focus — cross-app patterns, not per-app navigation."""
    insights = generate_cross_app_insights(snapshot)
    if not insights:
        return
    st.markdown(
        '<div class="cc-section-title">🧭 Suite focus</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="cc-section-sub">How your week connects across apps — not a click count.</div>',
        unsafe_allow_html=True,
    )
    for item in insights:
        st.markdown(
            f'<div class="cc-insight-card" style="border-left-color:#0ea5e9;margin-bottom:0.5rem;">'
            f'<p class="cc-insight-text">{html.escape(item.message)}</p></div>',
            unsafe_allow_html=True,
        )


def _render_weekly_summary(snapshot: ActivitySnapshot) -> None:
    st.markdown(
        f'<div class="cc-section-title">{SECTION_ICONS["weekly"]} Weekly Summary</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="cc-section-sub">Accomplishments this week — meaningful work only.</div>',
        unsafe_allow_html=True,
    )

    summary = get_weekly_summary(snapshot)
    lines = weekly_accomplishment_lines(summary)
    if not lines:
        st.markdown(
            '<div class="cc-empty-box">No accomplishments logged this week yet. Practice, verify a chart, '
            "or run an analysis to see your progress here.</div>",
            unsafe_allow_html=True,
        )
        return

    items_html = "".join(
        f"<li class='cc-feed-item'>{html.escape(count)} {html.escape(label)}</li>"
        for count, label in lines
    )
    _render_unsafe_html(
        f"<p style='margin:0 0 0.35rem 0;font-weight:700;color:#334155;'>This week</p>"
        f"<ul class='cc-feed-list'>{items_html}</ul>"
    )


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
continue_cards = continue_cards_for_snapshot(snapshot, limit=6)
connections = _cached_connections()

_render_hero(snapshot)
_render_continue_section(snapshot, continue_cards)
_render_cross_app_section(snapshot)
_render_coach_insights(insights)
_render_recent_activity_feed()
_render_weekly_summary(snapshot)
_render_app_directory(snapshot)

with st.expander("Deployment & link audit (admin)"):
    from activity_diagnostics import run_live_activity_diagnostics
    from activity_feed import APP_LABELS

    diag = run_live_activity_diagnostics()
    probe = diag.secrets_probe
    try:
        from suite_account import account_summary

        acct = account_summary()
        st.markdown("#### Unified account memory")
        st.markdown(
            f"| Field | Value |\n|---|---|\n"
            f"| **Account id** | `{acct['external_id']}` |\n"
            f"| **Storage user** | `{acct['user_id'][:36]}…` |\n"
            f"| **Sync mode** | **{acct['mode']}** |\n"
            f"| Display name | {html.escape(acct['display_name'])} |"
        )
        st.caption(
            "Use the same `suite_user_id` in [suite_activity] secrets on phone, laptop, and every suite app. "
            "Run `supabase/migrations/002_suite_account_memory.sql` after migration 001."
        )
    except Exception:
        pass
    st.markdown("#### Live activity diagnostics (Supabase ↔ Command Center)")
    if probe is not None:
        st.markdown("##### Secrets detection (values never shown)")
        st.markdown(
            f"| Check | Result |\n|---|---|\n"
            f"| `st.secrets` available | {probe.streamlit_secrets_available} |\n"
            f"| **`[suite_activity]` section found** | **{probe.suite_activity_section_found}** |\n"
            f"| **`supabase_url` found** | **{probe.supabase_url_found}** |\n"
            f"| **`supabase_key` found** | **{probe.supabase_key_found}** |\n"
            f"| Top-level `supabase_url` (fallback) | {probe.top_level_url_found} |\n"
            f"| Top-level `supabase_key` (fallback) | {probe.top_level_key_found} |\n"
            f"| Env `SUITE_SUPABASE_URL` set | {probe.env_supabase_url_set} |\n"
            f"| Env `SUITE_SUPABASE_KEY` set | {probe.env_supabase_key_set} |\n"
            f"| Resolved source | `{probe.resolved_source}` |"
        )
        if probe.secrets_error:
            st.warning(probe.secrets_error)
        from suite_storage_config import EXPECTED_SECRETS_TOML

        st.markdown("##### Expected Streamlit Cloud Secrets (paste exactly)")
        st.code(EXPECTED_SECRETS_TOML, language="toml")
        st.caption(
            "Streamlit Cloud → this Command Center app → Settings → Secrets. "
            "Save, then Reboot app. Same block must be on Music and other suite apps."
        )
    st.markdown(
        f"| Check | Result |\n|---|---|\n"
        f"| Deployment mode | `{diag.deployment_mode}` |\n"
        f"| **Supabase configured** | **{diag.cloud_storage_configured}** |\n"
        f"| **Supabase reachable** | **{diag.cloud_storage_reachable}** |\n"
        f"| Supabase event count | {diag.supabase_event_count} |\n"
        f"| Command Center event count | {diag.command_center_event_count} |\n"
        f"| Verified in Recent Activity format | {diag.verified_in_feed} |\n"
        f"| Pipeline status | **{diag.failure_step}** |"
    )
    if diag.supabase_error:
        st.error(f"Supabase read error: {diag.supabase_error}")
    st.info(diag.recommendation)

    st.markdown("##### Event count by app")
    app_cols = st.columns(2)
    with app_cols[0]:
        st.caption("Supabase (direct)")
        if diag.counts_by_app_supabase:
            st.table(
                [{"app": k, "count": v} for k, v in sorted(diag.counts_by_app_supabase.items())]
            )
        else:
            st.write("—")
    with app_cols[1]:
        st.caption("Command Center (`load_all_events`)")
        if diag.counts_by_app_command_center:
            st.table(
                [
                    {"app": k, "count": v}
                    for k, v in sorted(diag.counts_by_app_command_center.items())
                ]
            )
        else:
            st.write("—")

    st.markdown("##### Most recent event by app")
    recent_cols = st.columns(2)
    with recent_cols[0]:
        st.caption("Supabase")
        for app in sorted(diag.last_event_by_app_supabase):
            label = APP_LABELS.get(app, app)
            st.text(f"{label}: {diag.last_event_by_app_supabase[app]}")
    with recent_cols[1]:
        st.caption("Command Center")
        for app in sorted(diag.last_event_by_app_command_center):
            label = APP_LABELS.get(app, app)
            st.text(f"{label}: {diag.last_event_by_app_command_center[app]}")

    st.markdown("##### Phase A — Music event verification")
    st.dataframe(
        [
            {
                "Event": row.event_type,
                "In Supabase": row.in_supabase,
                "CC reads row": row.in_command_center,
                "Recent Activity preview": row.feed_preview,
                "Latest": row.latest_timestamp,
            }
            for row in diag.phase_a_music
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("##### Phase A — Investment event verification")
    st.dataframe(
        [
            {
                "Event": row.event_type,
                "In Supabase": row.in_supabase,
                "CC reads row": row.in_command_center,
                "Recent Activity preview": row.feed_preview,
                "Latest": row.latest_timestamp,
            }
            for row in diag.phase_a_investment
        ],
        use_container_width=True,
        hide_index=True,
    )

    for title, rows in (
        ("Baseball", diag.phase_a_baseball),
        ("NBA", diag.phase_a_nba),
        ("Applied Intelligence", diag.phase_a_applied),
        ("Future Lens", diag.phase_a_future_lens),
    ):
        st.markdown(f"##### Phase A — {title} event verification")
        st.dataframe(
            [
                {
                    "Event": row.event_type,
                    "In Supabase": row.in_supabase,
                    "CC reads row": row.in_command_center,
                    "Recent Activity preview": row.feed_preview,
                    "Latest": row.latest_timestamp,
                }
                for row in rows
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("##### Last 10 raw events (Supabase)")
    for raw in diag.last_10_raw_supabase or ["—"]:
        st.code(raw, language="json")
    st.markdown("##### Last 10 raw events (Command Center)")
    for raw in diag.last_10_raw_command_center or ["—"]:
        st.code(raw, language="json")

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
