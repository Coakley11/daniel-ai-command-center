"""
Coach insight generator — actionable recommendations only.

Coach Insights answer "what should I do next?" They must not restate facts
already shown in Activity Summary (last song, last lesson, last team, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass

from activity_store import ActivitySnapshot
from suite_storage import load_active_resume_items


@dataclass(frozen=True)
class CoachInsight:
    key: str
    icon: str
    message: str
    priority: int


def generate_coach_insights(snapshot: ActivitySnapshot) -> list[CoachInsight]:
    """Return up to 5 actionable insights — one per app, no fact repetition."""
    candidates: list[CoachInsight] = []

    if snapshot.is_sunday_lineup_day:
        candidates.append(
            CoachInsight(
                key="baseball",
                icon="⚾",
                message="Review and set your fantasy baseball lineups for the week.",
                priority=5,
            )
        )
    elif snapshot.last_baseball_review_days_ago is not None and snapshot.last_baseball_review_days_ago >= 5:
        focus = snapshot.last_baseball_report or snapshot.last_baseball_projection or "projections"
        candidates.append(
            CoachInsight(
                key="baseball",
                icon="⚾",
                message=f"Update your lineup calls — check the latest {focus}.",
                priority=20 + snapshot.last_baseball_review_days_ago,
            )
        )

    if snapshot.last_portfolio_check_days_ago is not None and snapshot.last_portfolio_check_days_ago >= 7:
        days = snapshot.last_portfolio_check_days_ago
        candidates.append(
            CoachInsight(
                key="investment",
                icon="📊",
                message=(
                    f"You haven't checked portfolio health in {days} days — run a health check."
                    if days >= 10
                    else "Run a portfolio health check and rebalance if needed."
                ),
                priority=15 + days,
            )
        )

    if (
        snapshot.last_music_edit_days_ago is not None
        and snapshot.last_music_edit_days_ago <= 2
        and snapshot.last_song
        and (
            snapshot.last_music_practice_days_ago is None
            or snapshot.last_music_practice_days_ago > snapshot.last_music_edit_days_ago
        )
    ):
        candidates.append(
            CoachInsight(
                key="music",
                icon="🎵",
                message=(
                    f"You edited {snapshot.last_song} recently but haven't practiced it yet — "
                    "run a focused session."
                ),
                priority=6,
            )
        )
    elif (
        snapshot.last_music_upload_days_ago is not None
        and snapshot.last_music_upload_days_ago <= 3
        and snapshot.last_song
        and (
            snapshot.last_recording_review_days_ago is None
            or snapshot.last_recording_review_days_ago > snapshot.last_music_upload_days_ago
        )
    ):
        candidates.append(
            CoachInsight(
                key="music",
                icon="🎵",
                message=(
                    f"You uploaded a performance of {snapshot.last_song} — review it and "
                    "compare with older recordings."
                ),
                priority=7,
            )
        )
    elif snapshot.music_minutes_this_week >= 90 or snapshot.songs_practiced_this_week >= 4:
        candidates.append(
            CoachInsight(
                key="music",
                icon="🎵",
                message=(
                    f"Strong practice week ({snapshot.songs_practiced_this_week} songs, "
                    f"{snapshot.music_minutes_this_week:.0f} min) — keep the momentum."
                ),
                priority=12,
            )
        )
    elif (
        snapshot.last_instrument
        and snapshot.last_instrument_practice_days_ago is not None
        and snapshot.last_instrument_practice_days_ago >= 5
    ):
        candidates.append(
            CoachInsight(
                key="music",
                icon="🎵",
                message=(
                    f"You haven't practiced {snapshot.last_instrument.lower()} in "
                    f"{snapshot.last_instrument_practice_days_ago} days."
                ),
                priority=14 + snapshot.last_instrument_practice_days_ago,
            )
        )
    elif snapshot.music_overedited_song:
        candidates.append(
            CoachInsight(
                key="music",
                icon="🎵",
                message=(
                    f"You've edited {snapshot.music_overedited_song} several times this week "
                    "without logging practice — perform it once."
                ),
                priority=9,
            )
        )
    elif (
        snapshot.last_music_edit_label
        and snapshot.last_song
        and snapshot.last_music_edit_days_ago is not None
        and snapshot.last_music_edit_days_ago <= 3
    ):
        candidates.append(
            CoachInsight(
                key="music",
                icon="🎵",
                message=f"You recently {snapshot.last_music_edit_label.lower()} for {snapshot.last_song}.",
                priority=18,
            )
        )
    elif snapshot.last_music_practice_days_ago is not None and snapshot.last_music_practice_days_ago >= 2:
        if snapshot.last_song:
            message = f"Block 30 minutes to practice {snapshot.last_song}."
        else:
            message = "Block 30 minutes for a focused practice session."
        candidates.append(
            CoachInsight(
                key="music",
                icon="🎵",
                message=message,
                priority=10 + snapshot.last_music_practice_days_ago,
            )
        )
    elif (
        snapshot.last_music_practice_days_ago is not None
        and snapshot.last_music_practice_days_ago <= 1
        and snapshot.last_song
    ):
        candidates.append(
            CoachInsight(
                key="music",
                icon="🎵",
                message=f"You practiced music recently — continue {snapshot.last_song} for 20 minutes.",
                priority=20,
            )
        )

    if snapshot.last_nba_team:
        candidates.append(
            CoachInsight(
                key="nba",
                icon="🏀",
                message=f"Check today's {snapshot.last_nba_team} injury report before the slate.",
                priority=12,
            )
        )
    elif snapshot.last_nba_session_days_ago is not None and snapshot.last_nba_session_days_ago >= 4:
        candidates.append(
            CoachInsight(
                key="nba",
                icon="🏀",
                message="Review today's Knicks injury report and playoff matchup context.",
                priority=25,
            )
        )

    if snapshot.applied_intelligence_next_lesson:
        candidates.append(
            CoachInsight(
                key="applied_intelligence",
                icon="🧠",
                message=f"Continue Applied Intelligence: {snapshot.applied_intelligence_next_lesson}.",
                priority=18,
            )
        )
    elif snapshot.last_applied_intelligence_lesson and (snapshot.last_applied_intelligence_days_ago or 99) >= 2:
        candidates.append(
            CoachInsight(
                key="applied_intelligence",
                icon="🧠",
                message="Return to Applied Intelligence — pick up your next modeling or reasoning exercise.",
                priority=22,
            )
        )
    elif snapshot.last_applied_intelligence_days_ago is not None and snapshot.last_applied_intelligence_days_ago >= 5:
        candidates.append(
            CoachInsight(
                key="applied_intelligence",
                icon="🧠",
                message="Block time for one Applied Intelligence analysis or problem-solving session.",
                priority=24,
            )
        )

    for item in load_active_resume_items(limit=12):
        if item.app == "future_lens" and item.title:
            candidates.append(
                CoachInsight(
                    key="future_lens",
                    icon="🔮",
                    message=f"You started a Future Lens simulation — finish {item.title}.",
                    priority=14,
                )
            )
            break

    if snapshot.future_project or snapshot.last_simulation_name:
        label = snapshot.future_project or snapshot.last_simulation_name
        candidates.append(
            CoachInsight(
                key="future_lens",
                icon="🔮",
                message=f"Stress-test your {label} scenario with one new assumption.",
                priority=28,
            )
        )
    elif snapshot.last_future_lens_days_ago is not None and snapshot.last_future_lens_days_ago >= 7:
        candidates.append(
            CoachInsight(
                key="future_lens",
                icon="🔮",
                message="Run one new Future Simulator scenario this week.",
                priority=26,
            )
        )

    best: dict[str, CoachInsight] = {}
    for item in candidates:
        if item.key not in best or item.priority < best[item.key].priority:
            best[item.key] = item

    ordered = sorted(best.values(), key=lambda x: x.priority)
    return ordered[:5]
