"""
Daniel AI Command Center — personal dashboard for the Daniel AI Suite.

Single-page layout:
  1. Coach Insights — what should I do next?
  2. Activity Summary — what have I been doing recently?
  3. App Directory — launch any app
  4. Projects — suite overview (no duplicate recommendations)

Run: streamlit run ai_command_center.py
"""

from __future__ import annotations

import html
from datetime import datetime

import streamlit as st

from activity_store import ActivitySnapshot, format_days_ago, load_activity_snapshot
from app_registry import APP_DEFINITIONS, get_app_url, verify_connections
from coach_engine import CoachInsight, generate_coach_insights

APP_ICONS: dict[str, str] = {
    "music": "🎵",
    "investment": "📊",
    "baseball": "⚾",
    "nba": "🏀",
    "math": "🧮",
    "future_lens": "🔮",
}

st.set_page_config(
    page_title="Daniel AI Command Center",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .stApp { background: #f8fafc; }
    .block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 980px; }
    #MainMenu, footer { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent; }

    .cc-hero {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        border-radius: 18px;
        padding: 1.5rem 1.75rem;
        margin-bottom: 1.5rem;
        color: white;
    }
    .cc-hero h1 { margin: 0 0 0.25rem 0; font-size: 1.75rem; font-weight: 800; }
    .cc-hero p { margin: 0; opacity: 0.92; font-size: 0.95rem; line-height: 1.5; }

    .cc-section-title {
        font-size: 1.2rem;
        font-weight: 800;
        color: #0f172a;
        margin: 1.5rem 0 0.35rem 0;
    }
    .cc-section-sub {
        color: #64748b;
        font-size: 0.88rem;
        margin-bottom: 0.85rem;
    }

    .cc-insight {
        background: white;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #6366f1;
        border-radius: 12px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.55rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
    }
    .cc-insight-text { color: #1e293b; font-size: 0.92rem; line-height: 1.45; flex: 1; }

    .cc-directory-row {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
    }
    .cc-directory-name { font-weight: 700; color: #0f172a; font-size: 0.95rem; }
    .cc-directory-desc { color: #64748b; font-size: 0.82rem; margin-top: 0.1rem; }

    .cc-project-row {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 0.65rem 0.85rem;
        margin-bottom: 0.4rem;
        font-size: 0.88rem;
        color: #334155;
    }

    .cc-go-button {
        display: inline-block;
        padding: 0.4rem 0.85rem;
        background: #ef4444;
        color: white !important;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 600;
        font-size: 0.82rem;
        white-space: nowrap;
    }
    .cc-go-button:hover { background: #dc2626; }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 0.55rem 0.75rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _render_go_link(label: str, url: str, key: str) -> None:
    cleaned = url.strip()
    if not cleaned:
        st.caption("Not connected")
        return
    st.link_button(label, cleaned, use_container_width=True, key=key)


def _render_hero(snapshot: ActivitySnapshot) -> None:
    source = "live activity" if snapshot.has_real_data else "waiting for activity logs"
    st.markdown(
        f"""
        <div class="cc-hero">
            <h1>Daniel AI Command Center</h1>
            <p>Your personal dashboard — coach insights, recent activity, and app launchers. Data source: {source}.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_coach_insights(insights: list[CoachInsight]) -> None:
    st.markdown('<div class="cc-section-title">Coach Insights</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="cc-section-sub">What should you do next? One suggestion per app — no repeats.</div>',
        unsafe_allow_html=True,
    )
    for insight in insights:
        icon = APP_ICONS.get(insight.key, insight.icon)
        safe_msg = html.escape(insight.message)
        cols = st.columns([6, 1], gap="small")
        with cols[0]:
            st.markdown(
                f'<div class="cc-insight"><div class="cc-insight-text">{icon} {safe_msg}</div></div>',
                unsafe_allow_html=True,
            )
        with cols[1]:
            _render_go_link("Go", insight.url, f"coach_{insight.key}")


def _render_activity_summary(snapshot: ActivitySnapshot) -> None:
    st.markdown('<div class="cc-section-title">Activity Summary</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="cc-section-sub">What you have been doing recently — facts only, no recommendations.</div>',
        unsafe_allow_html=True,
    )

    music_hours = snapshot.music_minutes_this_week / 60.0
    c1, c2, c3 = st.columns(3)
    c4, c5, c6 = st.columns(3)

    with c1:
        st.metric("Music (hrs this week)", f"{music_hours:.1f}" if snapshot.has_real_data else "—")
        st.caption(format_days_ago(snapshot.last_music_practice_days_ago))
    with c2:
        st.metric("Portfolio checks", snapshot.portfolio_checks_this_week or "—")
        st.caption(format_days_ago(snapshot.last_portfolio_check_days_ago))
    with c3:
        st.metric("Baseball reviews", snapshot.baseball_reviews_this_week or "—")
        st.caption(format_days_ago(snapshot.last_baseball_review_days_ago))
    with c4:
        st.metric("Basketball sessions", snapshot.nba_sessions_this_week or "—")
        st.caption(format_days_ago(snapshot.last_nba_session_days_ago))
    with c5:
        st.metric("AI Homeroom sessions", snapshot.math_sessions_this_week or "—")
        st.caption(format_days_ago(snapshot.last_math_session_days_ago))
    with c6:
        st.metric("Future simulations", snapshot.future_simulations_this_week or "—")
        st.caption(format_days_ago(snapshot.last_future_lens_days_ago))

    if snapshot.last_song:
        st.caption(f"Last song practiced: **{snapshot.last_song}**")
    if not snapshot.has_real_data:
        st.info(
            "No cross-app activity logged yet. Use your apps normally — "
            "the Music app writes practice logs automatically; other apps will feed this hub as tracking is added."
        )


def _render_app_directory() -> None:
    st.markdown('<div class="cc-section-title">App Directory</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="cc-section-sub">Launch any app. Navigation only — no recommendations here.</div>',
        unsafe_allow_html=True,
    )

    for app in APP_DEFINITIONS:
        url = get_app_url(app.key)
        icon = APP_ICONS.get(app.key, app.icon)
        safe_name = html.escape(app.name)
        safe_desc = html.escape(app.description)
        cols = st.columns([5, 1], gap="small")
        with cols[0]:
            st.markdown(
                f"""
                <div class="cc-directory-row">
                    <div>
                        <div class="cc-directory-name">{icon} {safe_name}</div>
                        <div class="cc-directory-desc">{safe_desc} · {app.branch}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with cols[1]:
            _render_go_link("Go to App", url, f"app_{app.key}")


def _render_projects() -> None:
    st.markdown('<div class="cc-section-title">Portfolio / Projects</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="cc-section-sub">Apps in the Daniel AI Suite — status overview, not a marketing page.</div>',
        unsafe_allow_html=True,
    )
    for app in APP_DEFINITIONS:
        st.markdown(
            f'<div class="cc-project-row">{APP_ICONS.get(app.key, app.icon)} '
            f"<strong>{html.escape(app.name)}</strong> · {app.status} · {app.branch} branch</div>",
            unsafe_allow_html=True,
        )


@st.cache_data(ttl=300, show_spinner=False)
def _cached_connections():
    return verify_connections()


snapshot = load_activity_snapshot()
insights = generate_coach_insights(snapshot)
connections = _cached_connections()

_render_hero(snapshot)
_render_coach_insights(insights)
_render_activity_summary(snapshot)
_render_app_directory()
_render_projects()

with st.expander("Deployment status (admin)"):
    for conn in connections:
        st.markdown(f"**{conn.name}** — {conn.branch}")
        st.caption(conn.open_url or "Not connected")
        st.caption(
            f"Live: {'Yes' if conn.streamlit_live else 'No'} · "
            f"Verified: {conn.last_verified}"
        )

st.caption(
    f"Daniel AI Command Center · {datetime.now().strftime('%B %d, %Y')} · "
    f"{'Real activity' if snapshot.has_real_data else 'Activity tracking initializing'}"
)
