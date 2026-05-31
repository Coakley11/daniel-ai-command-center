"""
Daniel AI Command Center — friendly home hub for the Daniel AI Suite.

Standalone Streamlit prototype. Does not modify or import from sibling apps.

Future integration points (wire up when ready):
  - Shared activity database (SQLite/Postgres): last_used, session counts, weekly hours
  - Shared AI recommendation engine: Today's Briefing, Coach Summary, cross-app tips
  - Cross-app reports: weekly digest PDF/email, portfolio + practice + sports rollup
  - Notifications and reminders: push, email, in-dashboard alerts by app priority
  - Usage tracking: per-app open events, time-on-task, streaks, goal completion

Run: streamlit run ai_command_center.py
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import streamlit as st

from app_registry import (
    APP_DEFINITIONS,
    BASEBALL_APP_URL,
    BASEBALL_GITHUB_URL,
    BASEBALL_STREAMLIT_URL,
    FUTURE_LENS_APP_URL,
    FUTURE_LENS_GITHUB_URL,
    FUTURE_LENS_STREAMLIT_URL,
    INVESTMENT_APP_URL,
    INVESTMENT_GITHUB_URL,
    INVESTMENT_STREAMLIT_URL,
    MATH_APP_URL,
    MATH_GITHUB_URL,
    MATH_STREAMLIT_URL,
    MUSIC_APP_URL,
    MUSIC_GITHUB_URL,
    MUSIC_STREAMLIT_URL,
    NBA_APP_URL,
    NBA_GITHUB_URL,
    NBA_STREAMLIT_URL,
    AppStatus,
    ConnectionStatus,
    get_app_url,
    verify_connections,
)

# Re-export for easy editing in one place (app_registry.py)
FUTURE_LENS_URL = FUTURE_LENS_APP_URL

APP_THEMES: dict[str, dict[str, str]] = {
    "music": {"accent": "#a855f7", "bg": "#faf5ff", "border": "#e9d5ff", "emoji": "🎵"},
    "investment": {"accent": "#0d9488", "bg": "#f0fdfa", "border": "#99f6e4", "emoji": "📊"},
    "baseball": {"accent": "#16a34a", "bg": "#f0fdf4", "border": "#bbf7d0", "emoji": "⚾"},
    "nba": {"accent": "#ea580c", "bg": "#fff7ed", "border": "#fed7aa", "emoji": "🏀"},
    "math": {"accent": "#2563eb", "bg": "#eff6ff", "border": "#bfdbfe", "emoji": "🧮"},
    "future_lens": {"accent": "#7c3aed", "bg": "#f5f3ff", "border": "#ddd6fe", "emoji": "🔮"},
}

STATUS_STYLES: dict[AppStatus, dict[str, str]] = {
    "Active": {"bg": "#dcfce7", "text": "#166534", "border": "#86efac"},
    "Prototype": {"bg": "#dbeafe", "text": "#1e40af", "border": "#93c5fd"},
    "Needs Connection": {"bg": "#fef9c3", "text": "#854d0e", "border": "#fde047"},
    "Coming Soon": {"bg": "#f1f5f9", "text": "#475569", "border": "#cbd5e1"},
}

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Daniel AI Command Center",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Styles ────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    :root {
        --cc-text: #1e293b;
        --cc-muted: #64748b;
        --cc-bg: #f8fafc;
    }
    .stApp {
        background: linear-gradient(180deg, #fff7ed 0%, #f8fafc 18%, #f0f9ff 100%);
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2.5rem;
        max-width: 1200px;
    }
    #MainMenu, footer { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent; }

    .cc-hero {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 45%, #ec4899 100%);
        border-radius: 24px;
        padding: 2rem 2.2rem;
        margin-bottom: 1.25rem;
        color: white;
        box-shadow: 0 16px 40px rgba(99, 102, 241, 0.25);
    }
    .cc-hero h1 {
        margin: 0 0 0.35rem 0;
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.02em;
    }
    .cc-hero p {
        margin: 0;
        font-size: 1.05rem;
        line-height: 1.55;
        opacity: 0.95;
        max-width: 720px;
    }
    .cc-hero-tag {
        display: inline-block;
        background: rgba(255,255,255,0.2);
        border: 1px solid rgba(255,255,255,0.35);
        border-radius: 999px;
        padding: 0.25rem 0.75rem;
        font-size: 0.78rem;
        font-weight: 600;
        margin-bottom: 0.75rem;
    }

    .cc-start-here {
        background: white;
        border: 2px solid #c4b5fd;
        border-radius: 20px;
        padding: 1.35rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 24px rgba(99, 102, 241, 0.1);
    }
    .cc-start-title {
        font-size: 1.45rem;
        font-weight: 800;
        color: #4c1d95;
        margin-bottom: 0.25rem;
    }
    .cc-start-sub {
        color: #64748b;
        font-size: 0.95rem;
        margin-bottom: 0.75rem;
    }

    .cc-action-card {
        background: white;
        border-radius: 16px;
        padding: 1rem 1.1rem;
        margin-bottom: 0.65rem;
        border-left: 5px solid;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
        height: 100%;
    }
    .cc-action-icon { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .cc-action-title {
        font-size: 1rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.25rem;
    }
    .cc-action-why {
        font-size: 0.88rem;
        color: #64748b;
        line-height: 1.45;
        margin: 0;
    }

    .cc-coach-bubble {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border: 1px solid #fcd34d;
        border-radius: 18px;
        padding: 1.1rem 1.25rem;
        margin-bottom: 1rem;
        color: #78350f;
        font-size: 1rem;
        line-height: 1.55;
    }
    .cc-coach-label {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #b45309;
        margin-bottom: 0.35rem;
    }

    .cc-app-card {
        border-radius: 18px;
        padding: 1.15rem 1.2rem 0.25rem;
        height: 100%;
        min-height: 320px;
        box-shadow: 0 6px 20px rgba(15, 23, 42, 0.07);
        border: 1px solid;
    }
    .cc-app-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 0.5rem;
        margin-bottom: 0.35rem;
    }
    .cc-app-icon { font-size: 2rem; }
    .cc-status-badge {
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        border-radius: 999px;
        padding: 0.2rem 0.55rem;
        border: 1px solid;
        white-space: nowrap;
    }
    .cc-app-name {
        font-size: 1.05rem;
        font-weight: 800;
        color: #1e293b;
        margin-bottom: 0.3rem;
    }
    .cc-app-desc {
        color: #64748b;
        font-size: 0.88rem;
        line-height: 1.45;
        margin-bottom: 0.55rem;
    }
    .cc-meta {
        font-size: 0.78rem;
        color: #94a3b8;
        margin-bottom: 0.15rem;
    }
    .cc-why-box {
        border-radius: 10px;
        padding: 0.55rem 0.7rem;
        margin: 0.5rem 0 0.65rem;
        font-size: 0.82rem;
        line-height: 1.4;
    }
    .cc-why-label {
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.15rem;
    }
    .cc-next-box {
        border-radius: 10px;
        padding: 0.55rem 0.7rem;
        margin-bottom: 0.5rem;
        font-size: 0.84rem;
        line-height: 1.4;
        font-weight: 600;
    }

    .cc-section-title {
        font-size: 1.35rem;
        font-weight: 800;
        color: #1e293b;
        margin: 0.5rem 0 0.35rem 0;
    }
    .cc-section-sub {
        color: #64748b;
        font-size: 0.92rem;
        margin-bottom: 1rem;
    }
    .cc-vision-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.25rem 1.4rem;
        margin-bottom: 0.75rem;
    }
    .cc-vision-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.6rem;
    }
    @media (max-width: 768px) {
        .cc-vision-grid { grid-template-columns: 1fr 1fr; }
    }
    .cc-vision-item {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 0.65rem 0.8rem;
        font-size: 0.88rem;
        color: #334155;
        font-weight: 600;
    }
    .cc-week-chip {
        display: inline-block;
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 0.65rem 0.9rem;
        margin: 0 0.5rem 0.5rem 0;
        font-size: 0.88rem;
        color: #334155;
    }
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 0.65rem 0.85rem;
        box-shadow: 0 2px 8px rgba(15,23,42,0.04);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 0.5rem; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px 12px 0 0;
        padding: 0.6rem 1.1rem;
        font-weight: 600;
    }
    .cc-launch-row {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.55rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
    }
    .cc-launch-text {
        font-size: 0.95rem;
        color: #1e293b;
        font-weight: 600;
        line-height: 1.4;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Placeholder activity snapshot (replace via shared activity DB later) ──────


@dataclass
class ActivitySnapshot:
    """Demo fields that drive cross-app recommendations."""

    last_music_practice_days_ago: int = 3
    last_portfolio_check_days_ago: int = 7
    is_sunday_lineup_day: bool = datetime.now().weekday() == 6
    last_baseball_review_days_ago: int = 2
    nba_game_today: bool = True
    nba_playoffs_active: bool = True
    math_build_sessions_this_week: int = 2
    last_future_lens_days_ago: int = 9
    music_hours_this_week: float = 4.0


@dataclass(frozen=True)
class ActionItem:
    key: str
    icon: str
    title: str
    reason: str
    url: str
    priority: int


@dataclass(frozen=True)
class AppCard:
    key: str
    name: str
    icon: str
    description: str
    url: str
    status: AppStatus
    last_checked: str
    next_action: str
    why_it_matters: str
    button_label: str


@dataclass(frozen=True)
class CoachMessage:
    text: str


def _effective_status(app: AppCard) -> AppStatus:
    if app.status == "Coming Soon":
        return "Coming Soon"
    if not app.url.strip():
        return "Needs Connection"
    return app.status


def _status_badge_html(status: AppStatus) -> str:
    style = STATUS_STYLES[status]
    return (
        f'<span class="cc-status-badge" style="background:{style["bg"]};'
        f'color:{style["text"]};border-color:{style["border"]};">{status}</span>'
    )


def _url_for_key(key: str, connections: list[ConnectionStatus] | None = None) -> str:
    return get_app_url(key, connections)


def generate_recommendations(
    snapshot: ActivitySnapshot,
    connections: list[ConnectionStatus] | None = None,
) -> list[ActionItem]:
    """
    Cross-app coordination logic using placeholder activity fields.
    Replace with shared AI recommendation engine + activity DB later.
    """
    items: list[ActionItem] = []

    if snapshot.is_sunday_lineup_day:
        items.append(ActionItem(
            key="baseball",
            icon="⚾",
            title="Review fantasy baseball lineups",
            reason="It's Sunday — lineups may need a last-minute swap before games start.",
            url=_url_for_key("baseball", connections),
            priority=1,
        ))

    if snapshot.last_portfolio_check_days_ago >= 5:
        items.append(ActionItem(
            key="investment",
            icon="📊",
            title="Review portfolio health",
            reason=(
                f"Your portfolio hasn't been checked in {snapshot.last_portfolio_check_days_ago} days. "
                "A quick risk review keeps you on track."
            ),
            url=_url_for_key("investment", connections),
            priority=2,
        ))

    if snapshot.last_music_practice_days_ago >= 2:
        items.append(ActionItem(
            key="music",
            icon="🎵",
            title="Practice Piano Man for 20 minutes",
            reason=(
                f"You haven't practiced in {snapshot.last_music_practice_days_ago} days. "
                "Even 20 minutes keeps your momentum going!"
            ),
            url=_url_for_key("music", connections),
            priority=3,
        ))

    if snapshot.nba_game_today or snapshot.nba_playoffs_active:
        nba_reason = (
            "Knicks game today — check matchups, injuries, and the live game center."
            if snapshot.nba_game_today
            else "NBA playoffs are active — check the Live Game Center."
        )
        items.append(ActionItem(
            key="nba",
            icon="🏀",
            title="Check Knicks / NBA matchup",
            reason=nba_reason,
            url=_url_for_key("nba", connections),
            priority=4,
        ))

    if snapshot.math_build_sessions_this_week < 3:
        items.append(ActionItem(
            key="math",
            icon="🧮",
            title="Test one new Math Intelligence feature",
            reason=(
                f"You've logged {snapshot.math_build_sessions_this_week} math sessions this week. "
                "Try adding one new applied problem."
            ),
            url=_url_for_key("math", connections),
            priority=5,
        ))

    if snapshot.last_future_lens_days_ago >= 7:
        items.append(ActionItem(
            key="future_lens",
            icon="🔮",
            title="Explore one Future Lens scenario",
            reason="It's been a while since you looked ahead — explore how AI may change your world.",
            url=_url_for_key("future_lens", connections),
            priority=6,
        ))

    items.sort(key=lambda x: x.priority)
    return items[:5]


def generate_coach_messages(snapshot: ActivitySnapshot) -> list[CoachMessage]:
    """Daily Coach voice — friendly assistant nudges from placeholder data."""
    messages: list[CoachMessage] = []

    if snapshot.last_music_practice_days_ago >= 2:
        messages.append(CoachMessage(
            text=f"🎵 You haven't practiced music in {snapshot.last_music_practice_days_ago} days — "
            "how about one quick song today?"
        ))
    if snapshot.is_sunday_lineup_day:
        messages.append(CoachMessage(
            text="⚾ It's Sunday, so fantasy baseball lineups may need attention before first pitch."
        ))
    if snapshot.last_portfolio_check_days_ago >= 5:
        messages.append(CoachMessage(
            text="📊 Your portfolio has not been checked recently — a 10-minute review goes a long way."
        ))
    if snapshot.nba_game_today:
        messages.append(CoachMessage(
            text="🏀 Knicks game today! Peek at matchups and injuries before tip-off."
        ))
    elif snapshot.nba_playoffs_active:
        messages.append(CoachMessage(
            text="🏀 NBA playoffs are active — open the Live Game Center for matchup context."
        ))
    messages.append(CoachMessage(
        text="✨ Pick one small task below and complete it today — that's a win!"
    ))
    return messages


NEXT_ACTIONS: dict[str, str] = {
    "music": "Play Piano Man for 20 minutes.",
    "investment": "Run a quick portfolio health check.",
    "baseball": "Review Sunday lineups and swap any risky starters.",
    "nba": "Check today's Knicks matchup and injury report.",
    "math": "Add or test one new applied problem.",
    "future_lens": "Preview one 10-year AI scenario.",
}

LAST_CHECKED: dict[str, str] = {
    "music": "3 days ago",
    "investment": "7 days ago",
    "baseball": "2 days ago",
    "nba": "4 days ago",
    "math": "1 day ago",
    "future_lens": "9 days ago",
}


def _build_app_cards(connections: list[ConnectionStatus]) -> list[AppCard]:
    cards: list[AppCard] = []
    for app in APP_DEFINITIONS:
        cards.append(
            AppCard(
                key=app.key,
                name=app.name,
                icon=app.icon,
                description=app.description,
                url=get_app_url(app.key, connections),
                status=app.status,
                last_checked=LAST_CHECKED.get(app.key, "—"),
                next_action=NEXT_ACTIONS.get(app.key, "Open the app and take one small step."),
                why_it_matters=app.why_it_matters,
                button_label=app.button_label,
            )
        )
    return cards


def _render_go_button(label: str, url: str, key: str, coming_soon: bool = False) -> None:
    if url.strip() and not coming_soon:
        st.link_button(label, url, use_container_width=True, key=key)
    else:
        st.button(label, disabled=True, use_container_width=True, key=key)
        st.caption("Link not connected yet." if not coming_soon else "Coming soon!")


OPEN_LABELS: dict[str, str] = {
    "music": "Open Music App",
    "investment": "Open Investment App",
    "baseball": "Open Baseball App",
    "nba": "Open NBA App",
    "math": "Open Math App",
    "future_lens": "Open Future Lens",
}


def _render_action_card(action: ActionItem, accent: str, col_key: str) -> None:
    st.markdown(
        f"""
        <div class="cc-action-card" style="border-left-color:{accent};">
            <div class="cc-action-icon">{action.icon}</div>
            <div class="cc-action-title">{action.title}</div>
            <p class="cc-action-why">{action.reason}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    coming_soon = action.key == "future_lens"
    open_label = OPEN_LABELS.get(action.key, "Go to app →")
    _render_go_button(open_label, action.url, f"go_{col_key}", coming_soon=coming_soon)


