"""
Human-readable activity feed lines from suite event logs.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from activity_models import ActivityDashboard, ActivityFeedItem

try:
    from activity_time import parse_activity_timestamp, utc_iso_from_datetime
except ImportError:  # pragma: no cover — Streamlit deploy safety
    from datetime import timezone as _tz

    def parse_activity_timestamp(ts: str | None):
        raw = str(ts or "").strip()
        if not raw:
            return None
        text = raw.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(text[:26])
        except ValueError:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=_tz.utc)
        else:
            dt = dt.astimezone(_tz.utc)
        return dt

    def utc_iso_from_datetime(dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=_tz.utc)
        else:
            dt = dt.astimezone(_tz.utc)
        return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")

APP_LABELS: dict[str, str] = {
    "music": "Music",
    "baseball": "Baseball",
    "nba": "NBA",
    "investment": "Investment",
    "applied_intelligence": "Applied Intelligence",
    "future_lens": "Future Lens",
}

# Events stored for diagnostics/coach but omitted from Recent Activity unless summarized.
FEED_SUPPRESSED: frozenset[tuple[str, str]] = frozenset(
    {
        ("music", "song_selected"),
        ("music", "display_key_changed"),
        ("music", "backing_track_started"),
        ("music", "song_added"),
        ("investment", "investment_goal_selected"),
        ("investment", "holdings_updated"),
        ("investment", "ticker_analyzed"),
        ("investment", "risk_profile_changed"),
        ("investment", "frontier_viewed"),
    }
)

# Substrings that indicate low-value feed lines (opens, UI chrome).
_FEED_NOISE_MARKERS: tuple[str, ...] = (
    "opened ",
    "opened:",
    "viewed ",
    "selected ",
    "switched ",
    "changed tab",
    "changed filter",
    "sorted ",
    "clicked ",
    "dropdown",
    "minor holdings",
    "parameter change",
)

INVESTMENT_SETUP_EVENTS = frozenset(
    {
        "portfolio_created",
        "investment_goal_selected",
        "holdings_updated",
        "ticker_analyzed",
    }
)

SETUP_CLUSTER_WINDOW = timedelta(minutes=45)
DEDUPE_WINDOW = timedelta(minutes=20)
MESSAGE_DEDUPE_WINDOW = timedelta(minutes=45)
HIGHLIGHT_MAX_AGE = timedelta(days=7)
TODAY_ROLLUP_WINDOW = timedelta(hours=24)
SESSION_GAP = timedelta(minutes=90)
RECENT_ROLLUP_WINDOW = timedelta(minutes=90)

# Milestone events promoted to the Highlights section (when recent enough).
HIGHLIGHT_EVENTS: frozenset[tuple[str, str]] = frozenset(
    {
        ("investment", "investment_goal_selected"),
        ("investment", "portfolio_created"),
        ("investment", "portfolio_health_checked"),
        ("investment", "portfolio_check"),
        ("investment", "optimizer_run"),
        ("investment", "scenario_run"),
        ("music", "verified_chart_saved"),
        ("music", "lyrics_saved"),
        ("music", "chart_save"),
        ("music", "chord_save"),
        ("music", "practice"),
        ("music", "backing_track_completed"),
        ("music", "video_uploaded"),
        ("music", "audio_uploaded"),
        ("music", "recording_reviewed"),
        ("baseball", "draft_prep"),
        ("baseball", "trade_analysis"),
        ("baseball", "trade_eval"),
        ("baseball", "projection_report"),
        ("baseball", "roster_built"),
        ("baseball", "roster_build"),
        ("nba", "matchup_analysis"),
        ("nba", "injury_analysis"),
        ("nba", "playoff_simulation"),
        ("nba", "game_outlook"),
        ("future_lens", "simulation_completed"),
        ("future_lens", "timeline_completed"),
        ("future_lens", "simulation"),
        ("applied_intelligence", "lesson_completed"),
        ("applied_intelligence", "module_completed"),
        ("applied_intelligence", "problem_solved"),
    }
)

COMPARISON_ROLLUP_EVENTS: frozenset[tuple[str, str]] = frozenset(
    {
        ("baseball", "player_comparison"),
        ("baseball", "comparison"),
        ("nba", "player_comparison"),
    }
)

MUSIC_PRACTICE_ROLLUP_EVENTS: frozenset[tuple[str, str]] = frozenset(
    {
        ("music", "song_selected"),
        ("music", "practice"),
        ("music", "backing_track_completed"),
    }
)

INVESTMENT_PORTFOLIO_SESSION_EVENTS: frozenset[str] = frozenset(
    {
        "portfolio_health_checked",
        "portfolio_check",
        "allocation_reviewed",
        "rebalance_reviewed",
        "optimizer_run",
    }
)

NBA_ANALYSIS_ROLLUP_EVENTS: frozenset[str] = frozenset(
    {
        "matchup_analysis",
        "injury_analysis",
        "game_outlook",
        "playoff_simulation",
        "playoff_tracker_review",
        "playoff_tracking",
    }
)


def _metrics(event: dict[str, Any]) -> dict[str, Any]:
    raw = event.get("metrics")
    return raw if isinstance(raw, dict) else {}


def _parse_ts(event: dict[str, Any]) -> datetime:
    dt = parse_activity_timestamp(str(event.get("timestamp") or ""))
    if dt is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    return dt


def _music_title_artist(metrics: dict[str, Any]) -> str:
    title = str(metrics.get("song") or metrics.get("last_edited_song") or "").strip()
    artist = str(metrics.get("artist") or "").strip()
    if title and artist:
        return f"{title} — {artist}"
    return title


def _music_song_only(metrics: dict[str, Any]) -> str:
    return str(metrics.get("song") or metrics.get("last_edited_song") or "").strip()


def _music_edit_headline(event_type: str, metrics: dict[str, Any]) -> str:
    fields = metrics.get("edited_fields") or []
    if not isinstance(fields, list):
        fields = []
    field_set = {str(f) for f in fields}
    if event_type == "lyrics_saved" or (field_set == {"lyrics"}):
        return "Saved verified lyrics"
    if field_set >= {"chords", "lyrics"}:
        return "Saved verified chart & lyrics"
    if "chords" in field_set or event_type in ("verified_chart_saved", "chart_save", "chord_save"):
        return "Saved verified chords"
    return "Saved song edits"


def _summary_is_noise(text: str) -> bool:
    lower = text.strip().lower()
    if not lower:
        return True
    return any(marker in lower for marker in _FEED_NOISE_MARKERS)


def _executive_summary(event: dict[str, Any]) -> str | None:
    """Use app-provided summary when it reads like an accomplishment, not a click."""
    summary = str(event.get("summary") or "").strip()
    if not summary or _summary_is_noise(summary):
        return None
    return summary


def _player_pair(metrics: dict[str, Any]) -> str:
    a = str(metrics.get("player_a") or metrics.get("player") or "").strip()
    b = str(metrics.get("player_b") or "").strip()
    if a and b:
        return f"{a} vs {b}"
    return a or b


def _page_view_executive(
    app: str,
    metrics: dict[str, Any],
    page: str,
    summary: str,
) -> str | None:
    """Map legacy page_view hooks to executive lines; return None for passive browsing."""
    exec_summary = summary.strip()
    if exec_summary and not _summary_is_noise(exec_summary):
        return exec_summary

    pg = str(metrics.get("page") or page or "").strip()
    lower = pg.lower()
    team = str(metrics.get("team") or "").strip()

    if app == "nba":
        if "injury" in lower:
            return f"Reviewed injury report ({team})" if team else "Reviewed injury report"
        if "matchup" in lower or "game" in lower:
            return f"Analyzed {team} matchup" if team else "Analyzed a game matchup"
        if "playoff" in lower or "series" in lower:
            return "Simulated playoff series"
        if "compare" in lower or "player" in lower:
            pair = _player_pair(metrics)
            return f"Compared players: {pair}" if pair else "Compared players"
        if "outlook" in lower or "preview" in lower:
            return f"Generated game outlook ({team})" if team else "Generated game outlook"
        return None

    if app == "baseball":
        if "draft" in lower:
            return "Completed fantasy draft prep"
        if "sleeper" in lower:
            return "Reviewed sleeper candidates"
        if "trade" in lower:
            return "Evaluated trade proposal"
        if "projection" in lower or "report" in lower:
            return "Generated player projection report"
        if "roster" in lower or "lineup" in lower:
            return "Built fantasy roster"
        pair = _player_pair(metrics)
        if pair or "compare" in lower:
            return f"Compared {pair}" if pair else "Compared players"
        return None

    if app == "applied_intelligence":
        return None

    if app == "future_lens":
        if "timeline" in lower:
            return "Completed technology timeline"
        if "career" in lower or "transition" in lower:
            return "Compared future career scenarios"
        if "skill" in lower:
            return "Reviewed future skill recommendations"
        if pg or metrics.get("simulation"):
            sim = str(metrics.get("simulation") or pg or "").strip()
            return f"Simulated future of {sim}" if sim else None
        return None

    return None


def format_activity_message(event: dict[str, Any], *, for_feed: bool = True) -> str | None:
    """Return a scannable feed line, or None to skip noise-only events."""
    app = str(event.get("app") or "").strip()
    event_type = str(event.get("event") or "").strip()
    page = str(event.get("page") or "").strip()
    summary = str(event.get("summary") or "").strip()
    m = _metrics(event)

    if for_feed and (app, event_type) in FEED_SUPPRESSED:
        return None

    if event_type == "practice" and app == "music":
        song = str(m.get("song") or "").strip()
        mins = m.get("minutes")
        instrument = str(m.get("instrument") or "").strip()
        if song and mins and instrument:
            return f"Practiced {song} on {instrument} ({int(mins)} min)"
        if song and mins:
            return f"Practiced {song} ({int(mins)} min)"
        if song and instrument:
            return f"Practiced {song} on {instrument}"
        if song:
            return f"Practiced {song}"
        return "Logged a practice session"

    if event_type == "video_uploaded" and app == "music":
        song = _music_song_only(m)
        if song:
            return f"Uploaded performance of {song}"
        return "Uploaded a performance recording"

    if event_type == "audio_uploaded" and app == "music":
        song = _music_song_only(m)
        if song:
            return f"Uploaded recording of {song}"
        return "Uploaded an audio recording"

    if event_type == "display_key_changed" and app == "music":
        if for_feed:
            return None
        song = str(m.get("song") or "").strip()
        dk = str(m.get("display_key") or "").strip()
        if song and dk:
            return f"Changed {song} to {dk}"
        if dk:
            return f"Changed display key to {dk}"
        return "Changed display key"

    if event_type == "backing_track_started" and app == "music":
        if for_feed:
            return None
        line = _music_title_artist(m)
        if line:
            return f"Practiced with backing track: {line}"
        return "Started backing track session"

    if event_type == "backing_track_completed" and app == "music":
        line = _music_title_artist(m)
        if line:
            return f"Completed backing track session: {line}"
        return "Completed backing track session"

    if event_type in ("verified_chart_saved", "lyrics_saved", "chart_save", "chord_save") and app == "music":
        label = _music_edit_headline(event_type, m)
        song = _music_song_only(m)
        return f"{label} for {song}" if song else label

    if event_type == "song_added" and app == "music":
        if for_feed:
            return None
        line = _music_title_artist(m)
        return f"Added song: {line}" if line else "Added a new song"

    if event_type == "backing_track" and app == "music":
        line = _music_title_artist(m)
        return f"Generated backing track: {line}" if line else "Generated a backing track"

    if event_type == "recording_reviewed" and app == "music":
        line = _music_title_artist(m)
        return f"Reviewed recording: {line}" if line else "Reviewed a recording"

    if event_type == "song_selected" and app == "music":
        if for_feed:
            return None
        line = _music_title_artist(m)
        if line:
            return f"Opened: {line}"
        return summary or None

    if app == "investment":
        if event_type == "investment_goal_selected":
            if for_feed:
                return None
            goal = str(m.get("goal_title") or m.get("goal") or "").strip()
            if goal:
                return f"Selected investment goal: {goal}"
            return "Selected an investment goal"

        if event_type == "portfolio_created":
            count = m.get("holdings_count")
            goal = str(m.get("goal_title") or m.get("goal") or "").strip()
            if count is not None and goal:
                return f"Built starter portfolio: {int(count)} holdings ({goal})"
            if count is not None:
                return f"Built starter portfolio: {int(count)} holdings"
            return "Built a starter portfolio"

        if event_type == "holdings_updated":
            if for_feed:
                return None
            tickers = m.get("tickers") or []
            if isinstance(tickers, list) and tickers:
                sample = ", ".join(str(t).upper() for t in tickers[:6])
                if len(tickers) > 6:
                    sample += f", +{len(tickers) - 6} more"
                return f"Updated holdings: {sample}"
            return "Updated portfolio holdings"

        if event_type in ("portfolio_health_checked", "portfolio_check"):
            label = str(m.get("review_type") or "portfolio health").strip()
            score = m.get("score")
            if score is not None:
                return f"Ran portfolio health check ({label}, {float(score):.0f}/100)"
            return "Ran portfolio health check"

        if event_type == "risk_profile_changed":
            if for_feed:
                return None
            profile = str(m.get("risk_profile") or m.get("objective") or "").strip()
            if profile:
                return f"Risk profile: {profile.replace('_', ' ').title()}"
            return "Changed risk profile"

        if event_type == "allocation_reviewed":
            return "Reviewed allocation drift"

        if event_type == "frontier_viewed":
            if for_feed:
                return None
            return "Viewed efficient frontier"

        if event_type == "macro_environment_applied":
            return "Applied macro environment to portfolio outlook"

        if event_type == "scenario_run":
            ctx = str(m.get("scenario_type") or m.get("context") or "").strip().lower()
            if "monte" in ctx or "carlo" in ctx:
                return "Ran Monte Carlo simulation"
            if ctx:
                return f"Completed scenario analysis ({ctx})"
            return "Completed scenario analysis"

        if event_type == "optimizer_run":
            return "Completed optimizer analysis"

        if event_type == "ticker_analyzed":
            if for_feed:
                return None
            ticker = str(m.get("ticker") or "").strip().upper()
            return f"Analyzed ticker {ticker}" if ticker else "Analyzed a ticker"

        if event_type == "rebalance_reviewed":
            return "Reviewed rebalance guidance"

    if app == "baseball" and event_type in {
        "comparison",
        "player_comparison",
    }:
        pair = _player_pair(m)
        if pair:
            return f"Compared {pair}"
        player = str(m.get("player") or "").strip()
        return f"Completed player comparison{f' — {player}' if player else ''}"

    if event_type == "lineup_review" and app == "baseball":
        team = str(m.get("team") or m.get("league") or "").strip()
        if team:
            return f"Reviewed fantasy lineup ({team})"
        return "Reviewed fantasy lineup"

    if app == "baseball" and event_type in {"trade_eval", "trade_analysis"}:
        trade = str(m.get("trade") or summary or "").strip()
        return f"Evaluated trade proposal: {trade}" if trade else "Evaluated trade proposal"

    if event_type == "draft_prep" and app == "baseball":
        league = str(m.get("league") or m.get("team") or "").strip()
        return f"Completed fantasy draft prep ({league})" if league else "Completed fantasy draft prep"

    if app == "baseball" and event_type in {"sleeper_review", "sleeper_research"}:
        return "Reviewed sleeper candidates"

    if event_type == "projection_report" and app == "baseball":
        focus = str(m.get("report") or m.get("projection") or page or "").strip()
        return f"Generated player projection report ({focus})" if focus else "Generated player projection report"

    if app == "baseball" and event_type in {"roster_built", "roster_build"}:
        team = str(m.get("team") or m.get("league") or "").strip()
        return f"Built fantasy roster ({team})" if team else "Built fantasy roster"

    if event_type == "trend_analysis" and app == "baseball":
        player = str(m.get("player") or "").strip()
        return f"Reviewed recent trends for {player}" if player else "Reviewed recent trends"

    if event_type == "breakout_analysis" and app == "baseball":
        return "Analyzed breakout candidates"

    if event_type == "simulation" and app == "future_lens":
        sim = str(m.get("simulation") or m.get("domain") or "").strip()
        project = str(m.get("project") or m.get("area") or "").strip()
        if sim and project:
            return f"Simulated future of {sim} ({project})"
        if sim:
            return f"Simulated future of {sim}"
        line = _executive_summary(event)
        return line or "Completed a future scenario"

    if event_type == "problem_solved" and app == "applied_intelligence":
        topic = str(m.get("lesson") or m.get("analysis") or m.get("topic") or page or "").strip()
        return f"Solved applied math problem: {topic}" if topic else "Solved applied math problem"

    if event_type == "module_completed" and app == "applied_intelligence":
        topic = str(m.get("lesson") or page or "").strip()
        return f"Finished learning module: {topic}" if topic else "Finished learning module"

    if event_type == "reasoning_exercise_completed" and app == "applied_intelligence":
        topic = str(m.get("lesson") or page or "").strip()
        return f"Completed reasoning exercise: {topic}" if topic else "Completed reasoning exercise"

    if event_type in ("analysis", "lesson_completed", "case_study_completed") and app == "applied_intelligence":
        topic = str(
            m.get("lesson")
            or m.get("analysis")
            or m.get("topic")
            or page
            or ""
        ).strip()
        if event_type == "lesson_completed":
            return f"Completed AI lesson: {topic}" if topic else "Completed an AI lesson"
        if event_type == "case_study_completed":
            return f"Finished case study: {topic}" if topic else "Finished a case study"
        if m.get("concept"):
            return f"Explored concept: {m.get('concept')}"
        return f"Solved applied problem: {topic}" if topic else "Completed a reasoning exercise"

    if event_type == "concept_explored" and app == "applied_intelligence":
        concept = str(m.get("concept") or m.get("topic") or page or "").strip()
        return f"Explored machine learning concept: {concept}" if concept else "Explored a new concept"

    if app == "nba" and event_type in {"injury_review", "injury_analysis"}:
        team = str(m.get("team") or "").strip()
        return f"Reviewed injury report ({team})" if team else "Reviewed injury report"

    if event_type == "playoff_tracker_review" and app == "nba":
        team = str(m.get("team") or "").strip()
        return f"Updated playoff tracker ({team})" if team else "Updated playoff tracker"

    if event_type == "matchup_analysis" and app == "nba":
        team = str(m.get("team") or "").strip()
        return f"Analyzed {team} matchup" if team else "Analyzed a game matchup"

    if event_type == "playoff_simulation" and app == "nba":
        label = str(m.get("series") or m.get("matchup") or "").strip()
        return f"Simulated playoff series ({label})" if label else "Simulated playoff series"

    if event_type == "player_comparison" and app == "nba":
        pair = _player_pair(m)
        return f"Compared players: {pair}" if pair else "Compared players"

    if event_type == "game_outlook" and app == "nba":
        team = str(m.get("team") or "").strip()
        return f"Generated game outlook ({team})" if team else "Generated game outlook"

    if event_type == "playoff_tracking" and app == "nba":
        return "Tracked playoff performance"

    if app == "future_lens" and event_type in {"timeline_completed", "technology_timeline_review"}:
        topic = str(m.get("simulation") or m.get("project") or page or "").strip()
        return f"Completed technology timeline: {topic}" if topic else "Completed technology timeline"

    if app == "future_lens" and event_type in {"career_scenario", "career_analysis"}:
        label = str(m.get("scenario") or m.get("project") or "").strip()
        return f"Compared future careers ({label})" if label else "Compared future career scenarios"

    if event_type == "future_comparison" and app == "future_lens":
        label = str(m.get("scenario") or m.get("project") or "").strip()
        return f"Compared future scenarios ({label})" if label else "Compared future scenarios"

    if app == "future_lens" and event_type in {"skill_review", "skill_forecast_review"}:
        return "Reviewed future skill recommendations"

    if event_type == "page_view":
        if for_feed:
            line = _page_view_executive(app, m, page, summary)
            return line
        if app == "applied_intelligence":
            return None
        return _page_view_executive(app, m, page, summary) or summary or None

    if event_type == "session":
        line = _executive_summary(event)
        if line:
            return line

    if summary:
        line = _executive_summary(event)
        if line:
            return line
        if not for_feed:
            return summary
        return None
    if page and event_type:
        return f"{event_type.replace('_', ' ').title()}: {page}"
    return None


def _feed_priority(event: dict[str, Any]) -> int:
    """Higher = prefer in Recent Activity over noisy opens."""
    app = str(event.get("app") or "")
    event_type = str(event.get("event") or "")
    if app == "music" and event_type in {
        "verified_chart_saved",
        "lyrics_saved",
        "chart_save",
        "chord_save",
    }:
        return 6
    if app == "music" and event_type in {
        "practice",
        "recording_reviewed",
        "video_uploaded",
        "audio_uploaded",
        "backing_track_completed",
        "backing_track",
    }:
        return 5
    if app == "investment" and event_type in {
        "portfolio_health_checked",
        "portfolio_check",
        "optimizer_run",
        "scenario_run",
        "rebalance_reviewed",
        "allocation_reviewed",
    }:
        return 6
    if app == "investment" and event_type == "portfolio_created":
        return 3
    if app == "baseball" and event_type in {
        "draft_prep",
        "trade_eval",
        "trade_analysis",
        "projection_report",
        "roster_built",
        "roster_build",
        "comparison",
        "player_comparison",
        "sleeper_review",
        "sleeper_research",
        "trend_analysis",
        "breakout_analysis",
    }:
        return 6
    if app == "nba" and event_type in {
        "matchup_analysis",
        "injury_review",
        "injury_analysis",
        "playoff_simulation",
        "player_comparison",
        "game_outlook",
        "playoff_tracking",
        "playoff_tracker_review",
    }:
        return 6
    if event_type in {"comparison", "trade_eval", "lineup_review"}:
        return 5
    if app == "future_lens" and event_type in {
        "simulation",
        "simulation_completed",
        "timeline_completed",
        "technology_timeline_review",
        "career_scenario",
        "career_analysis",
        "skill_review",
        "skill_forecast_review",
        "future_comparison",
    }:
        return 5
    if app == "applied_intelligence" and event_type in {
        "analysis",
        "lesson_completed",
        "case_study_completed",
        "concept_explored",
        "problem_solved",
        "module_completed",
        "reasoning_exercise_completed",
    }:
        return 5
    if app == "investment" and event_type == "macro_environment_applied":
        return 4
    if event_type == "page_view":
        line = _page_view_executive(app, _metrics(event), str(event.get("page") or ""), str(event.get("summary") or ""))
        return 4 if line else 0
    if event_type == "session":
        return 4 if _executive_summary(event) else 0
    if (app, event_type) in FEED_SUPPRESSED:
        return 0
    return 2


def investment_directory_rank(event_type: str) -> int:
    """Higher rank wins on Investment App Directory card."""
    if event_type in {"portfolio_health_checked", "portfolio_check"}:
        return 5
    if event_type in {"allocation_reviewed", "rebalance_reviewed", "optimizer_run"}:
        return 4
    if event_type in {"scenario_run"}:
        return 3
    if event_type == "portfolio_created":
        return 2
    return 0


def music_directory_rank(event_type: str) -> int:
    """Higher rank wins on App Directory card (passive opens are lowest)."""
    if event_type in {"verified_chart_saved", "lyrics_saved", "chart_save", "chord_save"}:
        return 4
    if event_type == "practice":
        return 3
    if event_type in {
        "video_uploaded",
        "audio_uploaded",
        "backing_track_completed",
        "backing_track",
        "recording_reviewed",
    }:
        return 2
    if event_type == "song_selected":
        return 1
    return 0


def _summarize_investment_setup(cluster: list[dict[str, Any]]) -> str | None:
    goal = ""
    holdings = 0
    latest_ts = datetime.min.replace(tzinfo=timezone.utc)
    for event in cluster:
        m = _metrics(event)
        g = str(m.get("goal_title") or m.get("goal") or "").strip()
        if g:
            goal = g
        try:
            holdings = max(holdings, int(m.get("holdings_count") or 0))
        except (TypeError, ValueError):
            pass
        tickers = m.get("tickers")
        if isinstance(tickers, list):
            holdings = max(holdings, len(tickers))
        ts = _parse_ts(event)
        if ts > latest_ts:
            latest_ts = ts
    if holdings <= 0 and not goal:
        return None
    if goal and holdings:
        return f"Built starter portfolio: {holdings} holdings ({goal})"
    if holdings:
        return f"Built starter portfolio: {holdings} holdings"
    return f"Set investment goal: {goal}" if goal else None


def _normalize_feed_message(message: str) -> str:
    return " ".join(str(message or "").strip().lower().split())


def _cluster_investment_setup(events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[tuple[datetime, str, str]]]:
    """
    Collapse setup clicks in a time window into synthetic feed lines.
    Returns (remaining_events, synthetic_lines as (sort_key, app, message)).
    """
    sorted_events = sorted(events, key=_parse_ts)
    consumed: set[int] = set()
    synthetic: list[tuple[datetime, str, str]] = []

    i = 0
    while i < len(sorted_events):
        if i in consumed:
            i += 1
            continue
        event = sorted_events[i]
        if str(event.get("app") or "") != "investment":
            i += 1
            continue
        if str(event.get("event") or "") not in INVESTMENT_SETUP_EVENTS:
            i += 1
            continue
        anchor = _parse_ts(event)
        cluster = [event]
        consumed.add(i)
        j = i + 1
        while j < len(sorted_events):
            other = sorted_events[j]
            if str(other.get("app") or "") != "investment":
                j += 1
                continue
            if str(other.get("event") or "") not in INVESTMENT_SETUP_EVENTS:
                j += 1
                continue
            if _parse_ts(other) - anchor > SETUP_CLUSTER_WINDOW:
                break
            cluster.append(other)
            consumed.add(j)
            j += 1
        msg = _summarize_investment_setup(cluster)
        if msg:
            latest = max(_parse_ts(e) for e in cluster)
            synthetic.append((latest, "investment", msg))
        i = j

    remaining = [e for idx, e in enumerate(sorted_events) if idx not in consumed]
    return remaining, synthetic


def _dedupe_items_by_message(
    items: list[tuple[int, datetime, ActivityFeedItem]],
    *,
    window: timedelta = MESSAGE_DEDUPE_WINDOW,
) -> list[tuple[int, datetime, ActivityFeedItem]]:
    """
    One line per (app, message) inside the time window — keep newest / highest priority.
    """
    ranked = sorted(items, key=lambda row: (row[1], row[0]), reverse=True)
    kept: list[tuple[int, datetime, ActivityFeedItem]] = []
    anchors: list[tuple[str, str, datetime, int]] = []

    for priority, sort_key, item in ranked:
        norm = _normalize_feed_message(item.message)
        if not norm:
            continue
        skip = False
        for app, prev_norm, prev_ts, prev_pri in anchors:
            if app != item.app or prev_norm != norm:
                continue
            if abs((sort_key - prev_ts).total_seconds()) <= window.total_seconds():
                if priority <= prev_pri:
                    skip = True
                    break
        if skip:
            continue
        kept.append((priority, sort_key, item))
        anchors.append((item.app, norm, sort_key, priority))

    return kept


def _event_key(event: dict[str, Any]) -> tuple[str, str]:
    return (str(event.get("app") or ""), str(event.get("event") or ""))


def _is_highlight_event(event: dict[str, Any], *, now: datetime) -> bool:
    app, event_type = _event_key(event)
    if (app, event_type) not in HIGHLIGHT_EVENTS:
        return False
    ts = _parse_ts(event)
    if ts == datetime.min.replace(tzinfo=timezone.utc):
        return False
    if now - ts > HIGHLIGHT_MAX_AGE:
        return False
    if (app, event_type) in COMPARISON_ROLLUP_EVENTS:
        return False
    if app == "music" and event_type == "practice":
        m = _metrics(event)
        if not m.get("minutes") and not m.get("song"):
            return False
    return True


def _make_feed_item(
    event: dict[str, Any] | None,
    *,
    app: str,
    message: str,
    sort_key: datetime,
    is_highlight: bool = False,
    is_rollup: bool = False,
) -> ActivityFeedItem:
    ts_iso = utc_iso_from_datetime(sort_key)
    return ActivityFeedItem(
        app=app,
        app_label=APP_LABELS.get(app, app.replace("_", " ").title()),
        timestamp=ts_iso,
        message=message,
        sort_key=sort_key,
        is_highlight=is_highlight,
        is_rollup=is_rollup,
    )


def _format_item_message(event: dict[str, Any], *, for_highlight: bool = False) -> str | None:
    if for_highlight and _event_key(event) in HIGHLIGHT_EVENTS:
        msg = format_activity_message(event, for_feed=False)
        if msg and not _summary_is_noise(msg):
            return msg
    return format_activity_message(event, for_feed=True)


def _events_today(
    events: list[dict[str, Any]], *, now: datetime
) -> list[dict[str, Any]]:
    from activity_time import to_display_local

    local_now = to_display_local(now)
    today = local_now.date()
    out: list[dict[str, Any]] = []
    for event in events:
        ts = _parse_ts(event)
        if ts == datetime.min.replace(tzinfo=timezone.utc):
            continue
        if to_display_local(ts).date() == today:
            out.append(event)
    return out


def _session_spans(events: list[dict[str, Any]]) -> list[tuple[list[dict[str, Any]], datetime, datetime]]:
    """Split chronologically sorted events into sessions separated by SESSION_GAP."""
    if not events:
        return []
    ordered = sorted(events, key=_parse_ts)
    sessions: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = [ordered[0]]
    for event in ordered[1:]:
        if _parse_ts(event) - _parse_ts(current[-1]) > SESSION_GAP:
            sessions.append(current)
            current = [event]
        else:
            current.append(event)
    sessions.append(current)
    spans: list[tuple[list[dict[str, Any]], datetime, datetime]] = []
    for block in sessions:
        start = _parse_ts(block[0])
        end = _parse_ts(block[-1])
        spans.append((block, start, end))
    return spans


def _minutes_between(start: datetime, end: datetime) -> int:
    return max(1, int((end - start).total_seconds()) // 60)


def _app_label_for_summary(app: str) -> str:
    labels = {
        "music": "Music Coach",
        "investment": "Investment App",
        "baseball": "Baseball",
        "nba": "NBA Companion",
        "future_lens": "Future Lens",
        "applied_intelligence": "Applied Intelligence",
    }
    return labels.get(app, APP_LABELS.get(app, app.title()))


def build_today_summaries(
    events: list[dict[str, Any]],
    *,
    now: datetime | None = None,
) -> tuple[str, ...]:
    """Build the Today's Work summary strip from today's events."""
    if now is None:
        now = datetime.now(timezone.utc)
    today_events = _events_today(events, now=now)
    if not today_events:
        return ()

    summaries: list[str] = []
    by_app: dict[str, list[dict[str, Any]]] = {}
    for event in today_events:
        app = str(event.get("app") or "")
        if app:
            by_app.setdefault(app, []).append(event)

    for app, app_events in by_app.items():
        spans = _session_spans(app_events)
        total_minutes = sum(_minutes_between(s, e) for _, s, e in spans)
        if app == "investment":
            portfolio_events = [
                e
                for e in app_events
                if str(e.get("event") or "") in INVESTMENT_PORTFOLIO_SESSION_EVENTS
            ]
            if portfolio_events:
                summaries.append("Completed portfolio analysis")
            elif total_minutes >= 5:
                summaries.append(
                    f"Worked on {_app_label_for_summary(app)} for {total_minutes} minutes"
                )
            continue

        if app == "music":
            songs: set[str] = set()
            practice_mins = 0
            for event in app_events:
                et = str(event.get("event") or "")
                m = _metrics(event)
                song = str(m.get("song") or "").strip()
                if et in {"song_selected", "practice", "backing_track_completed"} and song:
                    songs.add(song)
                try:
                    practice_mins += int(m.get("minutes") or 0)
                except (TypeError, ValueError):
                    pass
            if songs:
                n = len(songs)
                summaries.append(
                    f"Practiced {n} song{'s' if n != 1 else ''}"
                    + (f" ({practice_mins} min)" if practice_mins else "")
                )
            elif total_minutes >= 5:
                summaries.append(
                    f"Worked on {_app_label_for_summary(app)} for {total_minutes} minutes"
                )
            continue

        if app == "baseball":
            comparisons = sum(
                1 for e in app_events if _event_key(e) in COMPARISON_ROLLUP_EVENTS
            )
            if comparisons >= 2:
                summaries.append(f"Ran {comparisons} player comparisons in Baseball")
            elif comparisons == 1:
                summaries.append("Ran a player comparison in Baseball")
            elif total_minutes >= 5:
                summaries.append(
                    f"Worked on {_app_label_for_summary(app)} for {total_minutes} minutes"
                )
            continue

        if app == "nba":
            analyses = sum(
                1 for e in app_events if str(e.get("event") or "") in NBA_ANALYSIS_ROLLUP_EVENTS
            )
            if analyses >= 2:
                summaries.append(f"Ran {analyses} NBA analyses")
            elif analyses == 1:
                summaries.append("Ran an NBA analysis")
            elif total_minutes >= 5:
                summaries.append(
                    f"Worked on {_app_label_for_summary(app)} for {total_minutes} minutes"
                )
            continue

        if total_minutes >= 10:
            summaries.append(
                f"Worked on {_app_label_for_summary(app)} for {total_minutes} minutes"
            )

    return tuple(summaries[:6])


def _rollup_comparison_message(app: str, count: int) -> str:
    label = APP_LABELS.get(app, app.title())
    if count == 1:
        return f"Ran a player comparison in {label}"
    return f"Ran {count} player comparisons in {label}"


def _rollup_music_practice_message(events: list[dict[str, Any]]) -> str:
    songs: set[str] = set()
    total_mins = 0
    for event in events:
        m = _metrics(event)
        song = str(m.get("song") or "").strip()
        if song:
            songs.add(song)
        try:
            total_mins += int(m.get("minutes") or 0)
        except (TypeError, ValueError):
            pass
    n = len(songs) or len(events)
    if total_mins:
        return f"Practiced {n} song{'s' if n != 1 else ''} ({total_mins} min total)"
    return f"Practiced {n} song{'s' if n != 1 else ''}"


def _rollup_portfolio_session_message(events: list[dict[str, Any]]) -> str:
    types = {str(e.get("event") or "") for e in events}
    if types & {"portfolio_health_checked", "portfolio_check"}:
        if types & {"allocation_reviewed", "rebalance_reviewed", "optimizer_run"}:
            return "Worked on portfolio analysis session"
        return "Completed portfolio health review"
    if "optimizer_run" in types:
        return "Ran portfolio optimizer analysis"
    return "Reviewed portfolio allocation and rebalance"


def _rollup_nba_analysis_message(count: int) -> str:
    if count == 1:
        return "Ran an NBA analysis"
    return f"Ran {count} NBA analyses"


def _group_rollup_events(
    events: list[dict[str, Any]],
    *,
    window: timedelta,
    predicate: Any,
) -> list[tuple[list[dict[str, Any]], datetime]]:
    """Group consecutive matching events within ``window`` (chronological)."""
    ordered = sorted([e for e in events if predicate(e)], key=_parse_ts)
    groups: list[tuple[list[dict[str, Any]], datetime]] = []
    current: list[dict[str, Any]] = []
    for event in ordered:
        if not current:
            current = [event]
            continue
        if _parse_ts(event) - _parse_ts(current[-1]) <= window:
            current.append(event)
        else:
            if len(current) >= 2:
                groups.append((current, max(_parse_ts(e) for e in current)))
            current = [event]
    if len(current) >= 2:
        groups.append((current, max(_parse_ts(e) for e in current)))
    return groups


def _event_identity(event: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(event.get("app") or ""),
        str(event.get("event") or ""),
        str(event.get("timestamp") or ""),
    )


def _build_rollup_items(
    events: list[dict[str, Any]],
    *,
    now: datetime,
) -> tuple[set[tuple[str, str, str]], list[ActivityFeedItem]]:
    rollup_items: list[ActivityFeedItem] = []
    consumed: set[tuple[str, str, str]] = set()
    pool = [e for e in events if _parse_ts(e) != datetime.min.replace(tzinfo=timezone.utc)]
    pool = [e for e in pool if now - _parse_ts(e) <= TODAY_ROLLUP_WINDOW]

    for app in ("baseball", "nba"):
        app_pool = [e for e in pool if str(e.get("app") or "") == app]
        for cluster, latest in _group_rollup_events(
            app_pool,
            window=RECENT_ROLLUP_WINDOW,
            predicate=lambda e, a=app: _event_key(e) in COMPARISON_ROLLUP_EVENTS
            and str(e.get("app") or "") == a,
        ):
            msg = _rollup_comparison_message(app, len(cluster))
            rollup_items.append(
                _make_feed_item(None, app=app, message=msg, sort_key=latest, is_rollup=True)
            )
            for e in cluster:
                consumed.add(_event_identity(e))

    for cluster, latest in _group_rollup_events(
        [e for e in pool if str(e.get("app") or "") == "music"],
        window=RECENT_ROLLUP_WINDOW,
        predicate=lambda e: _event_key(e) in MUSIC_PRACTICE_ROLLUP_EVENTS,
    ):
        msg = _rollup_music_practice_message(cluster)
        rollup_items.append(
            _make_feed_item(None, app="music", message=msg, sort_key=latest, is_rollup=True)
        )
        for e in cluster:
            consumed.add(_event_identity(e))

    for cluster, latest in _group_rollup_events(
        [e for e in pool if str(e.get("app") or "") == "investment"],
        window=RECENT_ROLLUP_WINDOW,
        predicate=lambda e: str(e.get("event") or "") in INVESTMENT_PORTFOLIO_SESSION_EVENTS,
    ):
        msg = _rollup_portfolio_session_message(cluster)
        rollup_items.append(
            _make_feed_item(None, app="investment", message=msg, sort_key=latest, is_rollup=True)
        )
        for e in cluster:
            consumed.add(_event_identity(e))

    for cluster, latest in _group_rollup_events(
        [e for e in pool if str(e.get("app") or "") == "nba"],
        window=RECENT_ROLLUP_WINDOW,
        predicate=lambda e: str(e.get("event") or "") in NBA_ANALYSIS_ROLLUP_EVENTS,
    ):
        msg = _rollup_nba_analysis_message(len(cluster))
        rollup_items.append(
            _make_feed_item(None, app="nba", message=msg, sort_key=latest, is_rollup=True)
        )
        for e in cluster:
            consumed.add(_event_identity(e))

    return consumed, rollup_items


def build_activity_dashboard(
    events: list[dict[str, Any]],
    *,
    highlight_limit: int = 8,
    recent_limit: int = 15,
    now: datetime | None = None,
) -> ActivityDashboard:
    """Build Today's Work, Highlights, and Recent Activity sections."""
    if now is None:
        now = datetime.now(timezone.utc)

    today_summaries = build_today_summaries(events, now=now)
    remaining, synthetic_lines = _cluster_investment_setup(events)

    consumed_rollup_ids, rollup_items = _build_rollup_items(remaining, now=now)

    highlights: list[ActivityFeedItem] = []
    recent_candidates: list[ActivityFeedItem] = []

    for sort_key, app, message in synthetic_lines:
        if now - sort_key <= HIGHLIGHT_MAX_AGE:
            highlights.append(
                _make_feed_item(
                    None,
                    app=app,
                    message=message,
                    sort_key=sort_key,
                    is_highlight=True,
                )
            )

    sorted_events = sorted(remaining, key=_parse_ts, reverse=True)
    seen: list[tuple[str, datetime, int]] = []

    for event in sorted_events:
        if _event_identity(event) in consumed_rollup_ids:
            continue

        ts = _parse_ts(event)
        app = str(event.get("app") or "")
        priority = _feed_priority(event)

        if _is_highlight_event(event, now=now):
            msg = _format_item_message(event, for_highlight=True)
            if msg:
                highlights.append(
                    _make_feed_item(
                        event,
                        app=app,
                        message=msg,
                        sort_key=ts,
                        is_highlight=True,
                    )
                )
            continue

        message = format_activity_message(event, for_feed=True)
        if not message:
            continue
        if priority <= 0:
            continue
        if (app, str(event.get("event") or "")) in COMPARISON_ROLLUP_EVENTS:
            continue
        if (app, str(event.get("event") or "")) in MUSIC_PRACTICE_ROLLUP_EVENTS:
            continue
        if str(event.get("event") or "") in INVESTMENT_PORTFOLIO_SESSION_EVENTS and app == "investment":
            continue
        if str(event.get("event") or "") in NBA_ANALYSIS_ROLLUP_EVENTS and app == "nba":
            continue

        key = _dedupe_key(event)
        skip = False
        for prev_key, prev_ts, prev_pri in seen:
            if prev_key == key and abs((ts - prev_ts).total_seconds()) <= DEDUPE_WINDOW.total_seconds():
                if priority <= prev_pri:
                    skip = True
                    break
        if skip:
            continue
        seen.append((key, ts, priority))

        recent_candidates.append(
            _make_feed_item(event, app=app, message=message, sort_key=ts)
        )

    recent_candidates.extend(rollup_items)

    # Deduplicate highlights by message within window
    hl_ranked = sorted(highlights, key=lambda i: i.sort_key, reverse=True)
    hl_deduped: list[ActivityFeedItem] = []
    hl_seen: list[tuple[str, str, datetime]] = []
    for item in hl_ranked:
        norm = _normalize_feed_message(item.message)
        dup = False
        for app, prev_norm, prev_ts in hl_seen:
            if app == item.app and prev_norm == norm:
                if abs((item.sort_key - prev_ts).total_seconds()) <= MESSAGE_DEDUPE_WINDOW.total_seconds():
                    dup = True
                    break
        if dup:
            continue
        hl_deduped.append(item)
        hl_seen.append((item.app, norm, item.sort_key))

    recent_ranked = sorted(recent_candidates, key=lambda i: i.sort_key, reverse=True)
    recent_deduped: list[ActivityFeedItem] = []
    rc_seen: list[tuple[str, str, datetime]] = []
    for item in recent_ranked:
        norm = _normalize_feed_message(item.message)
        dup = False
        for app, prev_norm, prev_ts in rc_seen:
            if app == item.app and prev_norm == norm:
                if abs((item.sort_key - prev_ts).total_seconds()) <= MESSAGE_DEDUPE_WINDOW.total_seconds():
                    dup = True
                    break
        if dup:
            continue
        recent_deduped.append(item)
        rc_seen.append((item.app, norm, item.sort_key))

    return ActivityDashboard(
        today_summaries=today_summaries,
        highlights=tuple(hl_deduped[:highlight_limit]),
        recent=tuple(recent_deduped[:recent_limit]),
    )


