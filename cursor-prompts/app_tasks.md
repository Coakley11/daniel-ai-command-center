# Current Tasks — Daniel AI Command Center

**Last updated:** 2026-07-14 (Command Center fantasy workflow integration; Baseball in-season polish paused)

**Master plan:** [plans/2026-06-21-account-workspace-phase-completion.md](./plans/2026-06-21-account-workspace-phase-completion.md)

**Focus:** **Command Center fantasy workflow hub** — Continue / Activity / App Directory for shared leagues, trades, waivers, lineups, Live Draft. Baseball feature work paused after FA/waiver polish.

### P0 — Command Center Fantasy Workflow Integration (**ACTIVE**, 2026-07-14)

**Plan:** [plans/2026-07-14-command-center-fantasy-workflow.md](./plans/2026-07-14-command-center-fantasy-workflow.md)

**Philosophy (keep separated):**
- **Continue** — recent actionable resume (trade offer → Trade Center, invite → Library, waiver tx → Waiver Wire, …)
- **App Directory** — short identity reminders of meaningful Baseball work (not navigation)
- **Activity** — detailed history of what the user did

**Implementation order:**
1. [x] **CC-1** Taxonomy — map fantasy event types → Continue / Activity / Directory; supersede rules (offer → accepted)
2. [x] **CC-2** Deep links — proposal / invite / league / week / waiver tx resume params
3. [x] **CC-3** Continue cards for trade lifecycle, waiver, shared league, lineup lock/save, Live Draft complete, Active League change
4. [x] **CC-4** Activity formatters + grouping for the same events
5. [x] **CC-5** App Directory chips (Live Draft / Trades / Lineup / Waiver / Shared League) — high-level only
6. [x] **CC-6** Baseball emitters (if missing) for suite activity + continue-eligible payloads
7. [x] **CC-7** Tests — classification, supersede, deep links

**Shipped (2026-07-14):** `fantasy_workflow_activity.py` + Continue/Activity/Directory wiring; Baseball `baseball_fantasy_activity.py` emitters on trade/waiver/lineup/invite/claim/shared-league paths.
### Baseball pause notes (2026-07-14)

Shipped before pause (`baseball-stat-app` `dev`): shared-league ownership/Trade Center, Live Draft current-session bind, Waiver free-agent-only + league position awareness. Deferred polish: timer tuning, live chat, tutorial.

### P0 — Baseball Draft Reliability (`baseball-stat-app` `dev`, 2026-07-06) **PAUSED**

**Plan:** [plans/2026-07-06-draft-reliability-intelligence-ui.md](./plans/2026-07-06-draft-reliability-intelligence-ui.md) · Tracker: `baseball-stat-app/docs/DRAFT_RELIABILITY_SPRINT.md`

Much of shared-league / trade / waiver work landed in subsequent baseball sessions; remaining reliability items stay deferred while CC is primary.


### P1 — Uploaded Drafts → Shared Leagues (`baseball-stat-app` `dev`, 2026-07-08) **PLANNED**

**Plan:** [plans/2026-07-08-uploaded-drafts-shared-leagues-team-claims-trades.md](./plans/2026-07-08-uploaded-drafts-shared-leagues-team-claims-trades.md) · `baseball-stat-app/docs/UPLOADED_DRAFTS_SHARED_LEAGUES_PLAN.md`

**Prerequisite:** FLC v1 foundation + draft import validation (shipped); Real Accounts (Sprint C) soft dependency for prod multi-user trades.

**Implementation order:**
1. [ ] **UDSL-1** Unified import pipeline + strict validation mode (no skip for shared league)
2. [ ] **UDSL-2** Entry UI from Draft Room + Standings → common wizard
3. [ ] **UDSL-3** `save_imported_league_context` + `real_league` context type
4. [ ] **UDSL-4** Shared store publish + fingerprint dedupe
5. [ ] **UDSL-5** Team claim UI + library / Active League integration
6. [ ] **UDSL-6** Trade gating hardening + imported-league trade smoke

**Start after:** Draft Reliability P0 green + active fantasy source UI validation complete.

### P0 — Draft Assistant performance slice 1 ✅ (`9c6da75`, 2026-07-06)

- [x] Deferred settings persist (dirty flag + page-leave / debounced flush)
- [x] Scoring cache key — pool/board revision + window/style/format
- [x] Why-this-pick session cache
- [x] Profile: settings 978ms→16ms; why-text cached 501ms→0.2ms

### P0 — Workspace Profiles close-out ✅