def _render_app_card(app: AppCard) -> None:
    theme = APP_THEMES[app.key]
    status = _effective_status(app)
    st.markdown(
        f"""
        <div class="cc-app-card" style="background:{theme['bg']};border-color:{theme['border']};">
            <div class="cc-app-header">
                <div class="cc-app-icon">{app.icon}</div>
                {_status_badge_html(status)}
            </div>
            <div class="cc-app-name">{app.name}</div>
            <div class="cc-app-desc">{app.description}</div>
            <div class="cc-meta">Last checked · {app.last_checked}</div>
            <div class="cc-why-box" style="background:white;border:1px solid {theme['border']};color:#475569;">
                <div class="cc-why-label" style="color:{theme['accent']};">Why it matters</div>
                {app.why_it_matters}
            </div>
            <div class="cc-next-box" style="background:white;border:1px solid {theme['border']};color:{theme['accent']};">
                👉 {app.next_action}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    coming_soon = status == "Coming Soon"
    _render_go_button(app.button_label, app.url, f"app_{app.key}", coming_soon=coming_soon)


def _render_launch_workspace(actions: list[ActionItem]) -> None:
    st.markdown(
        '<div class="cc-section-title">🚀 Launch Workspace</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="cc-section-sub">Today\'s recommended actions — pick one and jump straight into the app.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("**Today's Recommended Actions**")

    for i, action in enumerate(actions[:6]):
        cols = st.columns([5, 1], gap="small")
        with cols[0]:
            st.markdown(
                f'<div class="cc-launch-text">{action.icon} {action.title}</div>',
                unsafe_allow_html=True,
            )
        with cols[1]:
            open_label = f"→ {OPEN_LABELS.get(action.key, 'Open')}"
            coming_soon = action.key == "future_lens"
            _render_go_button(open_label, action.url, f"launch_{action.key}_{i}", coming_soon=coming_soon)


def _render_connected_apps_status(connections: list[ConnectionStatus]) -> None:
    st.markdown(
        '<div class="cc-section-title">🔗 Connected Apps Status</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="cc-section-sub">Auto-discovered from your GitHub repos and Streamlit Cloud deployments.</div>',
        unsafe_allow_html=True,
    )

    rows = []
    for conn in connections:
        rows.append(
            {
                "App": conn.name,
                "Connected": "Yes" if conn.connected else "No",
                "Streamlit URL found?": "Yes" if conn.streamlit_found else "No",
                "GitHub URL found?": "Yes" if conn.github_found else "No",
                "Last verified": conn.last_verified,
            }
        )
    st.dataframe(rows, use_container_width=True, hide_index=True)

    with st.expander("View full URLs"):
        for conn in connections:
            st.markdown(f"**{conn.name}**")
            if conn.streamlit_url:
                st.caption(f"Streamlit: {conn.streamlit_url}")
            if conn.github_url:
                st.caption(f"GitHub: {conn.github_url}")
            if conn.open_url:
                st.caption(f"Opens: {conn.open_url}")
            st.divider()


def _render_cross_app_nudges(snapshot: ActivitySnapshot) -> None:
    st.markdown(
        '<div class="cc-section-title">💡 Cross-App Coach Nudges</div>',
        unsafe_allow_html=True,
    )
    nudges: list[str] = []
    if snapshot.is_sunday_lineup_day:
        nudges.append("⚾ It's Sunday — fantasy baseball lineups may need attention.")
    if snapshot.last_music_practice_days_ago >= 2:
        nudges.append("🎵 Practice one song today — you haven't played in a few days.")
    if snapshot.last_portfolio_check_days_ago >= 5:
        nudges.append("📊 Review portfolio health — the Investment App hasn't been visited recently.")
    if snapshot.nba_playoffs_active:
        nudges.append("🏀 NBA playoffs are active — check the Live Game Center.")
    if snapshot.math_build_sessions_this_week < 3:
        nudges.append("🧮 Build or test one math idea to keep your reasoning lab growing.")
    if snapshot.last_future_lens_days_ago >= 7:
        nudges.append("🔮 Explore one Future Lens scenario about how AI may change your work.")
    for nudge in nudges:
        st.info(nudge)


def _render_hero(connected_count: int) -> None:
    st.markdown(
        """
        <div class="cc-hero">
            <div class="cc-hero-tag">👋 Welcome back · Daniel AI Suite</div>
            <h1>🏠 Daniel AI Command Center</h1>
            <p>Your homepage for the entire Daniel AI Suite — see what to do today, which app to open,
            and what needs attention. {connected_count} apps connected right now.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_start_here(actions: list[ActionItem], coach_msgs: list[CoachMessage]) -> None:
    st.markdown(
        """
        <div class="cc-start-here">
            <div class="cc-start-title">✅ What should I do now?</div>
            <div class="cc-start-sub">Pick one action below — your AI coach picked these based on your week.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for msg in coach_msgs[:3]:
        st.markdown(
            f"""
            <div class="cc-coach-bubble">
                <div class="cc-coach-label">Daily Coach</div>
                {msg.text}
            </div>
            """,
            unsafe_allow_html=True,
        )

    if not actions:
        st.info("You're all caught up! Explore an app below or check back tomorrow.")
        return

    cols = st.columns(min(len(actions), 3), gap="medium")
    for col, action in zip(cols, actions[:3]):
        with col:
            accent = APP_THEMES.get(action.key, {}).get("accent", "#6366f1")
            _render_action_card(action, accent, f"top_{action.key}")

    if len(actions) > 3:
        st.markdown("**More ideas for today**")
        extra_cols = st.columns(min(len(actions) - 3, 2), gap="medium")
        for col, action in zip(extra_cols, actions[3:]):
            with col:
                accent = APP_THEMES.get(action.key, {}).get("accent", "#6366f1")
                _render_action_card(action, accent, f"extra_{action.key}")


def _render_home_tab(
    snapshot: ActivitySnapshot,
    actions: list[ActionItem],
    coach_msgs: list[CoachMessage],
    connections: list[ConnectionStatus],
) -> None:
    _render_start_here(actions, coach_msgs)
    _render_launch_workspace(actions)
    _render_cross_app_nudges(snapshot)
    _render_connected_apps_status(connections)

    st.markdown(
        '<div class="cc-section-title">🌈 One personal AI system</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="cc-section-sub">
        Your AI Command Center connects your creative, financial, sports, and intellectual work
        into one weekly operating system — not six separate projects, but one helpful coach.
        </div>
        """,
        unsafe_allow_html=True,
    )

    quick_cols = st.columns(3, gap="medium")
    highlights = [
        ("🎵", "Music", f"{snapshot.music_hours_this_week:.0f} hrs this week"),
        ("⚾", "Baseball", f"Last review {snapshot.last_baseball_review_days_ago}d ago"),
        ("📊", "Portfolio", f"Last check {snapshot.last_portfolio_check_days_ago}d ago"),
    ]
    for col, (emoji, label, detail) in zip(quick_cols, highlights):
        with col:
            st.markdown(
                f"""
                <div class="cc-vision-card" style="text-align:center;">
                    <div style="font-size:2rem;">{emoji}</div>
                    <div style="font-weight:700;color:#1e293b;">{label}</div>
                    <div style="font-size:0.85rem;color:#64748b;">{detail}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_apps_tab(apps: list[AppCard]) -> None:
    st.markdown('<div class="cc-section-title">📱 Your Apps</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="cc-section-sub">Tap an app to jump in — each one has a suggested next step waiting for you.</div>',
        unsafe_allow_html=True,
    )
    for row in (apps[:3], apps[3:]):
        cols = st.columns(3, gap="medium")
        for col, app in zip(cols, row):
            with col:
                _render_app_card(app)


def _render_weekly_coach_tab(snapshot: ActivitySnapshot, actions: list[ActionItem]) -> None:
    st.markdown('<div class="cc-section-title">🧠 Weekly AI Coach</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="cc-section-sub">Your personal advisor for the week — powered by placeholder data for now.</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="cc-coach-bubble">
            <div class="cc-coach-label">This week's vibe</div>
            Hey! You're doing great on baseball ({snapshot.last_baseball_review_days_ago} days since last review)
            but your portfolio check is {snapshot.last_portfolio_check_days_ago} days overdue.
            Music is at {snapshot.music_hours_this_week:.0f} hours this week — nice!
            Pick one small win today and you'll feel on top of everything. 💪
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.markdown("**Needs attention**")
        attention = []
        if snapshot.last_portfolio_check_days_ago >= 5:
            attention.append("📊 Portfolio — overdue for a check-in")
        if snapshot.last_music_practice_days_ago >= 3:
            attention.append(f"🎵 Music — {snapshot.last_music_practice_days_ago} days since practice")
        if snapshot.is_sunday_lineup_day:
            attention.append("⚾ Baseball — Sunday lineup day")
        for item in attention or ["✅ Nothing urgent — keep your streak going!"]:
            st.warning(item)

    with c2:
        st.markdown("**Suggested this week**")
        for i, action in enumerate(actions[:4], start=1):
            st.success(f"{i}. {action.icon} {action.title}")

    st.markdown("**Activity this week**")
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    metrics = [
        (m1, "Music (hrs)", f"{snapshot.music_hours_this_week:.1f}"),
        (m2, "Portfolio checks", "1"),
        (m3, "Baseball reviews", "5"),
        (m4, "NBA sessions", "3"),
        (m5, "Math builds", str(snapshot.math_build_sessions_this_week)),
        (m6, "Future Lens", "1"),
    ]
    for col, label, val in metrics:
        with col:
            st.metric(label, val)


def _render_vision_tab() -> None:
    st.markdown('<div class="cc-section-title">🔭 Platform Vision</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="cc-vision-card">
            <p style="color:#475569;line-height:1.65;margin:0 0 1rem 0;">
            The <strong>Daniel AI Suite</strong> is one integrated AI ecosystem — six specialized apps
            connected by this Command Center. Music, money, sports, math, and future-thinking all
            feed into one weekly operating system that helps you decide what matters most today.
            </p>
            <div class="cc-vision-grid">
                <div class="cc-vision-item">🎵 Music Practice Coach</div>
                <div class="cc-vision-item">📊 Investment Portfolio Analyzer</div>
                <div class="cc-vision-item">⚾ Baseball Analytics</div>
                <div class="cc-vision-item">🏀 NBA Playoff Companion</div>
                <div class="cc-vision-item">🧮 Advanced Math Intelligence</div>
                <div class="cc-vision-item">🔮 Future Lens</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("**How it fits together**")
    pillars = [
        ("🎨 Creative", "Music App — practice, learn, perform"),
        ("💰 Financial", "Investment App — track, analyze, decide"),
        ("🏆 Sports", "Baseball + NBA — lineups, matchups, live insights"),
        ("🧠 Intellectual", "Math App — build reasoning skills"),
        ("🚀 Future", "Future Lens — explore what's coming next"),
    ]
    pcols = st.columns(5, gap="small")
    for col, (title, desc) in zip(pcols, pillars):
        with col:
            st.markdown(
                f"""
                <div class="cc-vision-card" style="text-align:center;padding:0.9rem;">
                    <div style="font-weight:800;color:#1e293b;margin-bottom:0.25rem;">{title}</div>
                    <div style="font-size:0.78rem;color:#64748b;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.caption(
        "Future: shared activity database · AI recommendation engine · cross-app reports · "
        "notifications · usage tracking"
    )


# ── Main layout ───────────────────────────────────────────────────────────────


@st.cache_data(ttl=300, show_spinner=False)
def _cached_connections() -> list[ConnectionStatus]:
    return verify_connections()


connections = _cached_connections()
snapshot = ActivitySnapshot()
apps = _build_app_cards(connections)
actions = generate_recommendations(snapshot, connections)
coach_msgs = generate_coach_messages(snapshot)
connected_count = sum(1 for c in connections if c.connected)

_render_hero(connected_count)

tab_home, tab_apps, tab_coach, tab_vision = st.tabs(
    ["🏠 Home / Today", "📱 Apps", "🧠 Weekly Coach", "🔭 Platform Vision"]
)

with tab_home:
    _render_home_tab(snapshot, actions, coach_msgs, connections)

with tab_apps:
    _render_apps_tab(apps)

with tab_coach:
    _render_weekly_coach_tab(snapshot, actions)

with tab_vision:
    _render_vision_tab()

st.caption(
    f"Daniel AI Command Center · Daniel AI Suite · {datetime.now().strftime('%B %d, %Y')} · "
    "activity data is demo/placeholder · app links auto-discovered from GitHub + Streamlit Cloud."
)
