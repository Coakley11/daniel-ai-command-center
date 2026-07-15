"""
Fantasy lifecycle events for Command Center Continue / Activity / App Directory.

Continue  = actionable, resumable tasks only (lifecycle-superseded).
Activity  = chronological history of what the user did.
App Directory = short identity chips for the app (not status, not resume).
"""

from __future__ import annotations

from typing import Any

# Events emitted by Baseball for fantasy transaction workflows.
FANTASY_TRADE_EVENTS: frozenset[str] = frozenset(
    {
        "trade_offer_sent",
        "trade_offer_received",
        "trade_accepted",
        "trade_declined",
        "trade_canceled",
        "trade_expired",
    }
)

FANTASY_WAIVER_EVENTS: frozenset[str] = frozenset(
    {
        "waiver_transaction",
        "waiver_add",
        "waiver_drop",
        "waiver_recommendation",
    }
)

FANTASY_LEAGUE_EVENTS: frozenset[str] = frozenset(
    {
        "shared_league_created",
        "shared_league_invite",
        "shared_league_invite_declined",
        "team_claimed",
        "active_draft_changed",
        "draft_saved",
        "saved_draft_archived",
        "saved_draft_activated",
    }
)

FANTASY_LINEUP_EVENTS: frozenset[str] = frozenset(
    {
        "lineup_reminder",
        "lineup_saved",
        "lineup_locked",
        "lineup_review",
    }
)

FANTASY_LIFECYCLE_EVENT_TYPES: frozenset[str] = frozenset(
    FANTASY_TRADE_EVENTS
    | FANTASY_WAIVER_EVENTS
    | FANTASY_LEAGUE_EVENTS
    | FANTASY_LINEUP_EVENTS
)

TRADE_TERMINAL_EVENTS: frozenset[str] = frozenset(
    {
        "trade_accepted",
        "trade_declined",
        "trade_canceled",
        "trade_expired",
    }
)

TRADE_OFFER_EVENTS: frozenset[str] = frozenset(
    {
        "trade_offer_sent",
        "trade_offer_received",
    }
)

# Completed / resolved work stays in Activity only — not Continue.
ACTIVITY_ONLY_EVENTS: frozenset[str] = frozenset(
    {
        "waiver_transaction",
        "waiver_add",
        "waiver_drop",
        "shared_league_invite_declined",
    }
)

# Pending / actionable Continue events (after lifecycle filters).
CONTINUE_ELIGIBLE_EVENTS: frozenset[str] = frozenset(
    {
        "trade_offer_sent",
        "trade_offer_received",
        "trade_accepted",
        "trade_declined",
        "trade_canceled",
        "trade_expired",
        "waiver_recommendation",
        "shared_league_created",
        "shared_league_invite",
        "team_claimed",
        "active_draft_changed",
        "saved_draft_activated",
        "draft_saved",
        "saved_draft_archived",
        "lineup_reminder",
        "lineup_saved",
        "lineup_locked",
        "lineup_review",
    }
)

INVITE_RESOLVED_EVENTS: frozenset[str] = frozenset(
    {
        "team_claimed",
        "shared_league_invite_declined",
    }
)

WAIVER_COMPLETED_EVENTS: frozenset[str] = frozenset(
    {
        "waiver_transaction",
        "waiver_add",
        "waiver_drop",
    }
)

LINEUP_COMPLETED_EVENTS: frozenset[str] = frozenset(
    {
        "lineup_saved",
        "lineup_locked",
    }
)


def baseball_directory_chip(event_type: str, metrics: dict[str, Any] | None = None) -> str:
    """Short App Directory identity chip — never a status/history sentence."""
    et = str(event_type or "").strip()
    m = metrics if isinstance(metrics, dict) else {}
    league = str(m.get("league_name") or m.get("league") or "").strip()

    if et in {"completed_live_draft", "live_draft_created", "live_draft_pick"}:
        return f"{league} Live Draft" if league else "Live Draft"
    if et in {"draft_analysis_created", "draft_prep", "draft_saved", "saved_draft_archived"}:
        return "Draft Simulations"
    if et in FANTASY_TRADE_EVENTS or et in {"trade_eval", "trade_analysis"}:
        return "Fantasy Trade Management"
    if et in FANTASY_WAIVER_EVENTS:
        return "Waiver Wire"
    if et in FANTASY_LINEUP_EVENTS:
        return "Fantasy Lineup"
    if et in {
        "shared_league_created",
        "shared_league_invite",
        "shared_league_invite_declined",
        "team_claimed",
        "active_draft_changed",
        "saved_draft_activated",
    }:
        return f"{league} Shared League" if league else "Shared Leagues"
    if et in {"hof_case_analysis"}:
        return "Hall of Fame Case Studies"
    if et == "breakout_analysis":
        return "Breakout Research"
    return ""


