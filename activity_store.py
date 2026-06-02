"""
Cross-app activity store for the Daniel AI Command Center.

SQLite-backed history + current state (see suite_storage.py), optional sibling-app
files (practice_history.json, per-app ``*_user_state.json``, legacy app_state.json),
and resume items for the Continue dashboard.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from activity_feed import format_activity_message, investment_directory_rank, music_directory_rank

from app_registry import get_app_url
from suite_storage import (
    load_active_resume_items,
    load_current_states,
    load_events as _load_db_events,
    record_activity as _record_activity,
    save_current_state,
    upsert_resume_item,
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

def _user_state_paths(app_key: str) -> tuple[Path, ...]:
    """Per-app ``data/{app}_user_state.json`` written by suite persistence."""
    repo = APP_REPO_DIRS.get(app_key, "")
    fname = f"{app_key}_user_state.json"
    if not repo:
        return ()
    return (
        Path(__file__).resolve().parent.parent / repo / "data" / fname,
        Path.home() / "Documents" / "GitHub" / repo / "data" / fname,
    )


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
    last_music_artist: str = ""
    last_music_edit_label: str = ""
    music_minutes_this_week: float = 0.0
    songs_practiced_this_week: int = 0
    music_streak_days: int = 0
    music_uploads_this_week: int = 0
    music_verified_edits_this_week: int = 0
    music_lyrics_edits_this_week: int = 0
    music_backing_sessions_this_week: int = 0
    last_music_upload_days_ago: int | None = None
    last_recording_review_days_ago: int | None = None
    last_music_edit_days_ago: int | None = None
    last_instrument_practice_days_ago: int | None = None
    music_directory_primary: str = ""
    music_overedited_song: str = ""

    # Investment
    last_portfolio_check_days_ago: int | None = None
    portfolio_checks_this_week: int = 0
    last_portfolio_review: str = ""
    last_investment_goal: str = ""
    last_investment_holdings_count: int = 0
    last_investment_risk_profile: str = ""
    investment_directory_primary: str = ""
    investment_scenarios_this_week: int = 0
    investment_optimizer_runs_this_week: int = 0
    investment_holdings_updates_this_week: int = 0
    investment_goals_selected_this_week: int = 0
    investment_last_holdings_update_days_ago: int | None = None
    investment_last_allocation_review_days_ago: int | None = None
    investment_last_scenario_days_ago: int | None = None
    investment_last_rebalance_review_days_ago: int | None = None
    investment_last_portfolio_created_days_ago: int | None = None

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

    # Meta / cross-app
    last_opened_app: str = ""
    last_opened_page: str = ""
    week_activity_by_app: dict[str, int] = field(default_factory=dict)
    top_project_label: str = ""
    top_research_area: str = ""
    pending_review_count: int = 0
    music_practice_sessions_this_week: int = 0
    baseball_analyses_this_week: int = 0
    nba_analyses_this_week: int = 0
    applied_lessons_completed_this_week: int = 0
    investment_rebalance_reviews_this_week: int = 0


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


def _flatten_user_state_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Unwrap ``{version, state: {core, session}}`` or flat ``state`` into one dict."""
    state = payload.get("state")
    if isinstance(state, dict):
        flat: dict[str, Any] = {}
        core = state.get("core")
        session = state.get("session")
        if isinstance(core, dict):
            flat.update(core)
        if isinstance(session, dict):
            flat.update(session)
        if flat:
            return flat
        return dict(state)
    if isinstance(payload.get("core"), dict) or isinstance(payload.get("session"), dict):
        flat = {}
        if isinstance(payload.get("core"), dict):
            flat.update(payload["core"])
        if isinstance(payload.get("session"), dict):
            flat.update(payload["session"])
        return flat
    return payload


def load_app_user_state_block(app_key: str) -> dict[str, Any]:
    """Load persisted session state from per-app user_state JSON (preferred) or legacy app_state."""
    for path in _user_state_paths(app_key):
        raw = _load_json_dict(path)
        flat = _flatten_user_state_payload(raw)
        if flat:
            return flat
    for path in APP_STATE_CANDIDATES.get(app_key, ()):
        raw = _load_json_dict(path)
        candidate = raw.get(app_key)
        if isinstance(candidate, dict) and candidate:
            return _flatten_user_state_payload(candidate)
    return {}


