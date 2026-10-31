"""Recording insight facts are correlated by recording ID, never latest song."""
from __future__ import annotations


def resource_delivery_key(event: dict) -> tuple | None:
    """A resource/action identity is independent of delivery time, filename and source title."""
    app = str(event.get('app') or '')
    if app.split('__', 1)[0] != 'music':
        return None
    kind = event.get('event')
    m = event.get('metrics') if isinstance(event.get('metrics'), dict) else {}
    field = ('recording_id' if kind in {'audio_uploaded', 'video_uploaded'}
             else 'export_id' if kind == 'multitrack_export_saved' else '')
    resource_id = str(m.get(field) or '').strip() if field else ''
    if not resource_id:
        return None  # Legacy events have no evidence for fuzzy resource matching.
    action = 'recording_uploaded' if kind in {'audio_uploaded', 'video_uploaded'} else kind
    return ('music-resource', app, str(m.get('workspace_id') or 'daniel'), action, resource_id)


def collapse_resource_deliveries(events: list[dict]) -> list[dict]:
    result, seen = [], set()
    for event in events:
        key = resource_delivery_key(event)
        if key is not None:
            if key in seen:
                continue
            seen.add(key)
        result.append(event)
    return result


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
