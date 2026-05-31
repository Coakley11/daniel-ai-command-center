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

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

import streamlit as st

# ── App URL placeholders — fill in when each app is deployed ─────────────────
MUSIC_APP_URL = ""
INVESTMENT_APP_URL = ""
BASEBALL_APP_URL = ""
NBA_APP_URL = ""
MATH_APP_URL = ""
FUTURE_LENS_URL = ""

AppStatus = Literal["Active", "Prototype", "Needs Connection", "Coming Soon"]

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
    is_sunday_lineup_day: bool = True
    last_baseball_review_days_ago: int = 2
    nba_game_today: bool = True
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


def _url_for_key(key: str) -> str:
    return {
        "music": MUSIC_APP_URL,
        "investment": INVESTMENT_APP_URL,
        "baseball": BASEBALL_APP_URL,
        "nba": NBA_APP_URL,
        "math": MATH_APP_URL,
        "future_lens": FUTURE_LENS_URL,
    }.get(key, "")


def generate_recommendations(snapshot: ActivitySnapshot) -> list[ActionItem]:
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
            url=BASEBALL_APP_URL,
            priority=1,
        ))

    if snapshot.last_portfolio_check_days_ago >= 5:
        items.append(ActionItem(
            key="investment",
            icon="📊",
            title="Check portfolio health",
            reason=(
                f"Your portfolio hasn't been checked in {snapshot.last_portfolio_check_days_ago} days. "
                "A quick risk review keeps you on track."
            ),
            url=INVESTMENT_APP_URL,
            priority=2,
        ))

    if snapshot.last_music_practice_days_ago >= 2:
        items.append(ActionItem(
            key="music",
            icon="🎵",
            title="Practice one song",
            reason=(
                f"You haven't practiced in {snapshot.last_music_practice_days_ago} days. "
                "Even 20 minutes keeps your momentum going!"
            ),
            url=MUSIC_APP_URL,
            priority=3,
        ))

    if snapshot.nba_game_today:
        items.append(ActionItem(
            key="nba",
            icon="🏀",
            title="Review Knicks / NBA matchup",
            reason="There's a game on today — check matchups, injuries, and the live game center.",
            url=NBA_APP_URL,
            priority=4,
        ))

    if snapshot.math_build_sessions_this_week < 3:
        items.append(ActionItem(
            key="math",
            icon="🧮",
            title="Build or test one math idea",
            reason=(
                f"You've logged {snapshot.math_build_sessions_this_week} math sessions this week. "
                "Try adding one new applied problem."
            ),
            url=MATH_APP_URL,
            priority=5,
        ))

    if snapshot.last_future_lens_days_ago >= 7:
        items.append(ActionItem(
            key="future_lens",
            icon="🔮",
            title="Explore one Future Lens scenario",
            reason="It's been a while since you looked ahead — explore how AI may change your world.",
            url=FUTURE_LENS_URL,
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
    messages.append(CoachMessage(
        text="✨ Pick one small task below and complete it today — that's a win!"
    ))
    return messages


def _placeholder_apps() -> list[AppCard]:
    return [
        AppCard(
            key="music",
            name="Music Practice Coach",
            icon="🎵",
            description="Your AI practice buddy — songs, chords, and progress tracking.",
            url=MUSIC_APP_URL,
            status="Active",
            last_checked="3 days ago",
            next_action="Play Piano Man for 20 minutes.",
            why_it_matters="Keeps your creative skills sharp and makes practice fun.",
            button_label="Go to Music App",
        ),
        AppCard(
            key="investment",
            name="Investment Portfolio Analyzer",
            icon="📊",
            description="See how your money is doing — risk, allocation, and smart next steps.",
            url=INVESTMENT_APP_URL,
            status="Active",
            last_checked="7 days ago",
            next_action="Run a quick portfolio health check.",
            why_it_matters="Stay confident about your financial decisions without overthinking.",
            button_label="Go to Investment App",
        ),
        AppCard(
            key="baseball",
            name="Fantasy Baseball",
            icon="⚾",
            description="Lineups, start/sit picks, and stats when you need an edge.",
            url=BASEBALL_APP_URL,
            status="Active",
            last_checked="2 days ago",
            next_action="Review Sunday lineups and swap any risky starters.",
            why_it_matters="Win more fantasy weeks with data-backed lineup calls.",
            button_label="Go to Baseball App",
        ),
        AppCard(
            key="nba",
            name="NBA Playoff Companion",
            icon="🏀",
            description="Matchups, injuries, and live game insights for basketball fans.",
            url=NBA_APP_URL,
            status="Active",
            last_checked="4 days ago",
            next_action="Check today's Knicks matchup and injury report.",
            why_it_matters="Walk into game day knowing who's playing and who to watch.",
            button_label="Go to NBA App",
        ),
        AppCard(
            key="math",
            name="Advanced Math Intelligence",
            icon="🧮",
            description="Build and test applied math ideas — simulations, puzzles, and reasoning.",
            url=MATH_APP_URL,
            status="Prototype",
            last_checked="1 day ago",
            next_action="Add or test one new applied problem.",
            why_it_matters="Strengthens how you think through real-world quantitative problems.",
            button_label="Go to Math App",
        ),
        AppCard(
            key="future_lens",
            name="Future Lens",
            icon="🔮",
            description="Explore how AI might reshape music, money, sports, and teaching.",
            url=FUTURE_LENS_URL,
            status="Coming Soon",
            last_checked="9 days ago",
            next_action="Preview one 10-year AI scenario.",
            why_it_matters="Helps you adapt early instead of reacting late.",
            button_label="Go to Future Lens",
        ),
    ]


def _render_go_button(label: str, url: str, key: str, coming_soon: bool = False) -> None:
    if url.strip() and not coming_soon:
        st.link_button(label, url, use_container_width=True, key=key)
    else:
        st.button(label, disabled=True, use_container_width=True, key=key)
        st.caption("Link not connected yet." if not coming_soon else "Coming soon!")


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
    _render_go_button("Go to app →", action.url, f"go_{col_key}", coming_soon=coming_soon)


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


def _render_hero() -> None:
    st.markdown(
        """
        <div class="cc-hero">
            <div class="cc-hero-tag">👋 Welcome back!</div>
            <h1>🏠 Daniel AI Command Center</h1>
            <p>Your friendly AI home base — one place to see what to do next across music,
            investing, sports, math, and the future.</p>
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


def _render_home_tab(snapshot: ActivitySnapshot, actions: list[ActionItem], coach_msgs: list[CoachMessage]) -> None:
    _render_start_here(actions, coach_msgs)

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

snapshot = ActivitySnapshot()
apps = _placeholder_apps()
actions = generate_recommendations(snapshot)
coach_msgs = generate_coach_messages(snapshot)

_render_hero()

tab_home, tab_apps, tab_coach, tab_vision = st.tabs(
    ["🏠 Home / Today", "📱 Apps", "🧠 Weekly Coach", "🔭 Platform Vision"]
)

with tab_home:
    _render_home_tab(snapshot, actions, coach_msgs)

with tab_apps:
    _render_apps_tab(apps)

with tab_coach:
    _render_weekly_coach_tab(snapshot, actions)

with tab_vision:
    _render_vision_tab()

st.caption(
    f"Daniel AI Command Center · demo data · {datetime.now().strftime('%B %d, %Y')} · "
    "connect app URLs at the top of this file when ready."
)