def trade_swap_label(metrics: dict[str, Any] | None) -> str:
    m = metrics if isinstance(metrics, dict) else {}
    trade = str(m.get("trade") or "").strip()
    if trade:
        return trade
    give = m.get("give") or m.get("proposer_gives") or []
    get = m.get("get") or m.get("proposer_receives") or []
    if isinstance(give, list) and isinstance(get, list) and give and get:
        g = " + ".join(str(x).strip() for x in give[:2] if str(x).strip())
        r = " + ".join(str(x).strip() for x in get[:2] if str(x).strip())
        if g and r:
            return f"{g} ⇄ {r}"
    return ""


def metrics_of(event: dict[str, Any]) -> dict[str, Any]:
    raw = event.get("metrics")
    return raw if isinstance(raw, dict) else {}


def proposal_id_from_event(event: dict[str, Any]) -> str:
    return str(metrics_of(event).get("proposal_id") or "").strip()


def invite_id_from_event(event: dict[str, Any]) -> str:
    return str(metrics_of(event).get("invite_id") or "").strip()


def waiver_league_key(metrics: dict[str, Any] | None) -> str:
    m = metrics if isinstance(metrics, dict) else {}
    return str(m.get("league_id") or m.get("league_context_id") or "").strip()


def lineup_week_key(metrics: dict[str, Any] | None) -> str:
    m = metrics if isinstance(metrics, dict) else {}
    league_id = str(m.get("league_id") or m.get("league_context_id") or "").strip()
    week = m.get("week")
    if week in (None, ""):
        return ""
    return f"{league_id}|w{week}" if league_id else f"w{week}"


def fantasy_activity_message(event_type: str, metrics: dict[str, Any] | None = None, *, summary: str = "") -> str | None:
    """Detailed Activity feed line for fantasy lifecycle events."""
    et = str(event_type or "").strip()
    m = metrics if isinstance(metrics, dict) else {}
    league = str(m.get("league_name") or m.get("league") or "").strip()
    from_team = str(m.get("from_team") or m.get("proposer_team") or "").strip()
    to_team = str(m.get("to_team") or m.get("recipient_team") or "").strip()
    trade = trade_swap_label(m)
    week = m.get("week")
    week_label = f"Week {week}" if week not in (None, "") else ""

    if et == "trade_offer_received":
        base = f"Received trade offer from {from_team}" if from_team else "Received a trade offer"
        return f"{base}: {trade}" if trade else base
    if et == "trade_offer_sent":
        base = f"Sent trade offer to {to_team}" if to_team else "Sent a trade offer"
        return f"{base}: {trade}" if trade else base
    if et == "trade_accepted":
        base = "Accepted trade" if not (from_team and to_team) else f"Accepted trade ({from_team} ⇄ {to_team})"
        return f"{base}: {trade}" if trade else "Trade completed"
    if et == "trade_declined":
        return f"Declined trade offer from {from_team}" if from_team else "Declined a trade offer"
    if et == "trade_canceled":
        return f"Canceled trade offer to {to_team}" if to_team else "Canceled a trade offer"
    if et == "trade_expired":
        return f"Trade offer expired ({from_team} → {to_team})" if from_team or to_team else "Trade offer expired"

    if et == "waiver_recommendation":
        player = str(m.get("player") or m.get("add_player") or "").strip()
        return f"Reviewed Waiver Wire recommendation ({player})" if player else "Reviewed Waiver Wire recommendations"
    if et == "waiver_transaction":
        added = m.get("added") or m.get("added_players") or []
        dropped = m.get("dropped") or m.get("dropped_players") or []
        add_s = ", ".join(str(x).strip() for x in (added if isinstance(added, list) else [added]) if str(x).strip())
        drop_s = ", ".join(str(x).strip() for x in (dropped if isinstance(dropped, list) else [dropped]) if str(x).strip())
        if add_s and drop_s:
            return f"Dropped {drop_s} and added {add_s}"
        if add_s:
            return f"Added {add_s} from Waiver Wire"
        if drop_s:
            return f"Dropped {drop_s}"
        return str(summary or "").strip() or "Completed a waiver transaction"
    if et == "waiver_add":
        player = str(m.get("player") or m.get("add_player") or "").strip()
        return f"Added {player} from Waiver Wire" if player else "Added a waiver player"
    if et == "waiver_drop":
        player = str(m.get("player") or m.get("drop_player") or "").strip()
        return f"Dropped {player}" if player else "Dropped a player"

    if et == "shared_league_created":
        return f"Created {league} Shared League" if league else "Created a Shared League"
    if et == "shared_league_invite":
        if m.get("as_invitee"):
            return f"Invited to {league}" if league else "Received a Shared League invitation"
        invitee = str(m.get("invitee") or m.get("invitee_workspace_id") or "").strip()
        if invitee and league:
            return f"Invited {invitee} to {league}"
        return f"Sent invite for {league}" if league else "Sent a Shared League invitation"
    if et == "shared_league_invite_declined":
        return f"Declined invite to {league}" if league else "Declined a Shared League invitation"
    if et == "team_claimed":
        team = str(m.get("team") or m.get("claimed_team") or "").strip()
        if team and league:
            return f"Claimed {team} in {league}"
        if team:
            return f"Claimed {team}"
        return "Claimed a Shared League team"
    if et == "active_draft_changed" or et == "saved_draft_activated":
        return f"Active League set to {league}" if league else "Changed Active League"
    if et == "draft_saved" or et == "saved_draft_archived":
        return f"Saved draft: {league}" if league else "Saved a draft"

    if et == "lineup_locked":
        return f"Locked {week_label} lineup".strip() if week_label else "Locked weekly lineup"
    if et in {"lineup_saved", "lineup_review"}:
        return f"Saved {week_label} lineup".strip() if week_label else "Saved weekly lineup"
    if et == "lineup_reminder":
        return f"Finish {week_label} lineup".strip() if week_label else "Finish weekly lineup"

    return None


