"""
Raw activity event rows for developer verification — no Continue filtering or ranking.
"""

from __future__ import annotations

from typing import Any

from activity_store import load_all_events

# Display-only hints (not used by Continue card logic).
_EVENT_PRIORITY_HINT: dict[str, int] = {
    "player_comparison": 59,
    "player_trend_viewed": 58,
    "trend_comparison_viewed": 57,
    "trend_analysis": 58,
    "draft_prep": 56,
    "trade_eval": 54,
    "trade_analysis": 54,
    "breakout_analysis": 35,
    "game_outlook": 60,
    "matchup_analysis": 56,
    "portfolio_health_checked": 58,
}


def _metrics(event: dict[str, Any]) -> dict[str, Any]:
    raw = event.get("metrics")
    return raw if isinstance(raw, dict) else {}


def infer_resume_key(event_type: str, metrics: dict[str, Any]) -> str:
    player = str(metrics.get("player") or "").strip()
    if event_type in {"player_trend_viewed", "trend_analysis"} and player:
        return f"trend:{player}"
    pa = str(metrics.get("player_a") or "").strip()
    pb = str(metrics.get("player_b") or "").strip()
    if event_type == "trend_comparison_viewed" and pa and pb:
        return f"trendcompare:{pa}:{pb}"
    if event_type == "player_comparison" and pa and pb:
        return f"compare:{pa}:{pb}"
    if event_type == "draft_prep":
        return "bb:draft"
    if event_type in {"trade_eval", "trade_analysis"}:
        return "bb:trade"
    if event_type == "breakout_analysis":
        return "baseball:breakouts"
    team = str(metrics.get("team") or "").strip()
    if event_type == "game_outlook" and team:
        return f"nba:game:{team}"
    return ""


def raw_app_events(app: str, *, limit: int = 20) -> list[dict[str, Any]]:
    """Newest events for one app straight from load_all_events — no Continue logic."""
    target = str(app or "").strip()
    rows: list[dict[str, Any]] = []
    for event in sorted(
        load_all_events(limit=500),
        key=lambda e: str(e.get("timestamp") or ""),
        reverse=True,
    ):
        if str(event.get("app") or "").strip() != target:
            continue
        event_type = str(event.get("event") or "").strip()
        m = _metrics(event)
        player = str(m.get("player") or "").strip()
        if not player:
            pa = str(m.get("player_a") or "").strip()
            pb = str(m.get("player_b") or "").strip()
            if pa and pb:
                player = f"{pa} vs {pb}"
        rk = infer_resume_key(event_type, m)
        hint = _EVENT_PRIORITY_HINT.get(event_type)
        rows.append(
            {
                "timestamp": str(event.get("timestamp") or "")[:19],
                "event_type": event_type,
                "resume_key": rk or "—",
                "player": player or "—",
                "priority": hint if hint is not None else "—",
            }
        )
        if len(rows) >= limit:
            break
    return rows


def raw_baseball_events(*, limit: int = 20) -> list[dict[str, Any]]:
    return raw_app_events("baseball", limit=limit)
