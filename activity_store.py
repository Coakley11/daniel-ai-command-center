"""
Cross-app activity store for the Daniel AI Command Center.

SQLite-backed history + current state (see suite_storage.py), optional sibling-app
files (practice_history.json, per-app app_state.json), and resume items for the
Continue dashboard.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from suite_storage import (
    load_active_resume_items,
    load_current_states,
    load_events as _load_db_events,
    record_activity as _record_activity,
)

DATA_DIR = Path(__file__).resolve().parent / "data"
ACTIVITY_FILE = DATA_DIR / "suite_activity.json"

# Legacy suite event keys mapped to current homepage app keys.
ACTIVITY_APP_ALIASES: dict[str, str] = {
    "math": "applied_intelligence",
    "applied_intelligence": "applied_intelligence",
}

# Optional local paths to sibling-app logs (first match wins).
MUSIC_LOG_CANDIDATES = (
    Path(__file__).resolve().parent.parent / "ai-music-practice-coach" / "practice_history.json",
    Path.home() / "Documents" / "GitHub" / "ai-music-practice-coach" / "practice_history.json",
)

APP_REPO_DIRS: dict[str, str] = {
    "music": "ai-music-practice-coach",
    "baseball": "baseball-stat-app",
    "investment": "investment-portfolio-analyzer",
    "nba": "nba-playoff-companion-ai",
    "applied_intelligence": "Applied-mathematical-intelligence",
    "future_lens": "future-lens-ai-transition-simulator",
}

APP_STATE_CANDIDATES: dict[str, tuple[Path, ...]] = {
    "music": (
        Path(__file__).resolve().parent.parent / "ai-music-practice-coach" / "data" / "app_state.json",
        Path.home() / "Documents" / "GitHub" / "ai-music-practice-coach" / "data" / "app_state.json",
    ),
    "baseball": (
        Path(__file__).resolve().parent.parent / "baseball-stat-app" / "data" / "app_state.json",
        Path.home() / "Documents" / "GitHub" / "baseball-stat-app" / "data" / "app_state.json",
    ),
    "investment": (
        Path(__file__).resolve().parent.parent / "investment-portfolio-analyzer" / "data" / "app_state.json",
        Path.home() / "Documents" / "GitHub" / "investment-portfolio-analyzer" / "data" / "app_state.json",
    ),
    "applied_intelligence": (
        Path(__file__).resolve().parent.parent / "Applied-mathematical-intelligence" / "data" / "app_state.json",
        Path.home() / "Documents" / "GitHub" / "Applied-mathematical-intelligence" / "data" / "app_state.json",
    ),
    "future_lens": (
        Path(__file__).resolve().parent.parent / "future-lens-ai-transition-simulator" / "data" / "app_state.json",
        Path.home() / "Documents" / "GitHub" / "future-lens-ai-transition-simulator" / "data" / "app_state.json",
    ),
    "nba": (
        Path(__file__).resolve().parent.parent / "nba-playoff-companion-ai" / "data" / "app_state.json",
        Path.home() / "Documents" / "GitHub" / "nba-playoff-companion-ai" / "data" / "app_state.json",
    ),
}


@dataclass
class ActivitySnapshot:
    """Unified activity view for coach + summary sections."""

    loaded_at: datetime = field(default_factory=datetime.now)
    has_real_data: bool = False

    # Music
    last_music_practice_days_ago: int | None = None
    last_song: str = ""
    last_song_focus: str = ""
    last_instrument: str = ""
    last_display_key: str = ""
    music_minutes_this_week: float = 0.0
    songs_practiced_this_week: int = 0
    music_streak_days: int = 0

    # Investment
    last_portfolio_check_days_ago: int | None = None
    portfolio_checks_this_week: int = 0
    last_portfolio_review: str = ""

    # Baseball
    last_baseball_review_days_ago: int | None = None
    baseball_reviews_this_week: int = 0
    last_baseball_player: str = ""
    last_baseball_report: str = ""
    last_baseball_projection: str = ""
    is_sunday_lineup_day: bool = False

    # Basketball
    last_nba_session_days_ago: int | None = None
    nba_sessions_this_week: int = 0
    last_nba_team: str = ""
    last_nba_page: str = ""

    # Applied Intelligence
    last_applied_intelligence_days_ago: int | None = None
    applied_intelligence_sessions_this_week: int = 0
    last_applied_intelligence_page: str = ""
    last_applied_intelligence_analysis: str = ""
    last_applied_intelligence_lesson: str = ""
    applied_intelligence_next_lesson: str = ""

    # Future Lens
    last_future_lens_days_ago: int | None = None
    future_simulations_this_week: int = 0
    future_project: str = ""
    last_simulation_name: str = ""

    # Meta
    last_opened_app: str = ""
    last_opened_page: str = ""


def _parse_date(value: str) -> date | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%m/%d/%Y"):
        try:
            return datetime.strptime(value[:19], fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _days_ago(d: date | None) -> int | None:
    if d is None:
        return None
    return max(0, (date.today() - d).days)


def _week_start() -> date:
    today = date.today()
    return today - timedelta(days=today.weekday())


def _load_json(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]
    return []


def _load_json_dict(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return raw if isinstance(raw, dict) else {}


def _fallback_event_paths(app: str) -> tuple[Path, ...]:
    repo = APP_REPO_DIRS.get(app, "")
    names: list[Path] = [
        DATA_DIR / f"{app}_activity_fallback.json",
    ]
    if repo:
        names.extend(
            [
                Path(__file__).resolve().parent.parent / repo / "data" / f"{app}_activity_fallback.json",
                Path(__file__).resolve().parent.parent / repo / f"{app}_activity_fallback.json",
                Path.home() / "Documents" / "GitHub" / repo / "data" / f"{app}_activity_fallback.json",
            ]
        )
    return tuple(names)


def _load_fallback_events() -> list[dict[str, Any]]:
    """Per-app JSON logs written when SQLite is unavailable (isolated per deployment)."""
    merged: list[dict[str, Any]] = []
    for app in APP_REPO_DIRS:
        for path in _fallback_event_paths(app):
            if not path.is_file():
                continue
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(raw, list):
                continue
            for row in raw:
                if isinstance(row, dict) and row.get("app"):
                    merged.append(row)
            break
    return merged


def load_events() -> list[dict[str, Any]]:
    return _load_db_events()


def load_all_events(limit: int = 500) -> list[dict[str, Any]]:
    """SQLite history plus per-app fallback files (deduped, chronological)."""
    db_events = _load_db_events(limit=limit)
    fallbacks = _load_fallback_events()
    if not fallbacks:
        return db_events
    seen: set[tuple[str, str, str]] = set()
    combined: list[dict[str, Any]] = []
    for event in db_events + fallbacks:
        key = (
            str(event.get("app") or ""),
            str(event.get("timestamp") or ""),
            str(event.get("event") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        combined.append(event)
    combined.sort(key=lambda e: str(e.get("timestamp") or ""))
    return combined[-limit:]


def log_event(
    app: str,
    event: str,
    *,
    page: str = "",
    metrics: dict[str, Any] | None = None,
) -> None:
    """Append one activity event to the shared store."""
    _record_activity(app, event, page=page, metrics=metrics)


def _ingest_app_state_files(snapshot: ActivitySnapshot) -> None:
    """Merge per-app local state files when the shared DB has not been populated yet."""
    for app_key, candidates in APP_STATE_CANDIDATES.items():
        block: dict[str, Any] | None = None
        for path in candidates:
            raw = _load_json_dict(path)
            candidate = raw.get(app_key)
            if isinstance(candidate, dict) and candidate:
                block = candidate
                snapshot.has_real_data = True
                break
        if not block:
            continue
        page = str(block.get("page") or block.get("studio_page") or block.get("active_page") or "")
        summary = str(block.get("summary") or block.get("song") or block.get("title") or "")
        if app_key == "music":
            if block.get("song"):
                snapshot.last_song = str(block["song"])
            if block.get("focus"):
                snapshot.last_song_focus = str(block["focus"])
            if block.get("instrument"):
                snapshot.last_instrument = str(block["instrument"])
            if block.get("display_key"):
                snapshot.last_display_key = str(block["display_key"])
            if block.get("practice_focus_section"):
                snapshot.last_song_focus = str(block["practice_focus_section"])
        if app_key == "baseball" and block.get("player"):
            snapshot.last_baseball_player = str(block["player"])
        if app_key == "baseball" and block.get("report"):
            snapshot.last_baseball_report = str(block["report"])
        if app_key == "investment" and block.get("review_type"):
            snapshot.last_portfolio_review = str(block["review_type"])
        if app_key == "applied_intelligence":
            if page:
                snapshot.last_applied_intelligence_page = page
            if block.get("lesson"):
                snapshot.last_applied_intelligence_lesson = str(block["lesson"])
        if app_key == "future_lens":
            if block.get("project"):
                snapshot.future_project = str(block["project"])
            if block.get("simulation"):
                snapshot.last_simulation_name = str(block["simulation"])
        if app_key == "nba":
            if block.get("team"):
                snapshot.last_nba_team = str(block["team"])
            if block.get("page") or block.get("page_label"):
                snapshot.last_nba_page = str(block.get("page_label") or block.get("page") or "")
        if page and not snapshot.last_opened_page:
            snapshot.last_opened_app = app_key
            snapshot.last_opened_page = page
        if summary and app_key == snapshot.last_opened_app:
            pass  # summary consumed by continue cards via storage layer


def _ingest_music_logs(snapshot: ActivitySnapshot) -> None:
    for path in MUSIC_LOG_CANDIDATES:
        logs = _load_json(path)
        if not logs:
            continue

        snapshot.has_real_data = True
        week_start = _week_start()
        week_minutes = 0.0
        week_songs: set[str] = set()

        dated: list[tuple[date, dict[str, Any]]] = []
        for entry in logs:
            d = _parse_date(str(entry.get("date", "")))
            if d:
                dated.append((d, entry))

        if not dated:
            continue

        dated.sort(key=lambda x: x[0], reverse=True)
        latest_date, latest = dated[0]
        snapshot.last_music_practice_days_ago = _days_ago(latest_date)
        snapshot.last_song = str(latest.get("song") or latest.get("title") or "").strip()
        snapshot.last_song_focus = str(latest.get("focus") or latest.get("practice") or "").strip()
        snapshot.last_instrument = str(latest.get("instrument") or "").strip()

        for d, entry in dated:
            if d >= week_start:
                try:
                    week_minutes += float(entry.get("minutes") or 0)
                except (TypeError, ValueError):
                    pass
                song = str(entry.get("song") or "").strip()
                if song:
                    week_songs.add(song)

        snapshot.music_minutes_this_week = week_minutes
        snapshot.songs_practiced_this_week = len(week_songs)

        # Practice streak: consecutive calendar days with a log entry
        practice_dates = sorted({d for d, _ in dated}, reverse=True)
        streak = 0
        expected = date.today()
        for d in practice_dates:
            if d == expected or d == expected - timedelta(days=1):
                streak += 1
                expected = d - timedelta(days=1)
            else:
                break
        snapshot.music_streak_days = streak
        return


MEANINGFUL_WEEK_EVENTS = frozenset(
    {
        "session",
        "page_view",
        "analysis",
        "practice",
        "simulation",
        "portfolio_check",
        "lineup_review",
        "comparison",
        "trade_eval",
        "song_selected",
        "chord_save",
        "chart_save",
        "backing_track",
    }
)


@dataclass(frozen=True)
class WeeklySummary:
    music_minutes: float
    songs_practiced: int
    baseball_reviews: int
    portfolio_checks: int
    nba_sessions: int
    applied_intelligence_sessions: int
    future_simulations: int

    @property
    def has_any(self) -> bool:
        return any(
            (
                self.music_minutes > 0,
                self.songs_practiced > 0,
                self.baseball_reviews > 0,
                self.portfolio_checks > 0,
                self.nba_sessions > 0,
                self.applied_intelligence_sessions > 0,
                self.future_simulations > 0,
            )
        )


def get_weekly_summary(snapshot: ActivitySnapshot) -> WeeklySummary:
    return WeeklySummary(
        music_minutes=snapshot.music_minutes_this_week,
        songs_practiced=snapshot.songs_practiced_this_week,
        baseball_reviews=snapshot.baseball_reviews_this_week,
        portfolio_checks=snapshot.portfolio_checks_this_week,
        nba_sessions=snapshot.nba_sessions_this_week,
        applied_intelligence_sessions=snapshot.applied_intelligence_sessions_this_week,
        future_simulations=snapshot.future_simulations_this_week,
    )


def _ingest_suite_events(snapshot: ActivitySnapshot) -> None:
    events = load_all_events()
    if not events:
        return

    snapshot.has_real_data = True
    week_start = _week_start()
    week_start_dt = datetime.combine(week_start, datetime.min.time())

    by_app: dict[str, list[datetime]] = {}
    week_counts: dict[str, int] = {
        "investment": 0,
        "baseball": 0,
        "nba": 0,
        "applied_intelligence": 0,
        "future_lens": 0,
        "music": 0,
    }
    last_opened: tuple[str, str, datetime] | None = None

    for event in events:
        raw_app = str(event.get("app", "")).strip()
        app = ACTIVITY_APP_ALIASES.get(raw_app, raw_app)
        if not app:
            continue
        ts_raw = str(event.get("timestamp", ""))
        try:
            ts = datetime.fromisoformat(ts_raw)
        except ValueError:
            continue

        by_app.setdefault(app, []).append(ts)

        if ts >= week_start_dt:
            event_name = str(event.get("event", ""))
            metrics = event.get("metrics") or {}
            if app in week_counts and event_name in MEANINGFUL_WEEK_EVENTS:
                week_counts[app] += 1

            if app == "future_lens" and metrics.get("project"):
                snapshot.future_project = str(metrics["project"])
            if app == "future_lens" and metrics.get("simulation"):
                snapshot.last_simulation_name = str(metrics["simulation"])
            if app == "applied_intelligence" and metrics.get("next_lesson"):
                snapshot.applied_intelligence_next_lesson = str(metrics["next_lesson"])
            if app == "applied_intelligence" and metrics.get("lesson"):
                snapshot.last_applied_intelligence_lesson = str(metrics["lesson"])
            if app == "applied_intelligence" and metrics.get("analysis"):
                snapshot.last_applied_intelligence_analysis = str(metrics["analysis"])
            if app == "applied_intelligence" and event.get("page"):
                snapshot.last_applied_intelligence_page = str(event.get("page") or "")
            if app == "investment" and metrics.get("review_type"):
                snapshot.last_portfolio_review = str(metrics["review_type"])
            if app == "baseball" and metrics.get("player"):
                snapshot.last_baseball_player = str(metrics["player"])
            if app == "baseball" and metrics.get("report"):
                snapshot.last_baseball_report = str(metrics["report"])
            if app == "baseball" and metrics.get("projection"):
                snapshot.last_baseball_projection = str(metrics["projection"])
            if app == "music" and metrics.get("instrument"):
                snapshot.last_instrument = str(metrics["instrument"])
            if app == "nba" and metrics.get("team"):
                snapshot.last_nba_team = str(metrics["team"])
            if app == "nba" and metrics.get("page"):
                snapshot.last_nba_page = str(metrics["page"])
            if app == "music" and not snapshot.last_song and metrics.get("song"):
                snapshot.last_song = str(metrics["song"])
            if app == "music" and metrics.get("focus"):
                snapshot.last_song_focus = str(metrics["focus"])
            if app == "music" and metrics.get("display_key"):
                snapshot.last_display_key = str(metrics["display_key"])

        if last_opened is None or ts >= last_opened[2]:
            last_opened = (app, str(event.get("page") or ""), ts)

    if last_opened:
        snapshot.last_opened_app = last_opened[0]
        snapshot.last_opened_page = last_opened[1]

    current_states = load_current_states()
    newest_state: tuple[str, str, str] | None = None
    for app_key, state in current_states.items():
        page = str(state.get("page") or "")
        metrics = state.get("metrics") or {}
        updated_at = str(state.get("updated_at") or "")
        if app_key == "music" and metrics.get("song"):
            snapshot.last_song = str(metrics["song"])
        if app_key == "music" and metrics.get("instrument"):
            snapshot.last_instrument = str(metrics["instrument"])
        if app_key == "applied_intelligence" and page:
            snapshot.last_applied_intelligence_page = page
        if app_key == "future_lens" and metrics.get("project"):
            snapshot.future_project = str(metrics["project"])
        if updated_at and (newest_state is None or updated_at >= newest_state[2]):
            newest_state = (app_key, page, updated_at)
    if newest_state and newest_state[2] >= (last_opened[2].isoformat() if last_opened else ""):
        snapshot.last_opened_app = newest_state[0]
        snapshot.last_opened_page = newest_state[1]

    def _latest_days(app: str) -> int | None:
        times = by_app.get(app)
        if not times:
            return None
        return _days_ago(max(times).date())

    if snapshot.last_portfolio_check_days_ago is None:
        snapshot.last_portfolio_check_days_ago = _latest_days("investment")
    if snapshot.last_baseball_review_days_ago is None:
        snapshot.last_baseball_review_days_ago = _latest_days("baseball")
    if snapshot.last_nba_session_days_ago is None:
        snapshot.last_nba_session_days_ago = _latest_days("nba")
    if snapshot.last_applied_intelligence_days_ago is None:
        snapshot.last_applied_intelligence_days_ago = _latest_days("applied_intelligence")
    if snapshot.last_future_lens_days_ago is None:
        snapshot.last_future_lens_days_ago = _latest_days("future_lens")
    if snapshot.last_music_practice_days_ago is None:
        snapshot.last_music_practice_days_ago = _latest_days("music")

    snapshot.portfolio_checks_this_week = week_counts["investment"]
    snapshot.baseball_reviews_this_week = week_counts["baseball"]
    snapshot.nba_sessions_this_week = week_counts["nba"]
    snapshot.applied_intelligence_sessions_this_week = week_counts["applied_intelligence"]
    snapshot.future_simulations_this_week = week_counts["future_lens"]


def load_activity_snapshot() -> ActivitySnapshot:
    snapshot = ActivitySnapshot(is_sunday_lineup_day=date.today().weekday() == 6)
    _ingest_music_logs(snapshot)
    _ingest_suite_events(snapshot)
    _ingest_app_state_files(snapshot)
    return snapshot


def get_resume_item_count() -> int:
    return len(load_active_resume_items(limit=20))


def format_days_ago(days: int | None) -> str:
    if days is None:
        return "No activity yet"
    if days == 0:
        return "Today"
    if days == 1:
        return "Yesterday"
    return f"{days} days ago"


@dataclass(frozen=True)
class AppDirectoryCard:
    """Compact launch card: dynamic highlights + optional last-active hint."""

    highlights: tuple[str, ...]
    when: str | None


def _app_last_active_days(snapshot: ActivitySnapshot, app_key: str) -> int | None:
    return {
        "music": snapshot.last_music_practice_days_ago,
        "investment": snapshot.last_portfolio_check_days_ago,
        "baseball": snapshot.last_baseball_review_days_ago,
        "nba": snapshot.last_nba_session_days_ago,
        "applied_intelligence": snapshot.last_applied_intelligence_days_ago,
        "future_lens": snapshot.last_future_lens_days_ago,
    }.get(app_key)


def _labeled(label: str, value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        return ""
    return f"{label}: {cleaned}"


def get_app_directory_card(snapshot: ActivitySnapshot, app_key: str) -> AppDirectoryCard:
    """Scannable highlights for the App Directory — short labels, real values only."""
    lines: list[str] = []

    if app_key == "music":
        if snapshot.last_song:
            lines.append(_labeled("Last song", snapshot.last_song))
        if snapshot.last_instrument:
            lines.append(_labeled("Instrument", snapshot.last_instrument))
        if snapshot.music_streak_days > 0:
            days_word = "day" if snapshot.music_streak_days == 1 else "days"
            lines.append(_labeled("Streak", f"{snapshot.music_streak_days} {days_word}"))
    elif app_key == "investment":
        if snapshot.last_portfolio_review:
            lines.append(_labeled("Last review", snapshot.last_portfolio_review))
    elif app_key == "baseball":
        player = snapshot.last_baseball_player or snapshot.last_baseball_projection
        if player:
            lines.append(_labeled("Last player", player))
        if snapshot.last_baseball_report:
            lines.append(_labeled("Last report", snapshot.last_baseball_report))
    elif app_key == "nba":
        if snapshot.last_nba_team:
            lines.append(_labeled("Last team", snapshot.last_nba_team))
        if snapshot.last_nba_page:
            lines.append(_labeled("Last page", snapshot.last_nba_page))
    elif app_key == "applied_intelligence":
        topic = (
            snapshot.last_applied_intelligence_analysis
            or snapshot.last_applied_intelligence_lesson
            or snapshot.applied_intelligence_next_lesson
            or snapshot.last_applied_intelligence_page
        )
        if topic:
            lines.append(_labeled("Last topic", topic))
    elif app_key == "future_lens":
        sim = snapshot.last_simulation_name or snapshot.future_project
        if sim:
            lines.append(_labeled("Last simulation", sim))

    lines = [line for line in lines if line]

    days = _app_last_active_days(snapshot, app_key)
    when = format_days_ago(days) if days is not None and lines else None

    if not lines:
        return AppDirectoryCard(highlights=("Ready to start.",), when=None)

    return AppDirectoryCard(highlights=tuple(lines[:3]), when=when)


def get_activity_rows(snapshot: ActivitySnapshot) -> list[dict[str, str]]:
    """Factual recent-activity rows for the Activity Summary section."""

    EMPTY_DETAILS: dict[str, str] = {
        "music": "No recent music practice detected",
        "investment": "No portfolio reviews detected",
        "baseball": "No baseball reports viewed yet",
        "nba": "No basketball sessions recorded yet",
        "applied_intelligence": "No activity recorded yet",
        "future_lens": "No simulations run yet",
    }

    def _detail(app: str, real: str) -> str:
        return real if real else EMPTY_DETAILS.get(app, "No activity recorded yet")

    rows = [
        {
            "App": "Music Practice Coach",
            "Last activity": format_days_ago(snapshot.last_music_practice_days_ago),
            "Details": _detail(
                "music",
                " · ".join(
                    p
                    for p in [
                        f"Last song: {snapshot.last_song}" if snapshot.last_song else "",
                        f"{snapshot.music_minutes_this_week:.0f} min this week"
                        if snapshot.music_minutes_this_week
                        else "",
                        f"{snapshot.music_streak_days}-day streak"
                        if snapshot.music_streak_days
                        else "",
                    ]
                    if p
                ),
            ),
        },
        {
            "App": "Investment Analytics",
            "Last activity": format_days_ago(snapshot.last_portfolio_check_days_ago),
            "Details": _detail(
                "investment",
                snapshot.last_portfolio_review
                or (
                    f"{snapshot.portfolio_checks_this_week} checks this week"
                    if snapshot.portfolio_checks_this_week
                    else ""
                ),
            ),
        },
        {
            "App": "Baseball Analytics",
            "Last activity": format_days_ago(snapshot.last_baseball_review_days_ago),
            "Details": _detail(
                "baseball",
                " · ".join(
                    p
                    for p in [
                        f"Last player: {snapshot.last_baseball_player}"
                        if snapshot.last_baseball_player
                        else "",
                        f"Last report: {snapshot.last_baseball_report}" if snapshot.last_baseball_report else "",
                        f"Last projection: {snapshot.last_baseball_projection}"
                        if snapshot.last_baseball_projection
                        else "",
                    ]
                    if p
                ),
            ),
        },
        {
            "App": "Basketball Companion",
            "Last activity": format_days_ago(snapshot.last_nba_session_days_ago),
            "Details": _detail(
                "nba",
                " · ".join(
                    p
                    for p in [
                        f"Last team: {snapshot.last_nba_team}" if snapshot.last_nba_team else "",
                        f"Last page: {snapshot.last_nba_page}" if snapshot.last_nba_page else "",
                    ]
                    if p
                ),
            ),
        },
        {
            "App": "Applied Intelligence",
            "Last activity": format_days_ago(snapshot.last_applied_intelligence_days_ago),
            "Details": _detail(
                "applied_intelligence",
                " · ".join(
                    p
                    for p in [
                        f"Last opened: {snapshot.last_applied_intelligence_page}"
                        if snapshot.last_applied_intelligence_page
                        else "",
                        f"{snapshot.applied_intelligence_sessions_this_week} sessions this week"
                        if snapshot.applied_intelligence_sessions_this_week
                        else "",
                        f"Last analysis: {snapshot.last_applied_intelligence_analysis}"
                        if snapshot.last_applied_intelligence_analysis
                        else "",
                        snapshot.last_applied_intelligence_lesson
                        or snapshot.applied_intelligence_next_lesson,
                    ]
                    if p
                ),
            ),
        },
        {
            "App": "AI Future Simulator",
            "Last activity": format_days_ago(snapshot.last_future_lens_days_ago),
            "Details": _detail(
                "future_lens",
                snapshot.last_simulation_name or snapshot.future_project,
            ),
        },
    ]
    return rows
