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

PHASE_A_BASEBALL_EVENTS = (
    "player_comparison",
    "draft_prep",
    "sleeper_research",
    "trade_analysis",
    "projection_report",
    "roster_build",
    "trend_analysis",
    "player_trend_viewed",
    "trend_comparison_viewed",
    "breakout_analysis",
    "live_draft_created",
    "live_draft_pick",
    "completed_live_draft",
    "draft_analysis_created",
    "draft_analysis_attempted",
)

PHASE_A_NBA_EVENTS = (
    "matchup_analysis",
    "injury_analysis",
    "playoff_simulation",
    "player_comparison",
    "game_outlook",
    "playoff_tracker_review",
)

PHASE_A_APPLIED_EVENTS = (
    "analytical_question",
    "session_activity",
    "lesson_completed",
    "case_study_completed",
    "module_completed",
    "problem_solved",
    "reasoning_exercise_completed",
)

PHASE_A_FUTURE_LENS_EVENTS = (
    "simulation_completed",
    "career_analysis",
    "skill_forecast_review",
    "technology_timeline_review",
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
    phase_a_baseball: list[PhaseAEventStatus] = field(default_factory=list)
    phase_a_nba: list[PhaseAEventStatus] = field(default_factory=list)
    phase_a_applied: list[PhaseAEventStatus] = field(default_factory=list)
    phase_a_future_lens: list[PhaseAEventStatus] = field(default_factory=list)
    verified_in_feed: bool = False
    investment_health_in_feed: bool = False
    # Legacy fields for compact summary row
    can_command_center_see_music_verified: bool = False
    sqlite_verified_count: int = 0
    workspace_namespace: dict[str, Any] = field(default_factory=dict)


def build_workspace_activity_namespace_diagnostics(st: Any | None = None) -> dict[str, Any]:
    """Compare CC fetch namespace vs last AMI activity rows for active workspace."""
    out: dict[str, Any] = {
        "active_workspace_id": "",
        "suite_user_id": "",
        "account_user_id": "",
        "cc_fetch_namespaces": [],
        "applied_intelligence_fetch_key": "",
        "last_ami_event_in_cc": None,
        "last_ami_event_in_supabase_raw": None,
        "namespace_mismatch_hint": "",
    }
    try:
        from suite_user import get_account_user_id, get_external_user_id
        from suite_workspace import get_active_workspace_id, scoped_cloud_app_id, workspace_storage_app_keys

        if st is not None:
            ws = get_active_workspace_id(st)
        else:
            ws = get_active_workspace_id()
        out["active_workspace_id"] = ws
        out["suite_user_id"] = get_external_user_id()
        out["account_user_id"] = get_account_user_id()
        fetch_keys = sorted(workspace_storage_app_keys(ws))
        out["cc_fetch_namespaces"] = fetch_keys
        out["applied_intelligence_fetch_key"] = scoped_cloud_app_id("applied_intelligence", ws)
    except Exception as exc:
        out["error"] = str(exc)
        return out

    cc_events = load_all_events(limit=300)
    ami_cc = [
        e
        for e in cc_events
        if str(e.get("app") or "") == "applied_intelligence"
        and str(e.get("event") or "") in {"analytical_question", "problem_solved", "lesson_completed"}
    ]
    if ami_cc:
        latest = max(ami_cc, key=lambda e: str(e.get("timestamp") or ""))
        metrics = latest.get("metrics") if isinstance(latest.get("metrics"), dict) else {}
        out["last_ami_event_in_cc"] = {
            "event": latest.get("event"),
            "timestamp": latest.get("timestamp"),
            "page": latest.get("page"),
            "metrics_workspace_id": metrics.get("workspace_id"),
        }

    sb_events, sb_err = _load_supabase_events(300)
    out["supabase_error"] = sb_err
    expected = out["applied_intelligence_fetch_key"]
    ami_sb = [
        e
        for e in sb_events
        if str(e.get("app") or "") in {expected, "applied_intelligence", "applied_intelligence__ariel"}
        and str(e.get("event") or "") in {"analytical_question", "problem_solved", "lesson_completed"}
    ]
    if ami_sb:
        latest_sb = max(ami_sb, key=lambda e: str(e.get("timestamp") or ""))
        metrics = latest_sb.get("metrics") if isinstance(latest_sb.get("metrics"), dict) else {}
        out["last_ami_event_in_supabase_raw"] = {
            "app": latest_sb.get("app"),
            "event": latest_sb.get("event"),
            "timestamp": latest_sb.get("timestamp"),
            "metrics_workspace_id": metrics.get("workspace_id"),
        }
        sb_app = str(latest_sb.get("app") or "")
        if ws != "daniel" and sb_app == "applied_intelligence":
            out["namespace_mismatch_hint"] = (
                "Supabase row uses Daniel unscoped app=applied_intelligence; "
                f"Ariel CC reads {expected} only."
            )
        elif ws == "daniel" and sb_app.endswith("__ariel"):
            out["namespace_mismatch_hint"] = (
                "Supabase row is Ariel-scoped but CC Daniel profile reads unscoped applied_intelligence."
            )
    elif ws != "daniel":
        out["namespace_mismatch_hint"] = (
            f"No AMI events in Supabase for {expected}. "
            "Confirm AMI opened with ?suite_workspace=ariel (AMI deploy defaults to daniel)."
        )
    return out


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
    *,
    app: str | None = None,
) -> PhaseAEventStatus:
    def _latest(events: list[dict[str, Any]]) -> dict[str, Any] | None:
        found = [
            e
            for e in events
            if str(e.get("event") or "") == event_type
            and (app is None or str(e.get("app") or "") == app)
        ]
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
        _phase_a_status(name, supabase_events, cc_events, app="music")
        for name in PHASE_A_MUSIC_EVENTS
    ]
    phase_a_investment = [
        _phase_a_status(name, supabase_events, cc_events, app="investment")
        for name in PHASE_A_INVESTMENT_EVENTS
    ]
    phase_a_baseball = [
        _phase_a_status(name, supabase_events, cc_events, app="baseball")
        for name in PHASE_A_BASEBALL_EVENTS
    ]
    phase_a_nba = [
        _phase_a_status(name, supabase_events, cc_events, app="nba")
        for name in PHASE_A_NBA_EVENTS
    ]
    phase_a_applied = [
        _phase_a_status(name, supabase_events, cc_events, app="applied_intelligence")
        for name in PHASE_A_APPLIED_EVENTS
    ]
    phase_a_future_lens = [
        _phase_a_status(name, supabase_events, cc_events, app="future_lens")
        for name in PHASE_A_FUTURE_LENS_EVENTS
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
        cloud_cfg
        and cloud_ok
        and any(p.in_supabase for p in phase_a_music if p.event_type == "verified_chart_saved")
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

    workspace_ns = build_workspace_activity_namespace_diagnostics()

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
        phase_a_baseball=phase_a_baseball,
        phase_a_nba=phase_a_nba,
        phase_a_applied=phase_a_applied,
        phase_a_future_lens=phase_a_future_lens,
        verified_in_feed=verified_feed,
        investment_health_in_feed=investment_health_feed,
        can_command_center_see_music_verified=bool(verified_cc),
        sqlite_verified_count=len(verified_cc),
        workspace_namespace=workspace_ns,
    )


