"""
Daniel AI Command Center — central hub for the Daniel AI Suite.

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

STATUS_STYLES: dict[AppStatus, dict[str, str]] = {
    "Active": {"bg": "rgba(52, 211, 153, 0.15)", "border": "#34d399", "text": "#6ee7b7"},
    "Prototype": {"bg": "rgba(91, 156, 255, 0.15)", "border": "#5b9cff", "text": "#93c5fd"},
    "Needs Connection": {"bg": "rgba(240, 180, 41, 0.15)", "border": "#f0b429", "text": "#fcd34d"},
    "Coming Soon": {"bg": "rgba(148, 163, 184, 0.12)", "border": "#64748b", "text": "#94a3b8"},
}

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Daniel AI Command Center",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Styles ────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    :root {
        --cc-bg: #070b14;
        --cc-surface: #0f1624;
        --cc-surface-2: #151f32;
        --cc-surface-3: #1b2740;
        --cc-border: #243049;
        --cc-text: #eef4ff;
        --cc-muted: #8fa3bf;
        --cc-accent: #5b9cff;
        --cc-accent-2: #8b5cf6;
        --cc-gold: #f0b429;
        --cc-green: #34d399;
    }
    .stApp {
        background: radial-gradient(ellipse at 20% 0%, rgba(91, 156, 255, 0.08) 0%, transparent 55%),
                    radial-gradient(ellipse at 80% 10%, rgba(139, 92, 246, 0.06) 0%, transparent 50%),
                    var(--cc-bg);
    }
    .block-container {
        padding-top: 1.25rem;
        padding-bottom: 3rem;
        max-width: 1440px;
    }
    #MainMenu, footer, header { visibility: hidden; }
    .cc-hero {
        background: linear-gradient(135deg, #0a1220 0%, #121f35 45%, #182845 100%);
        border: 1px solid var(--cc-border);
        border-radius: 20px;
        padding: 2rem 2.25rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.4);
        position: relative;
        overflow: hidden;
    }
    .cc-hero::before {
        content: "";
        position: absolute;
        top: -30%;
        right: -5%;
        width: 320px;
        height: 320px;
        background: radial-gradient(circle, rgba(91, 156, 255, 0.2) 0%, transparent 70%);
        pointer-events: none;
    }
    .cc-hero-badge {
        display: inline-block;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--cc-accent);
        background: rgba(91, 156, 255, 0.12);
        border: 1px solid rgba(91, 156, 255, 0.35);
        border-radius: 999px;
        padding: 0.25rem 0.75rem;
        margin-bottom: 0.75rem;
        font-weight: 600;
    }
    .cc-hero h1 {
        margin: 0 0 0.4rem 0;
        font-size: 2.35rem;
        font-weight: 800;
        color: var(--cc-text);
        letter-spacing: -0.03em;
        line-height: 1.15;
    }
    .cc-hero p {
        margin: 0;
        color: var(--cc-muted);
        font-size: 1.08rem;
        line-height: 1.55;
        max-width: 820px;
    }
    .cc-hero-stats {
        display: flex;
        flex-wrap: wrap;
        gap: 1.25rem;
        margin-top: 1.35rem;
    }
    .cc-stat-pill {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid var(--cc-border);
        border-radius: 12px;
        padding: 0.55rem 1rem;
        min-width: 120px;
    }
    .cc-stat-value {
        font-size: 1.35rem;
        font-weight: 700;
        color: var(--cc-text);
        line-height: 1.2;
    }
    .cc-stat-label {
        font-size: 0.75rem;
        color: var(--cc-muted);
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .cc-vision {
        background: linear-gradient(120deg, rgba(139, 92, 246, 0.1) 0%, rgba(91, 156, 255, 0.08) 100%);
        border: 1px solid rgba(139, 92, 246, 0.25);
        border-radius: 16px;
        padding: 1.5rem 1.75rem;
        margin-bottom: 1.5rem;
    }
    .cc-vision-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: var(--cc-text);
        margin-bottom: 0.5rem;
    }
    .cc-vision-body {
        color: var(--cc-muted);
        font-size: 0.98rem;
        line-height: 1.6;
        margin-bottom: 1rem;
    }
    .cc-vision-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.65rem;
    }
    @media (max-width: 900px) {
        .cc-vision-grid { grid-template-columns: repeat(2, 1fr); }
    }
    .cc-vision-item {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid var(--cc-border);
        border-radius: 10px;
        padding: 0.65rem 0.85rem;
        font-size: 0.88rem;
        color: var(--cc-text);
    }
    .cc-section-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: var(--cc-text);
        margin: 1.75rem 0 0.85rem 0;
        padding-bottom: 0.45rem;
        border-bottom: 1px solid var(--cc-border);
        letter-spacing: -0.01em;
    }
    .cc-section-sub {
        color: var(--cc-muted);
        font-size: 0.92rem;
        margin: -0.5rem 0 1rem 0;
    }
    .cc-briefing {
        background: linear-gradient(120deg, #121f35 0%, #182845 100%);
        border: 1px solid rgba(91, 156, 255, 0.35);
        border-left: 4px solid var(--cc-accent);
        border-radius: 14px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
    }
    .cc-briefing-title {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--cc-accent);
        font-weight: 600;
        margin-bottom: 0.45rem;
    }
    .cc-briefing-body {
        color: var(--cc-text);
        font-size: 1.12rem;
        line-height: 1.55;
        margin: 0;
    }
    .cc-coach-card {
        background: var(--cc-surface-2);
        border: 1px solid var(--cc-border);
        border-radius: 14px;
        padding: 1.15rem 1.25rem;
        height: 100%;
    }
    .cc-coach-label {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        color: var(--cc-accent-2);
        font-weight: 600;
        margin-bottom: 0.4rem;
    }
    .cc-coach-text {
        color: var(--cc-text);
        font-size: 0.95rem;
        line-height: 1.5;
        margin: 0;
    }
    .cc-app-card {
        background: var(--cc-surface);
        border: 1px solid var(--cc-border);
        border-radius: 16px;
        padding: 1.2rem 1.3rem 0.5rem;
        height: 100%;
        min-height: 300px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.22);
        transition: border-color 0.2s, transform 0.2s;
    }
    .cc-app-card:hover {
        border-color: rgba(91, 156, 255, 0.45);
    }
    .cc-app-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 0.5rem;
        margin-bottom: 0.35rem;
    }
    .cc-app-icon { font-size: 1.85rem; }
    .cc-status-badge {
        font-size: 0.68rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        border-radius: 999px;
        padding: 0.2rem 0.55rem;
        white-space: nowrap;
        border: 1px solid;
    }
    .cc-app-name {
        font-size: 1.08rem;
        font-weight: 700;
        color: var(--cc-text);
        margin-bottom: 0.3rem;
        line-height: 1.3;
    }
    .cc-app-desc {
        color: var(--cc-muted);
        font-size: 0.86rem;
        line-height: 1.45;
        margin-bottom: 0.65rem;
        min-height: 2.6rem;
    }
    .cc-meta {
        font-size: 0.76rem;
        color: var(--cc-muted);
        margin-bottom: 0.2rem;
    }
    .cc-nba-card {
        background: linear-gradient(135deg, rgba(240, 180, 41, 0.08) 0%, rgba(91, 156, 255, 0.06) 100%);
        border: 1px solid rgba(240, 180, 41, 0.3);
        border-radius: 10px;
        padding: 0.65rem 0.75rem;
        margin: 0.5rem 0 0.65rem;
    }
    .cc-nba-label {
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--cc-gold);
        font-weight: 600;
        margin-bottom: 0.25rem;
    }
    .cc-nba-text {
        font-size: 0.84rem;
        color: var(--cc-text);
        line-height: 1.45;
        margin: 0;
    }
    .cc-rec-card {
        background: var(--cc-surface-2);
        border: 1px solid var(--cc-border);
        border-radius: 12px;
        padding: 1rem 1.1rem;
        margin-bottom: 0.65rem;
        height: 100%;
    }
    .cc-rec-label {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--cc-accent);
        font-weight: 600;
        margin-bottom: 0.35rem;
    }
    .cc-rec-text {
        color: var(--cc-text);
        font-size: 0.92rem;
        line-height: 1.5;
        margin: 0;
    }
    .cc-perf-card {
        background: var(--cc-surface);
        border: 1px solid var(--cc-border);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        height: 100%;
    }
    .cc-perf-icon { font-size: 1.65rem; margin-bottom: 0.3rem; }
    .cc-perf-title {
        font-weight: 600;
        color: var(--cc-text);
        font-size: 0.9rem;
        margin-bottom: 0.2rem;
    }
    .cc-perf-link { font-size: 0.78rem; color: var(--cc-muted); }
    .cc-divider {
        border: none;
        border-top: 1px solid var(--cc-border);
        margin: 1.75rem 0;
    }
    div[data-testid="stMetric"] {
        background: var(--cc-surface);
        border: 1px solid var(--cc-border);
        border-radius: 12px;
        padding: 0.7rem 0.85rem;
    }
    div[data-testid="stMetric"] label { color: var(--cc-muted) !important; }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: var(--cc-text) !important; }
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] { font-size: 0.75rem !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Placeholder data (replace via shared activity DB / AI engine later) ───────


@dataclass(frozen=True)
class AppCard:
    key: str
    name: str
    icon: str
    description: str
    url: str
    status: AppStatus
    last_used: str
    weekly_usage: str
    next_action: str
    button_label: str


@dataclass(frozen=True)
class CrossAppRecommendation:
    category: str
    icon: str
    message: str


@dataclass(frozen=True)
class WeeklyMetric:
    label: str
    value: str
    delta: str | None = None


@dataclass(frozen=True)
class PerformanceCategory:
    icon: str
    title: str
    app_label: str


@dataclass(frozen=True)
class CoachSummary:
    headline: str
    needs_attention: str
    not_checked: str
    suggested_actions: list[str]
    weekly_insight: str


@dataclass(frozen=True)
class PlatformStat:
    value: str
    label: str


def _effective_status(app: AppCard) -> AppStatus:
    """Derive display status: empty URL overrides to Needs Connection unless Coming Soon."""
    if app.status == "Coming Soon":
        return "Coming Soon"
    if not app.url.strip():
        return "Needs Connection"
    return app.status


def _status_badge_html(status: AppStatus) -> str:
    style = STATUS_STYLES[status]
    return (
        f'<span class="cc-status-badge" style="background:{style["bg"]};'
        f'border-color:{style["border"]};color:{style["text"]};">{status}</span>'
    )


def _placeholder_apps() -> list[AppCard]:
    return [
        AppCard(
            key="music",
            name="Music Practice Coach",
            icon="🎵",
            description="AI-guided practice sessions, song library, chord tools, and progress tracking.",
            url=MUSIC_APP_URL,
            status="Active",
            last_used="May 28, 2026 · 7:42 PM",
            weekly_usage="4.2 hrs this week",
            next_action="Practice Piano Man for 20 minutes — focus on verse transitions.",
            button_label="Open Music App",
        ),
        AppCard(
            key="investment",
            name="Investment Portfolio Analyzer",
            icon="📊",
            description="Portfolio risk, allocation, projections, and AI decision coaching.",
            url=INVESTMENT_APP_URL,
            status="Active",
            last_used="May 24, 2026 · 9:15 AM",
            weekly_usage="1 check-in this week",
            next_action="Review risk score, sector allocation, and projected 5-year returns.",
            button_label="Open Investment App",
        ),
        AppCard(
            key="baseball",
            name="Fantasy Baseball / Baseball Analytics",
            icon="⚾",
            description="Lineups, start/sit calls, stats explorer, and fantasy league tools.",
            url=BASEBALL_APP_URL,
            status="Active",
            last_used="May 29, 2026 · 6:30 PM",
            weekly_usage="5 lineup reviews",
            next_action="Review Sunday fantasy lineups and swap any questionable starters.",
            button_label="Open Baseball App",
        ),
        AppCard(
            key="nba",
            name="NBA Playoff Companion",
            icon="🏀",
            description="Matchups, injuries, live game center, and playoff analytics.",
            url=NBA_APP_URL,
            status="Active",
            last_used="May 27, 2026 · 8:00 PM",
            weekly_usage="3 analysis sessions",
            next_action="Check Knicks matchup, injury report, and live game center before tip-off.",
            button_label="Open NBA App",
        ),
        AppCard(
            key="math",
            name="Advanced Math Intelligence",
            icon="🧮",
            description="Applied math reasoning, simulations, idea explorer, and problem lab.",
            url=MATH_APP_URL,
            status="Prototype",
            last_used="May 30, 2026 · 2:10 PM",
            weekly_usage="2 build sessions",
            next_action="Add or test one new applied problem in the reasoning lab.",
            button_label="Open Math App",
        ),
        AppCard(
            key="future_lens",
            name="Future Lens",
            icon="🔮",
            description="AI transition simulator — explore how technology reshapes your domains.",
            url=FUTURE_LENS_URL,
            status="Coming Soon",
            last_used="May 22, 2026 · 4:55 PM",
            weekly_usage="1 exploration",
            next_action="Preview scenarios: how AI may change teaching, investing, and sports over 10–20 years.",
            button_label="Open Future Lens",
        ),
    ]


def _placeholder_briefing() -> dict[str, str]:
    return {
        "focus": (
            "Today's focus: update fantasy baseball lineups, check your portfolio risk, "
            "and practice one song for 20 minutes."
        ),
        "needs_attention": "Investment Portfolio Analyzer — no check-in this week.",
        "not_checked": "Future Lens (9 days ago) · NBA App (4 days ago).",
        "best_action": "Start with a quick portfolio review, then open the Baseball App for Sunday lineups.",
    }


def _placeholder_coach_summary() -> CoachSummary:
    return CoachSummary(
        headline="Your AI coach reviewed all six apps. Here's your weekly game plan.",
        needs_attention=(
            "**Investment Portfolio Analyzer** needs a check-in — you haven't reviewed risk or "
            "allocation since last Tuesday."
        ),
        not_checked=(
            "**Future Lens** (9 days) and **NBA Playoff Companion** (4 days) haven't been opened recently. "
            "Both have timely context worth a quick look."
        ),
        suggested_actions=[
            "Open Investment App → run a portfolio risk and allocation review (≈10 min).",
            "Open Baseball App → finalize Sunday fantasy lineups and start/sit calls.",
            "Open Music App → 20-minute focused session on Piano Man.",
            "Open NBA App → check Knicks matchup and injury updates before the game.",
            "Open Math App → add one applied problem to your reasoning lab.",
        ],
        weekly_insight=(
            "You're strongest on baseball analytics this week (5 lineup reviews) but light on "
            "financial check-ins. Balancing both keeps your Personal Performance OS aligned."
        ),
    )


def _placeholder_platform_stats() -> list[PlatformStat]:
    return [
        PlatformStat("6", "Integrated Apps"),
        PlatformStat("4", "Active This Week"),
        PlatformStat("16", "Sessions Logged"),
        PlatformStat("1", "Needs Attention"),
    ]


def _placeholder_recommendations() -> list[CrossAppRecommendation]:
    return [
        CrossAppRecommendation(
            category="Music",
            icon="🎵",
            message=(
                "You practiced music for 4 hours this week but haven't practiced in 3 days. "
                "Go back to the Music App and practice Piano Man or choose a new song."
            ),
        ),
        CrossAppRecommendation(
            category="Investing",
            icon="📊",
            message=(
                "You haven't checked your portfolio this week. Open the Investment App and "
                "review risk, allocation, and projected returns."
            ),
        ),
        CrossAppRecommendation(
            category="Fantasy Baseball",
            icon="⚾",
            message=(
                "It's Sunday — time to review fantasy baseball lineups. Open the Baseball App "
                "and check start/sit recommendations."
            ),
        ),
        CrossAppRecommendation(
            category="Basketball",
            icon="🏀",
            message=(
                "Knicks game upcoming. Open the NBA App to check matchup, injuries, "
                "and live game center."
            ),
        ),
        CrossAppRecommendation(
            category="Math Intelligence",
            icon="🧮",
            message=(
                "You've been building math reasoning tools. Open the Advanced Math App and "
                "add or test one new applied problem."
            ),
        ),
        CrossAppRecommendation(
            category="Future Lens",
            icon="🔮",
            message=(
                "Explore how AI may change teaching, investing, music practice, or sports "
                "analysis over the next 10–20 years."
            ),
        ),
    ]


def _placeholder_weekly_metrics() -> list[WeeklyMetric]:
    return [
        WeeklyMetric("Music practice (hrs)", "4.2", "+0.8 vs last week"),
        WeeklyMetric("Portfolio check-ins", "1", "−2 vs last week"),
        WeeklyMetric("Baseball lineup reviews", "5", "+1 vs last week"),
        WeeklyMetric("Basketball sessions", "3", "same as last week"),
        WeeklyMetric("Math build sessions", "2", "+1 vs last week"),
        WeeklyMetric("Future Lens explorations", "1", "same as last week"),
    ]


def _performance_categories() -> list[PerformanceCategory]:
    return [
        PerformanceCategory("🎨", "Creative Performance", "Music App"),
        PerformanceCategory("💰", "Financial Performance", "Investment App"),
        PerformanceCategory("🏆", "Sports / Fantasy Performance", "Baseball + NBA Apps"),
        PerformanceCategory("🧠", "Intellectual Performance", "Math App"),
        PerformanceCategory("🚀", "Future Adaptation", "Future Lens"),
    ]


def _render_app_link_button(app: AppCard) -> None:
    """Open app URL or show disconnected state."""
    display_status = _effective_status(app)
    if app.url.strip() and display_status != "Coming Soon":
        st.link_button(app.button_label, app.url, use_container_width=True)
    else:
        st.button(
            app.button_label,
            disabled=True,
            use_container_width=True,
            help="Link not connected yet." if display_status != "Coming Soon" else "Coming soon.",
        )
        if display_status == "Coming Soon":
            st.caption("Coming soon — not yet available.")
        else:
            st.caption("Link not connected yet.")


def _render_app_card(app: AppCard) -> None:
    display_status = _effective_status(app)
    st.markdown(
        f"""
        <div class="cc-app-card">
            <div class="cc-app-header">
                <div class="cc-app-icon">{app.icon}</div>
                {_status_badge_html(display_status)}
            </div>
            <div class="cc-app-name">{app.name}</div>
            <div class="cc-app-desc">{app.description}</div>
            <div class="cc-meta">Last used · {app.last_used}</div>
            <div class="cc-meta">{app.weekly_usage}</div>
            <div class="cc-nba-card">
                <div class="cc-nba-label">Next Best Action</div>
                <p class="cc-nba-text">{app.next_action}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _render_app_link_button(app)


