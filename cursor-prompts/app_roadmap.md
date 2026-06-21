# Daniel AI Command Center — Master Roadmap

**Last updated:** 2026-06-21 · **Branch:** `dev` · **Entry app:** `ai_command_center.py` · **Build:** `2026-06-03-v30`

This is the master planning document. Related files:

| File | Purpose |
|------|---------|
| [app_tasks.md](./app_tasks.md) | Active work and near-term execution |
| [app_feature_backlog.md](./app_feature_backlog.md) | Queued ideas and enhancements |
| [app_completed_features.md](./app_completed_features.md) | Shipped capabilities by area |

---

# Project Description

**Daniel Cohen AI Command Center** is the suite homepage and cross-app dashboard for the Daniel AI ecosystem. It aggregates real activity from six sibling Streamlit apps (Music, Investment, Baseball, NBA, Applied Intelligence, Future Lens), surfaces actionable coach recommendations, resume/continue deep links, and an app launcher — without duplicating each app's full UX.

**Stack:** Python 3, Streamlit, optional Supabase (PostgREST), local SQLite fallback, shared suite modules copied to sibling repos via `scripts/sync_suite_cloud_modules.py`.

**Deployment:** Daily work on `origin/dev` (Streamlit Cloud dev homepage). Production `main` may lag; see [docs/DEPLOYMENTS.md](../docs/DEPLOYMENTS.md) and [docs/SUITE_DEV_DEPLOY.md](../docs/SUITE_DEV_DEPLOY.md).

---

# Current Priorities

**Confirmed sequence (2026-06-21, revised):** Finish **Account / Workspace phase** (Settings in all apps → workspace polish → **Real Accounts foundation** → persistence validation) → **then** AMI Real Problem Importer (scaffolding first). Kalshi coach and template library follow Importer MVP. Live Draft Room remains after Real Accounts stable.

**Plan:** [plans/2026-06-21-account-workspace-phase-completion.md](./plans/2026-06-21-account-workspace-phase-completion.md)

1. **Account Settings Sprint B** — ✅ code shipped; manual A1–A4 + deploy sync pending.
2. **Workspace polish (P1b)** — ✅ audit helpers + deep-link fix; manual W1–W8 pending.
3. **Real Accounts foundation (Sprint C)** — ✅ scaffolding shipped (`suite_auth.py`, auth gate); enable on prod + C1–C5 pending.
4. **Persistence validation (Sprint D)** — acceptance doc ready; matrix execution pending.
5. **AMI Real Problem Importer (Phase 0 scaffolding → MVP)** — **blocked** until steps 1–4 exit criteria pass.
6. **Kalshi / prediction-market coach** — after Importer MVP.
7. **More real-life templates** — universal routing registry (car purchase, job offers, …).
8. **AMI Baseball Draft Intelligence** — deferred until Importer v1 or narrow draft fixes.
9. **Live Draft Room** — Phase 3+ after Real Accounts stable (unchanged).

---

# Next Features

### Active (approved order — gate Importer until Account/Workspace complete)

- **Account Settings Sprint B** — code complete; deploy sync + manual sign-off pending
- **Real Accounts foundation** — scaffolding complete; enable `SUITE_AUTH_ENABLED` + manual C1–C5
- **Persistence validation matrix** — execute `docs/SUITE_ACCOUNT_WORKSPACE_ACCEPTANCE.md`
- **AMI Importer Phase 0** — architecture only (after Sprint D gate): `decision_templates`, `decision_router`, `decision_math`, `decision_registry`
- **AMI Importer MVP** — Kalshi-style prediction-market import (paste/CSV/manual) → Betting/EV section with implied prob, break-even, EV, edge, risk/reward, position size; educational disclaimer
- **Universal decision router** — car/lease, job offers, consumer purchase, business C/B, trade/risk-reward, treatment/risk-benefit (registry entries after MVP)

### Queued (do not start yet)