- [x] FutureLens — Daniel/Ariel validation (10 tests pass in `future-lens-ai-transition-simulator`)
- [x] Command Center — final activity isolation pass
- [x] AMI — persistence, cloud sync, UI-state one-shot reapply (`87d2785`)

### P1 — Account Settings Sprint A ✅ (Command Center)

- [x] Command Center Account Settings page — email, display name, `suite_user_id`, Supabase `user_id`, cloud mode
- [x] Active workspace + scoped cloud key preview (Daniel vs Ariel)
- [x] Read-only persistence/namespace diagnostics + mismatch warnings
- [x] Password reset — stub until Supabase Auth (Sprint C)
- [x] Shared `suite_account_settings.py` + sync script entry
- [x] Global workspace badge in CC sidebar

### P1b — Account Settings Sprint B + workspace polish (**mostly complete — manual sign-off pending**)

- [x] `suite_app_shell.py` — shared sidebar badge + account panel + namespace notices + CC link
- [x] `suite_workspace_deep_link_audit.py` + `suite_activity_audit.py` + tests (`test_suite_sprint_b_audit.py`)
- [x] `continue_dashboard.recently_used_apps()` — `?suite_workspace=` on Open URLs
- [x] Sync script includes account/shell/auth modules; wired in AMI, Investment, NBA, Music, FutureLens, Command Center
- [x] `scripts/wire_suite_app_shell.py` + `scripts/wire_suite_auth_gate.py`
- [ ] Run sync + commit sibling repos; reboot Streamlit Cloud deployments
- [ ] Baseball — wire shell when `streamlit_app.py` entry exists locally
- [ ] Manual A1–A4 + W1–W8 acceptance (`docs/SUITE_ACCOUNT_WORKSPACE_ACCEPTANCE.md`)

### P1c — Real Accounts foundation (**Sprint C — scaffolding shipped; enable on prod pending**)

- [x] `suite_auth.py` — Supabase Auth signup, login, logout, reset, workspace ownership clamp
- [x] `SUITE_AUTH_ENABLED` feature flag (default off — no behavior change)
- [x] Account panel delegates to `render_auth_panel()` when flag enabled
- [x] `apply_suite_auth_gate()` wired in CC + all sibling entry files (via sync + wire script)
- [ ] Enable Supabase Auth + `SUITE_AUTH_ENABLED=true` on deployments
- [ ] Manual C1–C5 acceptance (login isolation Daniel vs Ariel)
- [ ] Map auth user → `suite_users` by auth UUID (not email heuristic only)

### P1d — Persistence validation (**Sprint D — gate**)

- [x] Acceptance matrix template — `docs/SUITE_ACCOUNT_WORKSPACE_ACCEPTANCE.md`
- [ ] Cross-app workspace isolation matrix (manual + doc)
- [ ] Cross-device cloud restore sign-off (Music, AMI, Baseball minimum)
- [ ] Music CPL regression pass (v29k–v29l behaviors)
- [ ] Document in `docs/SUITE_ACCOUNT_WORKSPACE_ACCEPTANCE.md`

### P2 — AMI Real Problem Importer (**blocked until P1b–P1d exit**)

**Product direction (2026-06-21):** AMI becomes a **router for real-world decisions**, not just calculators.

```
Real-world problem → Import → Classify → Route → Prefill framework → Teach & solve
```

**V1 proof target:** Kalshi-style **prediction market / bet import** → **Betting / Expected Value** section.

**Import channels (architecture supports all; V1 prioritizes paste/CSV/manual correction):**
- Copy/paste, CSV, manual entry (V1)
- Screenshot, URL (later)

**Kalshi-style extract fields:** market question, YES/NO prices, contract side, cost, payout, expiration, metadata, source text.

**EV outputs:** implied probability, break-even probability, expected value, edge, risk/reward, profit/loss, conservative position size.

**Framing:** mathematical decision-analysis tool — not gambling advice. Disclaimer: results depend on user probability assumptions, fees, liquidity, jurisdiction, risk tolerance.

**Future routing targets:**
| Problem | Route target |
|---------|--------------|
| Car lease / purchase | Financial Decisions / Major Purchase Analysis |
| Compare two cars | Financial Decisions / Major Purchase Comparison |
| Cell phone purchase | Consumer Purchase Comparison |
| Job offers | Career / Job Offer Decision Analysis |
| Business deal | Cost-Benefit Analysis |
| Single stock / short-term trade | Trade / Risk-Reward Decision |
| Prediction market / bet | Betting / Expected Value |
| Treatment decision | Risk-Benefit Analysis |

