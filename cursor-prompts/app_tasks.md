# Current Tasks — Daniel AI Command Center

**Last updated:** 2026-06-19

---

# Project Description

Central hub repo (`daniel-ai-command-center`) for suite homepage, activity aggregation, Supabase account memory, and shared modules synced to sibling apps.

---

# Current Priorities

**Focus (2026-06-19): Finish Workspace Profiles v1 — the primary foundation of the ecosystem. Do not start Real Accounts or Live Draft Room until P0 is stable.**

**Master plan:** [plans/2026-06-19-workspace-profiles-real-accounts-live-draft-room.md](./plans/2026-06-19-workspace-profiles-real-accounts-live-draft-room.md) *(user confirmed priority order)*

### P0 — Workspace Profiles Phase 1 (finish isolation)

**Model:** `workspace_id → app_id → state` · Command Center = profile switcher · Not real auth yet.

**Hard gates:** Do **not** start Phase 2 (Real Accounts) or Phase 3+ (Live Draft Room) until P0 exit criteria pass.

**Mostly complete (v1):**

- [x] Command Center — sidebar selector, workspace badge, scoped activity/resume reads
- [x] Investment Portfolio Analyzer
- [x] Baseball Analytics
- [x] Applied Mathematical Intelligence
- [x] Music Practice Coach

**Remaining rollout (final major milestone: FutureLens + ecosystem validation):**

1. [x] **NBA Companion AI** — workspace isolation validated (team persistence, CC activity isolation, Fast Load, Daniel/Ariel separation)
2. [ ] **FutureLens** — workspace isolation implemented; **awaiting user validation** (career/timeline/sim + Continue/Directory under Ariel vs Daniel)
3. [ ] **Command Center** — verify activity isolation across profiles (final ecosystem-wide validation after FutureLens)
4. [ ] **Music** — verify isolation if needed on acceptance pass

**Exit criteria:** Switch Daniel → Ariel; no shared drafts, portfolios, AMI history, or cross-profile activity in feed/Continue.

### P1 — AMI Baseball Draft Intelligence (after P0; behind workspace completion)

**Primary owner:** send/hydration / context packaging — not catcher logic, not player-specific logic, not new AMI reasoning modes.

**Known symptoms:** generic Q3/Q4 recommendations; incorrect player pool; wrong available-player context; top-12 EV slice not hydrated correctly; occasional fallback behavior.

**Sequence:**

1. [ ] Confirm Baseball AMI context counts in Dev Mode (`available_players`, `draft_snapshot`, `needed_positions`, `category_needs`, `hydrate_source`, deploy builds)
2. [ ] Verify `available_players` hydration on deployed Dev Mode
3. [ ] Fix top-12 EV → position-representative pool issue
4. [ ] Fix remaining AMI draft context packaging problems
5. [ ] Secondary: restatement layer unknown intent → compare default

**Related plan:** [plans/2026-06-11-ami-enhancement-roadmap.md](./plans/2026-06-11-ami-enhancement-roadmap.md)

### P2 — AMI Enhancement Program (parallel where not blocked)

1. [ ] **Phase 0:** Blob-first hydration by `question_id`; teaching response template
2. [ ] **Phase 1:** Baseball contextual transfer — remaining pages (Career, Leaderboards, Valuation, ML, Historical numerics depth)
   - [x] Draft board persistence unblocked (v15 JSON sanitize)
   - [x] Draft AMI context depth: Draft Assistant, Live Draft Room, Fantasy Sleepers
3. [ ] **Phase 2:** Music AMI — richer send context + music router/solvers
4. [ ] **Phase 3:** Applied Math teaching layer — interactive what-if, NBA/Investment hooks

### P0 (previous) — Baseball Phase 2 / Suite port

**Plan:** [plans/2026-06-08-baseball-phase-2-page-audit.md](./plans/2026-06-08-baseball-phase-2-page-audit.md)  
**Primary repo:** `baseball-stat-app` · **Shared modules:** sync via `scripts/sync_suite_cloud_modules.py`

#### Shipped (Sprint 1 — navigation foundation)
- [x] Page navigation ownership — `claim_user_page_ownership`, reconcile stale nav (CC `4d2205b`, Baseball `a293b34`)
- [x] Cloud insight hydrate no longer forces page navigation
- [x] AMI return consume on page match
- [x] Tests: `test_page_navigation_ownership.py` (43 passed)