def _apply_block_to_snapshot(app_key: str, block: dict[str, Any], snapshot: ActivitySnapshot) -> None:
    page = str(block.get("page") or block.get("studio_page") or block.get("active_page") or "")
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
        if page and snapshot.last_music_practice_days_ago is None:
            snapshot.last_music_practice_days_ago = 0
    if app_key == "baseball" and block.get("player"):
        snapshot.last_baseball_player = str(block["player"])
    if app_key == "baseball" and block.get("report"):
        snapshot.last_baseball_report = str(block["report"])
    if app_key == "investment":
        review = str(block.get("review_type") or block.get("health_active_tab") or "").strip()
        if review:
            snapshot.last_portfolio_review = review
        if snapshot.last_portfolio_check_days_ago is None and (
            block.get("holdings_df") or block.get("sidebar_portfolio_value")
        ):
            snapshot.last_portfolio_check_days_ago = 0
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
        team = str(
            block.get("team")
            or block.get("favorite_team")
            or block.get("favorite_team_sidebar")
            or ""
        ).strip()
        if team:
            snapshot.last_nba_team = team
        nba_page = str(block.get("page_label") or block.get("page_label_last") or block.get("page_override") or "")
        if nba_page:
            snapshot.last_nba_page = nba_page
        if snapshot.last_nba_session_days_ago is None and (team or nba_page):
            snapshot.last_nba_session_days_ago = 0
    if page and not snapshot.last_opened_page:
        snapshot.last_opened_app = app_key
        snapshot.last_opened_page = page


def _disk_resume_from_block(app_key: str, block: dict[str, Any]) -> tuple[str, str, str, str, str, dict[str, Any]] | None:
    """Return page, summary, resume_key, title, subtitle, metrics — or None if nothing to show."""
    page = str(
        block.get("page")
        or block.get("studio_page")
        or block.get("active_page")
        or block.get("health_active_tab")
        or block.get("page_label_last")
        or block.get("page_override")
        or ""
    ).strip()
    metrics: dict[str, Any] = {}

    if app_key == "music":
        song = str(block.get("song") or "").strip()
        if not song:
            return None
        artist = str(block.get("artist") or "").strip()
        pick_key = str(block.get("pick_key") or song).strip()
        metrics = {
            "song": song,
            "artist": artist,
            "instrument": str(block.get("instrument") or ""),
            "focus": str(block.get("focus") or block.get("practice_focus_section") or ""),
            "display_key": str(block.get("display_key") or ""),
        }
        subtitle = " · ".join(p for p in [artist, page] if p)
        return (
            page,
            f"Practice {song}",
            f"song:{pick_key}",
            f"Continue: {song}",
            subtitle,
            metrics,
        )

    if app_key == "investment":
        holdings = block.get("holdings_df")
        n_holdings = len(holdings) if isinstance(holdings, list) else 0
        exp = str(block.get("experience") or "").strip()
        val = block.get("sidebar_portfolio_value")
        parts = [p for p in [exp, page or str(block.get("health_active_tab") or "")] if p]
        if isinstance(val, (int, float)) and val:
            parts.append(f"${float(val):,.0f}")
        if n_holdings:
            parts.append(f"{n_holdings} holdings")
        if not parts and not page:
            return None
        metrics = {"review_type": page or exp, "holdings": n_holdings}
        return (
            page or "Portfolio Health",
            "Portfolio review",
            "portfolio:main",
            "Continue portfolio review",
            " · ".join(parts),
            metrics,
        )

    if app_key == "baseball":
        active = page or str(block.get("active_page") or "").strip()
        if not active:
            return None
        return (
            active,
            active,
            f"page:{active}",
            f"Return to {active}",
            "",
            {"page": active},
        )

    if app_key == "nba":
        team = str(
            block.get("team")
            or block.get("favorite_team")
            or block.get("favorite_team_sidebar")
            or ""
        ).strip()
        nba_page = str(block.get("page_label_last") or block.get("page_override") or page or "").strip()
        if not team and not nba_page:
            return None
        metrics = {"team": team, "page": nba_page}
        title = f"Continue: {team}" if team else f"Return to {nba_page}"
        subtitle = nba_page if team and nba_page else team or nba_page
        return (
            nba_page or page,
            team or nba_page,
            f"nba:{team or nba_page}",
            title,
            subtitle if subtitle != title else "",
            metrics,
        )

    if app_key == "applied_intelligence":
        lesson = str(block.get("lesson") or block.get("next_lesson") or "").strip()
        if not lesson and not page:
            return None
        metrics = {"lesson": lesson} if lesson else {}
        title = f"Continue: {lesson}" if lesson else f"Return to {page}"
        return (page, lesson or page, f"lesson:{lesson or page}", title, page, metrics)

    if app_key == "future_lens":
        sim = str(block.get("simulation") or block.get("project") or "").strip()
        if not sim:
            return None
        metrics = {"simulation": sim, "project": str(block.get("project") or "")}
        return (page, sim, f"sim:{sim}", f"Continue: {sim}", page, metrics)

    return None


