"""
Group repeated suite activity events into accomplishment summaries.

Raw events remain in storage; this module only shapes the Command Center feed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

WEEK_WINDOW = timedelta(days=7)

MILESTONE_EVENTS: frozenset[tuple[str, str]] = frozenset(
    {
        ("investment", "portfolio_created"),
        ("investment", "holdings_updated"),
        ("baseball", "draft_prep"),
        ("baseball", "trade_eval"),
        ("baseball", "trade_analysis"),
        ("baseball", "sleeper_review"),
        ("baseball", "sleeper_research"),
        ("baseball", "roster_built"),
        ("baseball", "roster_build"),
        ("music", "practice"),
        ("music", "backing_track_completed"),
        ("music", "backing_track"),
        ("nba", "playoff_simulation"),
        ("nba", "matchup_analysis"),
        ("nba", "playoff_tracker_review"),
        ("nba", "playoff_tracking"),
    }
)


def _parse_ts(event: dict[str, Any], parse_fn: Callable[[str | None], datetime | None]) -> datetime:
    dt = parse_fn(str(event.get("timestamp") or ""))
    if dt is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    return dt


def _metrics(event: dict[str, Any]) -> dict[str, Any]:
    raw = event.get("metrics")
    return raw if isinstance(raw, dict) else {}


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
        if et == "holdings_updated":
            return "portfolio_allocation_updated"
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
        if et in ("sleeper_review", "sleeper_research"):
            return "sleeper_analysis"

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
    ("investment", "portfolio_health_review"): "Portfolio Health",
    ("investment", "portfolio_optimizer"): "Portfolio Optimizer",
    ("investment", "portfolio_scenario"): "Risk Assessment",
    ("investment", "portfolio_built"): "New portfolio created",
    ("investment", "portfolio_allocation_updated"): "Portfolio allocation updated",
    ("investment", "goal_selected"): "Investment goal selected",
    ("baseball", "player_comparison"): "Player Comparison",
    ("baseball", "trade_analysis"): "Trade Analysis",
    ("baseball", "draft_prep"): "Draft prep",
    ("baseball", "draft_question"): "Draft Recommendations Viewed",
    ("baseball", "sleeper_analysis"): "Sleeper Analysis",
    ("music", "practice_session"): "Practice session",
    ("music", "backing_track_studio"): "Backing Track Generated",
    ("music", "chart_edit"): "Chord Coach Used",
    ("nba", "nba_analysis"): "Matchup Analysis",
    ("applied_intelligence", "applied_math_work"): "Applied Math work",
    ("future_lens", "future_simulation"): "Future simulation",
}

APP_SUMMARY_LABELS: dict[str, str] = {
    "music": "Music App",
    "investment": "Investment App",
    "baseball": "Baseball App",
    "nba": "NBA App",
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


def _app_line(app: str, detail: str) -> str:
    app_name = APP_SUMMARY_LABELS.get(app, app.title())
    return f"{app_name} · {detail}"


def _group_message(app: str, action_id: str, count: int) -> str:
    label = action_display_label(app, action_id)
    if count >= 2:
        return _app_line(app, f"{label} ({count} runs)")
    return _app_line(app, label)


def milestone_today_line(event: dict[str, Any]) -> str | None:
    """Promote a single meaningful event to Today's Work (app-prefixed line)."""
    app = str(event.get("app") or "").strip()
    et = str(event.get("event") or "").strip()
    m = _metrics(event)
    page = str(event.get("page") or "").strip().lower()
    summary = str(event.get("summary") or "").strip()

    if (app, et) not in MILESTONE_EVENTS and not (
        app == "baseball" and et == "page_view" and "draft" in page
    ):
        return None

    if app == "investment" and et == "portfolio_created":
        return _app_line(app, "New portfolio created")

    if app == "investment" and et == "holdings_updated":
        return _app_line(app, "Portfolio allocation updated")

    if app == "music" and et == "practice":
        song = str(m.get("song") or "").strip()
        if song:
            return _app_line(app, f"Practiced {song}")
        return _app_line(app, "Practice session")

    if app == "music" and et in ("backing_track_completed", "backing_track"):
        song = str(m.get("song") or m.get("title") or "").strip()
        if song:
            return _app_line(app, f"Backing Track Generated ({song})")
        return _app_line(app, "Backing Track Generated")

    if app == "baseball" and et == "draft_prep":
        return _app_line(app, "Live Draft Session Started")

    if app == "baseball" and et == "page_view" and "draft" in page:
        return _app_line(app, "Live Draft Session Started")

    if app == "baseball" and et in ("trade_eval", "trade_analysis"):
        return _app_line(app, "Trade Analysis")

    if app == "baseball" and et in ("sleeper_review", "sleeper_research"):
        return _app_line(app, "Sleeper Analysis Completed")

    if app == "nba" and et == "playoff_simulation":
        return _app_line(app, "Playoff Simulation Run")

    if app == "nba" and et in ("matchup_analysis", "playoff_tracker_review", "playoff_tracking"):
        return _app_line(app, "Matchup Analysis Completed")

    if summary and len(summary) > 8 and "opened" not in summary.lower():
        return _app_line(app, summary)

    return None