def fantasy_continue_copy(event_type: str, metrics: dict[str, Any] | None = None) -> tuple[str, str, int]:
    """Return (title, subtitle, priority) for Continue cards."""
    et = str(event_type or "").strip()
    m = metrics if isinstance(metrics, dict) else {}
    league = str(m.get("league_name") or m.get("league") or "").strip()
    from_team = str(m.get("from_team") or m.get("proposer_team") or "").strip()
    to_team = str(m.get("to_team") or m.get("recipient_team") or "").strip()
    team = str(m.get("my_team") or m.get("team") or m.get("claimed_team") or "").strip()
    trade = trade_swap_label(m)
    week = m.get("week")
    week_label = f"Week {week}" if week not in (None, "") else "Weekly"
    league_bit = league or "league"
    team_bit = f" · {team}" if team else ""

    if et == "trade_offer_received":
        title = f"Trade offer from {from_team}" if from_team else "New trade offer"
        return title, f"{league_bit}{team_bit}" if league or team else (trade or "Trade Center"), 68
    if et == "trade_offer_sent":
        title = f"Trade offer to {to_team}" if to_team else "Outgoing trade offer"
        return title, trade or f"{league_bit}{team_bit}" or "Trade Center", 64
    if et == "trade_accepted":
        return "Trade completed", trade or f"{from_team} ⇄ {to_team}".strip(" ⇄") or "Trade Center", 67
    if et == "trade_declined":
        return "Trade offer declined", from_team or "Trade Center", 50
    if et == "trade_canceled":
        return "Trade offer canceled", to_team or "Trade Center", 48
    if et == "trade_expired":
        return "Trade offer expired", trade or "Trade Center", 48

    if et == "waiver_recommendation":
        player = str(m.get("player") or m.get("add_player") or "").strip()
        title = f"Waiver pickup: {player}" if player else "Review Waiver Wire"
        return title, f"{league_bit}{team_bit}", 66

    if et == "shared_league_invite":
        return f"Invited to {league}" if league else "Shared League invitation", "Claim a team", 70
    if et == "shared_league_created":
        return f"{league} created successfully" if league else "Shared League created", "Saved Draft Library", 60
    if et == "team_claimed":
        title = f"Claimed {team}" if team else "Team claimed"
        return title, league or "Saved Draft Library", 58
    if et in {"active_draft_changed", "saved_draft_activated"}:
        return f"Active League: {league}" if league else "Active League changed", "Saved Draft Library", 57
    if et in {"draft_saved", "saved_draft_archived"}:
        return f"Saved draft: {league}" if league else "Draft saved", "Saved Draft Library", 52

    if et == "lineup_locked":
        return f"{week_label} lineup locked", f"{league_bit}{team_bit}", 65
    if et in {"lineup_saved"}:
        return f"{week_label} lineup saved", f"{league_bit}{team_bit}", 55
    if et in {"lineup_reminder", "lineup_review"}:
        return f"Finish {week_label} lineup", f"{league_bit}{team_bit}", 54

    return et.replace("_", " ").title(), "Baseball Analytics", 45


