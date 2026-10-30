"""Recording insight facts are correlated by recording ID, never latest song."""
from __future__ import annotations


def latest_recording_context(events: list[dict]) -> dict:
    from music_command_center_dashboard import event_matches_active_workspace
    scoped = [e for e in events if e.get("app") == "music" and event_matches_active_workspace(e)]
    uploads = [e for e in scoped if e.get("event") in {"audio_uploaded", "video_uploaded"}]
    if not uploads:
        return {}
    upload = max(uploads, key=lambda e: str(e.get("timestamp") or ""))
    m = upload.get("metrics") if isinstance(upload.get("metrics"), dict) else {}
    # Legacy facts can name their own recording, but cannot borrow a global owner.
    result = {k:m.get(k, "") for k in ("recording_id", "song", "source_type", "source_id",
                                       "instrument", "display_key", "artist")}
    result["uploaded_at"] = upload.get("timestamp", "")
    rid = str(m.get("recording_id") or "")
    result["reviewed"] = bool(rid and any(
        e.get("event") == "recording_reviewed" and
        (e.get("metrics") or {}).get("recording_id") == rid and
        str(e.get("timestamp") or "") >= str(upload.get("timestamp") or "") for e in scoped))
    return result
