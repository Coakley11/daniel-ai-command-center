# Workspace Profiles → Real Accounts → Live Draft Room

**Last updated:** 2026-06-19 (user confirmed priority order)  
**Branch:** `dev`  
**Status:** Phase 1 active — finish workspace isolation before auth or multiplayer draft

**Hard gates (confirmed):** Do **not** start Real Accounts (Phase 2) or Live Draft Room (Phase 3+) until Workspace Profiles v1 is stable across all apps.

---

## Summary

The suite is at **Workspace Profiles v1**, not full real accounts yet. Profile/workspace separation is mostly working for Daniel, Ariel, and Guest/Test-style profiles. Command Center is the profile switcher; each profile gets separate app state (portfolios, drafts, history). Daniel-only developer tools are gated by workspace.

This is the correct foundation for real authentication and future Live Draft Room multiplayer — but it is **not** the same as login/auth.

---

## Current state (Workspace Profiles v1)

### What a workspace profile is

| Aspect | Workspace profile (now) | Real account (later) |
|--------|-------------------------|----------------------|
| Identity | Preset id (`daniel`, `ariel`, `guest`, `test_user`) | `user_id`, email, login |
| Switching | Command Center sidebar selector + `?suite_workspace=` | Authenticated session |
| Storage | `data/workspaces/{workspace_id}/` + scoped cloud keys (`app__ariel`) | Private cloud per authenticated user |
| Permissions | Daniel dev tools only | Roles (admin vs normal user) |
| Security | Practical separation, not auth | Password / OAuth, invites |

### Architecture target (every app)

```
workspace_id → app_id → state
```

No Daniel data should leak into Ariel (or vice versa) for activity, resume, disk state, or cloud `full_session`.

### Shared modules (Command Center repo)

- `suite_workspace.py` — presets, normalization, selector, dev gating, cloud app id scoping
- `suite_user_persistence.py` — workspace-scoped disk paths + cloud restore
- `suite_deep_links.py` / `suite_resume_launch.py` — propagate `suite_workspace` on Continue URLs
- `suite_storage_supabase.py` — workspace-filtered activity and resume reads
- Tests: `test_suite_workspace.py`, `test_workspace_cc_activity.py`

---

## Validation status (2026-06-19)

### Mostly validated / working

- [x] Command Center — profile switcher, workspace badge, scoped activity aggregation
- [x] Investment Portfolio Analyzer
- [x] Baseball Analytics
- [x] Applied Mathematical Intelligence
- [x] Music Practice Coach

### Remaining Phase 1 gaps (final major milestone: NBA + FutureLens)

- [ ] **NBA Companion AI** — full workspace isolation (LGC, Legacy Tracker, team/page state)
- [ ] **FutureLens** — full workspace isolation (career/timeline/sim state + activity)
- [ ] **Command Center** — final activity isolation validation (edge cases across profiles)
- [ ] **Music** — final validation if needed on acceptance passes

Finishing **NBA + FutureLens** is the final major Workspace Profile milestone before Phase 2.

---

## Phase 1 — Finish Workspace Profiles (active)

**Goal:** Every suite app follows `workspace_id → app_id → state` with no cross-profile leaks.

### Tasks

1. NBA Companion AI — audit + wire `init_suite_workspace`, scoped persistence, cloud keys, activity writes
2. FutureLens — same pattern; verify Continue + App Directory under Ariel vs Daniel
3. Command Center — audit activity feed, coach, continue cards for profile bleed
4. Music — re-run phone↔Dell acceptance under non-Daniel profiles if issues surface
5. Sync shared modules to all sibling repos after each change (`scripts/sync_suite_cloud_modules.py`)
6. Document acceptance matrix: Daniel action → Ariel sees empty/different state

### Exit criteria

- Switch Daniel → Ariel in Command Center; open each app — no shared drafts, portfolios, or AMI history
- Activity feed, Continue, and resume URLs only show active workspace events
- Cloud `full_session` uses scoped app ids (`baseball__ariel`, etc.) consistently

---

**Do not start until:** Phase 1 acceptance passes on all six apps + Command Center. **Do not start Real Accounts yet.**

**At migration:** Workspace Profiles become real authenticated accounts — Daniel = admin/developer account; Ariel = normal user account.

---