#### Sprint 2 — Career Totals + Comparison AMI parity (accepted 2026-06-08)
- [x] Audit Career Totals widget keys vs `PAGE_STATE_REGISTRY`
- [x] Create `career_totals_state.py` (canonical pattern)
- [x] Add `apply_comparison_source_state_from_ami` (Trend parity)
- [x] Sync trace + force cloud save (`be91f64`)
- [x] Manual acceptance A–E on phone + Dell (Career Totals) — **PASS**

#### Sprint 3 — Draft cluster + watchlist (accepted 2026-06-08)
- [x] Create `draft_state.py` (queue + watchlist canonical pattern)
- [x] Persist `draft_queue` + watchlist in disk/cloud blob
- [x] Fix Draft Room envelope key mismatch (`Draft Room Simulator`)
- [x] AMI build/apply for queue + watchlist
- [x] `?dev=1` debug panel (`render_draft_state_debug`)
- [x] Tests: `test_draft_state.py` acceptance A–E (13 passed)
- [x] Manual acceptance A–E on phone + Dell — **PASS** (`a569612`)

#### Sprint 4 — Historical Explorer (accepted 2026-06-08)
- [x] Create `historical_state.py` (canonical filters + stat mins)
- [x] Full `historical_filters` workspace envelope
- [x] AMI build/apply via `apply_historical_source_state_from_ami`
- [x] `?dev=1` debug panel (`render_historical_state_debug`)
- [x] Tests: `test_historical_state.py` acceptance A–E (11 passed)
- [x] Hotfix: `historical_filter_changed` ordering (`7647f61`)
- [x] Manual acceptance A–E on phone + Dell — **PASS**

#### Sprint 5 — Valuation + ML Predictions (accepted 2026-06-08)
- [x] Create `valuation_state.py` (filters + stat mins + selected player)
- [x] Create `projections_state.py` (scope/tuning/display/pipeline)
- [x] Workspace envelope: `valuation_filters`, `projections_filters`
- [x] AMI build/apply for Valuation + ML Predictions
- [x] `?dev=1` debug panels (`render_valuation_state_debug`, `render_projections_state_debug`)
- [x] Tests: `test_valuation_state.py`, `test_projections_state.py` acceptance A–E (23 passed)
- [x] AMI insight eligible pages fix (`7e370f4` / `51df10e`)
- [x] Manual acceptance A–E on phone + Dell (Valuation + ML Predictions) — **PASS**

#### Sprint 6 — Fantasy cluster + sign-off (accepted 2026-06-08)
- [x] Create `fantasy_state.py` (sleepers / standings / lineup sections)
- [x] Create `leaderboards_state.py` (year range, weights, stat mins)
- [x] Workspace envelope: `fantasy_*_filters`, `leaderboards_filters`
- [x] AMI build/apply for Leaderboards + Fantasy pages
- [x] `?dev=1` debug panels (`render_fantasy_state_debug`, `render_leaderboards_state_debug`)
- [x] Tests: `test_fantasy_state.py`, `test_leaderboards_state.py` acceptance A–E (23 passed)
- [x] AMI eligible pages fix for Fantasy cluster + Leaderboards (`990c25e` / `ab8faef`)
- [x] Manual acceptance A–E on phone + Dell — **PASS** (incl. Fantasy Standings AMI return)

#### Final Baseball Acceptance Sweep (accepted 2026-06-08)
- [x] Audit all 14 sidebar pages — canonical ownership, AMI, persistence
- [x] Automated suite: **147 passed** (state + persistence + AMI scope)
- [x] `docs/BASEBALL_PAGE_STATE_PROTOCOL.md` — canonical architecture reference
- [x] `docs/BASEBALL_ACCEPTANCE_MATRIX.md` — PASS/FAIL by page + P0/P1/P2 bugs
- [x] Draft Room `PAGE_STATE_DEBUG_PREFIXES` cleanup
- [x] **Suite port gate: PASS** — tagged `baseball-sync-reference-v1`

#### Sprint 7 — Suite port (active)

**Plan:** [plans/2026-06-08-sprint-7-suite-port.md](./plans/2026-06-08-sprint-7-suite-port.md)  
**Reference tag:** `baseball-sync-reference-v1` on `baseball-stat-app` `dev`  
**Music Phase A:** [ai-music-practice-coach/docs/MUSIC_PHASE_A_AUDIT.md](../ai-music-practice-coach/docs/MUSIC_PHASE_A_AUDIT.md) (+ `MUSIC_ACCEPTANCE_MATRIX_DRAFT.md`, `MUSIC_PAGE_STATE_PROTOCOL_DRAFT.md`)  
**Rule:** Architecture migration only — no new product features.