- **Phase 3 — Simple Live Draft Room v1** — room code, join room, shared board/picks/rosters/**clock** (after Real Accounts stable)
- **Phase 4 — Advanced Live Draft Room** — private queues/notes/AMI, permissions, reconnect, conflict prevention, team-specific intelligence. Shared vs private state split enforced.

### Near-term (parallel where safe)

- **Baseball reference protocol** — Phase 2 complete; port to Music, NBA, Investment, Applied Intelligence (Sprint 7)
- **AMI send/hydration** — position-representative `available_players` for draft-market questions (catchers, scarcity, player fit)
- Per-app activity coverage expansion; smarter Continue cards when `full_session` is richer
- Homepage dev/prod URL auto-discovery refresh (`scripts/resolve_deploy_urls.py`)

---

# Long-Term Vision

### Identity & multiplayer (sequenced — confirmed)

1. **Workspace Profiles v1** (now, P0) — preset profiles, Command Center switcher, `workspace_id → app_id → state`
2. **AMI Baseball draft context** (P1) — after workspace complete
3. **Real accounts** (Phase 2) — do not start yet
4. **Simple Live Draft Room** (Phase 3) — shared room state only; after Phase 2
5. **Advanced Live Draft Room** (Phase 4) — private user state + realtime polish

### Suite platform

- Unified **suite identity** — workspace today → `user_id` tomorrow; consistent resume URLs; session sync on every app
- **AI command layer** — LLM weekly narrative from real events; AMI with full draft-context hydration
- **Mobile-first homepage** — compact continue row, swipe-friendly app cards
- **Operational dashboard** — deploy health, last event per app, secret rotation checklist in UI
- **Teacher/coach mode** — share read-only activity summaries (future)

---

# Completed Features

See [app_completed_features.md](./app_completed_features.md) for the full shipped list. Highlights:

- Single-page homepage with six major sections + admin expander
- Supabase + SQLite dual storage for events and resume state
- Phase A activity verification per app in admin diagnostics
- Account memory migrations and deep-link resume launch helpers
- Cross-app project intelligence and accomplishment weekly lines

---

# Notes

- Command Center does **not** host Baseball/Music/etc. UIs — it links out via `app_registry.py` / `app_urls.py`.
- README still says "placeholder data" — outdated; activity can be live when Supabase is configured.
- Uncommitted local work (as of roadmap creation): activity feed Phase B files — track in [app_tasks.md](./app_tasks.md).

---

## Current application status

**Product:** Streamlit-wide homepage prototype evolved into a **live cross-app hub** when Supabase secrets are configured; falls back to local `data/suite_activity.json` for development.

**Registered suite apps (6):**

| Key | Name | Status | Main file (sibling repo) |
|-----|------|--------|--------------------------|
| `music` | Music Practice Coach | Active | `streamlit_music_practice_app.py` |
| `investment` | Investment Analytics | Active | `streamlit_app.py` |
| `baseball` | Baseball Analytics | Active | `streamlit_app.py` |
| `nba` | Basketball Companion | Active | `streamlit_app.py` |
| `applied_intelligence` | Applied Intelligence | Active | `streamlit_app.py` |
| `future_lens` | AI Future Simulator | Active | `streamlit_app.py` |

---

## Key pages and workflows (homepage sections)

Rendered top-to-bottom in `ai_command_center.py`:

| Section | Purpose | Primary modules |
|---------|---------|-----------------|
| **Hero** | Welcome, build version, live vs waiting tag | `ai_command_center.py`, `activity_store.py` |
| **Continue where you left off** | Resume cards + deep links | `continue_dashboard.py`, `project_intelligence.py`, `suite_storage.py` |
| **Suite focus** | Cross-app weekly patterns | `project_intelligence.py` |
| **Coach Insights** | Actionable next steps (not fact repetition) | `coach_engine.py` |
| **Activity** | Today's Work → Highlights → Recent Activity | `activity_feed.py`, `activity_time.py` |
| **Weekly Summary** | Accomplishment counts this week | `activity_store.py`, `project_intelligence.py` |
| **App Directory** | Themed cards + Open buttons | `app_registry.py`, `app_branding.py` |
| **Deployment & link audit (admin)** | Secrets probe, Supabase diagnostics, Phase A tables | `activity_diagnostics.py`, `suite_account.py` |

**User workflow:** Open Command Center → scan continue/coach → review activity → launch app via Open/Continue → sibling app applies `suite_resume_launch` query params.

---

## High-priority future enhancements

- Finish and deploy Activity Feed Phase B (executive dashboard UX).
- Real-time or near-real-time activity refresh (today: load on page render).
- Expand coach insights to use cloud `full_session` summaries per app.
- Automated deploy URL verification in CI (`scripts/verify_public_apps.py`).
- Document and enforce reset-to-default pattern across all suite apps from Command Center checklist.

---

## Known bugs

| Issue | Area | Notes |
|-------|------|-------|
| Workspace isolation incomplete | FutureLens (edge cases) | Automated tests pass; re-verify in Sprint D matrix |
| Real auth not wired | All apps | Secrets-based identity; Sprint C blocker before Importer |
| Account Settings CC-only | Suite UX | Sprint B — siblings lack badge/panel |
| AMI draft context too thin | Baseball AMI | Top-12 EV `available_players` often omits catchers and key targets; not a reasoning bug |
| AMI restatement defaults to compare | AMI | Unknown Draft Assistant intents show generic compare framing |
| README claims "placeholder data" | Docs | Misleading when Supabase is live |
| Cloud deploy lag | Activity feed | Confirm Streamlit dev shows build `2026-06-03-v30` |
| `APP_BRANCH` shows `DEV` not `dev` | `app_urls.py` | Display string only; Streamlit uses `dev` |
| Coach insights can be empty with sparse events | Coach | Expected empty state; not a crash |
| Connection probe timeouts | App registry | `verify_connections()` HTTP GET can false-negative |
| Sibling apps out of sync | Shared modules | Must run `sync_suite_cloud_modules.py` manually |
| Baseball pages without canonical state | Baseball | Only Trend + Comparison have full ownership modules; 12 pages on generic `page_state` |
| Reset button hidden if import fails | Sibling apps | `try/except: pass` in app entrypoints |

---

## UI/UX improvement opportunities

- Sidebar or sticky quick-launch strip for frequent apps.
- Collapse admin expander behind role flag or `?admin=1` query param.
- Stronger visual distinction between Highlights vs Recent Activity.
- Empty-state CTAs that deep-link into a suggested first action per app.
- Dark mode / reduced-motion theme tokens in hero CSS.
- Show relative timestamps consistently (depends on Phase B deploy).

---

## AI enhancement opportunities

- LLM weekly digest from `load_all_events()` → narrative paragraph in Suite focus.
- Personalized continue ranking (ML or heuristic) beyond `project_intelligence` rules.
- Anomaly detection ("you haven't practiced in 5 days") with coach priority boost.
- Natural-language search over activity history.
- Suggested next app based on time-of-day and past patterns.

---

## Technical debt items

| Item | Notes |
|------|-------|
| Duplicate test paths (`tests\` vs `tests/`) | Windows path artifacts |
| `homepage_sections.py` vs inline renderers | Partial abstraction; not all sections use HOMEPAGE_RENDERERS |
| Legacy SQLite + cloud dual write paths | Documented in `docs/SUITE_CLOUD_ACTIVITY.md` |
| Manual module sync to 6 repos | No CI gate on drift |
| Large `activity_feed.py` | Candidate for split (rollup vs highlight vs today) |
| Phase A diagnostics tables duplicated per app | Could be data-driven from config |
