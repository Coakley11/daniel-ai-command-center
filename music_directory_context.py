"""Select one timestamped Music resource fact, without mixing global fields."""
from __future__ import annotations

from activity_time import parse_activity_timestamp

MEANINGFUL_EVENTS = frozenset({
    "practice_session_started", "practice", "practice_log_saved", "instrument_changed",
    "backing_track_started", "backing_track_completed", "backing_track",
    "mission_started", "song_coaching_used", "verified_chart_saved",
    "lyrics_saved", "chart_save", "chord_save", "composition_saved",
})


def latest_music_context(events: list[dict]) -> dict:
    from music_command_center_dashboard import event_matches_active_workspace

    candidates = []
    for event in events:
        if event.get("app") != "music" or event.get("event") not in MEANINGFUL_EVENTS:
            continue
        if not event_matches_active_workspace(event):
            continue
        timestamp = parse_activity_timestamp(str(event.get("timestamp") or ""))
        metrics = event.get("metrics") or {}
        payload = metrics.get("resume_payload") or {}
        if not isinstance(payload, dict):
            payload = {}
        # Prefer explicit event fields. A conflicting envelope is untrustworthy.
        fields = {name: str(metrics.get(name) or payload.get(other) or "").strip()
                  for name, other in (("song", "song"), ("instrument", "instrument"),
                                      ("source_id", "pick_key"), ("source_type", "source_type"))}
        if any(metrics.get(name) and payload.get(other) and str(metrics[name]) != str(payload[other])
               for name, other in (("song", "song"), ("instrument", "instrument"),
                                   ("source_id", "pick_key"), ("source_type", "source_type"))):
            continue
        if not timestamp or not all(fields.values()) or fields["source_type"] not in {"catalog", "custom", "composition"}:
            continue
        if payload.get("source_id") and str(payload["source_id"]) != fields["source_id"]:
            continue
        pick = fields["source_id"]
        owner = "custom" if pick.startswith(("custom::", "custom\x1f")) else (
            "composition" if pick.startswith(("composition::", "composition\x1f")) else "catalog")
        if fields["source_type"] != owner:
            continue
        candidates.append((timestamp, fields["source_id"], fields["song"], fields["instrument"], fields))
    return max(candidates, key=lambda c: c[:4])[-1] if candidates else {}


def apply_music_directory_context(snapshot, events: list[dict]) -> None:
    context = latest_music_context(events)
    if not context:
        return
    source = {"catalog": "Catalog", "custom": "Custom", "composition": "Composition"}[context["source_type"]]
    snapshot.last_song = context["song"]
    snapshot.last_instrument = context["instrument"]
    snapshot.music_directory_primary = f"Last song: {context['song']} · {source}"
    snapshot.music_directory_instrument = context["instrument"]