Port order (Phase A → B → C → D per app):

1. [x] **Music Practice Coach** — Phase A audit complete (`docs/MUSIC_PHASE_A_AUDIT.md`)
   - [x] Phase B — shared suite modules + `prepare_music_workspace` + Music Coach stub (`docs/MUSIC_PHASE_B_PROTOCOL.md`) — **accepted**
   - [x] Phase C slice 1 — `active_song_state.py` + `studio_nav_state.py` (`docs/MUSIC_PHASE_C_PROTOCOL.md`) — **accepted**
   - [ ] Phase C slice 2 — `practice_state.py` — implement + live acceptance
   - [ ] **Watch:** first phone→Dell instrument/setup edit may lag once; re-check on next acceptance pass (non-blocker)
2. [ ] **NBA Playoff Companion** — Phase A audit
3. [ ] **Investment App** — Phase A audit
4. [ ] **Applied Intelligence / Calculus App** — Phase A audit

Per-app phases:
- **A:** Page / state / AMI / navigation inventory
- **B:** Shared modules (`suite_user_persistence`, `suite_cloud_state`, `applied_math_return_insight`, `suite_analytical_question`, `suite_deep_links`, `suite_resume_launch`)
- **C:** Canonical `{page}_state` modules + ownership rules + tests A–E
- **D:** Phone↔Dell + AMI + final acceptance matrix

### P1 — Command Center Continue vs App Directory

- [x] Full classification audit — [plans/suite-usability-audit-2026-06-08.md](./plans/suite-usability-audit-2026-06-08.md) §1
- [x] Prior audit — [plans/command-center-workflow-classification-audit.md](./plans/command-center-workflow-classification-audit.md)
- [x] **User approved** implementation order A→E
- [x] Remove passive Continue: `song_selected`, `holdings_updated`, instrument/key-only
- [x] Music dedupe: one Continue card per song (`music:song:{pick}`)
- [x] Wire Continue: Future Lens timeline/career/skill; NBA comparison/playoff tracker
- [x] Enrich Directory from disk user_state (draft workspace, NBA player focus, FL identity, portfolio preset)
- [ ] Explicit event-type tags (Continue / Directory / Both / Neither) — follow-up
- [ ] User smoke-test Continue vs Directory on live Command Center

### P2 — Music persistence (Priority C — implemented)

- [x] Full audit — [plans/suite-usability-audit-2026-06-08.md](./plans/suite-usability-audit-2026-06-08.md) §2
- [x] CPL bar widget persistence (`_cpl_widget_state`) — Music repo `1a54745`
- [x] Cloud session sync — synced `suite_user_persistence.py` (pick_restore_session, fingerprint, local_dirty)
- [x] Non-core override fix + restore flag + tests — Music repo `232398f`
- [x] Audit doc — Music `cursor-prompts/plans/music-persistence-audit-2026-06-08.md`
- [ ] Manual verify: Turn the Lights Back On + **non-core song** (user post-deploy)

### P3 — NBA persistence (Priority B — implemented)

- [x] Full audit — [plans/suite-usability-audit-2026-06-08.md](./plans/suite-usability-audit-2026-06-08.md) §3
- [x] Legacy Tracker player + LGC manual/matchup dynamic keys persisted
- [x] Silent restore failure → `_nba_restore_error`; Knicks default only on true first run
- [ ] Manual verify: non-Knicks + LGC + Legacy Tracker survives F5/reboot/cross-device

### P4 — Future Lens persistence (E1 + E2 — implemented)

- [x] Full audit — [plans/suite-usability-audit-2026-06-08.md](./plans/suite-usability-audit-2026-06-08.md) §4
- [x] Implementation plan — [plans/future-lens-persistence-implementation-2026-06-08.md](./plans/future-lens-persistence-implementation-2026-06-08.md)
- [x] E1 — Wire `log_career_analysis` on wizard complete (FL repo, pending commit)
- [x] E2 — Resume URL: `suite_fl_domain`, `suite_fl_area`, `suite_fl_timeline_year`, `suite_fl_sim_year`, `suite_fl_view` (CC + FL)
- [ ] Manual verify: FL refresh/reboot/cross-device + Continue + App Directory

