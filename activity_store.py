"""
Cross-app activity store for the Daniel AI Command Center.

Reads a shared JSON event log plus optional sibling-app data files (e.g. music
practice_history.json). Apps can append events via log_event() over time.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent / "data"
ACTIVITY_FILE = DATA_DIR / "suite_activity.json"

# Optional local paths to sibling-app logs (first match wins).
MUSIC_LOG_CANDIDATES = (
    Path(__file__).resolve().parent.parent / "ai-music-practice-coach" / "practice_history.json",
    Path.home() / "Documents" / "GitHub" / "ai-music-practice-coach" / "practice_history.json",
)


@dataclass
class ActivitySnapshot:
    """Unified activity view for coach + summary sections."""

    loaded_at: datetime = field(default_factory=datetime.now)
    has_real_data: bool = False

    # Music
    last_music_practice_days_ago: int | None = None
    last_song: str = ""
    last_song_focus: str = ""
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
    last_baseball_report: str = ""
    last_baseball_projection: str = ""
    is_sunday_lineup_day: bool = False

    # Basketball
    last_nba_session_days_ago: int | None = None
    nba_sessions_this_week: int = 0
    last_nba_team: str = ""
    last_nba_page: str = ""

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


def _ensure_activity_file() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not ACTIVITY_FILE.is_file():
        ACTIVITY_FILE.write_text("[]", encoding="utf-8")


def load_events() -> list[dict[str, Any]]:
    _ensure_activity_file()
    return _load_json(ACTIVITY_FILE)


def log_event(
    app: str,
    event: str,
    *,
    page: str = "",
    metrics: dict[str, Any] | None = None,
) -> None:
    """Append one activity event to the shared log."""
    _ensure_activity_file()
    events = load_events()
    events.append(
        {
            "app": app,
            "event": event,
            "page": page,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "metrics": metrics or {},
        }
    )
    ACTIVITY_FILE.write_text(json.dumps(events[-500:], indent=2), encoding="utf-8")


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


def _ingest_suite_events(snapshot: ActivitySnapshot) -> None:
    events = load_events()
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
        "future_lens": 0,
        "music": 0,
    }

    for event in events:
        app = str(event.get("app", "")).strip()
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
            if app in week_counts and event_name in {
                "session",
                "page_view",
                "analysis",
                "practice",
                "simulation",
                "portfolio_check",
                "lineup_review",
            }:
                week_counts[app] += 1

            if app == "future_lens" and metrics.get("project"):
                snapshot.future_project = str(metrics["project"])
            if app == "future_lens" and metrics.get("simulation"):
                snapshot.last_simulation_name = str(metrics["simulation"])
            if app == "investment" and metrics.get("review_type"):
                snapshot.last_portfolio_review = str(metrics["review_type"])
            if app == "baseball" and metrics.get("report"):
                snapshot.last_baseball_report = str(metrics["report"])
            if app == "baseball" and metrics.get("projection"):
                snapshot.last_baseball_projection = str(metrics["projection"])
            if app == "nba" and metrics.get("team"):
                snapshot.last_nba_team = str(metrics["team"])
            if app == "nba" and metrics.get("page"):
                snapshot.last_nba_page = str(metrics["page"])
            if app == "music" and not snapshot.last_song and metrics.get("song"):
                snapshot.last_song = str(metrics["song"])

        if app == snapshot.last_opened_app or not snapshot.last_opened_app:
            if not snapshot.last_opened_app or ts >= by_app.get(snapshot.last_opened_app, [datetime.min])[-1]:
                snapshot.last_opened_app = app
                snapshot.last_opened_page = str(event.get("page") or "")

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
    if snapshot.last_future_lens_days_ago is None:
        snapshot.last_future_lens_days_ago = _latest_days("future_lens")
    if snapshot.last_music_practice_days_ago is None:
        snapshot.last_music_practice_days_ago = _latest_days("music")

    snapshot.portfolio_checks_this_week = week_counts["investment"]
    snapshot.baseball_reviews_this_week = week_counts["baseball"]
    snapshot.nba_sessions_this_week = week_counts["nba"]
    snapshot.future_simulations_this_week = week_counts["future_lens"]


def load_activity_snapshot() -> ActivitySnapshot:
    snapshot = ActivitySnapshot(is_sunday_lineup_day=date.today().weekday() == 6)
    _ingest_music_logs(snapshot)
    _ingest_suite_events(snapshot)
    return snapshot


def format_days_ago(days: int | None) -> str:
    if days is None:
        return "No activity yet"
    if days == 0:
        return "Today"
    if days == 1:
        return "Yesterday"
    return f"{days} days ago"


def get_activity_rows(snapshot: ActivitySnapshot) -> list[dict[str, str]]:
    """Factual recent-activity rows for the Activity Summary section."""

    EMPTY_DETAILS: dict[str, str] = {
        "music": "No recent music practice detected",
        "investment": "No portfolio reviews detected",
        "baseball": "No baseball reports viewed yet",
        "nba": "No basketball sessions recorded yet",
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
            "App": "AI Future Simulator",
            "Last activity": format_days_ago(snapshot.last_future_lens_days_ago),
            "Details": _detail(
                "future_lens",
                snapshot.last_simulation_name or snapshot.future_project,
            ),
        },
    ]
    return rows
