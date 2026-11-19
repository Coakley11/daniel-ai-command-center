"""
Meaningful activity: what was actually accomplished, per app, today and this week.

One classifier, used by both Activity (today) and Weekly Summary (this week):

* Only confirmed, completed or saved work counts. Page views, filter changes, selections,
  "started" events and automatic background events are ignored.
* Each accomplishment is counted once: by ``metrics.event_key`` when the app sends one
  (Investment does), otherwise by a stable identity of the event.
* "Today" and "this week" use one clock: America/New_York (``activity_time``). The week
  starts Monday 00:00 there. Event timestamps are UTC and keep their real date.
* Investment keeps the real portfolio (My Portfolio ledger) apart from the planning
  (hypothetical) portfolio: a 100% VTI plan is never shown as a purchase.

Apps with no event that marks completed work (e.g. NBA, which only sends page views)
show nothing rather than an invented accomplishment.
"""

from __future__ import annotations

import json
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Iterable

APP_LABELS: dict[str, str] = {
    "investment": "Investment Portfolio Analyzer",
    "baseball": "Baseball Explorer",
    "music": "Music Practice Coach",
    "applied_intelligence": "Applied Mathematical Intelligence",
    "future_lens": "Future Lens",
    "nba": "NBA Playoff Companion",
}
APP_ORDER = ("investment", "baseball", "music", "applied_intelligence", "future_lens", "nba")


@dataclass(frozen=True)
class Accomplishment:
    app: str
    group: str  # items in one group combine into one line
    label: str  # the line when the group has a single item
    when: datetime  # aware, UTC
    key: str  # identity for de-duplication
    order: int = 50  # lower first within an app
    amount: float = 0.0
    detail: str = ""  # e.g. a ticker or song, collected for combined lines


@dataclass
class AppSection:
    app: str
    title: str
    lines: list[str] = field(default_factory=list)
    count: int = 0


# ── time ──────────────────────────────────────────────────────────────────────


def _parse(ts: Any) -> datetime | None:
    try:
        from activity_time import parse_activity_timestamp

        return parse_activity_timestamp(str(ts or ""))
    except Exception:
        return None


def _local(dt_utc: datetime) -> datetime:
    from activity_time import to_display_local

    return to_display_local(dt_utc)


def local_today(now: datetime | None = None) -> date:
    return _local(now or datetime.now(timezone.utc)).date()


def local_week_start(now: datetime | None = None) -> date:
    """Monday of the current week, in the display timezone."""
    today = local_today(now)
    return today - timedelta(days=today.weekday())


# ── helpers ───────────────────────────────────────────────────────────────────


def _m(event: dict[str, Any]) -> dict[str, Any]:
    m = event.get("metrics")
    return m if isinstance(m, dict) else {}


def _money(x: Any) -> str:
    try:
        return f"${float(x):,.2f}"
    except (TypeError, ValueError):
        return ""


def _shares(x: Any) -> str:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return ""
    if abs(v - round(v)) < 1e-9:
        n = int(round(v))
        return f"{n:,} share" + ("" if n == 1 else "s")
    return f"{v:,.4f}".rstrip("0").rstrip(".") + " shares"


def _title_text(text: Any, limit: int = 60) -> str:
    s = " ".join(str(text or "").split())
    return s if len(s) <= limit else s[: limit - 1] + "…"


def _identity(event: dict[str, Any]) -> str:
    m = _m(event)
    key = str(m.get("event_key") or "").strip()
    if key:
        return f"{event.get('app')}|{key}"
    for id_field in ("recording_id", "export_id", "practice_log_id", "transaction_id", "proposal_id"):
        if m.get(id_field):
            return f"{event.get('app')}|{event.get('event')}|{m.get(id_field)}"
    stable = {k: v for k, v in m.items() if k not in ("workspace_id", "timestamp", "resume_payload")}
    return "|".join(
        [str(event.get("app")), str(event.get("event")), str(event.get("timestamp"))[:19],
         json.dumps(stable, sort_keys=True, default=str)[:400]]
    )


# ── per-app classifiers ───────────────────────────────────────────────────────
# Each returns (group, label, order, amount, detail) or None when the event is not an
# accomplishment.

Classified = tuple[str, str, int, float, str]