def _dedupe_key(event: dict[str, Any]) -> str:
    app = str(event.get("app") or "")
    event_type = str(event.get("event") or "")
    if app == "investment" and event_type in INVESTMENT_SETUP_EVENTS | {"portfolio_created"}:
        msg = format_activity_message(event, for_feed=True)
        if msg:
            return f"{app}:msg:{_normalize_feed_message(msg)}"
    if app == "investment" and event_type == "holdings_updated":
        return f"{app}:holdings"
    return f"{app}:{event_type}"


def build_activity_feed(events: list[dict[str, Any]], *, limit: int = 20) -> list[ActivityFeedItem]:
    """Backward-compatible flat feed: highlights then recent, sorted by recency."""
    dashboard = build_activity_dashboard(
        events,
        highlight_limit=max(8, limit // 2),
        recent_limit=limit,
    )
    combined = list(dashboard.highlights) + [
        item for item in dashboard.recent if item not in dashboard.highlights
    ]
    combined.sort(key=lambda i: i.sort_key, reverse=True)
    seen_msgs: set[tuple[str, str]] = set()
    deduped: list[ActivityFeedItem] = []
    for item in combined:
        key = (item.app, _normalize_feed_message(item.message))
        if key in seen_msgs:
            continue
        seen_msgs.add(key)
        deduped.append(item)
    return deduped[:limit]


__all__ = (
    "APP_LABELS",
    "ActivityDashboard",
    "ActivityFeedItem",
    "build_activity_dashboard",
    "build_activity_feed",
    "format_activity_message",
    "investment_directory_rank",
    "music_directory_rank",
)
