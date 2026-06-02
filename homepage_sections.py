"""
Homepage data loading — safe to import without executing the Streamlit app body.
"""

from __future__ import annotations

from activity_feed import build_activity_feed
from activity_store import ActivitySnapshot, get_weekly_summary, load_activity_snapshot, load_all_events
from coach_engine import CoachInsight, generate_coach_insights
from continue_dashboard import ContinueCard, continue_cards_for_snapshot
from project_intelligence import generate_cross_app_insights, weekly_accomplishment_lines

HOMEPAGE_RENDERERS: tuple[str, ...] = (
    "_render_continue_section",
    "_render_cross_app_section",
    "_render_coach_insights",
    "_render_recent_activity_feed",
    "_render_weekly_summary",
)


def load_homepage_context() -> tuple[ActivitySnapshot, list[CoachInsight], list[ContinueCard]]:
    snapshot = load_activity_snapshot()
    insights = generate_coach_insights(snapshot)
    continue_cards = continue_cards_for_snapshot(snapshot, limit=6)
    return snapshot, insights, continue_cards


def cross_app_insights_for_snapshot(snapshot: ActivitySnapshot) -> list:
    return generate_cross_app_insights(snapshot)


def weekly_lines_for_snapshot(snapshot: ActivitySnapshot) -> list[tuple[str, str]]:
    return weekly_accomplishment_lines(get_weekly_summary(snapshot))


def activity_feed_items(limit: int = 20) -> list:
    return build_activity_feed(load_all_events(), limit=limit)