## P1 — AMI Baseball Draft Intelligence (after Phase 1; behind workspace completion)

**Primary owner:** send/hydration / context packaging — not catcher logic, not player-specific logic, not new AMI reasoning modes.

**Known symptoms:**

- Generic Q3/Q4 recommendations
- Incorrect player pool / wrong available-player context
- Top-12 EV slice not hydrated correctly (position gaps — e.g. zero catchers in sent pool)
- Occasional fallback behavior

**Sequence (P1):**

1. Confirm Baseball AMI context counts in Dev Mode (`?dev=1`)
2. Verify `available_players` hydration (`hydrate_source`, counts, sample positions)
3. Fix top-12 EV → position-representative pool issue
4. Fix remaining AMI draft context packaging problems
5. Secondary: restatement layer unknown intent → compare default

---

## Phase 2 — Real Accounts (after Phase 1 stable)

**Size:** Medium project (larger than workspace profiles; smaller than polished Live Draft Room)

**Scope:**

- Username, email, `user_id`
- Login / authentication (password and/or Google OAuth)
- Private cloud storage per authenticated user
- Permissions and roles — admin/developer (Daniel), standard user (Ariel)
- Invite links (later)

**Design note:** Workspace profile architecture (`workspace_id` scoping) maps to authenticated users — preset picker replaced by login session.

**Do not start until:** Phase 1 complete. **Do not start Real Accounts yet.**

---

## Phase 3 — Simple Live Draft Room v1 (after Phase 2 stable)

**Size:** Medium project

**Features (minimal multiplayer):**

- Room code; users join a room
- Each user/team has a profile in the room
- Shared draft board, picks, rosters, team names
- **Shared draft clock**
- Picks update for everyone (polling or simple refresh acceptable for v1)

**Prerequisite:** Phase 2 (Real Accounts) stable. **Do not start Live Draft Room yet.**

---

## Phase 4 — Advanced Live Draft Room (after Simple v1)

**Size:** Large project

**Features:**

- Real-time updates (WebSocket or Supabase realtime)
- Private queues, watchlists, notes per user
- Private AMI recommendations (not visible to other drafters)
- Permissions, invite links
- Reconnect handling
- Conflict prevention when two users pick simultaneously
- Team-specific intelligence / AMI recommendations

---

## State model — shared vs private (Live Draft Room)

### Shared room state

- `room_id`
- Draft board
- Picks (canonical order)
- Clock
- Rosters (per team, visible)
- Team names

### Private user state (never visible to other room members / teams)

- Queue
- Watchlist
- Notes
- AMI questions and answers
- Private recommendations
- Draft preferences and settings

**Principle:** Users must never see another team's private strategy data.

---

## Confirmed priority sequence (2026-06-19)

| Step | Phase | Status |
|------|-------|--------|
| 1 | Finish Workspace Profiles v1 | **Active P0** |
| 2 | Baseball AMI context packaging | **P1** — after workspace complete |
| 3 | Real Accounts | **Phase 2** — do not start yet |
| 4 | Simple Live Draft Room v1 | **Phase 3** — after Phase 2 |
| 5 | Advanced Live Draft Room | **Phase 4** — after Simple v1 |

---

## Recommended sequence (detail)

1. **Finish workspace profiles** across every app (Phase 1 / P0)
2. **Baseball AMI context packaging** — Dev Mode confirm, then hydration fix (P1)
3. **Add real account/login layer** (Phase 2)
4. **Build simple Live Draft Room v1** (Phase 3)
5. **Advanced Live Draft Room** — private queues/notes/AMI, realtime, conflicts (Phase 4)

**Do not** start Real Accounts or Live Draft Room until Workspace Profiles v1 is stable.

---

## Related work (P1 — blocked on Phase 1 completion)

- **AMI Baseball context packaging** — see P1 section above; primary owner send/hydration
- **AMI restatement layer** — unknown intent defaults to compare; secondary after pool fix

---

## Notes

- Work on branch **`dev`**; production `main` only on explicit release request.
- Command Center remains the profile switcher until real auth replaces preset selection.
- Live Draft Room builds on Baseball draft state (`draft_state.py`, `draft_ami_helpers.py`) but multiplayer room state is a new layer — do not conflate with single-user workspace blobs.