**Phase 0 — scaffolding only (no OCR/URL/screenshot UI):**
- [ ] `decision_templates.py`, `decision_router.py`, `decision_math.py`, `decision_registry.py`
- [ ] AMI empty section + template registry (no Kalshi form yet)

**Phase 1 — MVP:**
- [ ] Paste/CSV/manual prediction-market import → prefill Betting/EV → user adjusts assumptions → AMI explains math

### P2 — Baseball Fantasy League Context v1 (**active — `baseball-stat-app` `dev`**)

**Plan:** [plans/2026-07-04-fantasy-league-context-v1.md](./plans/2026-07-04-fantasy-league-context-v1.md)  
**Full plan:** `baseball-stat-app/docs/FANTASY_LEAGUE_CONTEXT_V1_IMPLEMENTATION_PLAN.md`  
**Status:** Sprint started 2026-07-04. Phase 1 in progress.

**Phase 1 (FLC-1) — Model + migration ✅ (`14d7898`)**
- [x] `fantasy_league_context.py` — schema, CRUD, builders, ownership map
- [x] `fantasy_league_context_state` in `_WORKFLOW_KEYS` + disk hook
- [x] Lazy migration for legacy `draft_archive_teams` (single-team)
- [x] `tests/test_fantasy_league_context.py`

**FLC-2 — Save flows + library activation ✅ (`0367e02`)**
- [x] `league_rosters` capture on live draft + simulator save
- [x] Save League Context / Save Mock League Context + legacy "my team only"
- [x] Saved Draft Library badges (Full League / My Team Only / Legacy / Mock / Live)
- [x] Set Active League Context button; Clear active clears archive + context

**FLC-3 — Standings + Lineup multi-team ✅ (`5219ce5`)**
- [x] `build_roster_stats_from_league_context()` — all teams
- [x] Standings Tracker reads full league from active context
- [x] Lineup Assistant reads active context; Trade Analyzer sees 2+ teams
- [x] Cache keyed by `league_context_id`

**FLC-5 — Trade/Acquire persistence + Lineup handoff (planning)**
- [ ] Workflow CRUD (`trade_candidates`, `acquire_targets`) in `fantasy_league_context.py`
- [ ] Replace global `pending_trade_*` in `player_trade_context.py`
- [ ] Handoff: auto-nav to Lineup Assistant + `_fantasy_trade_handoff` payload
- [ ] Lineup Trade Plan chips (visible, removable)
- [ ] Per-context isolation + migration tests
- Plan: [plans/2026-07-04-fantasy-league-context-flc5.md](./plans/2026-07-04-fantasy-league-context-flc5.md)

**Phase 3 — Trade persistence + handoff**
- [ ] Per-context `trade_candidates` / `acquire_targets` (replace global `pending_trade_*`)
- [ ] Lineup Assistant Trade Plan chips
- [ ] Trade/Acquire → Lineup Assistant handoff

**Blocked (Phase 4):** Waiver Wire / Add-Drop Center until `league_rosters` + ownership map ship

**P0 — Baseball performance sprint (`baseball-stat-app` `dev`, 2026-07-05)**

**Plan:** [plans/2026-07-05-performance-transaction-workflows.md](./plans/2026-07-05-performance-transaction-workflows.md)

1. **Profiling pass (start here)** — Developer Mode → Page performance panel; record top slow phases per page.
   - [ ] Live Draft Room — pick, queue add/remove, recommendation refresh
   - [ ] Draft Assistant Simulator — scoring, settings change
   - [ ] Draft Room Simulator — board interactions
   - [ ] Draft Lab / Simulation — simulation runs
   - [ ] Waiver Wire — pool build, filters, recommendations
   - [ ] Fantasy Lineup Assistant — diagnosis bundle load
   - [ ] Saved Draft Library + page navigation — hydration, reruns

2. **Speed targets**
   - [ ] Live Draft pick + queue near-instant
   - [ ] Recommendation refresh much faster (cache + incremental invalidation)
   - [ ] Settings changes avoid full recomputes
   - [ ] Reduce repeated pool/projection/scoring builds, dataframe transforms, cloud/disk reads, full-session saves
   - [ ] Fill instrumentation gaps (`live_draft_state.py`, waiver pool, draft sim board)