def build_draft_activity_read_diagnostics(st: Any | None = None) -> dict[str, Any]:
    """Read-side namespace + draft workflow event visibility for developer panel."""
    from suite_activity_namespace import DRAFT_ACTIVITY_EVENT_TYPES, activity_namespace_diagnostics

    out: dict[str, Any] = dict(activity_namespace_diagnostics(st=st))
    out["events_table"] = out.get("events_table") or "suite_activity_events"
    out["query_path"] = f"GET {out['events_table']} (workspace app keys + user scope)"

    events = load_all_events(limit=500)
    out["activity_event_count"] = len(events)

    recent = sorted(events, key=lambda e: str(e.get("timestamp") or ""), reverse=True)[:10]
    out["recent_10"] = [
        {
            "app": e.get("app"),
            "event": e.get("event"),
            "title": (
                (e.get("metrics") or {}).get("activity_type")
                if isinstance(e.get("metrics"), dict)
                else None
            ),
            "timestamp": e.get("timestamp"),
        }
        for e in recent
    ]

    draft_present: dict[str, bool] = {}
    draft_filter_reasons: dict[str, str] = {}
    for etype in sorted(DRAFT_ACTIVITY_EVENT_TYPES):
        matches = [
            e
            for e in events
            if str(e.get("event") or "") == etype
            and str(e.get("app") or "") in {"baseball", "baseball-stat-app", "Baseball Analytics"}
        ]
        draft_present[etype] = bool(matches)
        if not matches:
            draft_filter_reasons[etype] = "not in loaded store (namespace or write issue)"
            continue
        latest = max(matches, key=lambda e: str(e.get("timestamp") or ""))
        raw_app = str(latest.get("app") or "")
        if raw_app not in {"baseball"}:
            draft_filter_reasons[etype] = f"app normalized from {raw_app!r} to baseball"
        try:
            from project_intelligence import _MEANINGFUL_WORKFLOW_EVENTS, _raw_event_workflow_candidate

            if etype not in _MEANINGFUL_WORKFLOW_EVENTS:
                draft_filter_reasons[etype] = "unknown event type (not in _MEANINGFUL_WORKFLOW_EVENTS)"
            elif _raw_event_workflow_candidate(latest) is None:
                draft_filter_reasons[etype] = "workflow candidate rejected (stale timestamp or missing metrics)"
            else:
                draft_filter_reasons[etype] = "eligible for Continue / App Directory"
        except Exception as exc:
            draft_filter_reasons[etype] = f"diagnostic error: {exc}"

    out["draft_event_types_present"] = draft_present
    out["draft_event_filter_reasons"] = draft_filter_reasons
    return out


def run_activity_diagnostics() -> LiveActivityDiagnostics:
    """Alias for admin panel."""
    return run_live_activity_diagnostics()