### P5 — Applied Math quality audit (roadmap only)

- [x] Full audit + roadmap — [plans/applied-math-quality-audit-2026-06-08.md](./plans/applied-math-quality-audit-2026-06-08.md)
- [ ] **No implementation yet** — user review roadmap
- [ ] P0 backlog (post-approval): baseball slope/R² to context; AMI preload persistence; server-side context

### Paused — Investment formulas & macro

- [x] Transparency Phase 1 shipped in investment repo (`76969f4`) — labels, banners, lookback bug fixes
- [ ] Smoke-test Investment Phase 1 on Streamlit Cloud
- [ ] Phase 2+ transparency deferred until suite P1–P5 stable

### Previously shipped (persistence P0/P1)

- [x] Deep audit — [plans/suite-session-persistence-audit.md](./plans/suite-session-persistence-audit.md)
- [x] Baseball restore-before-resume (`16fbe29`); AMI cloud reset (`32c2158`)
- [x] P0: Music non-core override, Future Lens early restore, NBA team widget (`db30b53`)
- [x] P0: Investment cloud drift reconcile + EOR autosave guard
- [x] P1: Future Lens tab (`88d937e`), Music restore (`f0720e2`), Investment holdings (`cd5fa92`)

### Shipped (2026-06-07)

- [x] Clean Applied Math Continue cards — CC `d400e71`, synced to siblings
- [x] Commit + push dev across CC, Baseball, AMI, Investment, NBA

### P0 — Documentation & roadmap system

- [x] Create `cursor-prompts/` roadmap system (this commit)
- [x] Add `.cursor/rules/command-center-roadmap-docs.mdc`
- [x] Link root [README.md](../README.md) → `cursor-prompts/app_roadmap.md`

### P1 — Workflow coverage (systematic)

- [x] Suite workflow coverage audit — [plans/suite-workflow-coverage-audit.md](./plans/suite-workflow-coverage-audit.md) (2026-06-06)
- [x] Baseball `trend_comparison_viewed` logging + Continue card (priority 59)
- [ ] P1 backlog: Baseball Valuation, Live Draft picks, ML insight player hooks
- [ ] Verify Future Lens / Applied Math UI calls existing activity hooks on each app

### P1 — Activity Feed Phase B

- [x] Review and commit: `activity_time.py`, `activity_feed.py`, `activity_store.py`, `ai_command_center.py`, `homepage_sections.py`, suite storage clients, tests
- [x] Run activity pytest suite (time, dashboard, noise, priority, executive)
- [ ] Push verified on Streamlit Cloud dev — Today's Work / Highlights / Recent visible after redeploy (build `2026-06-03-v31`)
- [x] Bump `BUILD_VERSION` to `2026-06-03-v30`
- [x] Hotfix: `ActivityFeedItem` import crash — `activity_models.py` + import order (`v31`)

### P2 — Suite deploy & cross-device verification

- [ ] Confirm Command Center Streamlit Cloud branch = `dev`, secrets block complete, Reboot after secret changes
- [ ] Admin expander: `suite_activity section found` = true, Supabase reachable, pipeline status OK
- [ ] Cross-device test: phone Music event → laptop Command Center feed (see [docs/SUITE_DEV_DEPLOY.md](../docs/SUITE_DEV_DEPLOY.md) §5)
- [ ] Verify Baseball + Future Lens reset button on Cloud (`bc7dd0c`, `ab22c76` or later)

### P3 — Shared module hygiene

- [ ] After any `suite_*` edit here, run `python scripts/sync_suite_cloud_modules.py` and commit sibling repos as needed
- [ ] `python scripts/verify_account_memory.py` and `python scripts/verify_live_activity.py` locally

---

# Next Features

*(After P1–P2 or in parallel)*

- [ ] Data-driven Phase A verification table (one config for all apps)
- [ ] Homepage auto-refresh toggle or shorter cache TTL for connections probe
- [ ] Coach insights: ingest cloud `full_session` page/summary per app
- [ ] Update README to reflect live Supabase mode

---

# Long-Term Vision

### Sequenced (confirmed 2026-06-19 — do not skip)