2. **Persistence status (no longer P0 unless drafts disappear)** — Save Active Draft works, drafts appear in Saved Draft Library, survive refresh/reboot, Active Draft restores, Library shows expected counts, Persist OK=true.
   - [x] Explicit simulator save creates new library entry (`reuse_session_draft_id=False`)
   - [x] Cloud merge preserves richer workflow keys (`PROTECTED_WORKFLOW_PERSIST_KEYS`)
   - [x] Force-save reasons for simulator/live/archive writes
   - [x] Save/restore trace module + Developer Mode checklist (`draft_library_save_trace.py`)
   - [x] Local E2E script (`scripts/verify_saved_draft_library_e2e.py`) + runbook (`docs/SAVED_DRAFT_LIBRARY_E2E_RUNBOOK.md`)
   - [ ] Manual production sign-off on deployed `dev` (simulator + live paths)

3. **Existing performance instrumentation**
   - [x] Lineup diagnosis bundle cache (`lineup_diagnosis_bundle` — needs + waiver pool + outlook)
   - [x] Saved Draft Library load phase timing (`saved_draft_library_load`)
   - [x] Developer Mode sidebar shows last save trace + page perf breakdown

**P1 — Baseball execution workflows (`baseball-stat-app` `dev`, 2026-07-05)**

**Plan:** [plans/2026-07-05-performance-transaction-workflows.md](./plans/2026-07-05-performance-transaction-workflows.md)

**Waiver Wire execution (max 2 adds / 2 drops per transaction)**
- [ ] Select adds (≤2) + drops (≤2) with UI rule: "You can plan up to 2 adds and 2 drops at a time."
- [ ] Preview roster/category impact → Confirm → update Active Draft roster
- [ ] Persist to Saved Draft Library; reflect in Lineup, Standings, Waiver, Library
- [ ] Allowed: Add 1/Drop 1, Add 2/Drop 2 — not unlimited queue yet

**Trade Analyzer execution**
- [ ] Team A/B player selection → analyze → category/roster/standings impact
- [ ] Recommend accept/reject/counter; save/accept/reject/counter/complete flow
- [ ] On accept: move players, persist league state, update all fantasy pages
- [ ] Start simple: 1-for-1, 2-for-1, 2-for-2 (extend later)
- [ ] Leverage existing `fantasy_trade_proposals.py` accept/roster swap path

**P1 polish (parallel after P0 hot paths)**
- [ ] Fantasy Assistant / Waiver Wire UX — compact cards, team-needs summary, confidence/impact estimates

**Later — Command Center transaction integration**
- [ ] Activity: waiver move, add/drop, trade proposed/accepted/rejected/completed
- [ ] Continue cards: waiver plan, trade proposal, trade analysis, active league

**P2 — Baseball diagnostics cleanup (`baseball-stat-app` `dev`, 2026-07-05)**

- [ ] Separate Last Save Trace vs Last Activation Trace
- [ ] Soften cloud/disk wording in local/demo mode
- [ ] Refresh restore-source labels after disk-first/demo decisions
- [ ] Clean up misleading checklist failures when persistence is already confirmed

**P1 — Fantasy Lineup Assistant polish (2026-07-05, in progress on `dev`)**
- [x] Team Outlook “why” bullets (strengths + concerns below rating)
- [x] Clearer partial-roster slot message (“Lineup analysis is from a partial roster…”)
- [x] Waiver targets filtered to actual waiver pool / active league rosters (empty-state copy when none)
- [x] Action buttons use canonical page icons (`page_option_label`)
- [ ] Manual verify on deployed `dev` after next push

### Deferred — AMI Baseball Draft Intelligence

Resume after Importer v1 or narrow draft fixes when blocked.

**Master plan (workspace/auth/LDR):** [plans/2026-06-19-workspace-profiles-real-accounts-live-draft-room.md](./plans/2026-06-19-workspace-profiles-real-accounts-live-draft-room.md)

---

# Project Description

Central hub repo (`daniel-ai-command-center`) for suite homepage, activity aggregation, Supabase account memory, and shared modules synced to sibling apps.

---

# Current Priorities

See task sections above (Sprint B → C → D gate → Importer scaffolding).

### P2 (parallel) — AMI Enhancement Program (not blocked by Account Settings)

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
| [plans/2026-07-05-performance-transaction-workflows.md](./plans/2026-07-05-performance-transaction-workflows.md) | **Active P0** — Baseball perf + waiver/trade execution |
| [plans/2026-07-04-fantasy-league-context-v1.md](./plans/2026-07-04-fantasy-league-context-v1.md) | FLC v1 — persistence stable; execution sprint active |
| [plans/2026-06-19-account-settings-real-problem-importer-roadmap.md](./plans/2026-06-19-account-settings-real-problem-importer-roadmap.md) | Superseded order — Importer now after Real Accounts |
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
