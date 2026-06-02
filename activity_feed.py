"""
Human-readable activity feed lines from suite event logs.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

APP_LABELS: dict[str, str] = {
    "music": "Music",
    "baseball": "Baseball",
    "nba": "Basketball",
    "investment": "Investment",
    "applied_intelligence": "Applied Intelligence",
    "future_lens": "Future Lens",
}

# Events stored for diagnostics/coach but omitted from Recent Activity unless summarized.
FEED_SUPPRESSED: frozenset[tuple[str, str]] = frozenset(
    {
        ("music", "song_selected"),
        ("music", "display_key_changed"),
        ("music", "backing_track_started"),
        ("music", "song_added"),
        ("investment", "investment_goal_selected"),
        ("investment", "holdings_updated"),
        ("investment", "ticker_analyzed"),
        ("investment", "risk_profile_changed"),
        ("investment", "frontier_viewed"),
        ("investment", "macro_environment_applied"),
    }
)

INVESTMENT_SETUP_EVENTS = frozenset(
    {
        "portfolio_created",
        "investment_goal_selected",
        "holdings_updated",
        "ticker_analyzed",
    }
)

SETUP_CLUSTER_WINDOW = timedelta(minutes=45)
DEDUPE_WINDOW = timedelta(minutes=20)


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


def _parse_ts(event: dict[str, Any]) -> datetime:
    ts_raw = str(event.get("timestamp") or "")
    try:
        return datetime.fromisoformat(ts_raw)
    except ValueError:
        return datetime.min


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


def format_activity_message(event: dict[str, Any], *, for_feed: bool = True) -> str | None:
    """Return a scannable feed line, or None to skip noise-only events."""
    app = str(event.get("app") or "").strip()
    event_type = str(event.get("event") or "").strip()
    page = str(event.get("page") or "").strip()
    summary = str(event.get("summary") or "").strip()
    m = _metrics(event)

    if for_feed and (app, event_type) in FEED_SUPPRESSED:
        return None
    if for_feed and event_type == "page_view" and app not in {"nba", "baseball"}:
        return None

    if event_type == "practice" and app == "music":
        song = str(m.get("song") or "").strip()
        mins = m.get("minutes")
        instrument = str(m.get("instrument") or "").strip()
        if song and mins and instrument:
            return f"Practiced {song} on {instrument} ({int(mins)} min)"
        if song and mins:
            return f"Practiced {song} ({int(mins)} min)"
        if song and instrument:
            return f"Practiced {song} on {instrument}"
        if song:
            return f"Practiced {song}"
        return "Logged a practice session"

    if event_type == "video_uploaded" and app == "music":
        line = _music_title_artist(m)
        kind = str(m.get("upload_kind") or "performance video").strip()
        if line:
            return f"Uploaded {kind}: {line}"
        return f"Uploaded {kind}"

    if event_type == "audio_uploaded" and app == "music":
        line = _music_title_artist(m)
        kind = str(m.get("upload_kind") or "audio recording").strip()
        if line:
            return f"Uploaded {kind}: {line}"
        return f"Uploaded {kind}"

    if event_type == "display_key_changed" and app == "music":
        if for_feed:
            return None
        song = str(m.get("song") or "").strip()
        dk = str(m.get("display_key") or "").strip()
        if song and dk:
            return f"Changed {song} to {dk}"
        if dk:
            return f"Changed display key to {dk}"
        return "Changed display key"

    if event_type == "backing_track_started" and app == "music":
        if for_feed:
            return None
        line = _music_title_artist(m)
        if line:
            return f"Practiced with backing track: {line}"
        return "Started backing track session"

    if event_type == "backing_track_completed" and app == "music":
        line = _music_title_artist(m)
        if line:
            return f"Completed backing track session: {line}"
        return "Completed backing track session"

    if event_type in ("verified_chart_saved", "lyrics_saved", "chart_save", "chord_save") and app == "music":
        label = _music_edit_headline(event_type, m)
        line = _music_title_artist(m)
        return f"{label}: {line}" if line else label

    if event_type == "song_added" and app == "music":
        if for_feed:
            return None
        line = _music_title_artist(m)
        return f"Added song: {line}" if line else "Added a new song"

    if event_type == "backing_track" and app == "music":
        line = _music_title_artist(m)
        return f"Generated backing track: {line}" if line else "Generated a backing track"

    if event_type == "recording_reviewed" and app == "music":
        line = _music_title_artist(m)
        return f"Reviewed recording: {line}" if line else "Reviewed a recording"

    if event_type == "song_selected" and app == "music":
        if for_feed:
            return None
        line = _music_title_artist(m)
        if line:
            return f"Opened: {line}"
        return summary or None

    if app == "investment":
        if event_type == "investment_goal_selected":
            if for_feed:
                return None
            goal = str(m.get("goal_title") or m.get("goal") or "").strip()
            if goal:
                return f"Selected investment goal: {goal}"
            return "Selected an investment goal"

        if event_type == "portfolio_created":
            count = m.get("holdings_count")
            if count is not None:
                return f"Built starter portfolio: {int(count)} holdings"
            return "Built a starter portfolio"

        if event_type == "holdings_updated":
            if for_feed:
                return None
            tickers = m.get("tickers") or []
            if isinstance(tickers, list) and tickers:
                sample = ", ".join(str(t).upper() for t in tickers[:6])
                if len(tickers) > 6:
                    sample += f", +{len(tickers) - 6} more"
                return f"Updated holdings: {sample}"
            return "Updated portfolio holdings"

        if event_type in ("portfolio_health_checked", "portfolio_check"):
            label = str(m.get("review_type") or "portfolio health").strip()
            score = m.get("score")
            if score is not None:
                return f"Ran portfolio health check ({label}, {float(score):.0f}/100)"
            return "Ran portfolio health check"

        if event_type == "risk_profile_changed":
            if for_feed:
                return None
            profile = str(m.get("risk_profile") or m.get("objective") or "").strip()
            if profile:
                return f"Risk profile: {profile.replace('_', ' ').title()}"
            return "Changed risk profile"

        if event_type == "allocation_reviewed":
            return "Reviewed allocation drift"

        if event_type == "optimizer_run":
            return "Ran portfolio optimizer"

        if event_type == "frontier_viewed":
            if for_feed:
                return None
            return "Viewed efficient frontier"

        if event_type == "macro_environment_applied":
            if for_feed:
                return None
            return "Applied current macro environment"

        if event_type == "scenario_run":
            ctx = str(m.get("scenario_type") or m.get("context") or "").strip()
            if ctx:
                return f"Ran investment scenario ({ctx})"
            return "Ran investment scenario"

        if event_type == "ticker_analyzed":
            if for_feed:
                return None
            ticker = str(m.get("ticker") or "").strip().upper()
            return f"Analyzed ticker {ticker}" if ticker else "Analyzed a ticker"

        if event_type == "rebalance_reviewed":
            return "Reviewed rebalance guidance"

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
            return f"Completed simulation: {sim} ({project})"
        if sim:
            return f"Completed simulation: {sim}"
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
            if for_feed:
                return None
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
            if for_feed:
                return None
            lesson = str(m.get("lesson") or page or "").strip()
            if lesson:
                return f"Opened topic: {lesson}"
        if summary:
            return summary
        if page and app != "nba":
            return None
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
    }:
        return 6
    if app == "music" and event_type in {
        "practice",
        "recording_reviewed",
        "video_uploaded",
        "audio_uploaded",
        "backing_track_completed",
        "backing_track",
    }:
        return 5
    if app == "investment" and event_type in {
        "portfolio_health_checked",
        "portfolio_check",
        "optimizer_run",
        "scenario_run",
        "rebalance_reviewed",
        "allocation_reviewed",
    }:
        return 6
    if app == "investment" and event_type == "portfolio_created":
        return 3
    if event_type in {"comparison", "trade_eval", "lineup_review"}:
        return 5
    if event_type == "simulation" and app == "future_lens":
        return 5
    if event_type == "analysis" and app == "applied_intelligence":
        return 5
    if app == "nba" and event_type == "page_view":
        return 4
    if (app, event_type) in FEED_SUPPRESSED:
        return 0
    if event_type == "page_view":
        return 0
    return 2


def investment_directory_rank(event_type: str) -> int:
    """Higher rank wins on Investment App Directory card."""
    if event_type in {"portfolio_health_checked", "portfolio_check"}:
        return 5
    if event_type in {"allocation_reviewed", "rebalance_reviewed", "optimizer_run"}:
        return 4
    if event_type in {"scenario_run"}:
        return 3
    if event_type == "portfolio_created":
        return 2
    return 0


def music_directory_rank(event_type: str) -> int:
    """Higher rank wins on App Directory card (passive opens are lowest)."""
    if event_type in {"verified_chart_saved", "lyrics_saved", "chart_save", "chord_save"}:
        return 4
    if event_type == "practice":
        return 3
    if event_type in {
        "video_uploaded",
        "audio_uploaded",
        "backing_track_completed",
        "backing_track",
        "recording_reviewed",
    }:
        return 2
    if event_type == "song_selected":
        return 1
    return 0


def _summarize_investment_setup(cluster: list[dict[str, Any]]) -> str | None:
    goal = ""
    holdings = 0
    latest_ts = datetime.min
    for event in cluster:
        m = _metrics(event)
        g = str(m.get("goal_title") or m.get("goal") or "").strip()
        if g:
            goal = g
        try:
            holdings = max(holdings, int(m.get("holdings_count") or 0))
        except (TypeError, ValueError):
            pass
        tickers = m.get("tickers")
        if isinstance(tickers, list):
            holdings = max(holdings, len(tickers))
        ts = _parse_ts(event)
        if ts > latest_ts:
            latest_ts = ts
    if holdings <= 0 and not goal:
        return None
    if goal and holdings:
        return f"Built starter portfolio: {holdings} holdings ({goal})"
    if holdings:
        return f"Built starter portfolio: {holdings} holdings"
    return f"Set investment goal: {goal}" if goal else None


def _cluster_investment_setup(events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[tuple[datetime, str, str]]]:
    """
    Collapse setup clicks in a time window into synthetic feed lines.
    Returns (remaining_events, synthetic_lines as (sort_key, app, message)).
    """
    sorted_events = sorted(events, key=_parse_ts)
    consumed: set[int] = set()
    synthetic: list[tuple[datetime, str, str]] = []

    i = 0
    while i < len(sorted_events):
        event = sorted_events[i]
        if str(event.get("app") or "") != "investment":
            i += 1
            continue
        if str(event.get("event") or "") not in INVESTMENT_SETUP_EVENTS:
            i += 1
            continue
        anchor = _parse_ts(event)
        cluster = [event]
        consumed.add(i)
        j = i + 1
        while j < len(sorted_events):
            other = sorted_events[j]
            if str(other.get("app") or "") != "investment":
                j += 1
                continue
            if str(other.get("event") or "") not in INVESTMENT_SETUP_EVENTS:
                j += 1
                continue
            if _parse_ts(other) - anchor > SETUP_CLUSTER_WINDOW:
                break
            cluster.append(other)
            consumed.add(j)
            j += 1
        msg = _summarize_investment_setup(cluster)
        if msg:
            synthetic.append((anchor, "investment", msg))
        i += 1

    remaining = [e for idx, e in enumerate(sorted_events) if idx not in consumed]
    return remaining, synthetic


def _dedupe_key(event: dict[str, Any]) -> str:
    app = str(event.get("app") or "")
    event_type = str(event.get("event") or "")
    if app == "investment" and event_type == "holdings_updated":
        return f"{app}:holdings"
    return f"{app}:{event_type}"


def build_activity_feed(events: list[dict[str, Any]], *, limit: int = 20) -> list[ActivityFeedItem]:
    remaining, synthetic_lines = _cluster_investment_setup(events)

    items: list[tuple[int, datetime, ActivityFeedItem]] = []
    for sort_key, app, message in synthetic_lines:
        items.append(
            (
                4,
                sort_key,
                ActivityFeedItem(
                    app=app,
                    app_label=APP_LABELS.get(app, app.replace("_", " ").title()),
                    timestamp=sort_key.isoformat(timespec="seconds"),
                    message=message,
                    sort_key=sort_key,
                ),
            )
        )

    sorted_events = sorted(remaining, key=_parse_ts, reverse=True)
    seen: list[tuple[str, datetime, int]] = []

    for event in sorted_events:
        message = format_activity_message(event, for_feed=True)
        if not message:
            continue
        app = str(event.get("app") or "")
        sort_key = _parse_ts(event)
        priority = _feed_priority(event)
        if priority <= 0:
            continue

        key = _dedupe_key(event)
        skip = False
        for prev_key, prev_ts, prev_pri in seen:
            if prev_key == key and abs((sort_key - prev_ts).total_seconds()) <= DEDUPE_WINDOW.total_seconds():
                if priority <= prev_pri:
                    skip = True
                    break
        if skip:
            continue
        seen.append((key, sort_key, priority))

        items.append(
            (
                priority,
                sort_key,
                ActivityFeedItem(
                    app=app,
                    app_label=APP_LABELS.get(app, app.replace("_", " ").title()),
                    timestamp=str(event.get("timestamp") or ""),
                    message=message,
                    sort_key=sort_key,
                ),
            )
        )

    items.sort(key=lambda row: (row[0], row[1]), reverse=True)
    return [row[2] for row in items[:limit]]