def _investment(event: dict[str, Any]) -> Classified | None:
    name = str(event.get("event") or "")
    m = _m(event)
    alloc = str(m.get("allocation_label") or "").strip()
    if name == "real_cash_deposited":
        return ("real_deposit", f"Added {_money(m.get('amount'))} to your real portfolio", 1, float(m.get("amount") or 0), "")
    if name == "real_cash_withdrawn":
        return ("real_withdrawal", f"Withdrew {_money(m.get('amount'))} from your real portfolio", 2, float(m.get("amount") or 0), "")
    if name in ("real_investment_purchased", "real_investment_sold"):
        sym = str(m.get("ticker") or "").upper()
        buy = name == "real_investment_purchased"
        first = buy and bool(m.get("first_purchase_of_ticker"))
        verb = ("Recorded first real " if first else "Recorded real ") + sym + (" purchase" if buy else " sale")
        label = f"{verb} — {_shares(m.get('shares'))} at {_money(m.get('price'))}"
        group = ("real_first_purchase:" + sym) if first else ("real_buy" if buy else "real_sell")
        return (group, label, 0 if first else 3, float(m.get("amount") or 0), sym)
    if name == "real_contribution_recorded":
        n = int(m.get("purchase_count") or 0)
        return ("real_contribution", f"Recorded a {_money(m.get('amount'))} contribution ({n} purchase{'s' if n != 1 else ''})", 4, float(m.get("amount") or 0), "")
    if name == "real_transaction_removed":
        return ("real_removed", "Corrected the real portfolio ledger (removed a transaction)", 6, 0.0, "")
    if name == "real_strategy_target_saved":
        w = m.get("strategy_target_weights") if isinstance(m.get("strategy_target_weights"), dict) else {}
        parts = sorted(((str(k), float(v)) for k, v in w.items()), key=lambda x: -x[1])[:4]
        scale = 100.0 if parts and sum(v for _, v in parts) <= 1.0001 else 1.0
        label = ", ".join(f"{v * scale:.0f}% {k}" for k, v in parts) or "updated"
        return ("real_strategy", f"Saved real-portfolio strategy target — {label}", 5, 0.0, "")
    if name == "investment_goal_selected":
        goal = _title_text(m.get("goal_title") or m.get("goal") or m.get("objective"))
        return ("goal", f"Set investment goal: {goal}" if goal else "Set an investment goal", 10, 0.0, goal)
    if name == "risk_profile_changed":
        prof = str(m.get("risk_profile") or m.get("objective") or "").replace("_", " ").title()
        return ("strategy", f"Changed investment strategy — {prof}" if prof else "Changed investment strategy", 11, 0.0, prof)
    if name == "portfolio_created":
        what = alloc or (f"{m.get('holdings_count')} holdings" if m.get("holdings_count") else "")
        return ("planning_created", f"Built a planning portfolio — {what}" if what else "Built a planning portfolio", 12, 0.0, what)
    if name == "holdings_updated":
        if not m.get("portfolio_kind"):
            # Older app versions logged every editor change; keep one per day (deduped below).
            return ("planning_updated_legacy", "Updated the planning portfolio", 13, 0.0, "")
        removed = [str(t) for t in (m.get("removed") or [])]
        tail = f" (removed {', '.join(removed)})" if removed else ""
        return ("planning_updated", f"Updated planning portfolio — {alloc or 'new allocation'}{tail}", 13, 0.0, alloc)
    analyses = {
        "portfolio_health_checked": ("health", "Completed a portfolio health evaluation"),
        "portfolio_check": ("health", "Completed a portfolio health evaluation"),
        "risk_analysis_completed": ("risk", "Completed a portfolio risk analysis"),
        "optimizer_run": ("optimizer", "Ran a portfolio optimization"),
        "frontier_viewed": ("frontier", "Built an efficient frontier"),
        "macro_environment_applied": ("macro", "Ran a forward-looking macro analysis"),
        "rebalance_reviewed": ("rebalance", "Reviewed rebalance guidance"),
        "allocation_reviewed": ("rebalance", "Reviewed allocation drift"),
    }
    if name in analyses:
        group, label = analyses[name]
        if name in ("portfolio_health_checked", "portfolio_check") and m.get("review_type"):
            score = m.get("score")
            label += f" — {m.get('review_type')}" + (f" ({float(score):.0f})" if isinstance(score, (int, float)) else "")
        return (group, label, 20, 0.0, "")
    if name == "scenario_run":
        kind = str(m.get("scenario_type") or "Monte Carlo")
        label = "Ran a Monte Carlo simulation" if kind == "Monte Carlo" else f"Ran {kind}"
        return ("scenario", label, 21, 0.0, "")
    if name == "analytical_question":
        return ("question", "Asked an investment question", 30, 0.0, "")
    return None


