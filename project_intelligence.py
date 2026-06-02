"""
Derive active projects, cross-app insights, and accomplishment lines from real events.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from activity_store import ActivitySnapshot, load_all_events
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
        return title if not title.lower().startswith("continue") else f"Continue {title.split(':', 1)[-1].strip()}", subtitle, 48

    return title, subtitle, priority


def _projects_from_events(snapshot: ActivitySnapshot) -> list[tuple[int, str, str, str, str]]:
    """
    Scan events (newest first) and emit (priority, app, title, subtitle, dedupe_key).
    """
    out: list[tuple[int, str, str, str, str]] = []
    events = sorted(load_all_events(), key=lambda e: str(e.get("timestamp") or ""), reverse=True)

    song_state: dict[str, dict[str, datetime | None]] = {}
    inv_health: datetime | None = None
    inv_scenario: datetime | None = None
    inv_scenario_monte = False
    inv_rebalance: datetime | None = None
    inv_holdings: datetime | None = None
    inv_allocation: datetime | None = None
    baseball_draft: datetime | None = None
    baseball_trade: datetime | None = None
    baseball_projection = False
    nba_team = ""
    nba_injury = False
    nba_matchup = False
    nba_playoff = False
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
            elif event_name == "practice":
                if st["practice"] is None:
                    st["practice"] = ts
            elif event_name in {"video_uploaded", "audio_uploaded"}:
                if st["upload"] is None:
                    st["upload"] = ts
            elif event_name == "recording_reviewed":
                if st["review"] is None:
                    st["review"] = ts

        elif app == "investment":
            if event_name in ("portfolio_health_checked", "portfolio_check") and inv_health is None:
                inv_health = ts
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
            if event_name == "draft_prep" and baseball_draft is None:
                baseball_draft = ts
            elif event_name == "trade_eval" and baseball_trade is None:
                baseball_trade = ts
            elif event_name in {"projection_report", "comparison"}:
                baseball_projection = True

        elif app == "nba":
            team = str(m.get("team") or snapshot.last_nba_team or "").strip()
            if team:
                nba_team = team
            pg = str(m.get("page") or event.get("page") or "").lower()
            if event_name == "injury_review" or "injury" in pg:
                nba_injury = True
            if event_name in {"matchup_analysis", "game_outlook"} or "matchup" in pg:
                nba_matchup = True
            if event_name == "playoff_simulation" or "playoff" in pg:
                nba_playoff = True

        elif app == "future_lens" and event_name == "simulation":
            sim = str(m.get("simulation") or m.get("domain") or "").strip()
            if sim and not future_sim:
                future_sim = sim
                lower = sim.lower()
                future_career = any(w in lower for w in ("career", "transition", "ai"))

        elif app == "applied_intelligence" and event_name in {
            "lesson_completed",
            "case_study_completed",
            "analysis",
        }:
            lesson = str(m.get("lesson") or m.get("analysis") or "").strip()
            if lesson and not ai_lesson:
                ai_lesson = lesson

    for song, st in song_state.items():
        edit, practice, upload, review = st["edit"], st["practice"], st["upload"], st["review"]
        if edit and (practice is None or (practice and edit > practice)) and not _stale(edit):
            out.append((60, "music", f"Continue {song} chord edits", "Reinforce verified chart work", f"music:edit:{song}"))
        if upload and (review is None or (review and upload > review)) and not _stale(upload):
            out.append((55, "music", f"Review uploaded {song} recording", "Listen back & note improvements", f"music:upload:{song}"))
        if practice and not _stale(practice):
            if edit is None or (edit and practice >= edit):
                out.append((42, "music", f"Continue {song} practice plan", "Build on your last session", f"music:practice:{song}"))

    if inv_health and (inv_rebalance is None or (inv_rebalance and inv_health > inv_rebalance)) and not _stale(inv_health):
        out.append((58, "investment", "Review portfolio health results", snapshot.last_portfolio_review or "Health & recommendations", "inv:health"))
    if inv_scenario and (inv_rebalance is None or (inv_rebalance and inv_scenario > inv_rebalance)) and not _stale(inv_scenario):
        title = "Continue Monte Carlo analysis" if inv_scenario_monte else "Continue scenario analysis"
        out.append((50, "investment", title, "Review recommendations next", "inv:scenario"))
    if inv_holdings and (inv_allocation is None or (inv_allocation and inv_holdings > inv_allocation)) and not _stale(inv_holdings):
        out.append((48, "investment", "Review allocation recommendations", "Check drift after holdings changes", "inv:allocation"))

    if baseball_draft and not _stale(baseball_draft):
        out.append((56, "baseball", "Continue fantasy draft prep", snapshot.last_baseball_report or "Rankings & sleepers", "bb:draft"))
    if baseball_trade and not _stale(baseball_trade):
        out.append((54, "baseball", "Review trade analysis", "Finalize accept/decline", "bb:trade"))
    if baseball_projection:
        out.append((50, "baseball", "Continue player projection research", snapshot.last_baseball_player or "Projections tab", "bb:proj"))

    if nba_team:
        if nba_matchup:
            out.append((56, "nba", f"Continue {nba_team} matchup analysis", "Game outlook & rotations", f"nba:match:{nba_team}"))
        if nba_injury:
            out.append((52, "nba", f"Review injury report implications ({nba_team})", "Update lineup assumptions", f"nba:injury:{nba_team}"))
        if nba_playoff:
            out.append((54, "nba", f"Continue {nba_team} playoff outlook", "Series context & matchups", f"nba:playoff:{nba_team}"))

    if future_sim:
        lower = future_sim.lower()
        if "teach" in lower or "education" in lower:
            out.append((55, "future_lens", "Continue teaching simulation", future_sim, "fl:teach"))
        elif future_career:
            out.append((54, "future_lens", "Continue AI career transition analysis", future_sim, "fl:career"))
        else:
            out.append((50, "future_lens", f"Continue {future_sim} simulation", snapshot.future_project or "", "fl:sim"))

    if ai_lesson:
        out.append((48, "applied_intelligence", f"Continue: {ai_lesson}", "Next exercise in sequence", f"ai:{ai_lesson}"))

    # Snapshot fallbacks when events are thin
    if snapshot.last_song and snapshot.last_music_edit_days_ago is not None and snapshot.last_music_edit_days_ago <= 5:
        key = f"music:edit:{snapshot.last_song}"
        if not any(x[4] == key for x in out):
            out.append((45, "music", f"Continue {snapshot.last_song} chord edits", snapshot.last_music_edit_label, key))
    if snapshot.last_nba_team and not any(x[1] == "nba" for x in out):
        out.append((40, "nba", f"Continue {snapshot.last_nba_team} matchup analysis", snapshot.last_nba_page, f"nba:{snapshot.last_nba_team}"))
    if (snapshot.future_project or snapshot.last_simulation_name) and not any(x[1] == "future_lens" for x in out):
        label = snapshot.future_project or snapshot.last_simulation_name
        lower = label.lower()
        if "teach" in lower:
            out.append((45, "future_lens", "Continue teaching simulation", label, "fl:teach"))
        elif "career" in lower or "ai" in lower:
            out.append((45, "future_lens", "Continue AI career transition analysis", label, "fl:career"))

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
    themes = {
        "music": "🎵",
        "investment": "📊",
        "baseball": "⚾",
        "nba": "🏀",
        "applied_intelligence": "🧠",
        "future_lens": "🔮",
    }

    merged: dict[str, tuple[int, ContinueCard]] = {}

    for priority, app, title, subtitle, dedupe in _projects_from_events(snapshot):
        if app not in meta or not meta[app]["url"]:
            continue
        card = ContinueCard(
            app_key=app,
            app_name=meta[app]["name"],
            title=title,
            subtitle=subtitle,
            action_url=meta[app]["url"],
            emoji=themes.get(app, "▶"),
        )
        prev = merged.get(dedupe)
        if prev is None or priority > prev[0]:
            merged[dedupe] = (priority, card)

    for item in load_active_resume_items(limit=30):
        if item.app not in meta or not meta[item.app]["url"]:
            continue
        title, subtitle, priority = _polish_resume(item)
        dedupe = f"resume:{item.app}:{item.item_key}"
        card = ContinueCard(
            app_key=item.app,
            app_name=meta[item.app]["name"],
            title=title,
            subtitle=subtitle,
            action_url=meta[item.app]["url"],
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
