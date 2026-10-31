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


SOURCE_LABELS = {"catalog": "Catalog", "custom": "Custom", "composition": "Composition"}


def source_label(p: dict) -> str:
    """Catalog / Custom / Composition, derived only from the stable pick key."""
    pick = str(p.get("pick_key") or "")
    if pick.startswith(("composition::", "composition")):
        return SOURCE_LABELS["composition"]
    if pick.startswith(("custom::", "custom")):
        return SOURCE_LABELS["custom"]
    return SOURCE_LABELS["catalog"]


def workflow_label(p: dict) -> str:
    destination = p.get("activity_destination")
    if destination == "missions":
        return "Mission"
    if destination == "coaching":
        return "Song-Aware Coaching"
    return "Backing" if p.get("resume_kind") == "backing" else "Practice"


def _positive_bpm(*values: Any) -> str:
    for value in values:
        try:
            bpm = int(float(value))
        except (TypeError, ValueError):
            continue
        if bpm > 0:
            return f"{bpm} BPM"
    return ""


def candidate_copy(p: dict) -> tuple[str, str]:
    """Resource first, workflow second, setup metadata third.

    Only fields present in the restoration payload are shown; nothing is
    inferred. ``display_key`` is called "Concert" only when the producer says
    so with ``key_kind == "concert"``; otherwise it is the neutral Practice Key.
    """
    title = f"Continue {str(p['song']).strip()} — {workflow_label(p)}"
    key = str(p.get("display_key") or "").strip()
    bpm = (_positive_bpm(p.get("backing_track_bpm"), p.get("bpm"))
           if p.get("resume_kind") == "backing" else _positive_bpm(p.get("bpm")))
    details = [source_label(p), str(p.get("instrument") or "").strip(),
               ((f"Concert {key}" if str(p.get("key_kind") or "").lower() == "concert"
                 else f"Practice Key: {key}") if key else ""), bpm]
    if p.get("activity_destination") == "missions":
        details.append(str(p.get("mission") or "").replace("_", " ").strip())
    return title, " · ".join(x for x in details if x)


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
