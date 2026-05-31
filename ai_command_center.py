"""
Daniel AI Command Center — personal dashboard for the Daniel AI Suite.

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

from activity_store import get_activity_rows, load_activity_snapshot
from app_registry import APP_DEFINITIONS, get_app_url, verify_connections
from app_urls import BUILD_VERSION, HOMEPAGE_DEV_URL, HOMEPAGE_PRODUCTION_URL
from coach_engine import generate_coach_insights

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
    .block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 960px; }
    #MainMenu, footer { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent; }
    .cc-hero {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        border-radius: 16px; padding: 1.25rem 1.5rem; margin-bottom: 1.25rem; color: white;
    }
    .cc-hero h1 { margin: 0; font-size: 1.6rem; font-weight: 800; }
    .cc-hero p { margin: 0.35rem 0 0; opacity: 0.9; font-size: 0.88rem; }
    .cc-section-title { font-size: 1.15rem; font-weight: 800; color: #0f172a; margin: 1.25rem 0 0.25rem; }
    .cc-section-sub { color: #64748b; font-size: 0.85rem; margin-bottom: 0.75rem; }
    .cc-insight {
        background: white; border: 1px solid #e2e8f0; border-left: 4px solid #6366f1;
        border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 0.45rem;
        color: #1e293b; font-size: 0.92rem; line-height: 1.45;
    }
    .cc-directory-row {
        background: white; border: 1px solid #e2e8f0; border-radius: 10px;
        padding: 0.75rem 1rem; margin-bottom: 0.45rem;
    }
    .cc-directory-name { font-weight: 700; color: #0f172a; font-size: 0.93rem; }
    .cc-directory-desc { color: #64748b; font-size: 0.8rem; margin-top: 0.15rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


def _render_go_button(label: str, url: str, key: str) -> None:
    cleaned = url.strip()
    if cleaned:
        st.link_button(label, cleaned, use_container_width=True, key=key)
    else:
        st.caption("Not connected")


def _render_coach_insights(insights) -> None:
    st.markdown('<div class="cc-section-title">Coach Insights</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="cc-section-sub">Personalized next steps — recommendations only, no launch buttons here.</div>',
        unsafe_allow_html=True,
    )
    if not insights:
        st.caption("No coach insights right now. Activity will drive recommendations as you use your apps.")
        return
    for insight in insights:
        icon = APP_ICONS.get(insight.key, insight.icon)
        st.markdown(
            f'<div class="cc-insight">{icon} {html.escape(insight.message)}</div>',
            unsafe_allow_html=True,
        )


def _render_activity_summary(snapshot) -> None:
    st.markdown('<div class="cc-section-title">Activity Summary</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="cc-section-sub">What you actually did recently — facts only, no recommendations.</div>',
        unsafe_allow_html=True,
    )
    st.dataframe(get_activity_rows(snapshot), use_container_width=True, hide_index=True)
    if not snapshot.has_real_data:
        st.caption(
            "Music practice logs load automatically when available. Other apps will populate this "
            "table as cross-app tracking is wired in."
        )


def _render_app_directory() -> None:
    st.markdown('<div class="cc-section-title">App Directory</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="cc-section-sub">All suite apps — what each does, and a launch button.</div>',
        unsafe_allow_html=True,
    )
    for app in APP_DEFINITIONS:
        url = get_app_url(app.key)
        icon = APP_ICONS.get(app.key, app.icon)
        cols = st.columns([5, 1], gap="small")
        with cols[0]:
            st.markdown(
                f"""
                <div class="cc-directory-row">
                    <div class="cc-directory-name">{icon} {html.escape(app.name)}</div>
                    <div class="cc-directory-desc">{html.escape(app.description)} · {app.branch}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with cols[1]:
            _render_go_button("Go to App", url, f"dir_{app.key}")


@st.cache_data(ttl=300, show_spinner=False)
def _cached_connections():
    return verify_connections()


snapshot = load_activity_snapshot()
insights = generate_coach_insights(snapshot)
connections = _cached_connections()

st.markdown(
    f"""
    <div class="cc-hero">
        <h1>Daniel AI Command Center</h1>
        <p>Build {BUILD_VERSION} · {'Live activity' if snapshot.has_real_data else 'Waiting for activity data'}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

_render_coach_insights(insights)
_render_activity_summary(snapshot)
_render_app_directory()

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

st.caption(f"Daniel AI Command Center · {datetime.now().strftime('%B %d, %Y')} · build {BUILD_VERSION}")
