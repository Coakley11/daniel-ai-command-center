"""
Activity namespace + app-key normalization shared by Baseball and Command Center.

Ensures writes and reads use the same Supabase ``app`` / ``user_id`` / workspace keys.
"""

from __future__ import annotations

from typing import Any

ACTIVITY_APP_ALIASES: dict[str, str] = {
    "math": "applied_intelligence",
    "applied_intelligence": "applied_intelligence",
    "baseball-stat-app": "baseball",
    "baseball_stat_app": "baseball",
    "Baseball Analytics": "baseball",
    "baseball analytics": "baseball",
    "baseball analytics app": "baseball",
}

DRAFT_ACTIVITY_EVENT_TYPES: frozenset[str] = frozenset(
    {
        "live_draft_created",
        "live_draft_pick",
        "completed_live_draft",
        "draft_analysis_created",
        "draft_analysis_attempted",
    }
)

FANTASY_LIFECYCLE_EVENT_TYPES: frozenset[str] = frozenset(
    {
        "trade_offer_sent",
        "trade_offer_received",
        "trade_accepted",
        "trade_declined",
        "trade_canceled",
        "trade_expired",
        "waiver_transaction",
        "waiver_add",
        "waiver_drop",
        "shared_league_created",
        "shared_league_invite",
        "team_claimed",
        "active_draft_changed",
        "draft_saved",
        "saved_draft_archived",
        "saved_draft_activated",
        "lineup_saved",
        "lineup_locked",
        "lineup_review",
    }
)

_TABLE_EVENTS = "suite_activity_events"
_TABLE_RESUME = "suite_resume_items"
_TABLE_STATE = "suite_app_state"


def normalize_activity_app_key(raw: str) -> str:
    key = str(raw or "").strip()
    if not key:
        return ""
    if key in ACTIVITY_APP_ALIASES:
        return ACTIVITY_APP_ALIASES[key]
    try:
        from suite_workspace import logical_storage_app_key

        logical = logical_storage_app_key(key)
        return ACTIVITY_APP_ALIASES.get(logical, logical)
    except ImportError:
        if "__" in key:
            return key.split("__", 1)[0]
        return key


def stamp_activity_metrics(metrics: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(metrics or {})
    try:
        from suite_user import get_external_user_id

        out.setdefault("suite_external_id", get_external_user_id())
    except ImportError:
        pass
    try:
        from suite_workspace import get_active_workspace_id

        out.setdefault("workspace_id", get_active_workspace_id())
    except ImportError:
        pass
    return out


def activity_namespace_diagnostics(*, st: Any | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {
        "suite_external_id": "",
        "account_user_id": "",
        "cloud_user_id": "",
        "account_mode": "",
        "active_workspace_id": "",
        "cloud_app_key_baseball": "",
        "workspace_storage_app_keys": [],
        "events_table": _TABLE_EVENTS,
        "resume_table": _TABLE_RESUME,
        "state_table": _TABLE_STATE,
    }
    try:
        from suite_user import account_mode, get_account_user_id, get_external_user_id

        out["suite_external_id"] = get_external_user_id()
        out["account_user_id"] = get_account_user_id()
        out["account_mode"] = account_mode()
    except ImportError:
        pass
    try:
        from suite_storage_supabase import _cloud_user_id

        out["cloud_user_id"] = _cloud_user_id() or ""
    except ImportError:
        pass
    try:
        from suite_workspace import get_active_workspace_id, scoped_cloud_app_id, workspace_storage_app_keys

        ws = get_active_workspace_id(st)
        out["active_workspace_id"] = ws
        out["cloud_app_key_baseball"] = scoped_cloud_app_id("baseball", ws)
        out["workspace_storage_app_keys"] = sorted(workspace_storage_app_keys(ws))
    except ImportError:
        pass
    try:
        from suite_storage_config import cloud_storage_enabled

        out["cloud_storage_enabled"] = cloud_storage_enabled()
    except ImportError:
        out["cloud_storage_enabled"] = False
    return out
