"""
Coach insight generator — one personalized recommendation list, no duplicates.
"""

from __future__ import annotations

from dataclasses import dataclass

from activity_store import ActivitySnapshot, format_days_ago
from app_registry import get_app_url


@dataclass(frozen=True)
class CoachInsight:
    key: str
    icon: str
    message: str
    url: str
    priority: int


def generate_coach_insights(snapshot: ActivitySnapshot) -> list[CoachInsight]:
    """Return prioritized coach messages — each app appears at most once."""
    insights: list[CoachInsight] = []

    # Music — gap or continue last song
    if snapshot.last_music_practice_days_ago is not None and snapshot.last_music_practice_days_ago >= 2:
        mins = 30 if snapshot.last_music_practice_days_ago >= 3 else 20
        insights.append(
            CoachInsight(
                key="music",
                icon="🎵",
                message=(
                    f"You haven't practiced in {snapshot.last_music_practice_days_ago} days. "
                    f"Consider a {mins}-minute session today."
                ),
                url=get_app_url("music"),
                priority=10 + snapshot.last_music_practice_days_ago,
            )
        )
    elif snapshot.last_song:
        focus = f" Continue working on {snapshot.last_song_focus}." if snapshot.last_song_focus else "."
        insights.append(
            CoachInsight(
                key="music",
                icon="🎵",
                message=f"Last song practiced: {snapshot.last_song}.{focus}",
                url=get_app_url("music"),
                priority=30,
            )
        )

    # Baseball — Sunday lineups
    if snapshot.is_sunday_lineup_day:
        insights.append(
            CoachInsight(
                key="baseball",
                icon="⚾",
                message="It's Sunday. Review and set your fantasy baseball lineups.",
                url=get_app_url("baseball"),
                priority=5,
            )
        )
    elif snapshot.last_baseball_review_days_ago is not None and snapshot.last_baseball_review_days_ago >= 5:
        insights.append(
            CoachInsight(
                key="baseball",
                icon="⚾",
                message=(
                    f"You haven't checked MLB projections in {snapshot.last_baseball_review_days_ago} days. "
                    "Review lineups or player trends."
                ),
                url=get_app_url("baseball"),
                priority=20 + snapshot.last_baseball_review_days_ago,
            )
        )

    # Portfolio
    if snapshot.last_portfolio_check_days_ago is not None and snapshot.last_portfolio_check_days_ago >= 7:
        insights.append(
            CoachInsight(
                key="investment",
                icon="📊",
                message=(
                    f"You haven't checked your portfolio in {snapshot.last_portfolio_check_days_ago} days. "
                    "Run a quick health review."
                ),
                url=get_app_url("investment"),
                priority=15 + snapshot.last_portfolio_check_days_ago,
            )
        )

    # Basketball
    if snapshot.last_nba_session_days_ago is not None and snapshot.last_nba_session_days_ago >= 4:
        insights.append(
            CoachInsight(
                key="nba",
                icon="🏀",
                message=(
                    f"No basketball analysis in {snapshot.last_nba_session_days_ago} days. "
                    "Check playoff matchups or injury reports."
                ),
                url=get_app_url("nba"),
                priority=25 + snapshot.last_nba_session_days_ago,
            )
        )

    # AI Homeroom
    if snapshot.math_next_lesson:
        insights.append(
            CoachInsight(
                key="math",
                icon="🧮",
                message=f"Complete your next AI Homeroom lesson: {snapshot.math_next_lesson}.",
                url=get_app_url("math"),
                priority=18,
            )
        )
    elif snapshot.last_math_session_days_ago is not None and snapshot.last_math_session_days_ago >= 5:
        insights.append(
            CoachInsight(
                key="math",
                icon="🧮",
                message="Complete your next AI Homeroom lesson — pick up where you left off.",
                url=get_app_url("math"),
                priority=22 + snapshot.last_math_session_days_ago,
            )
        )

    # Future Lens
    if snapshot.future_project:
        insights.append(
            CoachInsight(
                key="future_lens",
                icon="🔮",
                message=f"Continue your AI Future Simulator project: {snapshot.future_project}.",
                url=get_app_url("future_lens"),
                priority=28,
            )
        )
    elif snapshot.last_future_lens_days_ago is not None and snapshot.last_future_lens_days_ago >= 7:
        insights.append(
            CoachInsight(
                key="future_lens",
                icon="🔮",
                message="Continue your AI Future Simulator — explore one new scenario this week.",
                url=get_app_url("future_lens"),
                priority=26 + snapshot.last_future_lens_days_ago,
            )
        )

    if not insights:
        insights.append(
            CoachInsight(
                key="music",
                icon="✨",
                message="You're all caught up. Open any app below to start logging real activity.",
                url=get_app_url("music"),
                priority=99,
            )
        )

    # One insight per app — keep highest priority (lowest number)
    best: dict[str, CoachInsight] = {}
    for item in insights:
        if item.key not in best or item.priority < best[item.key].priority:
            best[item.key] = item

    ordered = sorted(best.values(), key=lambda x: x.priority)
    return ordered[:5]