def _baseball(event: dict[str, Any]) -> Classified | None:
    name = str(event.get("event") or "")
    m = _m(event)
    league = _title_text(m.get("league_name") or m.get("league_label") or m.get("league") or "", 40)
    simple = {
        "shared_league_created": ("league_created", f"Created shared league{' — ' + league if league else ''}", 1),
        "team_claimed": ("league_joined", f"Joined a shared league{' — ' + league if league else ''}", 2),
        "live_draft_created": ("draft_started", "Started a live fantasy draft", 3),
        "completed_live_draft": ("draft_completed", "Completed a live draft", 4),
        "live_draft_pick": ("draft_pick", "Made a live draft selection", 5),
        "trade_accepted": ("trade_done", "Completed a trade", 6),
        "trade_offer_sent": ("trade_offer", "Sent a trade offer", 7),
        "waiver_transaction": ("roster_move", "Made a roster move", 8),
        "lineup_saved": ("lineup", "Saved a lineup", 9),
        "lineup_locked": ("lineup_locked", "Locked a lineup", 10),
        "draft_analysis_created": ("draft_analysis", "Completed a draft analysis", 11),
        "saved_draft_archived": ("draft_saved", "Saved a draft to the library", 12),
    }
    if name in simple:
        g, label, order = simple[name]
        return (g, label, order, 0.0, "")
    if name in (
        "player_comparison", "projection_report", "historical_analysis", "hof_case_analysis",
        "trade_analysis", "sleeper_research", "breakout_analysis", "draft_prep", "roster_build",
    ):
        return ("analysis", "Completed a player or roster analysis", 20, 0.0, "")
    return None


def _music(event: dict[str, Any]) -> Classified | None:
    name = str(event.get("event") or "")
    m = _m(event)
    song = _title_text(m.get("song") or m.get("export_name") or "", 40)
    if name == "composition_saved":
        updated = str(m.get("composition_milestone") or "") == "updated"
        return ("composition_updated" if updated else "composition_saved",
                ("Updated original composition" if updated else "Saved original composition") + (f" — {song}" if song else ""), 1, 0.0, song)
    if name == "multitrack_export_saved":
        return ("multitrack", "Saved a multitrack recording" + (f" — {song}" if song else ""), 2, 0.0, song)
    if name == "practice_log_saved":
        minutes = float(m.get("minutes") or 0)
        label = "Completed a practice session" + (f" — {song}" if song and song != "Practice session" else "")
        if minutes:
            label += f" ({minutes:.0f} min)"
        return ("practice", label, 3, minutes, "")
    if name == "recording_reviewed":
        return ("coaching_review", "Completed an AI coaching review" + (f" — {song}" if song else ""), 4, 0.0, song)
    if name in ("audio_uploaded", "video_uploaded"):
        return ("upload", "Uploaded a recording for AI coaching", 5, 0.0, "")
    if name == "song_coaching_used":
        return ("song_coaching", "Completed a Song-Aware Coaching session" + (f" — {song}" if song else ""), 6, 0.0, song)
    if name in ("verified_chart_saved", "lyrics_saved"):
        what = "chart" if name == "verified_chart_saved" else "lyrics"
        return ("verified_edit", f"Saved verified {what}" + (f" — {song}" if song else ""), 7, 0.0, song)
    return None


def _applied_intelligence(event: dict[str, Any]) -> Classified | None:
    name = str(event.get("event") or "")
    if name == "problem_solved":
        return ("problem", "Saved a solved problem", 1, 0.0, "")
    if name == "analytical_question":
        return ("question", "Asked an analytical question", 2, 0.0, "")
    return None