def _sync_disk_user_states_to_storage() -> None:
    """Mirror sibling-app ``*_user_state.json`` files into SQLite for Continue + highlights."""
    for app_key in APP_REPO_DIRS:
        block = load_app_user_state_block(app_key)
        if not block:
            continue
        payload = _disk_resume_from_block(app_key, block)
        if not payload:
            continue
        page, summary, resume_key, title, subtitle, metrics = payload
        save_current_state(app_key, page=page, summary=summary, metrics=metrics)
        upsert_resume_item(
            app_key,
            resume_key,
            title=title,
            subtitle=subtitle,
            action_url=get_app_url(app_key),
        )


def _ingest_app_state_files(snapshot: ActivitySnapshot) -> None:
    """Merge per-app persisted session files into the activity snapshot."""
    for app_key in APP_STATE_CANDIDATES:
        block = load_app_user_state_block(app_key)
        if not block:
            continue
        snapshot.has_real_data = True
        _apply_block_to_snapshot(app_key, block, snapshot)


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
        "analysis",
        "practice",
        "simulation",
        "portfolio_check",
        "portfolio_health_checked",
        "portfolio_created",
        "allocation_reviewed",
        "optimizer_run",
        "macro_environment_applied",
        "scenario_run",
        "rebalance_reviewed",
        "lineup_review",
        "comparison",
        "trade_eval",
        "draft_prep",
        "sleeper_review",
        "projection_report",
        "roster_built",
        "chord_save",
        "chart_save",
        "backing_track",
        "backing_track_completed",
        "verified_chart_saved",
        "lyrics_saved",
        "video_uploaded",
        "audio_uploaded",
        "recording_reviewed",
        "lesson_completed",
        "case_study_completed",
        "concept_explored",
        "matchup_analysis",
        "injury_review",
        "playoff_simulation",
        "player_comparison",
        "game_outlook",
        "playoff_tracking",
        "timeline_completed",
        "career_scenario",
        "skill_review",
    }
)


def _apply_music_edit_metrics(snapshot: ActivitySnapshot, metrics: dict[str, Any], event_name: str) -> None:
    """Promote chart/lyrics saves to snapshot highlights (overrides passive song_selected)."""
    song = str(metrics.get("song") or metrics.get("last_edited_song") or "").strip()
    if not song:
        return
    snapshot.last_song = song
    artist = str(metrics.get("artist") or "").strip()
    if artist:
        snapshot.last_music_artist = artist
    fields = metrics.get("edited_fields") or []
    if not isinstance(fields, list):
        fields = []
    field_set = {str(f) for f in fields}
    if event_name == "lyrics_saved" or field_set == {"lyrics"}:
        snapshot.last_music_edit_label = "Saved verified lyrics"
    elif field_set >= {"chords", "lyrics"}:
        snapshot.last_music_edit_label = "Saved verified chart & lyrics"
    elif "chords" in field_set or event_name == "verified_chart_saved":
        snapshot.last_music_edit_label = "Saved verified chords"
    else:
        snapshot.last_music_edit_label = "Song edit saved"
    snapshot.last_music_practice_days_ago = 0
    snapshot.has_real_data = True


