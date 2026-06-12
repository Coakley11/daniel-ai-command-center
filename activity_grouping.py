"""
Group repeated suite activity events into accomplishment summaries.

Raw events remain in storage; this module only shapes the Command Center feed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

WEEK_WINDOW = timedelta(days=7)


def _parse_ts(event: dict[str, Any], parse_fn: Callable[[str | None], datetime | None]) -> datetime:
    dt = parse_fn(str(event.get("timestamp") or ""))
    if dt is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    return dt


def activity_action_id(event: dict[str, Any]) -> str | None:
    """Stable action key for grouping repeated work (app + semantic action)."""
    app = str(event.get("app") or "").strip()
    et = str(event.get("event") or "").strip()
    page = str(event.get("page") or "").strip().lower()

    if app == "investment":
        if et in ("portfolio_health_checked", "portfolio_check"):
            return "portfolio_analysis"
        if et in ("allocation_reviewed", "rebalance_reviewed"):
            return "portfolio_health_review"
        if et == "optimizer_run":
            return "portfolio_optimizer"
        if et == "scenario_run":
            return "portfolio_scenario"
        if et == "portfolio_created":
            return "portfolio_built"
        if et == "investment_goal_selected":
            return "goal_selected"

    if app == "baseball":
        if et in ("comparison", "player_comparison"):
            return "player_comparison"
        if et in ("trade_eval", "trade_analysis"):
            return "trade_analysis"
        if et == "draft_prep":
            return "draft_prep"
        if et == "analytical_question" and "draft" in page:
            return "draft_question"

    if app == "music":
        if et in ("practice",):
            return "practice_session"
        if et in ("backing_track_completed", "backing_track"):
            return "backing_track_studio"
        if et in ("verified_chart_saved", "lyrics_saved", "chart_save", "chord_save"):
            return "chart_edit"

    if app == "nba" and et in (
        "matchup_analysis",
        "injury_analysis",
        "game_outlook",
        "playoff_simulation",
        "playoff_tracker_review",
        "playoff_tracking",
    ):
        return "nba_analysis"

    if app == "applied_intelligence" and et in (
        "analysis",
        "lesson_completed",
        "case_study_completed",
        "problem_solved",
        "reasoning_exercise_completed",
    ):
        return "applied_math_work"

    if app == "future_lens" and et == "simulation":
        return "future_simulation"

    return None


ACTION_LABELS: dict[tuple[str, str], str] = {
    ("investment", "portfolio_analysis"): "Portfolio Analysis",
    ("investment", "portfolio_health_review"): "Portfolio Health reviewed",
    ("investment", "portfolio_optimizer"): "Portfolio Optimizer",
    ("investment", "portfolio_scenario"): "Scenario Analysis",
    ("investment", "portfolio_built"): "Portfolio built",
    ("investment", "goal_selected"): "Investment goal selected",
    ("baseball", "player_comparison"): "Player Comparison",
    ("baseball", "trade_analysis"): "Trade Analysis",
    ("baseball", "draft_prep"): "Draft prep",
    ("baseball", "draft_question"): "Draft question",
    ("music", "practice_session"): "Practice session",
    ("music", "backing_track_studio"): "Backing Track Studio",
    ("music", "chart_edit"): "Chart / lyrics edit",
    ("nba", "nba_analysis"): "NBA analysis",
    ("applied_intelligence", "applied_math_work"): "Applied Math work",
    ("future_lens", "future_simulation"): "Future simulation",
}

APP_SUMMARY_LABELS: dict[str, str] = {
    "music": "Music Practice",
    "investment": "Investment App",
    "baseball": "Baseball",
    "nba": "NBA Companion",
    "future_lens": "Future Lens",
    "applied_intelligence": "Applied Intelligence",
}


def action_display_label(app: str, action_id: str) -> str:
    return ACTION_LABELS.get((app, action_id), action_id.replace("_", " ").title())


def _event_identity(event: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(event.get("app") or ""),
        str(event.get("event") or ""),
        str(event.get("timestamp") or ""),
    )


@dataclass(frozen=True)
class ActionGroupResult:
    rollup_items: tuple[Any, ...]
    consumed_ids: frozenset[tuple[str, str, str]]
    today_summaries: tuple[str, ...]
    week_summaries: tuple[str, ...]
    recent_by_app: tuple[str, ...]
    most_active: tuple[str, ...]
    feed_trace: dict[str, Any]


def _period_label(*, today: bool) -> str:
    return "today" if today else "this week"


def _group_message(app: str, action_id: str, count: int, *, today: bool) -> str:
    label = action_display_label(app, action_id)
    period = _period_label(today=today)
    app_name = APP_SUMMARY_LABELS.get(app, app.title())
    if count == 1:
        return f"{app_name} — {label} (1 run {period})"
    return f"{app_name} — {label}: {count} runs {period}"


def build_action_groups(
    events: list[dict[str, Any]],
    *,
    now: datetime,
    parse_ts: Callable[[str | None], datetime | None],
    make_feed_item: Callable[..., Any],
    events_today_fn: Callable[[list[dict[str, Any]], datetime], list[dict[str, Any]]],
) -> ActionGroupResult:
    """
    Collapse repeated actions into rollup feed items and summary lines.

    ``make_feed_item`` signature: (event|None, app, message, sort_key, is_rollup=True)
    """
    today_events = events_today_fn(events, now)
    week_cutoff = now - WEEK_WINDOW

    buckets_today: dict[tuple[str, str], list[dict[str, Any]]] = {}
    buckets_week: dict[tuple[str, str], list[dict[str, Any]]] = {}

    for event in events:
        ts = _parse_ts(event, parse_ts)
        if ts == datetime.min.replace(tzinfo=timezone.utc):
            continue
        aid = activity_action_id(event)
        if not aid:
            continue
        app = str(event.get("app") or "")
        key = (app, aid)
        if event in today_events:
            buckets_today.setdefault(key, []).append(event)
        if ts >= week_cutoff:
            buckets_week.setdefault(key, []).append(event)

    consumed: set[tuple[str, str, str]] = set()
    rollup_items: list[Any] = []
    today_lines: list[str] = []
    week_lines: list[str] = []
    app_week_counts: dict[str, int] = {}
    top_groups: list[tuple[int, str, str, str]] = []

    for key, cluster in buckets_today.items():
        app, aid = key
        if len(cluster) >= 2:
            latest = max(_parse_ts(e, parse_ts) for e in cluster)
            msg = _group_message(app, aid, len(cluster), today=True)
            rollup_items.append(
                make_feed_item(None, app=app, message=msg, sort_key=latest, is_rollup=True)
            )
            for e in cluster:
                consumed.add(_event_identity(e))
            today_lines.append(msg)
            top_groups.append((len(cluster), app, aid, "today"))

    for key, cluster in buckets_week.items():
        app, aid = key
        if len(cluster) >= 2 and key not in {(a, b) for a, b, _, _ in top_groups}:
            if len(buckets_today.get(key, [])) >= 2:
                continue
            msg = _group_message(app, aid, len(cluster), today=False)
            week_lines.append(msg)
        app_week_counts[app] = app_week_counts.get(app, 0) + len(cluster)
        if len(cluster) >= 2:
            top_groups.append((len(cluster), app, aid, "week"))

    top_groups.sort(key=lambda x: (-x[0], x[1], x[2]))
    most_active = [
        _group_message(app, aid, count, today=(period == "today"))
        for count, app, aid, period in top_groups[:5]
    ]

    recent_by_app: list[str] = []
    for app, total in sorted(app_week_counts.items(), key=lambda x: (-x[1], x[0]))[:6]:
        if total >= 2:
            name = APP_SUMMARY_LABELS.get(app, app.title())
            recent_by_app.append(f"{name} — {total} actions this week")

    raw_count = len(events)
    grouped_count = len(rollup_items) + len(today_lines)
    trace = {
        "raw_event_count": raw_count,
        "grouped_event_count": grouped_count,
        "duplicate_events_collapsed": max(0, len(consumed) - len(rollup_items)),
        "events_consumed_by_groups": len(consumed),
        "top_activity_groups": [
            {"app": app, "action": aid, "count": count, "period": period}
            for count, app, aid, period in top_groups[:8]
        ],
        "app_activity_summary": dict(app_week_counts),
    }

    return ActionGroupResult(
        rollup_items=tuple(rollup_items),
        consumed_ids=frozenset(consumed),
        today_summaries=tuple(dict.fromkeys(today_lines)),
        week_summaries=tuple(dict.fromkeys(week_lines)),
        recent_by_app=tuple(recent_by_app),
        most_active=tuple(most_active),
        feed_trace=trace,
    )