def _future_lens(event: dict[str, Any]) -> Classified | None:
    if str(event.get("event") or "") == "simulation_completed":
        return ("simulation", "Ran a future-of-work simulation", 1, 0.0, "")
    return None


_CLASSIFIERS: dict[str, Callable[[dict[str, Any]], Classified | None]] = {
    "investment": _investment,
    "baseball": _baseball,
    "music": _music,
    "applied_intelligence": _applied_intelligence,
    "future_lens": _future_lens,
}

# How a group with several items reads. {n}=count, {amount}=sum, {details}=distinct details.
_PLURAL: dict[tuple[str, str], str] = {
    ("investment", "real_deposit"): "Added {amount} to your real portfolio ({n} deposits)",
    ("investment", "real_withdrawal"): "Withdrew {amount} from your real portfolio ({n} withdrawals)",
    ("investment", "real_buy"): "Recorded {n} real purchases ({details})",
    ("investment", "real_sell"): "Recorded {n} real sales ({details})",
    ("investment", "real_contribution"): "Recorded {n} contributions ({amount})",
    ("investment", "real_removed"): "Corrected the real portfolio ledger ({n} transactions removed)",
    ("investment", "real_strategy"): "Updated the real-portfolio strategy target ({n} times)",
    ("investment", "goal"): "Updated investment goal ({n} times) — now {last_detail}",
    ("investment", "strategy"): "Changed investment strategy ({n} times) — now {last_detail}",
    ("investment", "planning_created"): "Built {n} planning portfolios",
    ("investment", "planning_updated"): "Updated planning portfolio {n} times — now {last_detail}",
    ("investment", "planning_updated_legacy"): "Updated the planning portfolio",
    ("investment", "health"): "Completed {n} portfolio health evaluations",
    ("investment", "risk"): "Completed {n} portfolio risk analyses",
    ("investment", "optimizer"): "Ran {n} portfolio optimizations",
    ("investment", "frontier"): "Built {n} efficient frontiers",
    ("investment", "macro"): "Ran {n} forward-looking macro analyses",
    ("investment", "rebalance"): "Reviewed rebalance guidance ({n} times)",
    ("investment", "scenario"): "Ran {n} scenario simulations",
    ("investment", "question"): "Asked {n} investment questions",
    ("baseball", "league_created"): "Created {n} shared leagues",
    ("baseball", "league_joined"): "Joined {n} shared leagues",
    ("baseball", "draft_started"): "Started {n} live drafts",
    ("baseball", "draft_completed"): "Completed {n} live drafts",
    ("baseball", "draft_pick"): "Made {n} live draft selections",
    ("baseball", "trade_done"): "Completed {n} trades",
    ("baseball", "trade_offer"): "Sent {n} trade offers",
    ("baseball", "roster_move"): "Made {n} roster moves",
    ("baseball", "lineup"): "Saved {n} lineups",
    ("baseball", "lineup_locked"): "Locked {n} lineups",
    ("baseball", "draft_analysis"): "Completed {n} draft analyses",
    ("baseball", "draft_saved"): "Saved {n} drafts to the library",
    ("baseball", "analysis"): "Completed {n} player and roster analyses",
    ("music", "composition_saved"): "Saved {n} original compositions",
    ("music", "composition_updated"): "Updated original compositions ({n} saves)",
    ("music", "multitrack"): "Saved {n} multitrack recordings",
    ("music", "practice"): "Completed {n} practice sessions ({amount_min})",
    ("music", "coaching_review"): "Completed {n} AI coaching reviews",
    ("music", "upload"): "Uploaded {n} recordings for AI coaching",
    ("music", "song_coaching"): "Completed {n} Song-Aware Coaching sessions",
    ("music", "verified_edit"): "Saved {n} verified chart and lyrics edits",
    ("applied_intelligence", "problem"): "Saved {n} solved problems",
    ("applied_intelligence", "question"): "Asked {n} analytical questions",
    ("future_lens", "simulation"): "Ran {n} future-of-work simulations",
}


