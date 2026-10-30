"""Music Continue candidates use one detached workflow-owned envelope."""
from __future__ import annotations
from typing import Any

ELIGIBLE_EVENTS = frozenset({"practice_session_started", "backing_track_started",
    "backing_track_completed", "mission_started", "song_coaching_used",
    "verified_chart_saved", "lyrics_saved", "chart_save", "chord_save"})


def eligible_payload(event: str, metrics: dict[str, Any]) -> dict:
    if event not in ELIGIBLE_EVENTS:
        return {}
    raw = metrics.get("resume_payload")
    if not isinstance(raw, dict):
        return {}
    p = dict(raw)
    kind = p.get("resume_kind")
    if not p.get("song") or not p.get("pick_key") or not p.get("instrument") or not p.get("display_key"):
        return {}
    pick = str(p["pick_key"])
    source = ("composition" if pick.startswith(("composition::", "composition\x1f")) else
              "custom" if pick.startswith(("custom::", "custom\x1f")) else "catalog")
    if p.get("source_type") and p["source_type"] != source:
        return {}
    if p.get("source_id") and p["source_id"] != pick:
        return {}
    if metrics.get("source_type") and metrics["source_type"] != source:
        return {}
    destination = p.get("activity_destination")
    if kind in {"practice", "backing"} and p.get("studio_page") != kind:
        return {}
    if destination in {"missions", "coaching"} and (kind != "creative" or p.get("studio_page") != "creative"):
        return {}
    if event == "mission_started":
        if destination != "missions" or not p.get("mission") or p.get("source_type") != "catalog":
            return {}
    elif event == "song_coaching_used":
        if destination != "coaching" or p.get("source_type") != "catalog":
            return {}
    elif kind not in {"practice", "backing"}:
        return {}
    # Explicit event ownership must agree with its restoration envelope.
    for field, key in (("song", "song"), ("source_id", "pick_key"),
                       ("pick_key", "pick_key"), ("instrument", "instrument"),
                       ("practice_key", "display_key")):
        if metrics.get(field) and str(metrics[field]) != str(p.get(key) or ""):
            return {}
    return p


def candidate_copy(p: dict) -> tuple[str, str]:
    song = str(p["song"])
    destination = p.get("activity_destination")
    workflow = ("started mission" if destination == "missions" else
                "Song-Aware Coaching" if destination == "coaching" else
                "backing" if p.get("resume_kind") == "backing" else "practice")
    title = f"Continue {song} {workflow}"
    details = [str(p.get(k) or "") for k in ("display_key", "instrument")]
    if destination == "missions":
        details.append(str(p.get("mission") or ""))
    return title, " / ".join(x for x in details if x)


def continue_rows(events: list[dict]) -> list[tuple]:
    from music_command_center_dashboard import event_matches_active_workspace
    from music_resume_payload import payload_workspace_matches
    from music_command_center_dashboard import active_workspace_id
    rows = []
    for e in events:
        if e.get("app") != "music" or not event_matches_active_workspace(e):
            continue
        m = e.get("metrics") if isinstance(e.get("metrics"), dict) else {}
        p = eligible_payload(str(e.get("event") or ""), m)
        if not p or not payload_workspace_matches(p, active_workspace_id()):
            continue
        title, subtitle = candidate_copy(p)
        rows.append((61, "music", title, subtitle,
                     "music:workflow:" + str(p["pick_key"]), str(p.get("studio_page") or "practice"),
                     {**p, "resume_payload":p, "_continue_ts": str(e.get("timestamp") or "")}))
    return rows
