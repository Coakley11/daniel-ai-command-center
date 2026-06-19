# Feature Backlog — Daniel AI Command Center

**Last updated:** 2026-06-19

Ideas not yet scheduled. Active work: [app_tasks.md](./app_tasks.md).

---

# Project Description

Queued enhancements for the suite homepage and shared infrastructure — not sibling app feature work (track those in each app's `cursor-prompts/`).

---

# Current Priorities

*Active P0: Workspace Profiles v1 — finish NBA + FutureLens as final major milestone. Do not start Real Accounts or Live Draft Room. P1 AMI draft context stays behind P0.*

---

# Next Features

### Phase 2 — Real accounts (**do not start yet** — after workspace profiles stable)

- Username, email, `user_id`, login/authentication (password and/or Google OAuth)
- User-specific private cloud storage
- Permissions — admin/developer roles (Daniel), standard user roles (Ariel)
- Workspace profiles become real authenticated accounts
- Invite links (later)

### Phase 3 — Simple Live Draft Room v1 (**do not start yet** — after Phase 2)

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

- **Do not start** Real Accounts (Phase 2) or Live Draft Room (Phase 3+) until Workspace Profiles v1 is stable.
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