def classify(event: dict[str, Any]) -> Accomplishment | None:
    app = str(event.get("app") or "").strip()
    fn = _CLASSIFIERS.get(app)
    if fn is None:
        return None
    when = _parse(event.get("timestamp"))
    if when is None:
        return None
    try:
        hit = fn(event)
    except Exception:
        return None
    if hit is None:
        return None
    group, label, order, amount, detail = hit
    key = _identity(event)
    if group == "planning_updated_legacy":
        key = f"{app}|legacy_holdings|{_local(when).date().isoformat()}"
    return Accomplishment(app=app, group=group, label=label, when=when, key=key, order=order, amount=amount, detail=detail)


def accomplishments(events: Iterable[dict[str, Any]], *, start: date, end: date | None = None) -> list[Accomplishment]:
    """De-duplicated accomplishments whose local date is in [start, end]."""
    first: dict[str, Accomplishment] = {}
    for event in events:
        acc = classify(event)
        if acc is None:
            continue
        prev = first.get(acc.key)
        if prev is None or acc.when < prev.when:
            first[acc.key] = acc  # an action happened when it was first recorded
    out = []
    for acc in first.values():
        d = _local(acc.when).date()
        if d < start or (end is not None and d > end):
            continue
        out.append(acc)
    return sorted(out, key=lambda a: a.when)


def _combine(app: str, group: str, items: list[Accomplishment]) -> str:
    if len(items) == 1:
        return items[0].label
    template = _PLURAL.get((app, group))
    if not template:
        return f"{items[-1].label} (×{len(items)})"
    details = list(OrderedDict.fromkeys(i.detail for i in items if i.detail))
    amount = sum(i.amount for i in items)
    return template.format(
        n=len(items),
        amount=_money(amount),
        amount_min=f"{amount:.0f} min" if amount else "time not logged",
        details=", ".join(details) or "various",
        last_detail=items[-1].detail or items[-1].label,
    )


def sections(accs: list[Accomplishment]) -> list[AppSection]:
    """Group by app (suite order), combine repeated groups into one line each."""
    by_app: dict[str, dict[str, list[Accomplishment]]] = {}
    for a in accs:
        by_app.setdefault(a.app, OrderedDict()).setdefault(a.group, []).append(a)
    out: list[AppSection] = []
    for app in [a for a in APP_ORDER if a in by_app] + [a for a in by_app if a not in APP_ORDER]:
        groups = by_app[app]
        ordered = sorted(groups.items(), key=lambda kv: (min(i.order for i in kv[1]), kv[1][0].when))
        sec = AppSection(app=app, title=APP_LABELS.get(app, app.replace("_", " ").title()))
        for group, items in ordered:
            sec.lines.append(_combine(app, group, items))
            sec.count += len(items)
        out.append(sec)
    return out


def today_sections(events: Iterable[dict[str, Any]], *, now: datetime | None = None) -> list[AppSection]:
    today = local_today(now)
    return sections(accomplishments(events, start=today, end=today))


def week_sections(events: Iterable[dict[str, Any]], *, now: datetime | None = None) -> list[AppSection]:
    return sections(accomplishments(events, start=local_week_start(now), end=local_today(now)))


# ── App Directory: long-term Investment context ───────────────────────────────


def investment_directory_lines(events: Iterable[dict[str, Any]]) -> list[str]:
    """Latest real-portfolio and planning-portfolio facts (never mixed)."""
    real: dict[str, Any] | None = None
    planning: dict[str, Any] | None = None
    goal = ""
    for event in sorted((e for e in events if e.get("app") == "investment"), key=lambda e: str(e.get("timestamp") or "")):
        m = _m(event)
        kind = str(m.get("portfolio_kind") or "")
        if kind == "real" and "real_transaction_count" in m:
            real = m
        elif kind == "planning" and m.get("allocation_label"):
            planning = m
        g = str(m.get("goal_title") or m.get("goal") or "").strip()
        if g:
            goal = g
    lines: list[str] = []
    if real is not None:
        n = int(real.get("real_transaction_count") or 0)
        held = ", ".join(real.get("real_tickers") or []) or "cash only"
        line = f"Real portfolio: {held}"
        if real.get("real_cash_balance") is not None:
            line += f" · {_money(real.get('real_cash_balance'))} cash"
        line += f" · {n} transaction{'s' if n != 1 else ''}"
        lines.append(line)
    if planning is not None:
        lines.append(f"Planning portfolio: {planning.get('allocation_label')}")
    if goal:
        lines.append(f"Goal: {goal}")
    return lines
