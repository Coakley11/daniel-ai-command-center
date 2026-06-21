# Feature Backlog — Daniel AI Command Center

**Last updated:** 2026-06-21

Ideas not yet scheduled. Active work: [app_tasks.md](./app_tasks.md).

---

# Project Description

Queued enhancements for the suite homepage and shared infrastructure — not sibling app feature work (track those in each app's `cursor-prompts/`).

---

# Current Priorities

*Active: Finish Account / Workspace phase before AMI Importer. See [plan](./plans/2026-06-21-account-workspace-phase-completion.md).*

---

# Next Features

### Account Settings Sprint B (P1b — **code shipped; deploy sign-off pending**)

- [x] Sync `suite_account_settings.py` + `suite_app_shell.py` to sibling repos
- [x] Global workspace badge + account expander in app sidebars (AMI, Investment, NBA, Music, FutureLens, CC)
- [x] Command Center link preserves `?suite_workspace=`
- [ ] Baseball shell when entry file exists; manual A1–A4 acceptance

### Real Accounts foundation (P1c — **scaffolding shipped; enable on prod pending**)

- [x] `suite_auth.py` — signup, login, logout, reset (Supabase Auth)
- [x] `SUITE_AUTH_ENABLED` feature flag (default off)
- [x] Auth gate in app entrypoints via `apply_suite_auth_gate()`
- [ ] Enable on deployment; C1–C5 manual acceptance

### AMI Real Problem Importer (**blocked until Sprint D gate**)

**V1:** Kalshi-style prediction-market import → classify as **Prediction Market / Betting EV** → route to **Betting / Expected Value** → prefill fields → user adjusts → AMI explains math (decision analysis, not gambling advice).

**Import channels:** paste/CSV/manual (V1); screenshot + URL (architecture-ready, later).

**Phase 0:** `decision_templates`, `decision_router`, `decision_math`, `decision_registry` — no OCR/URL UI.

**Long-term routing registry:** car/lease, consumer purchase, job offers, investments, business C/B, trade/risk-reward, prediction markets, treatment/risk-benefit.

### Phase 2 — Real accounts (**moved to P1c active track** — before Importer, not after)

- Supabase Auth email/password (Google OAuth optional fast-follow)
- User-specific cloud storage tied to auth user
- Roles: Daniel admin/developer, Ariel standard user
- Workspace profiles bound to authenticated users

### Phase 3 — Simple Live Draft Room v1 (**do not start yet** — after Real Accounts stable)

- Room code; users join a room
- Shared draft board, picks, rosters, team names, **shared draft clock**
- Picks visible to all participants (polling/simple refresh OK for v1)

### Phase 4 — Advanced Live Draft Room

**Shared room state:** room, board, picks, rosters, clock

**Private user state (never shared — users must not see another team's strategy):** queues, notes, watchlists, AMI recommendations, draft preferences

**Advanced:** realtime updates, permissions, invite links, reconnect, simultaneous-pick conflict prevention, team-specific intelligence

### AMI Baseball Draft Intelligence (P1 — after P0; not parallel with workspace rollout)

- Dev Mode confirm → verify hydration → fix top-12 EV representative pool → remaining packaging fixes
- Restatement layer — stop defaulting unknown Draft Assistant intent to compare

### Suite port (Sprint 7 remainder)

- Music Phase C slice 2 — `practice_state.py`
- NBA, Investment, Applied Intelligence Phase A audits → B/C/D

### Near-term homepage

- Activity feed: user-toggle "show all events" vs executive summary only
- Continue card thumbnails or app-color badges by project type
- Export weekly summary as markdown/email draft
- Pin favorite app to top of App Directory
- Command Center sidebar mini-nav (jump to section anchors)

### Nice-to-have

- Sparkline of events per day in Weekly Summary
- Search box over Recent Activity
- "Last synced" timestamp when reading from Supabase
- Integrate `scripts/probe_public_urls.py` results into admin panel automatically
- Branding sync status indicator (last `sync_suite_branding.py` run)

---

# Long-Term Vision

- **Unified notifications** — browser/email when milestone events fire
- **Public share links** — read-only activity week for coach/teacher
- **Graph view** — nodes = apps, edges = correlated activity sessions
- **Embedded mini-widgets** — iframe or API snippets for single-app status on external sites
- **CLI / SDK homepage** — `cursor-sdk` agent reads suite state for automation

*Identity/multiplayer sequencing:* [plans/2026-06-19-workspace-profiles-real-accounts-live-draft-room.md](./plans/2026-06-19-workspace-profiles-real-accounts-live-draft-room.md)

---

# Completed Features

*Shipped items live in [app_completed_features.md](./app_completed_features.md).*

---

# Notes

- **Do not start** Real Accounts (Phase 2), Live Draft Room (Phase 3+), or FutureLens AMI expansion until Workspace Profiles v1 is stable across all apps.
- NBA Workspace Profiles v1 validated 2026-06-19. FutureLens implementation complete; user acceptance pass pending.
- Workspace Profiles v1 = primary foundation; not authentication.
- Experimental: LLM-generated coach insights; Supabase realtime subscription instead of poll-on-load
- Do not backlog duplicate features already owned by sibling apps — link out instead

---

## Future enhancements (detail)

| Idea | Value | Complexity |
|------|-------|------------|
| Real accounts (Phase 2) | Foundation for multiplayer + privacy | Medium |
| Simple Live Draft Room v1 | Shared draft with friends/league | Medium |
| Polished Live Draft Room | Production-grade multiplayer draft | High |
| AMI position-representative pool | Fixes draft Q3/Q4/generic fallbacks | Medium |
| LLM weekly narrative | High engagement | Medium (API + prompt) |
| Per-app health badges on directory cards | Quick deploy status | Low |

---

## Experimental ideas

- Voice summary of today's work (TTS)
- Calendar integration (Google) for "lineup day" coach hints
- GitHub commit activity correlated with dev app usage
- A/B test hero copy for onboarding
