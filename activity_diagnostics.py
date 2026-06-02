"""
Live activity diagnostics for Command Center admin (Supabase + feed wiring).
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from activity_feed import APP_LABELS, format_activity_message
from activity_store import APP_REPO_DIRS, _fallback_event_paths, load_all_events
from suite_storage_config import (
    EXPECTED_SECRETS_TOML,
    cloud_storage_enabled,
    probe_secrets,
    reset_cloud_config_cache,
)

_DATA_DIR = Path(__file__).resolve().parent / "data"
DB_PATH = _DATA_DIR / "suite_activity.db"

PHASE_A_MUSIC_EVENTS = (
    "verified_chart_saved",
    "lyrics_saved",
    "video_uploaded",
    "audio_uploaded",
    "display_key_changed",
    "backing_track_started",
    "backing_track_completed",
    "practice",
)

PHASE_A_INVESTMENT_EVENTS = (
    "investment_goal_selected",
    "portfolio_created",
    "holdings_updated",
    "portfolio_health_checked",
    "risk_profile_changed",
    "allocation_reviewed",
    "optimizer_run",
    "frontier_viewed",
    "macro_environment_applied",
    "scenario_run",
    "ticker_analyzed",
    "rebalance_reviewed",
)

SUITE_APPS = tuple(APP_LABELS.keys())


def _cloud_ping() -> bool:
    if not cloud_storage_enabled():
        return False
    try:
        from suite_storage_supabase import ping

        return ping()
    except Exception:
        return False


def _load_supabase_events(limit: int = 200) -> tuple[list[dict[str, Any]], str | None]:
    if not cloud_storage_enabled():
        probe = probe_secrets()
        detail = probe.secrets_error or "Supabase not configured"
        return [], detail
    try:
        from suite_storage_supabase import load_events

        return load_events(limit=limit), None
    except Exception as exc:
        return [], str(exc)


def _load_sqlite_events(limit: int = 200) -> list[dict[str, Any]]:
    if not DB_PATH.is_file():
        return []
    try:
        from suite_storage import load_events as sqlite_load

        if cloud_storage_enabled():
            return []
        return sqlite_load(limit=limit)
    except Exception:
        return []


def _counts_by_app(events: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for event in events:
        app = str(event.get("app") or "").strip()
        if app:
            counts[app] += 1
    return dict(counts)


def _last_by_app(events: list[dict[str, Any]]) -> dict[str, str]:
    latest: dict[str, tuple[str, str]] = {}
    for event in events:
        app = str(event.get("app") or "").strip()
        if not app:
            continue
        ts = str(event.get("timestamp") or "")
        ev = str(event.get("event") or "")
        m = event.get("metrics") if isinstance(event.get("metrics"), dict) else {}
        song = str(m.get("song") or "")
        line = ev
        if song:
            line += f" · {song}"
        if ts:
            line += f" ({ts})"
        prev = latest.get(app)
        if prev is None or ts >= prev[0]:
            latest[app] = (ts, line)
    return {app: line for app, (_, line) in latest.items()}


def _format_raw_event(event: dict[str, Any]) -> str:
    return json.dumps(
        {
            "app": event.get("app"),
            "event": event.get("event"),
            "timestamp": event.get("timestamp"),
            "page": event.get("page"),
            "metrics": event.get("metrics"),
        },
        ensure_ascii=False,
    )


@dataclass(frozen=True)
class PhaseAEventStatus:
    event_type: str
    in_supabase: bool
    in_command_center: bool
    feed_preview: str
    latest_timestamp: str


@dataclass
class LiveActivityDiagnostics:
    deployment_mode: str
    cloud_storage_configured: bool
    cloud_storage_reachable: bool
    failure_step: str
    recommendation: str
    secrets_probe: Any = None
    supabase_event_count: int = 0
    command_center_event_count: int = 0
    sqlite_event_count: int = 0
    supabase_error: str | None = None
    counts_by_app_supabase: dict[str, int] = field(default_factory=dict)
    counts_by_app_command_center: dict[str, int] = field(default_factory=dict)
    last_event_by_app_supabase: dict[str, str] = field(default_factory=dict)
    last_event_by_app_command_center: dict[str, str] = field(default_factory=dict)
    last_10_raw_supabase: list[str] = field(default_factory=list)
    last_10_raw_command_center: list[str] = field(default_factory=list)
    phase_a_music: list[PhaseAEventStatus] = field(default_factory=list)
    phase_a_investment: list[PhaseAEventStatus] = field(default_factory=list)
    verified_in_feed: bool = False
    investment_health_in_feed: bool = False
    # Legacy fields for compact summary row
    can_command_center_see_music_verified: bool = False
    sqlite_verified_count: int = 0


def _detect_deployment_mode() -> str:
    cc_root = Path(__file__).resolve().parent
    music_repo = cc_root.parent / APP_REPO_DIRS.get("music", "")
    if music_repo.is_dir() and (music_repo / "streamlit_music_practice_app.py").is_file():
        return "local_sibling_repos"
    return "isolated_deployments"


def _phase_a_status(
    event_type: str,
    supabase_events: list[dict[str, Any]],
    cc_events: list[dict[str, Any]],
) -> PhaseAEventStatus:
    def _latest(events: list[dict[str, Any]]) -> dict[str, Any] | None:
        found = [e for e in events if str(e.get("event") or "") == event_type]
        if not found:
            return None
        return max(found, key=lambda e: str(e.get("timestamp") or ""))

    sb = _latest(supabase_events)
    cc = _latest(cc_events)
    in_sb = sb is not None
    in_cc = cc is not None
    preview = ""
    ts = ""
    if cc:
        preview = format_activity_message(cc, for_feed=False) or ""
        ts = str(cc.get("timestamp") or "")
    elif sb:
        preview = format_activity_message(sb, for_feed=False) or "(in Supabase only — CC read issue)"
        ts = str(sb.get("timestamp") or "")
    return PhaseAEventStatus(
        event_type=event_type,
        in_supabase=in_sb,
        in_command_center=in_cc,
        feed_preview=preview or "—",
        latest_timestamp=ts,
    )


def run_live_activity_diagnostics() -> LiveActivityDiagnostics:
    reset_cloud_config_cache()
    secrets = probe_secrets()
    mode = _detect_deployment_mode()
    cloud_cfg = cloud_storage_enabled()
    cloud_ok = _cloud_ping() if cloud_cfg else False

    supabase_events, sb_err = _load_supabase_events(200)
    cc_events = load_all_events(limit=200)
    sqlite_events = _load_sqlite_events(200)

    music_cc = [e for e in cc_events if str(e.get("app") or "") == "music"]
    verified_cc = [e for e in music_cc if str(e.get("event") or "") == "verified_chart_saved"]

    phase_a_music = [
        _phase_a_status(name, supabase_events, cc_events)
        for name in PHASE_A_MUSIC_EVENTS
    ]
    phase_a_investment = [
        _phase_a_status(name, supabase_events, cc_events)
        for name in PHASE_A_INVESTMENT_EVENTS
    ]
    verified_feed = False
    investment_health_feed = False
    for event in reversed(cc_events):
        ev = str(event.get("event") or "")
        if ev == "verified_chart_saved" and not verified_feed:
            msg = format_activity_message(event) or ""
            verified_feed = "Verified chart saved" in msg
        if ev == "portfolio_health_checked" and not investment_health_feed:
            msg = format_activity_message(event) or ""
            investment_health_feed = "portfolio health check" in msg.lower()
        if verified_feed and investment_health_feed:
            break

    can_see = bool(verified_cc) or (
        cloud_cfg and cloud_ok and any(p.in_supabase for p in phase_a if p.event_type == "verified_chart_saved")
    )

    if cloud_cfg and cloud_ok and verified_cc and verified_feed:
        failure = "none — live pipeline OK"
        rec = "Recent Activity should match Phase A table below. Trigger new events in Music to refresh."
    elif cloud_cfg and not cloud_ok:
        failure = "Supabase configured but not reachable"
        rec = "Check URL/key and run supabase/migrations/001_suite_activity.sql."
    elif cloud_cfg and cloud_ok and not supabase_events:
        failure = "Supabase empty — Music not writing or wrong project"
        rec = "Add identical [suite_activity] secrets to Music Cloud app; save verified chords again."
    elif cloud_cfg and cloud_ok and supabase_events and not cc_events:
        failure = "Command Center not reading Supabase"
        rec = "Confirm CC deployment has suite_storage cloud-first code (dev v14+)."
    elif cloud_cfg and cloud_ok and verified_cc and not verified_feed:
        failure = "Events loaded but feed formatting failed"
        rec = "Check activity_feed.format_activity_message for verified_chart_saved."
    elif not cloud_cfg and mode == "isolated_deployments":
        failure = "No Supabase — Cloud cannot share activity"
        rec = "Configure [suite_activity] secrets on all Streamlit apps (docs/SUITE_CLOUD_ACTIVITY.md)."
    elif can_see:
        failure = "none — events reachable (local/SQLite)"
        rec = "For Cloud cross-app proof, configure Supabase on all deployments."
    else:
        failure = "No verified_chart_saved in Command Center store"
        rec = "Save as user verified in Music, then refresh Command Center admin panel."

    sb_sorted = sorted(supabase_events, key=lambda e: str(e.get("timestamp") or ""), reverse=True)
    cc_sorted = sorted(cc_events, key=lambda e: str(e.get("timestamp") or ""), reverse=True)

    return LiveActivityDiagnostics(
        deployment_mode=mode,
        cloud_storage_configured=cloud_cfg,
        cloud_storage_reachable=cloud_ok,
        failure_step=failure,
        recommendation=rec,
        secrets_probe=secrets,
        supabase_event_count=len(supabase_events),
        command_center_event_count=len(cc_events),
        sqlite_event_count=len(sqlite_events),
        supabase_error=sb_err,
        counts_by_app_supabase=_counts_by_app(supabase_events),
        counts_by_app_command_center=_counts_by_app(cc_events),
        last_event_by_app_supabase=_last_by_app(supabase_events),
        last_event_by_app_command_center=_last_by_app(cc_events),
        last_10_raw_supabase=[_format_raw_event(e) for e in sb_sorted[:10]],
        last_10_raw_command_center=[_format_raw_event(e) for e in cc_sorted[:10]],
        phase_a_music=phase_a_music,
        phase_a_investment=phase_a_investment,
        verified_in_feed=verified_feed,
        investment_health_in_feed=investment_health_feed,
        can_command_center_see_music_verified=bool(verified_cc),
        sqlite_verified_count=len(verified_cc),
    )


def run_activity_diagnostics() -> LiveActivityDiagnostics:
    """Alias for admin panel."""
    return run_live_activity_diagnostics()