def fantasy_resume_key(event_type: str, metrics: dict[str, Any] | None = None) -> str:
    et = str(event_type or "").strip()
    m = metrics if isinstance(metrics, dict) else {}
    proposal_id = str(m.get("proposal_id") or "").strip()
    league_id = str(m.get("league_id") or m.get("league_context_id") or "").strip()
    invite_id = str(m.get("invite_id") or "").strip()
    draft_id = str(m.get("draft_id") or "").strip()
    week = m.get("week")

    if et in FANTASY_TRADE_EVENTS and proposal_id:
        return f"bb:trade_center:{proposal_id}"
    if et in FANTASY_TRADE_EVENTS:
        return "bb:trade_center"
    if et == "waiver_recommendation":
        return f"bb:waiver:{league_id}" if league_id else "bb:waiver"
    if et == "shared_league_invite" and invite_id:
        return f"bb:invite:{invite_id}"
    if et in FANTASY_LEAGUE_EVENTS:
        if draft_id:
            return f"bb:saved_draft:{draft_id}"
        if league_id:
            return f"bb:library:{league_id}"
        return "bb:library"
    if et in FANTASY_LINEUP_EVENTS:
        if week not in (None, "") and league_id:
            return f"bb:lineup:{league_id}:w{week}"
        if week not in (None, ""):
            return f"bb:lineup:w{week}"
        return "bb:lineup"
    return ""


def fantasy_resume_page(event_type: str) -> str:
    et = str(event_type or "").strip()
    if et in FANTASY_TRADE_EVENTS:
        return "Trade Center"
    if et in {"waiver_recommendation"} | FANTASY_WAIVER_EVENTS:
        return "Waiver Wire / Add-Drop Center"
    if et in FANTASY_LEAGUE_EVENTS:
        return "Saved Draft Library"
    if et in FANTASY_LINEUP_EVENTS:
        return "Fantasy Lineup Assistant"
    return ""


def fantasy_continue_merge_key(event_type: str, metrics: dict[str, Any] | None = None) -> str:
    """One Continuity slot per lifecycle entity (proposal / invite / week / league waiver)."""
    rk = fantasy_resume_key(event_type, metrics)
    return rk or f"fantasy:{event_type}"


def collect_fantasy_lifecycle_sets(events: list[dict[str, Any]]) -> dict[str, set[str]]:
    """Pre-scan history for Continue supersede filters."""
    terminal_trades: set[str] = set()
    resolved_invites: set[str] = set()
    completed_waivers: set[str] = set()
    completed_lineups: set[str] = set()
    for event in events:
        if str(event.get("app") or "").strip() != "baseball":
            continue
        et = str(event.get("event") or "").strip()
        m = metrics_of(event)
        if et in TRADE_TERMINAL_EVENTS:
            pid = str(m.get("proposal_id") or "").strip()
            if pid:
                terminal_trades.add(pid)
        if et in INVITE_RESOLVED_EVENTS:
            iid = str(m.get("invite_id") or "").strip()
            if iid:
                resolved_invites.add(iid)
        if et in WAIVER_COMPLETED_EVENTS:
            lid = waiver_league_key(m)
            if lid:
                completed_waivers.add(lid)
        if et in LINEUP_COMPLETED_EVENTS:
            lk = lineup_week_key(m)
            if lk:
                completed_lineups.add(lk)
    return {
        "terminal_trades": terminal_trades,
        "resolved_invites": resolved_invites,
        "completed_waivers": completed_waivers,
        "completed_lineups": completed_lineups,
    }


def is_fantasy_continue_eligible(
    event_type: str,
    metrics: dict[str, Any] | None = None,
    *,
    terminal_trades: set[str] | None = None,
    resolved_invites: set[str] | None = None,
    completed_waivers: set[str] | None = None,
    completed_lineups: set[str] | None = None,
) -> bool:
    """Lifecycle gates for Continue — Activity still records the raw event."""
    et = str(event_type or "").strip()
    m = metrics if isinstance(metrics, dict) else {}
    if et in ACTIVITY_ONLY_EVENTS:
        return False
    if et not in CONTINUE_ELIGIBLE_EVENTS:
        return False

    terminal_trades = terminal_trades or set()
    resolved_invites = resolved_invites or set()
    completed_waivers = completed_waivers or set()
    completed_lineups = completed_lineups or set()

    if et in TRADE_OFFER_EVENTS:
        pid = str(m.get("proposal_id") or "").strip()
        if pid and pid in terminal_trades:
            return False

    if et == "shared_league_invite":
        iid = str(m.get("invite_id") or "").strip()
        if iid and iid in resolved_invites:
            return False
        # Commissioner "sent invite" is Activity; Continue is for invitees.
        if not m.get("as_invitee", True):
            return False

    if et == "waiver_recommendation":
        lid = waiver_league_key(m)
        if lid and lid in completed_waivers:
            return False

    if et in {"lineup_reminder", "lineup_review"}:
        lk = lineup_week_key(m)
        if lk and lk in completed_lineups:
            return False

    return True


def should_suppress_trade_offer_continue(
    event: dict[str, Any],
    *,
    terminal_proposal_ids: set[str],
) -> bool:
    et = str(event.get("event") or "").strip()
    if et not in TRADE_OFFER_EVENTS:
        return False
    pid = proposal_id_from_event(event)
    return bool(pid and pid in terminal_proposal_ids)