def _import_sibling_fallback_events() -> None:
    """Merge per-app fallback JSON from sibling repos into the Command Center SQLite log."""
    existing: set[tuple[str, str, str]] = set()
    for row in _load_db_events(limit=500):
        metrics = row.get("metrics") if isinstance(row.get("metrics"), dict) else {}
        song = str(metrics.get("song") or metrics.get("last_edited_song") or "")
        existing.add(
            (
                str(row.get("app") or ""),
                str(row.get("event") or ""),
                song,
            )
        )
    for event in _load_fallback_events():
        metrics = event.get("metrics") if isinstance(event.get("metrics"), dict) else {}
        song = str(metrics.get("song") or metrics.get("last_edited_song") or "")
        key = (str(event.get("app") or ""), str(event.get("event") or ""), song)
        if key in existing and song:
            continue
        if not song and (
            str(event.get("app") or ""),
            str(event.get("event") or ""),
            str(event.get("timestamp") or ""),
        ) in {
            (str(r.get("app") or ""), str(r.get("event") or ""), str(r.get("timestamp") or ""))
            for r in _load_db_events(limit=500)
        }:
            continue
        try:
            log_event(
                str(event.get("app") or ""),
                str(event.get("event") or "session"),
                page=str(event.get("page") or ""),
                metrics=event.get("metrics") if isinstance(event.get("metrics"), dict) else {},
            )
        except OSError:
            continue


# Public API — keep in sync with ai_command_center.py imports (see tests/test_import_smoke.py).
__all__ = (
    "ActivitySnapshot",
    "AppDirectoryCard",
    "WeeklySummary",
    "format_days_ago",
    "get_activity_rows",
    "get_app_directory_card",
    "get_resume_item_count",
    "get_weekly_summary",
    "load_activity_snapshot",
    "load_all_events",
    "load_events",
    "log_event",
)


@dataclass(frozen=True)
class WeeklySummary:
    music_minutes: float
    songs_practiced: int
    music_practice_sessions: int
    music_uploads: int
    music_verified_edits: int
    music_lyrics_edits: int
    music_backing_sessions: int
    baseball_analyses: int
    portfolio_checks: int
    investment_scenarios: int
    investment_optimizer_runs: int
    investment_rebalance_reviews: int
    nba_analyses: int
    applied_lessons_completed: int
    future_simulations: int

    @property
    def has_any(self) -> bool:
        return any(
            (
                self.music_minutes > 0,
                self.songs_practiced > 0,
                self.music_practice_sessions > 0,
                self.music_uploads > 0,
                self.music_verified_edits > 0,
                self.music_lyrics_edits > 0,
                self.music_backing_sessions > 0,
                self.baseball_analyses > 0,
                self.portfolio_checks > 0,
                self.investment_scenarios > 0,
                self.investment_optimizer_runs > 0,
                self.investment_rebalance_reviews > 0,
                self.nba_analyses > 0,
                self.applied_lessons_completed > 0,
                self.future_simulations > 0,
            )
        )


