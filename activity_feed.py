"""
Human-readable activity feed lines from suite event logs.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

APP_LABELS: dict[str, str] = {
    "music": "Music",
    "baseball": "Baseball",
    "nba": "Basketball",
    "investment": "Investment",
    "applied_intelligence": "Applied Intelligence",
    "future_lens": "Future Lens",
}


@dataclass(frozen=True)
class ActivityFeedItem:
    app: str
    app_label: str
    timestamp: str
    message: str
    sort_key: datetime


def _metrics(event: dict[str, Any]) -> dict[str, Any]:
    raw = event.get("metrics")
    return raw if isinstance(raw, dict) else {}


def _music_title_artist(metrics: dict[str, Any]) -> str:
    title = str(metrics.get("song") or metrics.get("last_edited_song") or "").strip()
    artist = str(metrics.get("artist") or "").strip()
    if title and artist:
        return f"{title} — {artist}"
    return title


def _music_edit_headline(event_type: str, metrics: dict[str, Any]) -> str:
    fields = metrics.get("edited_fields") or []
    if not isinstance(fields, list):
        fields = []
    field_set = {str(f) for f in fields}
    if event_type == "lyrics_saved" or (field_set == {"lyrics"}):
        return "Lyrics updated"
    if field_set >= {"chords", "lyrics"}:
        return "Verified chart & lyrics saved"
    if "chords" in field_set:
        return "Verified chart saved"
    return "Song edit saved"


def _player_pair(metrics: dict[str, Any]) -> str:
    a = str(metrics.get("player_a") or metrics.get("player") or "").strip()
    b = str(metrics.get("player_b") or "").strip()
    if a and b:
        return f"{a} vs {b}"
    return a or b


def format_activity_message(event: dict[str, Any]) -> str | None:
    """Return a scannable feed line, or None to skip noise-only events."""
    app = str(event.get("app") or "").strip()
    event_type = str(event.get("event") or "").strip()
    page = str(event.get("page") or "").strip()
    summary = str(event.get("summary") or "").strip()
    m = _metrics(event)

    if event_type == "practice" and app == "music":
        song = str(m.get("song") or "").strip()
        mins = m.get("minutes")
        if song and mins:
            return f"Practiced {song} ({int(mins)} min)"
        if song:
            return f"Practiced {song}"
        return "Logged a practice session"

    if event_type in ("verified_chart_saved", "lyrics_saved", "chart_save", "chord_save") and app == "music":
        label = _music_edit_headline(event_type, m)
        line = _music_title_artist(m)
        return f"{label}: {line}" if line else label

    if event_type == "song_added" and app == "music":
        line = _music_title_artist(m)
        return f"Added song: {line}" if line else "Added a new song"

    if event_type == "backing_track" and app == "music":
        line = _music_title_artist(m)
        return f"Generated backing track: {line}" if line else "Generated a backing track"

    if event_type == "song_selected" and app == "music":
        line = _music_title_artist(m)
        if line:
            return f"Opened: {line}"
        return summary or None

    if event_type == "portfolio_check" and app == "investment":
        label = str(m.get("review_type") or "portfolio health").strip()
        score = m.get("score")
        if score is not None:
            return f"Ran portfolio health check ({label}, {float(score):.0f}/100)"
        return f"Ran portfolio health check ({label})"

    if event_type == "comparison" and app == "baseball":
        pair = _player_pair(m)
        if pair:
            return f"Compared {pair}"
        player = str(m.get("player") or "").strip()
        return f"Ran comparison{f' — {player}' if player else ''}"

    if event_type == "lineup_review" and app == "baseball":
        team = str(m.get("team") or m.get("league") or "").strip()
        if team:
            return f"Reviewed fantasy lineup ({team})"
        return "Reviewed fantasy lineup"

    if event_type == "trade_eval" and app == "baseball":
        return str(m.get("trade") or summary or "Evaluated a trade")

    if event_type == "simulation" and app == "future_lens":
        sim = str(m.get("simulation") or "").strip()
        project = str(m.get("project") or "").strip()
        if sim and project:
            return f"Simulated {sim} ({project})"
        if sim:
            return f"Simulated {sim}"
        return summary or "Ran a future scenario"

    if event_type == "analysis" and app == "applied_intelligence":
        topic = str(m.get("analysis") or m.get("lesson") or page or "").strip()
        return f"Solved problem: {topic}" if topic else "Completed an analysis"

    if event_type == "page_view":
        if app == "nba":
            team = str(m.get("team") or "").strip()
            pg = str(m.get("page") or page or "").strip()
            if "injury" in pg.lower():
                return f"Viewed {team} injury report" if team else "Viewed injury report"
            if "live" in pg.lower():
                return f"Checked live games ({team})" if team else "Used Live Game Center"
            if team and pg:
                return f"Viewed {team} — {pg}"
            if team:
                return f"Viewed {team}"
        if app == "baseball":
            player = str(m.get("player") or "").strip()
            report = str(m.get("report") or page or "").strip()
            if player and report:
                return f"Viewed {player} on {report}"
            if player:
                return f"Searched player {player}"
            if report:
                return f"Opened {report}"
        if app == "applied_intelligence":
            lesson = str(m.get("lesson") or page or "").strip()
            if lesson:
                return f"Opened topic: {lesson}"
        if summary:
            return summary
        if page and app != "nba":
            return f"Opened {page}"
        return None

    if summary:
        return summary
    if page and event_type:
        return f"{event_type.replace('_', ' ').title()}: {page}"
    return None


def _feed_priority(event: dict[str, Any]) -> int:
    """Higher = prefer in Recent Activity over noisy opens."""
    app = str(event.get("app") or "")
    event_type = str(event.get("event") or "")
    if app == "music" and event_type in {
        "verified_chart_saved",
        "lyrics_saved",
        "chart_save",
        "chord_save",
        "practice",
        "backing_track",
        "song_added",
    }:
        return 3
    if app == "music" and event_type == "song_selected":
        return 0
    if event_type == "page_view":
        return 0
    return 2


def build_activity_feed(events: list[dict[str, Any]], *, limit: int = 20) -> list[ActivityFeedItem]:
    items: list[tuple[int, datetime, ActivityFeedItem]] = []
    for event in events:
        message = format_activity_message(event)
        if not message:
            continue
        app = str(event.get("app") or "")
        ts_raw = str(event.get("timestamp") or "")
        try:
            sort_key = datetime.fromisoformat(ts_raw)
        except ValueError:
            sort_key = datetime.min
        priority = _feed_priority(event)
        items.append(
            (
                priority,
                sort_key,
                ActivityFeedItem(
                    app=app,
                    app_label=APP_LABELS.get(app, app.replace("_", " ").title()),
                    timestamp=ts_raw,
                    message=message,
                    sort_key=sort_key,
                ),
            )
        )
    items.sort(key=lambda row: (row[0], row[1]), reverse=True)
    return [row[2] for row in items[:limit]]