| Step | Work | Gate |
|------|------|------|
| 1 | Finish Workspace Profiles v1 | **Active P0** |
| 2 | Baseball AMI context packaging | **P1** — after P0 |
| 3 | Real Accounts (Daniel admin, Ariel user) | **Phase 2** — do not start yet |
| 4 | Simple Live Draft Room v1 | **Phase 3** — after Phase 2 |
| 5 | Advanced Live Draft Room | **Phase 4** — after Simple v1 |

*Detail:* [plans/2026-06-19-workspace-profiles-real-accounts-live-draft-room.md](./plans/2026-06-19-workspace-profiles-real-accounts-live-draft-room.md) · [app_roadmap.md](./app_roadmap.md) · [app_feature_backlog.md](./app_feature_backlog.md)

---

# Completed Features

Recent task completions (see [app_completed_features.md](./app_completed_features.md)):

- [x] Cross-device cloud session persistence (`full_session`) — build v29 (`47273c2`)
- [x] Account-memory deep links + `suite_resume_launch` (`6594dd4`)
- [x] Supabase account memory with `user_id` on writes (`5bff893`)
- [x] Roadmap documentation system (`cursor-prompts/`)
- [x] Activity Feed Phase B — UTC timestamps, Today's Work, Highlights, Recent rollups (`2026-06-03-v30`)

---

# Notes

- Work on branch **`dev`**; push `origin/dev` for Streamlit Cloud dev homepage.
- When a task ships, move detail to `app_completed_features.md` and uncheck here.
- Large plans → `cursor-prompts/plans/YYYY-MM-DD-title.md` and link below.
- **FutureLens validation (P0):** Daniel Technology/domain/sim → refresh persists; Ariel Finance/different sim → refresh persists; CC Daniel feed shows Daniel FL only; CC Ariel feed shows Ariel FL only; Continue/Directory resume keys scoped per workspace; developer tools hidden for Ariel.

### Active plans

| Plan | Status |
|------|--------|
| [plans/2026-06-19-workspace-profiles-real-accounts-live-draft-room.md](./plans/2026-06-19-workspace-profiles-real-accounts-live-draft-room.md) | **Active P0** — finish profiles → accounts → Live Draft Room |
| [plans/2026-06-11-ami-enhancement-roadmap.md](./plans/2026-06-11-ami-enhancement-roadmap.md) | **Active P1/P2** — AMI context + teaching; draft pool hydration blocked on Dev Mode confirm |
| [plans/2026-06-08-baseball-phase-2-page-audit.md](./plans/2026-06-08-baseball-phase-2-page-audit.md) | Shipped — suite port reference |
| [plans/2026-06-08-sprint-7-suite-port.md](./plans/2026-06-08-sprint-7-suite-port.md) | Active — Music Phase C slice 2+; NBA/Investment/AMI audits |
| [plans/suite-usability-audit-2026-06-08.md](./plans/suite-usability-audit-2026-06-08.md) | **Active** — Continue, Music/NBA/FL persistence, Applied Math roadmap |
| [plans/command-center-workflow-classification-audit.md](./plans/command-center-workflow-classification-audit.md) | P1 — Continue vs Directory (detail) |
| [plans/investment-ui-transparency-mockups.md](./plans/investment-ui-transparency-mockups.md) | P3 — wording mockups |
| [plans/suite-session-persistence-audit.md](./plans/suite-session-persistence-audit.md) | P2 — persistence deep audit |
| [plans/investment-macro-return-volatility-audit.md](./plans/investment-macro-return-volatility-audit.md) | P3 — calculation audit |
| Activity Feed Phase B | Shipped on `dev` — verify Streamlit Cloud deploy |

---

## Deployment checks

- [ ] Streamlit Cloud: repo `Coakley11/daniel-ai-command-center`, branch `dev`, main file `ai_command_center.py`
- [ ] Dev URL live: `HOMEPAGE_DEV_URL` in `app_urls.py`
- [ ] `[suite_activity]` secrets: `supabase_url`, `supabase_key`, `suite_user_id`, `suite_user_email`
- [ ] Migrations applied: `001_suite_activity.sql`, `002_suite_account_memory*.sql`, `003_suite_account_memory_resume.sql`
- [ ] Reboot app after secrets or migration changes

---

## Testing tasks

- [ ] `pytest` (full suite or at minimum activity + storage tests)
- [ ] `python scripts/verify_imports.py`
- [ ] `python scripts/verify_homepage_links.py`
- [ ] Manual: empty Supabase → empty states render without traceback
- [ ] Manual: inject test event (`scripts/inject_test_music_event.py`) → appears in feed