def get_weekly_summary(snapshot: ActivitySnapshot) -> WeeklySummary:
    return WeeklySummary(
        music_minutes=snapshot.music_minutes_this_week,
        songs_practiced=snapshot.songs_practiced_this_week,
        music_practice_sessions=snapshot.music_practice_sessions_this_week,
        music_uploads=snapshot.music_uploads_this_week,
        music_verified_edits=snapshot.music_verified_edits_this_week,
        music_lyrics_edits=snapshot.music_lyrics_edits_this_week,
        music_backing_sessions=snapshot.music_backing_sessions_this_week,
        baseball_analyses=snapshot.baseball_analyses_this_week,
        portfolio_checks=snapshot.portfolio_checks_this_week,
        investment_scenarios=snapshot.investment_scenarios_this_week,
        investment_optimizer_runs=snapshot.investment_optimizer_runs_this_week,
        investment_rebalance_reviews=snapshot.investment_rebalance_reviews_this_week,
        nba_analyses=snapshot.nba_analyses_this_week,
        applied_lessons_completed=snapshot.applied_lessons_completed_this_week,
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
    music_dir_rank = 0
    music_dir_ts = datetime.min
    music_dir_line = ""
    inv_dir_rank = 0
    inv_dir_ts = datetime.min
    inv_dir_line = ""
    inv_health_week = 0
    music_edit_week: Counter[str] = Counter()
    inv_portfolio_ts: datetime | None = None
    inv_health_ts: datetime | None = None
    inv_holdings_ts: datetime | None = None
    inv_allocation_ts: datetime | None = None
    inv_scenario_ts: datetime | None = None
    inv_rebalance_ts: datetime | None = None
    music_practice_week: set[str] = set()
    last_upload_ts: datetime | None = None
    last_review_ts: datetime | None = None
    last_edit_ts: datetime | None = None
    last_instrument_practice: dict[str, datetime] = {}

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

        event_name = str(event.get("event", ""))
        metrics = event.get("metrics") if isinstance(event.get("metrics"), dict) else {}

        if app == "music":
            msg = format_activity_message(event)
            rank = music_directory_rank(event_name)
            if msg and rank and (
                rank > music_dir_rank or (rank == music_dir_rank and ts > music_dir_ts)
            ):
                music_dir_rank, music_dir_ts, music_dir_line = rank, ts, msg

            song_name = str(metrics.get("song") or metrics.get("last_edited_song") or "").strip()
            if event_name in {"verified_chart_saved", "lyrics_saved", "chart_save", "chord_save"}:
                if last_edit_ts is None or ts > last_edit_ts:
                    last_edit_ts = ts
                    snapshot.last_music_edit_days_ago = _days_ago(ts.date())
                if song_name and ts >= week_start_dt:
                    music_edit_week[song_name] += 1
                _apply_music_edit_metrics(snapshot, metrics, event_name)
            elif event_name in {"video_uploaded", "audio_uploaded"}:
                if last_upload_ts is None or ts > last_upload_ts:
                    last_upload_ts = ts
                if song_name:
                    snapshot.last_song = song_name
                    artist = str(metrics.get("artist") or "").strip()
                    if artist:
                        snapshot.last_music_artist = artist
            elif event_name == "practice":
                if ts >= week_start_dt:
                    snapshot.music_practice_sessions_this_week += 1
                if song_name:
                    snapshot.last_song = song_name
                    if ts >= week_start_dt:
                        music_practice_week.add(song_name)
                instrument = str(metrics.get("instrument") or "").strip()
                if instrument:
                    snapshot.last_instrument = instrument
                    last_instrument_practice[instrument] = ts
            elif event_name in {
                "backing_track_started",
                "backing_track_completed",
                "backing_track",
            }:
                if song_name:
                    snapshot.last_song = song_name

        if app == "investment":
            msg = format_activity_message(event)
            rank = investment_directory_rank(event_name)
            if msg and rank and (rank > inv_dir_rank or (rank == inv_dir_rank and ts > inv_dir_ts)):
                inv_dir_rank, inv_dir_ts, inv_dir_line = rank, ts, msg

            goal_title = str(
                metrics.get("goal_title") or metrics.get("goal") or ""
            ).strip()
            if goal_title:
                snapshot.last_investment_goal = goal_title
            if metrics.get("holdings_count") is not None:
                try:
                    snapshot.last_investment_holdings_count = int(metrics["holdings_count"])
                except (TypeError, ValueError):
                    pass
            risk = str(metrics.get("risk_profile") or metrics.get("objective") or "").strip()
            if risk:
                snapshot.last_investment_risk_profile = risk.replace("_", " ").title()
            review = str(metrics.get("review_type") or "").strip()
            if review:
                snapshot.last_portfolio_review = review

            if event_name == "portfolio_created":
                if inv_portfolio_ts is None or ts > inv_portfolio_ts:
                    inv_portfolio_ts = ts
                    snapshot.investment_last_portfolio_created_days_ago = _days_ago(ts.date())
            elif event_name in ("portfolio_health_checked", "portfolio_check"):
                if inv_health_ts is None or ts > inv_health_ts:
                    inv_health_ts = ts
                    snapshot.last_portfolio_check_days_ago = _days_ago(ts.date())
            elif event_name == "holdings_updated":
                if inv_holdings_ts is None or ts > inv_holdings_ts:
                    inv_holdings_ts = ts
                    snapshot.investment_last_holdings_update_days_ago = _days_ago(ts.date())
                tickers = metrics.get("tickers")
                if isinstance(tickers, list) and tickers:
                    snapshot.last_investment_holdings_count = len(tickers)
            elif event_name == "allocation_reviewed":
                if inv_allocation_ts is None or ts > inv_allocation_ts:
                    inv_allocation_ts = ts
                    snapshot.investment_last_allocation_review_days_ago = _days_ago(ts.date())
            elif event_name == "scenario_run":
                if inv_scenario_ts is None or ts > inv_scenario_ts:
                    inv_scenario_ts = ts
                    snapshot.investment_last_scenario_days_ago = _days_ago(ts.date())
            elif event_name == "rebalance_reviewed":
                if inv_rebalance_ts is None or ts > inv_rebalance_ts:
                    inv_rebalance_ts = ts
                    snapshot.investment_last_rebalance_review_days_ago = _days_ago(ts.date())

        if ts >= week_start_dt:
            if app in week_counts and event_name in MEANINGFUL_WEEK_EVENTS:
                week_counts[app] += 1

            if app == "music":
                if event_name in {"video_uploaded", "audio_uploaded"}:
                    snapshot.music_uploads_this_week += 1
                elif event_name == "verified_chart_saved":
                    snapshot.music_verified_edits_this_week += 1
                elif event_name == "lyrics_saved":
                    snapshot.music_lyrics_edits_this_week += 1
                elif event_name in {
                    "backing_track_started",
                    "backing_track_completed",
                    "backing_track",
                }:
                    snapshot.music_backing_sessions_this_week += 1
                elif event_name == "recording_reviewed":
                    if last_review_ts is None or ts > last_review_ts:
                        last_review_ts = ts

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
            if app == "investment":
                if event_name in ("portfolio_health_checked", "portfolio_check"):
                    inv_health_week += 1
                elif event_name == "scenario_run":
                    snapshot.investment_scenarios_this_week += 1
                elif event_name == "optimizer_run":
                    snapshot.investment_optimizer_runs_this_week += 1
                elif event_name == "holdings_updated":
                    snapshot.investment_holdings_updates_this_week += 1
                elif event_name == "rebalance_reviewed":
                    snapshot.investment_rebalance_reviews_this_week += 1
                if metrics.get("review_type"):
                    snapshot.last_portfolio_review = str(metrics["review_type"])
                if metrics.get("goal_title") or metrics.get("goal"):
                    snapshot.last_investment_goal = str(
                        metrics.get("goal_title") or metrics.get("goal")
                    )
                if metrics.get("holdings_count") is not None:
                    try:
                        snapshot.last_investment_holdings_count = int(metrics["holdings_count"])
                    except (TypeError, ValueError):
                        pass
                if metrics.get("risk_profile") or metrics.get("objective"):
                    snapshot.last_investment_risk_profile = str(
                        metrics.get("risk_profile") or metrics.get("objective")
                    ).replace("_", " ").title()
            if app == "baseball" and event_name in {
                "comparison",
                "trade_eval",
                "draft_prep",
                "sleeper_review",
                "projection_report",
                "roster_built",
                "lineup_review",
            }:
                snapshot.baseball_analyses_this_week += 1
            if app == "nba" and event_name in {
                "matchup_analysis",
                "injury_review",
                "playoff_simulation",
                "player_comparison",
                "game_outlook",
                "playoff_tracking",
            }:
                snapshot.nba_analyses_this_week += 1
            if app == "applied_intelligence" and event_name in {
                "lesson_completed",
                "case_study_completed",
            }:
                snapshot.applied_lessons_completed_this_week += 1
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
            if app == "music" and event_name == "song_added":
                _apply_music_edit_metrics(snapshot, metrics, event_name)
                snapshot.last_music_edit_label = "New song added"

        if last_opened is None or ts >= last_opened[2]:
            if not (app == "music" and event_name == "song_selected"):
                last_opened = (app, str(event.get("page") or ""), ts)

    if music_dir_line:
        snapshot.music_directory_primary = music_dir_line
    if inv_dir_line:
        snapshot.investment_directory_primary = inv_dir_line
    if last_upload_ts:
        snapshot.last_music_upload_days_ago = _days_ago(last_upload_ts.date())
    if last_review_ts:
        snapshot.last_recording_review_days_ago = _days_ago(last_review_ts.date())
    if last_instrument_practice and snapshot.last_instrument:
        inst_ts = last_instrument_practice.get(snapshot.last_instrument)
        if inst_ts:
            snapshot.last_instrument_practice_days_ago = _days_ago(inst_ts.date())
    for song, count in music_edit_week.items():
        if count >= 2 and song not in music_practice_week:
            snapshot.music_overedited_song = song
            break

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

    snapshot.portfolio_checks_this_week = inv_health_week
    snapshot.baseball_reviews_this_week = snapshot.baseball_analyses_this_week
    snapshot.nba_sessions_this_week = snapshot.nba_analyses_this_week
    snapshot.applied_intelligence_sessions_this_week = snapshot.applied_lessons_completed_this_week
    snapshot.future_simulations_this_week = week_counts.get("future_lens", 0)

    snapshot.week_activity_by_app = {k: v for k, v in week_counts.items() if v > 0}

    if snapshot.last_song and (
        snapshot.music_verified_edits_this_week
        or snapshot.songs_practiced_this_week
        or snapshot.music_uploads_this_week
    ):
        snapshot.top_project_label = snapshot.last_song
    elif snapshot.future_project or snapshot.last_simulation_name:
        snapshot.top_project_label = snapshot.future_project or snapshot.last_simulation_name

    if snapshot.portfolio_checks_this_week or snapshot.investment_optimizer_runs_this_week:
        snapshot.top_research_area = "portfolio analysis"
    elif snapshot.baseball_analyses_this_week:
        snapshot.top_research_area = "baseball research"
    elif snapshot.nba_analyses_this_week:
        snapshot.top_research_area = "basketball analysis"

    pending = 0
    if (
        snapshot.last_music_upload_days_ago is not None
        and (
            snapshot.last_recording_review_days_ago is None
            or snapshot.last_recording_review_days_ago > snapshot.last_music_upload_days_ago
        )
    ):
        pending += 1
    if (
        snapshot.last_music_edit_days_ago is not None
        and snapshot.last_song
        and (
            snapshot.last_music_practice_days_ago is None
            or snapshot.last_music_practice_days_ago > snapshot.last_music_edit_days_ago
        )
    ):
        pending += 1
    if (
        snapshot.investment_last_holdings_update_days_ago is not None
        and (
            snapshot.last_portfolio_check_days_ago is None
            or snapshot.investment_last_holdings_update_days_ago
            < snapshot.last_portfolio_check_days_ago
        )
    ):
        pending += 1
    if (
        snapshot.investment_last_scenario_days_ago is not None
        and (
            snapshot.investment_last_rebalance_review_days_ago is None
            or snapshot.investment_last_scenario_days_ago
            < snapshot.investment_last_rebalance_review_days_ago
        )
    ):
        pending += 1
    snapshot.pending_review_count = pending


def load_activity_snapshot() -> ActivitySnapshot:
    snapshot = ActivitySnapshot(is_sunday_lineup_day=date.today().weekday() == 6)
    _import_sibling_fallback_events()
    _sync_disk_user_states_to_storage()
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
        if snapshot.music_directory_primary:
            lines.append(snapshot.music_directory_primary)
        elif snapshot.last_music_edit_label and snapshot.last_song:
            artist_bit = f" — {snapshot.last_music_artist}" if snapshot.last_music_artist else ""
            lines.append(f"{snapshot.last_music_edit_label}: {snapshot.last_song}{artist_bit}")
        elif snapshot.last_song:
            lines.append(_labeled("Last song", snapshot.last_song))
        if snapshot.last_instrument:
            lines.append(_labeled("Instrument", snapshot.last_instrument))
        if snapshot.music_streak_days > 0:
            days_word = "day" if snapshot.music_streak_days == 1 else "days"
            lines.append(_labeled("Streak", f"{snapshot.music_streak_days} {days_word}"))
    elif app_key == "investment":
        if snapshot.investment_directory_primary:
            lines.append(snapshot.investment_directory_primary)
        elif snapshot.last_portfolio_review:
            lines.append(_labeled("Last review", snapshot.last_portfolio_review))
        if snapshot.last_investment_goal:
            lines.append(_labeled("Last goal", snapshot.last_investment_goal))
        if snapshot.last_investment_holdings_count > 0:
            lines.append(_labeled("Holdings", str(snapshot.last_investment_holdings_count)))
        if snapshot.last_investment_risk_profile:
            lines.append(_labeled("Risk profile", snapshot.last_investment_risk_profile))
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
                " · ".join(
                    p
                    for p in [
                        f"Goal: {snapshot.last_investment_goal}"
                        if snapshot.last_investment_goal
                        else "",
                        f"{snapshot.last_investment_holdings_count} holdings"
                        if snapshot.last_investment_holdings_count
                        else "",
                        snapshot.last_portfolio_review
                        or (
                            f"{snapshot.portfolio_checks_this_week} checks this week"
                            if snapshot.portfolio_checks_this_week
                            else ""
                        ),
                    ]
                    if p
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
