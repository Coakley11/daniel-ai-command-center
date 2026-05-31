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

from activity_store import ActivitySnapshot, format_days_ago, get_activity_rows, load_activity_snapshot
from app_registry import APP_DEFINITIONS, AppStatus, get_app_url, verify_connections
from app_urls import BUILD_VERSION, HOMEPAGE_DEV_URL, HOMEPAGE_PRODUCTION_URL
from coach_engine import CoachInsight, generate_coach_insights

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
    "activity": "📋",
    "apps": "📱",
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
        border-radius: 18px; padding: 1.15rem 1.2rem 0.25rem; height: 100%;
        min-height: 300px; box-shadow: 0 6px 20px rgba(15, 23, 42, 0.07); border: 1px solid;
    }
    .cc-app-header {
        display: flex; justify-content: space-between; align-items: flex-start;
        gap: 0.5rem; margin-bottom: 0.35rem;
    }
    .cc-app-icon { font-size: 2rem; }
    .cc-status-badge {
        font-size: 0.65rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.04em; border-radius: 999px; padding: 0.2rem 0.55rem;
        border: 1px solid; white-space: nowrap;
    }
    .cc-app-name { font-size: 1.05rem; font-weight: 800; color: #1e293b; margin-bottom: 0.3rem; }
    .cc-app-desc { color: #64748b; font-size: 0.88rem; line-height: 1.45; margin-bottom: 0.55rem; }
    .cc-meta { font-size: 0.78rem; color: #94a3b8; margin-bottom: 0.15rem; }
    .cc-why-box {
        border-radius: 10px; padding: 0.55rem 0.7rem; margin: 0.5rem 0 0.65rem;
        font-size: 0.82rem; line-height: 1.4;
    }
    .cc-why-label {
        font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.05em; margin-bottom: 0.15rem;
    }
    .cc-empty-box {
        background: white; border: 1px dashed #cbd5e1; border-radius: 16px;
        padding: 1.25rem 1.5rem; color: #64748b; font-size: 0.92rem; line-height: 1.5;
    }
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


def _render_hero(snapshot: ActivitySnapshot) -> None:
    activity_tag = "Live activity" if snapshot.has_real_data else "Waiting for activity data"
    st.markdown(
        f"""
        <div class="cc-hero">
            <div class="cc-hero-tag">👋 Welcome back</div>
            <h1>🏠 Daniel Cohen AI Command Center</h1>
            <p>Your personal AI dashboard — coach insights, recent activity, and app launchers.
            Build {BUILD_VERSION} · {activity_tag}.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


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


def _render_activity_summary(snapshot: ActivitySnapshot) -> None:
    st.markdown(
        f'<div class="cc-section-title">{SECTION_ICONS["activity"]} Activity Summary</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="cc-section-sub">What you actually did recently — facts only, no recommendations.</div>',
        unsafe_allow_html=True,
    )

    rows = get_activity_rows(snapshot)
    app_keys = [app.key for app in APP_DEFINITIONS]

    for group_start in (0, 3):
        cols = st.columns(3, gap="medium")
        chunk_keys = app_keys[group_start : group_start + 3]
        chunk_rows = rows[group_start : group_start + 3]
        for col, key, row in zip(cols, chunk_keys, chunk_rows):
            theme = APP_THEMES[key]
            has_activity = row["Last activity"] != "No activity yet"
            when_color = theme["accent"] if has_activity else "#94a3b8"
            with col:
                st.markdown(
                    f"""
                    <div class="cc-activity-card" style="background:{theme['bg']};border-color:{theme['border']};">
                        <div class="cc-activity-icon">{theme['emoji']}</div>
                        <div class="cc-activity-name">{html.escape(row['App'])}</div>
                        <div class="cc-activity-when" style="color:{when_color};">
                            {html.escape(row['Last activity'])}
                        </div>
                        <p class="cc-activity-detail">{html.escape(row['Details'])}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    if not snapshot.has_real_data:
        st.markdown(
            '<div class="cc-empty-box" style="margin-top:0.75rem;">'
            "No cross-app activity recorded yet. Music practice logs load automatically when available; "
            "other apps will populate this section as tracking is wired in.</div>",
            unsafe_allow_html=True,
        )


def _last_active_label(snapshot: ActivitySnapshot, key: str) -> str:
    days_map = {
        "music": snapshot.last_music_practice_days_ago,
        "investment": snapshot.last_portfolio_check_days_ago,
        "baseball": snapshot.last_baseball_review_days_ago,
        "nba": snapshot.last_nba_session_days_ago,
        "applied_intelligence": snapshot.last_applied_intelligence_days_ago,
        "future_lens": snapshot.last_future_lens_days_ago,
    }
    days = days_map.get(key)
    if days is None:
        return "No activity recorded yet"
    return f"Last active · {format_days_ago(days)}"


def _render_app_card(app_key: str, snapshot: ActivitySnapshot) -> None:
    app = next(a for a in APP_DEFINITIONS if a.key == app_key)
    theme = APP_THEMES[app.key]
    url = get_app_url(app.key)
    icon = theme["emoji"]

    st.markdown(
        f"""
        <div class="cc-app-card" style="background:{theme['bg']};border-color:{theme['border']};">
            <div class="cc-app-header">
                <div class="cc-app-icon">{icon}</div>
                {_status_badge_html(app.status)}
            </div>
            <div class="cc-app-name">{html.escape(app.name)}</div>
            <div class="cc-app-desc">{html.escape(app.description)}</div>
            <div class="cc-meta">{_last_active_label(snapshot, app.key)} · {app.branch} branch</div>
            <div class="cc-why-box" style="background:white;border:1px solid {theme['border']};color:#475569;">
                <div class="cc-why-label" style="color:{theme['accent']};">Why it matters</div>
                {html.escape(app.why_it_matters)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _render_go_button(app.button_label, url, f"app_{app.key}")


def _render_app_directory(snapshot: ActivitySnapshot) -> None:
    st.markdown(
        f'<div class="cc-section-title">{SECTION_ICONS["apps"]} App Directory</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="cc-section-sub">Launch any app — icons, descriptions, and one-click access.</div>',
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
connections = _cached_connections()

_render_hero(snapshot)
_render_coach_insights(insights)
_render_activity_summary(snapshot)
_render_app_directory(snapshot)

with st.expander("Deployment & link audit (admin)"):
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
