"""
Diagnostics for cross-app activity wiring (Music → Command Center).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from activity_store import APP_REPO_DIRS, _fallback_event_paths, load_all_events
from suite_storage_config import cloud_storage_enabled

# Mirror suite_storage.DATA_DIR / DB_PATH — avoid importing suite_storage here
# (can fail on Streamlit Cloud during partial/circular module init).
_DATA_DIR = Path(__file__).resolve().parent / "data"
DB_PATH = _DATA_DIR / "suite_activity.db"


def _cloud_ping() -> bool:
    if not cloud_storage_enabled():
        return False
    try:
        from suite_storage_supabase import ping

        return ping()
    except Exception:
        return False

MUSIC_MEANINGFUL_EVENTS = frozenset(
    {
        "verified_chart_saved",
        "lyrics_saved",
        "practice",
        "song_selected",
        "backing_track",
        "song_added",
    }
)


@dataclass(frozen=True)
class ActivityDiagnostics:
    deployment_mode: str
    cloud_storage_configured: bool
    cloud_storage_reachable: bool
    command_center_db: str
    command_center_db_exists: bool
    sqlite_music_event_count: int
    sqlite_verified_count: int
    sqlite_lyrics_count: int
    last_music_event: str
    last_verified_event: str
    music_fallback_paths_checked: tuple[str, ...]
    music_fallback_found: str | None
    music_fallback_verified_count: int
    sibling_repos_reachable: bool
    can_command_center_see_music_verified: bool
    failure_step: str
    recommendation: str


def _count_events(events: list[dict[str, Any]], *, event_name: str | None = None) -> int:
    if event_name:
        return sum(1 for e in events if str(e.get("event") or "") == event_name)
    return len(events)


def _last_event_line(
    events: list[dict[str, Any]], *, app: str | None = None, event_name: str | None = None
) -> str:
    for event in reversed(events):
        if app and str(event.get("app") or "") != app:
            continue
        if event_name and str(event.get("event") or "") != event_name:
            continue
        m = event.get("metrics") if isinstance(event.get("metrics"), dict) else {}
        song = str(m.get("song") or m.get("last_edited_song") or "")
        artist = str(m.get("artist") or "")
        when = str(event.get("timestamp") or "")
        ev = str(event.get("event") or "")
        label = f"{ev}"
        if song:
            label += f" · {song}"
        if artist:
            label += f" — {artist}"
        if when:
            label += f" ({when})"
        return label
    return "—"


def _load_music_fallback_file() -> tuple[str | None, list[dict[str, Any]]]:
    for path in _fallback_event_paths("music"):
        if not path.is_file():
            continue
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(raw, list):
            return str(path), raw
    return None, []


def _detect_deployment_mode() -> str:
    cc_root = Path(__file__).resolve().parent
    music_repo = cc_root.parent / APP_REPO_DIRS.get("music", "")
    if music_repo.is_dir() and (music_repo / "streamlit_music_practice_app.py").is_file():
        return "local_sibling_repos"
    return "isolated_deployments"


def run_activity_diagnostics() -> ActivityDiagnostics:
    mode = _detect_deployment_mode()
    db_path = str(DB_PATH)
    db_exists = DB_PATH.is_file()

    db_events = load_all_events(limit=500)
    music_db = [e for e in db_events if str(e.get("app") or "") == "music"]
    verified_db = [e for e in music_db if str(e.get("event") or "") == "verified_chart_saved"]
    lyrics_db = [e for e in music_db if str(e.get("event") or "") == "lyrics_saved"]

    fb_path, fb_rows = _load_music_fallback_file()
    fb_music = [r for r in fb_rows if str(r.get("app") or "") == "music"]
    fb_verified = [r for r in fb_music if str(r.get("event") or "") in {"verified_chart_saved", "lyrics_saved"}]

    paths_checked = tuple(str(p) for p in _fallback_event_paths("music"))
    sibling_ok = mode == "local_sibling_repos"
    can_see = bool(verified_db or lyrics_db) or (sibling_ok and bool(fb_verified))

    cloud_cfg = cloud_storage_enabled()
    cloud_ok = _cloud_ping() if cloud_cfg else False

    if can_see:
        failure = "none — events are reachable"
        rec = "Refresh Command Center. Verified saves should appear in Recent Activity and the Music card."
    elif cloud_cfg and not cloud_ok:
        failure = "step 4 — Supabase configured but not reachable"
        rec = "Check SUITE_SUPABASE_URL / key in Streamlit secrets and that migration SQL was applied."
    elif cloud_cfg and cloud_ok and not can_see:
        failure = "step 1–2 — Cloud connected; no verified/lyrics events in store yet"
        rec = (
            "Save as user verified in Music (with the same [suite_activity] secrets on the Music app). "
            "Then refresh Command Center."
        )
    elif mode == "isolated_deployments" and not cloud_cfg:
        failure = "step 4 — Command Center cannot read Music app storage on Streamlit Cloud"
        rec = (
            "Add [suite_activity] Supabase secrets to every Streamlit Cloud app (see docs/SUITE_CLOUD_ACTIVITY.md). "
            "Without cloud credentials, verified saves stay inside the Music container only."
        )
    elif not db_exists:
        failure = "step 3 — Command Center SQLite not initialized"
        rec = "Open Command Center once to create data/suite_activity.db, then save verified in Music again."
    elif fb_path and fb_verified and not verified_db:
        failure = "step 4 — fallback exists but not imported into Command Center DB"
        rec = "Reload Command Center (imports sibling fallback on startup). If still missing, check activity_store._import_sibling_fallback_events."
    else:
        failure = "step 1 or 2 — Music app did not write verified_chart_saved / lyrics_saved"
        rec = (
            "In Music: Save as user verified and watch for a yellow warning about activity logging. "
            "Confirm edited_fields is non-empty (chords and/or lyrics actually saved)."
        )

    return ActivityDiagnostics(
        deployment_mode=mode,
        cloud_storage_configured=cloud_cfg,
        cloud_storage_reachable=cloud_ok,
        command_center_db=db_path,
        command_center_db_exists=db_exists,
        sqlite_music_event_count=len(music_db),
        sqlite_verified_count=len(verified_db),
        sqlite_lyrics_count=len(lyrics_db),
        last_music_event=_last_event_line(music_db),
        last_verified_event=_last_event_line(music_db, event_name="verified_chart_saved")
        or _last_event_line(music_db, event_name="lyrics_saved"),
        music_fallback_paths_checked=paths_checked,
        music_fallback_found=fb_path,
        music_fallback_verified_count=len(fb_verified),
        sibling_repos_reachable=sibling_ok,
        can_command_center_see_music_verified=can_see,
        failure_step=failure,
        recommendation=rec,
    )