def group_today_work_for_display(lines: tuple[str, ...]) -> list[tuple[str, list[str]]]:
    """Group Today's Work lines by app label for section rendering."""
    order: list[str] = []
    buckets: dict[str, list[str]] = {}
    for line in lines:
        if " · " in line:
            app_name, detail = line.split(" · ", 1)
        else:
            app_name, detail = "Activity", line
        if app_name not in buckets:
            order.append(app_name)
            buckets[app_name] = []
        if detail not in buckets[app_name]:
            buckets[app_name].append(detail)
    return [(app, buckets[app]) for app in order]


@dataclass(frozen=True)
class ActionGroupResult:
    rollup_items: tuple[Any, ...]
    consumed_ids: frozenset[tuple[str, str, str]]
    today_summaries: tuple[str, ...]
    week_summaries: tuple[str, ...]
    recent_by_app: tuple[str, ...]
    most_active: tuple[str, ...]
    feed_trace: dict[str, Any]


def build_action_groups(
    events: list[dict[str, Any]],
    *,
    now: datetime,
    parse_ts: Callable[[str | None], datetime | None],
    make_feed_item: Callable[..., Any],
    events_today_fn: Callable[[list[dict[str, Any]], datetime], list[dict[str, Any]]],
) -> ActionGroupResult:
    """
    Collapse repeated actions into rollup feed items and Today's Work summary lines.

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
    handled_today: set[tuple[str, str, str]] = set()
    rollup_items: list[Any] = []
    today_lines: list[str] = []
    week_lines: list[str] = []
    app_week_counts: dict[str, int] = {}
    top_groups: list[tuple[int, str, str, str]] = []

    for key, cluster in buckets_today.items():
        app, aid = key
        count = len(cluster)
        if count == 1:
            mline = milestone_today_line(cluster[0])
            if mline:
                today_lines.append(mline)
                handled_today.add(_event_identity(cluster[0]))
                continue
        msg = _group_message(app, aid, count)
        latest = max(_parse_ts(e, parse_ts) for e in cluster)
        if count >= 2:
            rollup_items.append(
                make_feed_item(None, app=app, message=msg, sort_key=latest, is_rollup=True)
            )
            for e in cluster:
                consumed.add(_event_identity(e))
        today_lines.append(msg)
        for e in cluster:
            handled_today.add(_event_identity(e))
        top_groups.append((count, app, aid, "today"))

    milestone_consumed: set[tuple[str, str, str]] = set()
    for event in today_events:
        eid = _event_identity(event)
        if eid in handled_today:
            continue
        line = milestone_today_line(event)
        if not line:
            continue
        if line in today_lines:
            milestone_consumed.add(eid)
            continue
        today_lines.append(line)
        milestone_consumed.add(eid)

    for key, cluster in buckets_week.items():
        app, aid = key
        if len(cluster) >= 2 and key not in {(a, b) for a, b, _, _ in top_groups}:
            if len(buckets_today.get(key, [])) >= 2:
                continue
            week_lines.append(_group_message(app, aid, len(cluster)))
        app_week_counts[app] = app_week_counts.get(app, 0) + len(cluster)
        if len(cluster) >= 2:
            top_groups.append((len(cluster), app, aid, "week"))

    top_groups.sort(key=lambda x: (-x[0], x[1], x[2]))
    most_active = [
        _group_message(app, aid, count)
        for count, app, aid, period in top_groups[:5]
        if period == "today"
    ]

    recent_by_app: list[str] = []
    for app, total in sorted(app_week_counts.items(), key=lambda x: (-x[1], x[0]))[:6]:
        if total >= 2:
            name = APP_SUMMARY_LABELS.get(app, app.title())
            recent_by_app.append(f"{name} — {total} actions this week")

    raw_count = len(events)
    grouped_count = len(today_lines)
    trace = {
        "raw_event_count": raw_count,
        "grouped_event_count": grouped_count,
        "duplicate_events_collapsed": max(0, len(consumed) - len(rollup_items)),
        "events_consumed_by_groups": len(consumed),
        "milestone_events_promoted": len(milestone_consumed),
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
