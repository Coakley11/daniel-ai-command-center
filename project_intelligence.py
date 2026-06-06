"""
Derive active projects, cross-app insights, and accomplishment lines from real events.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from activity_store import ActivitySnapshot, load_all_events
from app_branding import suite_app_icons
from suite_storage import ResumeItem, load_active_resume_items

_PROJECT_STALE_DAYS = 14


@dataclass(frozen=True)
class CrossAppInsight:
    message: str
    priority: int = 10


def _parse_ts(raw: str) -> datetime | None:
    try:
        return datetime.fromisoformat(str(raw or "")[:19])
    except ValueError:
        return None


def _song(metrics: dict[str, Any]) -> str:
    return str(metrics.get("song") or metrics.get("last_edited_song") or "").strip()


def _metrics(event: dict[str, Any]) -> dict[str, Any]:
    raw = event.get("metrics")
    return raw if isinstance(raw, dict) else {}


def _latest_music_metrics_for_song(song: str) -> dict[str, Any]:
    """Most recent event metrics for a song — used when resume cards need pick_key/display_key."""
    target = str(song or "").strip()
    if not target:
        return {}
    for event in sorted(
        load_all_events(),
        key=lambda e: str(e.get("timestamp") or ""),
        reverse=True,
    ):
        if str(event.get("app") or "").strip() != "music":
            continue
        m = _metrics(event)
        if _song(m) == target:
            return dict(m)
    return {"song": target}


def _music_resume_metrics(sm: dict[str, Any], song: str) -> dict[str, Any]:
    return {
        "song": song,
        "artist": str(sm.get("artist") or ""),
        "pick_key": str(sm.get("pick_key") or "").strip(),
        "display_key": str(sm.get("display_key") or ""),
        "instrument": str(sm.get("instrument") or ""),
        "practice_focus_section": str(
            sm.get("practice_focus_section") or sm.get("focus") or ""
        ),
    }


def _stale(ts: datetime | None) -> bool:
    if ts is None:
        return True
    return datetime.now() - ts > timedelta(days=_PROJECT_STALE_DAYS)


def _polish_resume(item: ResumeItem) -> tuple[str, str, int]:
    """Turn resume rows into project titles; return (title, subtitle, priority)."""
    title = str(item.title or "").strip()
    subtitle = str(item.subtitle or "").strip()
    key = item.item_key.lower()
    blob = f"{key} {title} {subtitle}".lower()

    if title.lower().startswith("continue:"):
        subject = title.split(":", 1)[-1].strip()
        if item.app == "music":
            if any(w in blob for w in ("chord", "chart", "lyrics", "verified")):
                return f"Continue {subject} chord edits", subtitle or "Music Practice Coach", 58
            if any(w in blob for w in ("record", "upload")):
                return f"Review uploaded {subject} recording", subtitle or "Compare takes & feedback", 52
            return f"Continue {subject} practice plan", subtitle or "Log a focused session", 44
        if item.app == "investment":
            if "health" in blob or "portfolio" in blob:
                return "Review portfolio health results", subtitle or "Recommendations & drift", 58
            if any(w in blob for w in ("monte", "scenario")):
                return "Continue Monte Carlo analysis", subtitle or "Review scenario output", 50
            return "Review allocation recommendations", subtitle or "Portfolio Analytics", 48
        if item.app == "future_lens":
            sim = subject or subtitle
            lower = sim.lower()
            if "teach" in lower or "education" in lower:
                return "Continue teaching simulation", subtitle or sim, 56
            if "career" in lower or "transition" in lower or "ai" in lower:
                return "Continue AI career transition analysis", subtitle or sim, 54
            return f"Continue {sim} simulation", subtitle, 50
        return f"Continue {subject}", subtitle, 40

    if item.app == "baseball" and (key.startswith("trend:") or "trend chart" in blob):
        player = subtitle or key.split(":", 1)[-1].strip()
        if player:
            return f"Continue {player} trend chart", "Trend Value", 58
    if item.app == "baseball" and title.lower().startswith("return to"):
        page = title.replace("Return to", "").strip()
        if "draft" in blob:
            return "Continue fantasy draft prep", subtitle or page, 55
        if "trade" in blob:
            return "Review trade analysis", subtitle or page, 52
        return "Continue player projection research", subtitle or page, 48

    if item.app == "nba":
        team = title.replace("Continue:", "").strip() if ":" in title else title
        if "injury" in blob:
            return f"Review injury report implications ({team})", subtitle, 50
        if any(w in blob for w in ("playoff", "series")):
            return f"Continue {team} playoff outlook", subtitle, 52
        return f"Continue {team} matchup analysis", subtitle, 54

    priority = 35
    if item.app == "applied_intelligence" and "lesson" in blob:
        return (
            title
            if not title.lower().startswith("continue")
            else f"Continue {title.split(':', 1)[-1].strip()}",
            subtitle,
            48,
        )

    return title, subtitle, priority


_MEANINGFUL_WORKFLOW_EVENTS = frozenset(
    {
        "player_comparison",
        "player_trend_viewed",
        "trend_analysis",
        "draft_prep",
        "trade_eval",
        "trade_analysis",
        "breakout_analysis",
        "portfolio_health_checked",
        "portfolio_check",
        "scenario_run",
        "holdings_updated",
        "allocation_reviewed",
        "game_outlook",
        "matchup_analysis",
        "injury_review",
        "injury_analysis",
        "playoff_simulation",
        "verified_chart_saved",
        "practice",
        "backing_track_started",
        "backing_track_completed",
        "lesson_completed",
        "problem_solved",
        "simulation_completed",
    }
)


def _raw_event_workflow_candidate(event: dict[str, Any]) -> dict[str, Any] | None:
    """Map a single stored event to a Continue-style workflow candidate (if possible)."""
    app = str(event.get("app") or "").strip()
    event_name = str(event.get("event") or "").strip()
    if event_name not in _MEANINGFUL_WORKFLOW_EVENTS:
        return None
    ts_raw = str(event.get("timestamp") or "")
    ts = _parse_ts(ts_raw)
    if ts is None:
        return None
    m = _metrics(event)
    resume_key = ""
    priority = 40
    title = event_name.replace("_", " ").title()

    if app == "baseball":
        if event_name == "player_comparison":
            pa = str(m.get("player_a") or "").strip()
            pb = str(m.get("player_b") or "").strip()
            if not pa or not pb:
                return None
            resume_key = f"compare:{pa}:{pb}"
            priority = 59
            title = f"Continue {pa} vs {pb}"
        elif event_name in {"player_trend_viewed", "trend_analysis"}:
            player = str(m.get("player") or "").strip()
            if not player:
                return None
            resume_key = f"trend:{player}"
            priority = 58
            title = f"Continue {player} trend chart"
        elif event_name == "draft_prep":
            resume_key = "bb:draft"
            priority = 56
            title = "Continue fantasy draft prep"
        elif event_name in {"trade_eval", "trade_analysis"}:
            resume_key = "bb:trade"
            priority = 54
            title = "Review trade analysis"
        elif event_name == "breakout_analysis":
            resume_key = "baseball:breakouts"
            priority = 35
            title = "Continue breakout candidate research"
        else:
            return None
    elif app == "investment":
        if event_name in {"portfolio_health_checked", "portfolio_check"}:
            resume_key = "portfolio:health"
            priority = 58
            title = "Review portfolio health results"
        elif event_name == "scenario_run":
            resume_key = "inv:scenario"
            priority = 50
            title = "Continue scenario analysis"
        elif event_name == "holdings_updated":
            resume_key = "inv:allocation"
            priority = 48
            title = "Review allocation recommendations"
        elif event_name == "allocation_reviewed":
            resume_key = "inv:allocation"
            priority = 48
            title = "Review allocation recommendations"
        else:
            return None
    elif app == "nba":
        team = str(m.get("team") or "").strip()
        if not team:
            return None
        if event_name == "game_outlook":
            resume_key = f"nba:game:{team}"
            priority = 60
            title = f"Continue {team.split()[-1]} Live Game Center"
        elif event_name in {"matchup_analysis", "injury_review", "injury_analysis"}:
            resume_key = f"nba:matchup:{team}"
            priority = 56
            title = f"Continue {team} matchup analysis"
        elif event_name == "playoff_simulation":
            resume_key = f"nba:playoff:{team}"
            priority = 54
            title = f"Continue {team} playoff outlook"
        else:
            return None
    elif app == "music":
        song = _song(m)
        pick = str(m.get("pick_key") or "").strip()
        if event_name in {"verified_chart_saved", "lyrics_saved", "chart_save", "chord_save"}:
            resume_key = f"song:{pick}" if pick else f"music:edit:{song or 'song'}"
            priority = 60
            title = f"Continue {song or 'song'} chord edits"
        elif event_name == "practice":
            resume_key = f"song:{pick}" if pick else f"music:practice:{song or 'song'}"
            priority = 42
            title = f"Continue {song or 'song'} practice plan"
        elif event_name.startswith("backing_track"):
            resume_key = f"backing:{pick}" if pick else f"backing:{song or 'song'}"
            priority = 61
            title = f"Continue {song or 'song'}"
        else:
            return None
    else:
        return None

    return {
        "timestamp": ts_raw[:19],
        "app": app,
        "event_type": event_name,
        "resume_key": resume_key,
        "priority": priority,
        "title": title,
        "stale": _stale(ts),
    }


def _merged_continue_rank_map(
    snapshot: ActivitySnapshot,
    *,
    continue_limit: int = 6,
) -> dict[str, tuple[int, int]]:
    """resume_key -> (priority, rank) for slots that would appear in Continue."""
    from app_registry import APP_DEFINITIONS

    meta = {app.key: {"name": app.name, "url": app.streamlit_url.strip()} for app in APP_DEFINITIONS}
    merged: dict[str, int] = {}

    for priority, app, _title, _subtitle, resume_key, _page, _metrics in _projects_from_events(snapshot):
        if app not in meta or not meta[app]["url"]:
            continue
        prev = merged.get(resume_key)
        if prev is None or priority > prev:
            merged[resume_key] = priority

    for item in load_active_resume_items(limit=30):
        if item.app not in meta or not meta[item.app]["url"]:
            continue
        _title, _subtitle, priority = _polish_resume(item)
        dedupe = f"resume:{item.app}:{item.item_key}"
        prev = merged.get(dedupe)
        if prev is None or priority > prev:
            merged[dedupe] = priority
        prev_item = merged.get(item.item_key)
        if prev_item is None or priority > prev_item:
            merged[item.item_key] = priority

    ordered = sorted(merged.items(), key=lambda row: row[1], reverse=True)
    rank_map: dict[str, tuple[int, int]] = {}
    for rank, (rk, pr) in enumerate(ordered[:continue_limit], start=1):
        rank_map[rk] = (pr, rank)
    return rank_map


def diagnose_continue_workflow_candidates(
    snapshot: ActivitySnapshot | None = None,
    *,
    display_limit: int = 10,
    continue_limit: int = 6,
) -> list[dict[str, Any]]:
    """
    Top recent meaningful workflow events with Continue inclusion/exclusion reasons.
    """
    snap = snapshot or ActivitySnapshot()
    rank_map = _merged_continue_rank_map(snap, continue_limit=continue_limit)
    included_keys = set(rank_map.keys())

    events = sorted(load_all_events(limit=300), key=lambda e: str(e.get("timestamp") or ""), reverse=True)
    rows: list[dict[str, Any]] = []
    seen_event: set[tuple[str, str, str]] = set()

    for event in events:
        if len(rows) >= display_limit:
            break
        dedupe = (
            str(event.get("app") or ""),
            str(event.get("timestamp") or ""),
            str(event.get("event") or ""),
        )
        if dedupe in seen_event:
            continue
        cand = _raw_event_workflow_candidate(event)
        if cand is None:
            continue
        seen_event.add(dedupe)
        rk = cand["resume_key"]
        if cand["stale"]:
            status = "excluded"
            reason = f"Stale (>{_PROJECT_STALE_DAYS} days)"
        elif rk in rank_map:
            pr, rank = rank_map[rk]
            status = "included"
            reason = f"Continue rank {rank} (priority {pr})"
        elif rk in included_keys:
            status = "included"
            reason = "Included via resume item merge"
        else:
            status = "excluded"
            if rank_map and cand["priority"] < min(p for p, _ in rank_map.values()):
                reason = f"Below top {continue_limit} (priority {cand['priority']})"
            elif not rank_map:
                reason = "No Continue cards emitted from current snapshot"
            else:
                reason = (
                    f"Not in top {continue_limit} — aggregated out or lower priority "
                    f"({cand['priority']})"
                )
        rows.append(
            {
                "timestamp": cand["timestamp"],
                "app": cand["app"],
                "event_type": cand["event_type"],
                "resume_key": rk,
                "priority": cand["priority"],
                "status": status,
                "reason": reason,
            }
        )

    return rows


@dataclass
class BaseballContinueDiagnostic:
    """End-to-end trace for Baseball trend → Continue card pipeline."""

    trend_events_in_store: int = 0
    latest_trend_event: dict[str, Any] | None = None
    latest_baseball_workflow: dict[str, Any] | None = None
    workflow_would_emit: bool = False
    continue_cards_baseball: list[dict[str, Any]] = field(default_factory=list)
    continue_rank_all_apps: list[dict[str, Any]] = field(default_factory=list)
    in_top_six: bool = False
    blocked_reason: str = ""
    resume_trend_items: list[dict[str, Any]] = field(default_factory=list)


def diagnose_baseball_continue(
    snapshot: ActivitySnapshot | None = None,
    *,
    limit: int = 6,
) -> BaseballContinueDiagnostic:
    """Answer whether a Lorenzo Cain-style trend should appear in Continue."""
    from continue_dashboard import build_continue_cards
    from suite_storage import load_active_resume_items

    snap = snapshot or ActivitySnapshot()
    diag = BaseballContinueDiagnostic()
    events = load_all_events(limit=500)
    trend_events = [
        e
        for e in events
        if str(e.get("app") or "") == "baseball"
        and str(e.get("event") or "") in {"player_trend_viewed", "trend_analysis"}
    ]
    diag.trend_events_in_store = len(trend_events)
    if trend_events:
        diag.latest_trend_event = max(trend_events, key=lambda e: str(e.get("timestamp") or ""))

    for item in load_active_resume_items(limit=30):
        if item.app == "baseball" and (
            item.item_key.startswith("trend:") or "trend chart" in item.title.lower()
        ):
            diag.resume_trend_items.append(
                {
                    "item_key": item.item_key,
                    "title": item.title,
                    "subtitle": item.subtitle,
                    "updated_at": item.updated_at,
                }
            )

    derived = _projects_from_events(snap)
    baseball_derived = [c for c in derived if c[1] == "baseball"]
    for pr, app, title, subtitle, rk, page, bm in baseball_derived:
        diag.continue_cards_baseball.append(
            {
                "priority": pr,
                "title": title,
                "subtitle": subtitle,
                "resume_key": rk,
                "page": page,
                "metrics_player": bm.get("player"),
            }
        )
    for pr, app, title, subtitle, rk, page, bm in derived:
        if "trend" in rk or "trend chart" in title.lower():
            diag.latest_baseball_workflow = {
                "priority": pr,
                "app": app,
                "title": title,
                "resume_key": rk,
                "event_type": bm.get("event") if isinstance(bm, dict) else None,
                "player": bm.get("player") if isinstance(bm, dict) else None,
            }
            diag.workflow_would_emit = True
            break

    if not diag.workflow_would_emit and diag.latest_trend_event:
        m = diag.latest_trend_event.get("metrics")
        player = str((m or {}).get("player") or "").strip() if isinstance(m, dict) else ""
        if not player:
            diag.blocked_reason = "Latest trend event missing metrics.player"
        else:
            ts = _parse_ts(str(diag.latest_trend_event.get("timestamp") or ""))
            if _stale(ts):
                diag.blocked_reason = f"Trend event older than {_PROJECT_STALE_DAYS} days"
            else:
                diag.blocked_reason = "Trend event exists but was superseded by a newer baseball workflow"
    elif not diag.latest_trend_event:
        diag.blocked_reason = "No player_trend_viewed or trend_analysis events in Command Center store"

    all_cards = build_continue_cards(limit=limit, snapshot=snap)
    for i, card in enumerate(all_cards):
        diag.continue_rank_all_apps.append(
            {
                "rank": i + 1,
                "app": card.app_key,
                "title": card.title,
            }
        )
        if card.app_key == "baseball" and "trend" in card.title.lower():
            diag.in_top_six = True
    if diag.workflow_would_emit and not diag.in_top_six and not diag.blocked_reason:
        diag.blocked_reason = f"Trend card computed but not in top {limit} Continue slots (priority cap)"

    return diag


def _projects_from_events(
    snapshot: ActivitySnapshot,
) -> list[tuple[int, str, str, str, str, str, dict[str, Any]]]:
    """
    Scan events (newest first) and emit
    (priority, app, title, subtitle, resume_key, page, metrics).
    """
    out: list[tuple[int, str, str, str, str, str, dict[str, Any]]] = []
    events = sorted(load_all_events(), key=lambda e: str(e.get("timestamp") or ""), reverse=True)

    song_state: dict[str, dict[str, datetime | None]] = {}
    song_metrics: dict[str, dict[str, Any]] = {}
    inv_health: datetime | None = None
    inv_health_metrics: dict[str, Any] = {}
    inv_scenario: datetime | None = None
    inv_scenario_monte = False
    inv_rebalance: datetime | None = None
    inv_holdings: datetime | None = None
    inv_allocation: datetime | None = None
    baseball_draft: datetime | None = None
    baseball_trade: datetime | None = None
    baseball_projection = False
    baseball_compare: tuple[str, str, datetime, dict[str, Any]] | None = None
    baseball_trend: tuple[str, datetime, dict[str, Any]] | None = None
    latest_baseball_workflow: tuple[datetime, int, str, str, str, str, dict[str, Any]] | None = None
    latest_music_workflow: tuple[datetime, str, dict[str, Any], str] | None = None
    _MUSIC_WORKFLOW_PRIORITY = {
        "backing_track_started": 70,
        "backing_track_completed": 68,
        "practice": 65,
        "display_key_changed": 62,
        "instrument_changed": 60,
        "studio_page_entered": 58,
        "song_selected": 55,
    }
    nba_team = ""
    nba_injury = False
    nba_matchup = False
    nba_playoff = False
    nba_game: datetime | None = None
    nba_game_team = ""
    nba_game_page = ""
    future_sim = ""
    future_career = False
    ai_lesson = ""

    for event in events:
        app = str(event.get("app") or "").strip()
        event_name = str(event.get("event") or "").strip()
        ts = _parse_ts(str(event.get("timestamp") or ""))
        if ts is None:
            continue
        m = _metrics(event)

        if app == "music":
            song = _song(m)
            if not song:
                continue
            st = song_state.setdefault(song, {"edit": None, "practice": None, "upload": None, "review": None})
            if event_name in {"verified_chart_saved", "lyrics_saved", "chart_save", "chord_save"}:
                if st["edit"] is None:
                    st["edit"] = ts
                    song_metrics.setdefault(song, m)
            elif event_name == "practice":
                if st["practice"] is None:
                    st["practice"] = ts
                    song_metrics[song] = m
            elif event_name in {"video_uploaded", "audio_uploaded"}:
                if st["upload"] is None:
                    st["upload"] = ts
                    song_metrics.setdefault(song, m)
            elif event_name == "recording_reviewed":
                if st["review"] is None:
                    st["review"] = ts
            elif event_name in _MUSIC_WORKFLOW_PRIORITY and song:
                song_metrics[song] = {**song_metrics.get(song, {}), **m}
                pr = _MUSIC_WORKFLOW_PRIORITY[event_name]
                cur = latest_music_workflow
                if cur is None or pr > _MUSIC_WORKFLOW_PRIORITY.get(cur[3], 0) or (
                    pr == _MUSIC_WORKFLOW_PRIORITY.get(cur[3], 0) and ts > cur[0]
                ):
                    latest_music_workflow = (ts, song, m, event_name)

        elif app == "investment":
            if event_name in ("portfolio_health_checked", "portfolio_check") and inv_health is None:
                inv_health = ts
                inv_health_metrics = dict(m)
            elif event_name == "scenario_run":
                if inv_scenario is None:
                    inv_scenario = ts
                    ctx = str(m.get("scenario_type") or m.get("context") or "").lower()
                    inv_scenario_monte = "monte" in ctx or "carlo" in ctx
            elif event_name == "rebalance_reviewed" and inv_rebalance is None:
                inv_rebalance = ts
            elif event_name == "holdings_updated" and inv_holdings is None:
                inv_holdings = ts
            elif event_name == "allocation_reviewed" and inv_allocation is None:
                inv_allocation = ts

        elif app == "baseball":
            if event_name == "player_comparison":
                pa = str(m.get("player_a") or "").strip()
                pb = str(m.get("player_b") or "").strip()
                if pa and pb and (baseball_compare is None or ts >= baseball_compare[2]):
                    baseball_compare = (pa, pb, ts, m)
                    pair = f"{pa} vs {pb}"
                    cand = (
                        ts,
                        59,
                        f"Continue {pair}",
                        "Comparison Tool",
                        f"compare:{pa}:{pb}",
                        "Comparison Tool",
                        {"player_a": pa, "player_b": pb, **m},
                    )
                    if latest_baseball_workflow is None or ts >= latest_baseball_workflow[0]:
                        latest_baseball_workflow = cand
            elif event_name in {"player_trend_viewed", "trend_analysis"}:
                baseball_projection = True
                player = str(m.get("player") or "").strip()
                if player and (baseball_trend is None or ts >= baseball_trend[1]):
                    baseball_trend = (player, ts, m)
                    cand = (
                        ts,
                        58,
                        f"Continue {player} trend chart",
                        "Trend Value",
                        f"trend:{player}",
                        "Trend Value",
                        {"player": player, **m},
                    )
                    if latest_baseball_workflow is None or ts >= latest_baseball_workflow[0]:
                        latest_baseball_workflow = cand
            elif event_name == "draft_prep":
                cand = (
                    ts,
                    56,
                    "Continue fantasy draft prep",
                    snapshot.last_baseball_report or "Rankings & sleepers",
                    "bb:draft",
                    "Draft Simulation",
                    dict(m),
                )
                if latest_baseball_workflow is None or ts >= latest_baseball_workflow[0]:
                    latest_baseball_workflow = cand
            elif event_name in {"trade_eval", "trade_analysis"}:
                cand = (
                    ts,
                    54,
                    "Review trade analysis",
                    "Finalize accept/decline",
                    "bb:trade",
                    "Fantasy Lineup Assistant",
                    dict(m),
                )
                if latest_baseball_workflow is None or ts >= latest_baseball_workflow[0]:
                    latest_baseball_workflow = cand
            elif event_name in {
                "projection_report",
                "comparison",
                "breakout_analysis",
            }:
                baseball_projection = True

        elif app == "nba":
            team = str(m.get("team") or snapshot.last_nba_team or "").strip()
            if team:
                nba_team = team
            pg = str(m.get("page") or event.get("page") or "").lower()
            if event_name == "injury_review" or "injury" in pg:
                nba_injury = True
            if event_name in {"matchup_analysis"} or ("matchup" in pg and "live" not in pg):
                nba_matchup = True
            if event_name == "playoff_simulation" or "playoff" in pg:
                nba_playoff = True
            if event_name == "game_outlook" or ("live" in pg and "game" in pg):
                if nba_game is None:
                    nba_game = ts
                    nba_game_team = team
                    nba_game_page = str(m.get("page") or event.get("page") or "🔴 Live Game Center")

        elif app == "future_lens" and event_name in {"simulation", "simulation_completed"}:
            sim = str(m.get("simulation") or m.get("domain") or "").strip()
            if sim and not future_sim:
                future_sim = sim
                lower = sim.lower()
                future_career = any(w in lower for w in ("career", "transition", "ai"))

        elif app == "applied_intelligence" and event_name in {
            "lesson_completed",
            "case_study_completed",
            "analysis",
            "problem_solved",
            "module_completed",
            "reasoning_exercise_completed",
        }:
            lesson = str(m.get("lesson") or m.get("analysis") or "").strip()
            if lesson and not ai_lesson:
                ai_lesson = lesson

    for song, st in song_state.items():
        edit, practice, upload, review = st["edit"], st["practice"], st["upload"], st["review"]
        sm = song_metrics.get(song) or {}
        pick_key = str(sm.get("pick_key") or "").strip()
        resume_metrics = _music_resume_metrics(sm, song)
        if edit and (practice is None or (practice and edit > practice)) and not _stale(edit):
            rk = f"song:{pick_key}" if pick_key else f"music:edit:{song}"
            out.append(
                (60, "music", f"Continue {song} chord edits", "Reinforce verified chart work", rk, "practice", resume_metrics)
            )
        if upload and (review is None or (review and upload > review)) and not _stale(upload):
            rk = f"song:{pick_key}" if pick_key else f"music:upload:{song}"
            out.append(
                (55, "music", f"Review uploaded {song} recording", "Listen back & note improvements", rk, "recording", resume_metrics)
            )
        if practice and not _stale(practice):
            if edit is None or (edit and practice >= edit):
                rk = f"song:{pick_key}" if pick_key else f"music:practice:{song}"
                subtitle = str(sm.get("focus") or sm.get("artist") or "Build on your last session")
                out.append(
                    (42, "music", f"Continue {song} practice plan", subtitle, rk, "practice", resume_metrics)
                )

    if inv_health and (inv_rebalance is None or (inv_rebalance and inv_health > inv_rebalance)) and not _stale(inv_health):
        subtitle = snapshot.last_portfolio_review or str(inv_health_metrics.get("review_type") or "Health & recommendations")
        out.append(
            (
                58,
                "investment",
                "Review portfolio health results",
                subtitle,
                "portfolio:health",
                "Portfolio Health",
                inv_health_metrics,
            )
        )
    if inv_scenario and (inv_rebalance is None or (inv_rebalance and inv_scenario > inv_rebalance)) and not _stale(inv_scenario):
        title = "Continue Monte Carlo analysis" if inv_scenario_monte else "Continue scenario analysis"
        out.append((50, "investment", title, "Review recommendations next", "inv:scenario", "Efficient Frontier", {}))
    if inv_holdings and (inv_allocation is None or (inv_allocation and inv_holdings > inv_allocation)) and not _stale(inv_holdings):
        out.append(
            (48, "investment", "Review allocation recommendations", "Check drift after holdings changes", "inv:allocation", "Portfolio Health", {})
        )

    if latest_music_workflow and not _stale(latest_music_workflow[0]):
        ts, song, wm, ev = latest_music_workflow
        sm = {**song_metrics.get(song, {}), **wm}
        resume_metrics = _music_resume_metrics(sm, song)
        studio = str(sm.get("studio_page") or "").strip()
        if ev.startswith("backing") or studio == "backing":
            page = "backing"
            pick = str(resume_metrics.get("pick_key") or "").strip()
            rk = f"backing:{pick}" if pick else f"backing:{song}"
        else:
            page = "practice"
            pick = str(resume_metrics.get("pick_key") or "").strip()
            rk = f"song:{pick}" if pick else f"music:workflow:{song}"
        inst = str(resume_metrics.get("instrument") or "")
        dk = str(resume_metrics.get("display_key") or "")
        subtitle = " · ".join(p for p in [dk, inst, page] if p)
        out.append(
            (
                61,
                "music",
                f"Continue {song}",
                subtitle or "Resume your last session",
                rk,
                page,
                resume_metrics,
            )
        )

    if latest_baseball_workflow and not _stale(latest_baseball_workflow[0]):
        ts, pr, title, subtitle, rk, page, bm = latest_baseball_workflow
        out.append((pr, "baseball", title, subtitle, rk, page, bm))
    elif baseball_projection and not baseball_compare:
        out.append((50, "baseball", "Continue player projection research", snapshot.last_baseball_player or "Projections tab", "bb:proj", "ML Projections", {}))

    if nba_game and not _stale(nba_game):
        short = nba_game_team.split()[-1] if nba_game_team else "team"
        out.append(
            (
                60,
                "nba",
                f"Continue {short} Live Game Center",
                nba_game_page,
                f"nba:game:{nba_game_team}",
                "🔴 Live Game Center",
                {"team": nba_game_team, "page": nba_game_page},
            )
        )
    elif nba_team:
        if nba_matchup:
            out.append((56, "nba", f"Continue {nba_team} matchup analysis", "Game outlook & rotations", f"nba:matchup:{nba_team}", "🧠 Matchup Intelligence", {"team": nba_team}))
        if nba_injury:
            out.append((52, "nba", f"Review injury report implications ({nba_team})", "Update lineup assumptions", f"nba:injury:{nba_team}", "🧠 Matchup Intelligence", {"team": nba_team}))
        if nba_playoff:
            out.append((54, "nba", f"Continue {nba_team} playoff outlook", "Series context & matchups", f"nba:playoff:{nba_team}", "🏆 Playoff Bracket", {"team": nba_team}))

    if future_sim:
        lower = future_sim.lower()
        if "teach" in lower or "education" in lower:
            out.append((55, "future_lens", "Continue teaching simulation", future_sim, "fl:teach", "simulation", {"simulation": future_sim}))
        elif future_career:
            out.append((54, "future_lens", "Continue AI career transition analysis", future_sim, "fl:career", "simulation", {"simulation": future_sim}))
        else:
            out.append((50, "future_lens", f"Continue {future_sim} simulation", snapshot.future_project or "", "fl:sim", "simulation", {"simulation": future_sim}))

    if ai_lesson:
        out.append((48, "applied_intelligence", f"Continue: {ai_lesson}", "Next exercise in sequence", f"ai:{ai_lesson}", "lessons", {"lesson": ai_lesson}))

    # Snapshot fallbacks when events are thin
    if snapshot.last_song and snapshot.last_music_edit_days_ago is not None and snapshot.last_music_edit_days_ago <= 5:
        sm = _latest_music_metrics_for_song(snapshot.last_song)
        pick_key = str(sm.get("pick_key") or "").strip()
        rk = f"song:{pick_key}" if pick_key else f"music:edit:{snapshot.last_song}"
        if not any(x[4] == rk for x in out):
            out.append(
                (
                    45,
                    "music",
                    f"Continue {snapshot.last_song} chord edits",
                    snapshot.last_music_edit_label,
                    rk,
                    "practice",
                    _music_resume_metrics(sm, snapshot.last_song),
                )
            )
    if snapshot.last_nba_team and not any(x[1] == "nba" for x in out):
        out.append(
            (
                40,
                "nba",
                f"Continue {snapshot.last_nba_team} matchup analysis",
                snapshot.last_nba_page,
                f"nba:matchup:{snapshot.last_nba_team}",
                "🧠 Matchup Intelligence",
                {"team": snapshot.last_nba_team},
            )
        )
    if (snapshot.future_project or snapshot.last_simulation_name) and not any(x[1] == "future_lens" for x in out):
        label = snapshot.future_project or snapshot.last_simulation_name
        lower = label.lower()
        if "teach" in lower:
            out.append((45, "future_lens", "Continue teaching simulation", label, "fl:teach", "simulation", {"simulation": label}))
        elif "career" in lower or "ai" in lower:
            out.append((45, "future_lens", "Continue AI career transition analysis", label, "fl:career", "simulation", {"simulation": label}))

    return out


def build_project_continue_cards(
    snapshot: ActivitySnapshot,
    *,
    limit: int = 6,
    meta: dict[str, dict[str, str]] | None = None,
) -> list:
    from app_registry import APP_DEFINITIONS
    from continue_dashboard import ContinueCard

    if meta is None:
        meta = {app.key: {"name": app.name, "url": app.streamlit_url.strip()} for app in APP_DEFINITIONS}
    themes = suite_app_icons()

    merged: dict[str, tuple[int, ContinueCard]] = {}

    for priority, app, title, subtitle, resume_key, page, metrics in _projects_from_events(snapshot):
        if app not in meta or not meta[app]["url"]:
            continue
        try:
            from suite_deep_links import build_resume_action_url

            deep = build_resume_action_url(
                app,
                resume_key=resume_key,
                page=page,
                metrics=metrics,
                base_url=meta[app]["url"],
            )
        except Exception:
            deep = ""
        card = ContinueCard(
            app_key=app,
            app_name=meta[app]["name"],
            title=title,
            subtitle=subtitle,
            action_url=deep or meta[app]["url"],
            emoji=themes.get(app, "▶"),
        )
        prev = merged.get(resume_key)
        if prev is None or priority > prev[0]:
            merged[resume_key] = (priority, card)

    for item in load_active_resume_items(limit=30):
        if item.app not in meta or not meta[item.app]["url"]:
            continue
        title, subtitle, priority = _polish_resume(item)
        dedupe = f"resume:{item.app}:{item.item_key}"
        try:
            from suite_deep_links import build_resume_action_url, resume_metrics_from_item_key

            page_hint, metrics = resume_metrics_from_item_key(
                item.app,
                item.item_key,
                subtitle=item.subtitle,
            )
            if item.app == "music" and item.title.lower().startswith("continue:"):
                metrics.setdefault("song", item.title.split(":", 1)[-1].strip())
            deep = build_resume_action_url(
                item.app,
                resume_key=item.item_key,
                page=page_hint,
                metrics=metrics,
                base_url=meta[item.app]["url"],
            )
        except Exception:
            deep = ""
        url = deep or (item.action_url or "").strip() or meta[item.app]["url"]
        card = ContinueCard(
            app_key=item.app,
            app_name=meta[item.app]["name"],
            title=title,
            subtitle=subtitle,
            action_url=url,
            emoji=themes.get(item.app, "▶"),
        )
        prev = merged.get(dedupe)
        if prev is None or priority > prev[0]:
            merged[dedupe] = (priority, card)

    ordered = sorted(merged.values(), key=lambda row: row[0], reverse=True)
    return [card for _, card in ordered[:limit]]


def generate_cross_app_insights(snapshot: ActivitySnapshot) -> list[CrossAppInsight]:
    insights: list[CrossAppInsight] = []
    apps = snapshot.week_activity_by_app
    active = [(app, count) for app, count in apps.items() if count > 0]
    active.sort(key=lambda x: x[1], reverse=True)

    if len(active) >= 2:
        names = []
        for key, _ in active[:2]:
            names.append(
                {
                    "music": "music",
                    "investment": "investment",
                    "baseball": "baseball",
                    "nba": "basketball",
                    "applied_intelligence": "Applied Intelligence",
                    "future_lens": "Future Lens",
                }.get(key, key.replace("_", " "))
            )
        insights.append(
            CrossAppInsight(
                message=f"You spent most of your time this week on {names[0]} and {names[1]} projects.",
                priority=8,
            )
        )

    if snapshot.top_project_label:
        insights.append(
            CrossAppInsight(
                message=f"Your most active project is {snapshot.top_project_label}.",
                priority=10,
            )
        )

    if snapshot.top_research_area:
        insights.append(
            CrossAppInsight(
                message=f"Your most active research area is {snapshot.top_research_area}.",
                priority=12,
            )
        )

    pending = snapshot.pending_review_count
    if pending >= 2:
        insights.append(
            CrossAppInsight(
                message=f"{pending} projects are waiting for review — check Continue below.",
                priority=6,
            )
        )
    elif pending == 1:
        insights.append(
            CrossAppInsight(
                message="One project is waiting for review — see Continue for the next step.",
                priority=14,
            )
        )

    return sorted(insights, key=lambda x: x.priority)[:3]


def weekly_accomplishment_lines(summary: Any) -> list[tuple[str, str]]:
    """Human accomplishment lines: (count, label)."""
    lines: list[tuple[str, str]] = []
    if summary.songs_practiced > 0:
        n = summary.songs_practiced
        lines.append((str(n), f"practice session{'s' if n != 1 else ''}"))
    if summary.music_practice_sessions > 0 and summary.songs_practiced == 0:
        n = summary.music_practice_sessions
        lines.append((str(n), f"practice session{'s' if n != 1 else ''}"))
    if summary.music_verified_edits > 0:
        n = summary.music_verified_edits
        lines.append((str(n), f"verified chart edit{'s' if n != 1 else ''}"))
    if summary.music_lyrics_edits > 0:
        n = summary.music_lyrics_edits
        lines.append((str(n), f"verified lyrics edit{'s' if n != 1 else ''}"))
    if summary.music_uploads > 0:
        n = summary.music_uploads
        lines.append((str(n), f"recording{'s' if n != 1 else ''} uploaded"))
    if summary.music_backing_sessions > 0:
        n = summary.music_backing_sessions
        lines.append((str(n), f"backing track session{'s' if n != 1 else ''}"))
    if summary.portfolio_checks > 0:
        n = summary.portfolio_checks
        lines.append((str(n), f"portfolio review{'s' if n != 1 else ''}"))
    if summary.investment_optimizer_runs > 0:
        n = summary.investment_optimizer_runs
        lines.append((str(n), f"optimizer run{'s' if n != 1 else ''}"))
    if summary.investment_scenarios > 0:
        n = summary.investment_scenarios
        lines.append((str(n), f"scenario anal{'yses' if n != 1 else 'ysis'}"))
    if summary.investment_rebalance_reviews > 0:
        n = summary.investment_rebalance_reviews
        lines.append((str(n), f"rebalance review{'s' if n != 1 else ''}"))
    if summary.baseball_analyses > 0:
        n = summary.baseball_analyses
        lines.append((str(n), f"baseball anal{'yses' if n != 1 else 'ysis'}"))
    if summary.nba_analyses > 0:
        n = summary.nba_analyses
        lines.append((str(n), f"basketball anal{'yses' if n != 1 else 'ysis'}"))
    if summary.applied_lessons_completed > 0:
        n = summary.applied_lessons_completed
        lines.append((str(n), f"lesson{'s' if n != 1 else ''} completed"))
    if summary.future_simulations > 0:
        n = summary.future_simulations
        lines.append((str(n), f"future simulation{'s' if n != 1 else ''}"))
    if summary.music_minutes > 0 and not any("practice" in label for _, label in lines):
        lines.append((f"{summary.music_minutes:.0f}", "minutes practiced"))
    return lines