def _render_platform_vision() -> None:
    vision_items = [
        "🎵 Music Practice Coach",
        "📊 Investment Portfolio Analyzer",
        "⚾ Baseball Analytics",
        "🏀 NBA Playoff Companion",
        "🧮 Advanced Math Intelligence",
        "🔮 Future Lens",
    ]
    items_html = "".join(f'<div class="cc-vision-item">{item}</div>' for item in vision_items)
    st.markdown(
        f"""
        <div class="cc-vision">
            <div class="cc-vision-title">🌐 Platform Vision — One Integrated AI Ecosystem</div>
            <div class="cc-vision-body">
                Daniel AI Command Center is the home layer for a unified personal AI platform —
                not six separate projects, but one ecosystem where creative, financial, athletic,
                intellectual, and forward-looking tools share context, recommendations, and progress.
                Each app specializes; this hub orchestrates.
            </div>
            <div class="cc-vision-grid">{items_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_hero(stats: list[PlatformStat]) -> None:
    stats_html = "".join(
        f"""
        <div class="cc-stat-pill">
            <div class="cc-stat-value">{s.value}</div>
            <div class="cc-stat-label">{s.label}</div>
        </div>
        """
        for s in stats
    )
    st.markdown(
        f"""
        <div class="cc-hero">
            <div class="cc-hero-badge">Daniel AI Suite · Personal Performance OS</div>
            <h1>🎯 Daniel AI Command Center</h1>
            <p>One dashboard for music, investing, sports analytics, math intelligence,
            and future AI workflows — your unified command layer for the entire platform.</p>
            <div class="cc-hero-stats">{stats_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_coach_summary(coach: CoachSummary) -> None:
    st.markdown(
        '<div class="cc-section-title">🧠 Weekly AI Coach Summary</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="cc-section-sub">Your personal AI advisor across the full Daniel AI Suite.</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="cc-briefing" style="margin-bottom:1rem;">
            <div class="cc-briefing-title">Coach Overview</div>
            <p class="cc-briefing-body">{coach.headline}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.markdown(
            f"""
            <div class="cc-coach-card">
                <div class="cc-coach-label">Needs Attention</div>
                <p class="cc-coach-text">{coach.needs_attention}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="cc-coach-card">
                <div class="cc-coach-label">Not Checked Recently</div>
                <p class="cc-coach-text">{coach.not_checked}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("**Suggested next actions**")
    for i, action in enumerate(coach.suggested_actions, start=1):
        st.markdown(f"{i}. {action}")

    st.info(coach.weekly_insight)


# ── Main layout ───────────────────────────────────────────────────────────────

briefing = _placeholder_briefing()
apps = _placeholder_apps()
coach = _placeholder_coach_summary()
platform_stats = _placeholder_platform_stats()
recommendations = _placeholder_recommendations()
weekly_metrics = _placeholder_weekly_metrics()
perf_categories = _performance_categories()

_render_hero(platform_stats)
_render_platform_vision()

# ── Today's AI Briefing ───────────────────────────────────────────────────────

st.markdown(
    '<div class="cc-section-title">✨ Today\'s AI Briefing</div>',
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="cc-briefing">
        <div class="cc-briefing-title">What to focus on today</div>
        <p class="cc-briefing-body">{briefing["focus"]}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

b1, b2, b3 = st.columns(3)
with b1:
    st.markdown("**Which app needs attention?**")
    st.info(briefing["needs_attention"])
with b2:
    st.markdown("**What haven't you checked?**")
    st.warning(briefing["not_checked"])
with b3:
    st.markdown("**Best next action**")
    st.success(briefing["best_action"])

st.markdown('<hr class="cc-divider">', unsafe_allow_html=True)

_render_coach_summary(coach)

st.markdown('<hr class="cc-divider">', unsafe_allow_html=True)

# ── App cards ─────────────────────────────────────────────────────────────────

st.markdown('<div class="cc-section-title">📱 Suite Apps</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="cc-section-sub">Each module in the Daniel AI ecosystem — status, usage, and your next move.</div>',
    unsafe_allow_html=True,
)

for row in (apps[:3], apps[3:]):
    cols = st.columns(3, gap="medium")
    for col, app in zip(cols, row):
        with col:
            _render_app_card(app)

st.markdown('<hr class="cc-divider">', unsafe_allow_html=True)

# ── Cross-App Recommendations ─────────────────────────────────────────────────

st.markdown(
    '<div class="cc-section-title">🤖 Cross-App Recommendations</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="cc-section-sub">AI-style nudges powered by placeholder activity data — connect the shared recommendation engine later.</div>',
    unsafe_allow_html=True,
)

rec_cols = st.columns(2, gap="medium")
for i, rec in enumerate(recommendations):
    with rec_cols[i % 2]:
        st.markdown(
            f"""
            <div class="cc-rec-card">
                <div class="cc-rec-label">{rec.icon} {rec.category}</div>
                <p class="cc-rec-text">{rec.message}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown('<hr class="cc-divider">', unsafe_allow_html=True)

# ── Weekly Activity Summary ───────────────────────────────────────────────────

st.markdown(
    '<div class="cc-section-title">📈 Weekly Activity Summary</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="cc-section-sub">Placeholder metrics — wire to shared activity database and usage tracking.</div>',
    unsafe_allow_html=True,
)

metric_cols = st.columns(6, gap="small")
for col, metric in zip(metric_cols, weekly_metrics):
    with col:
        st.metric(metric.label, metric.value, metric.delta)

st.markdown('<hr class="cc-divider">', unsafe_allow_html=True)

# ── Personal Performance OS ───────────────────────────────────────────────────

st.markdown(
    '<div class="cc-section-title">⚡ Your Personal Performance Operating System</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    This dashboard connects your **creative**, **financial**, **athletic**,
    **intellectual**, and **analytical** work into one AI-guided system —
    a single operating layer for how you perform, decide, and adapt.
    """
)

perf_cols = st.columns(5, gap="medium")
for col, cat in zip(perf_cols, perf_categories):
    with col:
        st.markdown(
            f"""
            <div class="cc-perf-card">
                <div class="cc-perf-icon">{cat.icon}</div>
                <div class="cc-perf-title">{cat.title}</div>
                <div class="cc-perf-link">→ {cat.app_label}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown('<hr class="cc-divider">', unsafe_allow_html=True)

# ── Quick navigation ──────────────────────────────────────────────────────────

st.markdown(
    '<div class="cc-section-title">🧭 Quick Navigation</div>',
    unsafe_allow_html=True,
)

nav_cols = st.columns(6, gap="small")
for col, app in zip(nav_cols, apps):
    with col:
        _render_app_link_button(app)

st.caption(
    f"Daniel AI Command Center · Daniel AI Suite · {datetime.now().strftime('%B %d, %Y')} · "
    "demo data — connect shared activity DB, AI engine, and app URLs when ready."
)
