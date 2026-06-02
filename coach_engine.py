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
                message="Finalize weekly fantasy lineups — Sunday is lineup day.",
                priority=5,
            )
        )
    elif snapshot.last_baseball_player and snapshot.last_baseball_review_days_ago is not None:
        if snapshot.last_baseball_review_days_ago <= 2:
            candidates.append(
                CoachInsight(
                    key="baseball",
                    icon="⚾",
                    message=(
                        "You reviewed projections but have not finalized rankings — "
                        "lock your draft board next."
                    ),
                    priority=12,
                )
            )
        elif snapshot.last_baseball_review_days_ago >= 5:
            focus = snapshot.last_baseball_report or snapshot.last_baseball_projection or "pitching"
            candidates.append(
                CoachInsight(
                    key="baseball",
                    icon="⚾",
                    message=f"{focus.title()} analysis has not been updated recently.",
                    priority=20 + snapshot.last_baseball_review_days_ago,
                )
            )

    if (
        snapshot.investment_last_portfolio_created_days_ago is not None
        and snapshot.investment_last_portfolio_created_days_ago <= 14
        and (
            snapshot.last_portfolio_check_days_ago is None
            or (
                snapshot.investment_last_portfolio_created_days_ago
                < snapshot.last_portfolio_check_days_ago
            )
        )
    ):
        candidates.append(
            CoachInsight(
                key="investment",
                icon="📊",
                message="You built a portfolio but have not run a health check yet.",
                priority=8,
            )
        )
    elif (
        snapshot.investment_last_holdings_update_days_ago is not None
        and snapshot.investment_last_holdings_update_days_ago <= 7
        and (
            snapshot.last_portfolio_check_days_ago is None
            or snapshot.investment_last_holdings_update_days_ago
            < snapshot.last_portfolio_check_days_ago
        )
    ):
        candidates.append(
            CoachInsight(
                key="investment",
                icon="📊",
                message="Your portfolio was updated but not health-checked — run a review.",
                priority=7,
            )
        )
    elif (
        snapshot.investment_last_holdings_update_days_ago is not None
        and snapshot.investment_last_holdings_update_days_ago <= 7
        and (
            snapshot.investment_last_allocation_review_days_ago is None
            or snapshot.investment_last_holdings_update_days_ago
            < snapshot.investment_last_allocation_review_days_ago
        )
    ):
        candidates.append(
            CoachInsight(
                key="investment",
                icon="📊",
                message="Holdings changed — review allocation drift before the next trade.",
                priority=9,
            )
        )
    elif snapshot.last_portfolio_check_days_ago is not None and snapshot.last_portfolio_check_days_ago >= 7:
        days = snapshot.last_portfolio_check_days_ago
        candidates.append(
            CoachInsight(
                key="investment",
                icon="📊",
                message=(
                    f"You have not checked portfolio health in {days} days."
                    if days >= 10
                    else "Run a portfolio health check and rebalance if needed."
                ),
                priority=15 + days,
            )
        )
    elif (
        snapshot.investment_last_scenario_days_ago is not None
        and snapshot.investment_last_scenario_days_ago <= 7
        and (
            snapshot.investment_last_rebalance_review_days_ago is None
            or snapshot.investment_last_scenario_days_ago
            < snapshot.investment_last_rebalance_review_days_ago
        )
    ):
        candidates.append(
            CoachInsight(
                key="investment",
                icon="📊",
                message="Scenario analysis completed — review recommendations next.",
                priority=10,
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
                    f"You edited {snapshot.last_song} but have not practiced it yet."
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
                    f"You uploaded a recording of {snapshot.last_song} but have not reviewed feedback yet."
                ),
                priority=7,
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
    if snapshot.last_nba_team:
        page_hint = (snapshot.last_nba_page or "").lower()
        if "playoff" in page_hint or "series" in page_hint:
            msg = f"Continue playoff analysis for {snapshot.last_nba_team}."
            priority = 10
        elif "injury" in page_hint:
            msg = "Injury updates may affect your matchup outlook — review before tip-off."
            priority = 9
        elif "matchup" in page_hint or "game" in page_hint:
            msg = f"{snapshot.last_nba_team} has a game on the slate — revisit your matchup outlook."
            priority = 11
        else:
            msg = f"Pick up where you left off with {snapshot.last_nba_team} analysis."
            priority = 14
        candidates.append(
            CoachInsight(
                key="nba",
                icon="🏀",
                message=msg,
                priority=priority,
            )
        )
    elif snapshot.last_nba_session_days_ago is not None and snapshot.last_nba_session_days_ago >= 4:
        candidates.append(
            CoachInsight(
                key="nba",
                icon="🏀",
                message="Return to game analysis — injury and matchup context may have changed.",
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
        lower = label.lower()
        if "teach" in lower or "education" in lower:
            msg = "Teaching simulation suggests stronger focus on AI-assisted instruction."
        elif "research" in lower:
            msg = "Research skills remain valuable across the scenarios you explored."
        elif any(w in lower for w in ("quant", "math", "analytic", "data")):
            msg = "Quantitative analysis appears consistently resilient in your scenarios."
        else:
            msg = f"Continue your {label} simulation — try one new assumption."
        candidates.append(
            CoachInsight(
                key="future_lens",
                icon="🔮",
                message=msg,
                priority=16,
            )
        )
    best: dict[str, CoachInsight] = {}
    for item in candidates:
        if item.key not in best or item.priority < best[item.key].priority:
            best[item.key] = item

    ordered = sorted(best.values(), key=lambda x: x.priority)
    return ordered[:5]
