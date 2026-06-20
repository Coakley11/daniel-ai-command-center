# Completed Features — Daniel AI Command Center

**Last updated:** 2026-06-19

---

# Project Description

Historical record of shipped Command Center and shared-suite infrastructure capabilities.

---

# Current Priorities

*None — this file is the historical record. See [app_tasks.md](./app_tasks.md) for active work.*

---

# Next Features

*See [app_feature_backlog.md](./app_feature_backlog.md).*

---

# Long-Term Vision

*See [app_roadmap.md](./app_roadmap.md).*

---

# Completed Features

### AMI persistence & workspace sync (2026-06-19)

- [x] AMI UI-state cloud persistence (`_ami_ui_state`, `mie_*`/`ps_*` keys) — `maybe_persist`, one-shot reapply fix (`87d2785`)
- [x] Cloud-first workspace restore; Explore + session activity to Command Center
- [x] CC workspace activity namespace diagnostics; `analytical_question` in weekly stats
- [x] Tests: `test_applied_intelligence_ui_cloud_persist.py`, `test_workspace_cc_activity.py`

### Account Settings UX — Sprint A (2026-06-20)

- [x] `suite_account_settings.py` — identity summary, scoped cloud key preview, namespace mismatch warnings
- [x] Command Center — global workspace badge (sidebar), Account & workspace panel (homepage)
- [x] Password reset stub (Real Accounts Phase 2)
- [x] Tests: `test_account_settings_panel.py`; extended `test_workspace_cc_activity.py`, `test_suite_workspace.py`
- [x] FutureLens workspace validation — 10 passed in sibling repo

### Workspace Profiles v1 — Phase 1 foundation (2026-06-19)

- [x] `suite_workspace.py` — presets (Daniel, Ariel, Guest, Test User), normalization, legacy migration to Daniel workspace dir
- [x] Workspace-scoped disk paths — `data/workspaces/{workspace_id}/{app}_user_state.json` via `suite_user_persistence.py`
- [x] Cloud app id scoping — `scoped_cloud_app_id()` (`investment__ariel`, etc.) for Supabase isolation
- [x] Command Center profile switcher — sidebar selector, workspace badge in hero, dev-tools gating for Daniel workspace
- [x] Deep links — `suite_workspace` query param on Continue/Open URLs (`suite_deep_links.py`, `suite_resume_launch.py`)
- [x] Activity/resume reads filtered by active workspace (`suite_storage_supabase.py`, `test_workspace_cc_activity.py`)
- [x] Tests: `test_suite_workspace.py` (normalization, paths, migration, cloud keys, selector)
- [x] **Mostly validated across apps:** Command Center, Investment, Baseball, Applied Math, Music, **NBA** (2026-06-19)

### Workspace Profiles v1 — NBA Companion AI (2026-06-19)

- [x] `workspace_id → nba → state` — scoped disk paths, cloud keys (`nba__ariel`), activity writes with `workspace_id`
- [x] Team selector persistence — profile defaults (Daniel→Knicks, Ariel→Celtics), no Hawks reset on refresh
- [x] Shell-first Fast Load — defer cloud sync, usable startup without forced team reset
- [x] Command Center activity isolation — scoped fallback files, Ariel/Daniel feed filtering
- [x] Daniel-only startup diagnostics; developer tools hidden for non-Daniel workspaces
- [x] User validation PASS — team persistence, workspace separation, CC activity isolation, Fast Load

### Workspace Profiles v1 — FutureLens (2026-06-19, pending validation)

- [x] `prepare_future_lens_workspace()` — `sync_workspace_protocol`, disk shell restore, startup flag clearing on profile switch
- [x] `init_suite_workspace` + workspace bootstrap in `future_lens_boot.py`
- [x] Activity writes tag `workspace_id`; scoped fallback paths in `suite_activity_client.py`
- [x] Cloud keys via `scoped_cloud_app_id` (`future_lens__ariel`); disk `data/workspaces/{id}/future_lens_user_state.json`
- [x] Command Center — `future_lens` in workspace-scoped fallback import filter; CC activity/resume read tests
- [x] Tests: `test_future_lens_workspace.py`, extended CC workspace activity tests
- [ ] **User validation pending** — Daniel vs Ariel domain/area/sim, Continue/Directory, CC feed isolation

### Baseball AMI Phase 1 — Draft context depth (2026-06-11)

- [x] `draft_ami_helpers.py` — JSON-safe recommendation/sleeper rows, live draft section gather, page-specific AMI guidance
- [x] `cache_draft_assistant_ami_context` — roster needs, category needs, scarcity, best available, canonical board
- [x] `cache_live_draft_ami_context` — round/pick, my next pick, recommendations, latest picks, queue/watchlist
- [x] `cache_fantasy_sleepers_ami_context` — sleeper candidates, bust risks, drafted exclusions, roster needs
- [x] Streamlit hooks on Draft Assistant, Live Draft Room, Fantasy Sleepers pages
- [x] Tests: `test_draft_ami_helpers.py`, extended `test_applied_math_context.py`

### Baseball Career Totals canonical state (2026-06-08)

- [x] `career_totals_state.py` — canonical filters, dirty flags, cloud restore, AMI return, `?dev=1` debug panel
- [x] `baseball_persistent_state.py` — `career_state` in disk blob + workspace envelope; user-nav page preservation fix
- [x] `apply_comparison_source_state_from_ami` — Comparison Tool AMI return uses canonical applier (Trend parity)
- [x] Tests: `test_career_totals_state.py` (acceptance A–E unit coverage), extended comparison/applied_math tests

### Baseball workspace sync & navigation (2026-06-08)

- [x] AMI return page-lock fix — consume resume, clear stale `_navigate_to_page` (CC `5477743`)
- [x] Page navigation ownership — `claim_user_page_ownership`, cloud overwrite protection (CC `4d2205b`)
- [x] Baseball sidebar wired to `claim_user_page_ownership` (baseball-stat-app `a293b34`)
- [x] Cloud insight hydrate no longer forces page navigation
- [x] Tests: `test_page_navigation_ownership.py`, `test_ami_resume_consume.py` (43 passed)

### Homepage UI (`ai_command_center.py`)

- [x] Wide-layout Streamlit page with custom CSS (hero gradient, cards, feed styling)
- [x] Hero banner with build version and live/waiting activity tag
- [x] **Continue where you left off** — up to 6 cards, 3-column grid, Continue link buttons
- [x] Recently used apps caption + last opened app/page
- [x] **Suite focus** — cross-app weekly insight cards (`project_intelligence.py`)
- [x] **Coach Insights** — prioritized actionable messages (`coach_engine.py`)
- [x] **Activity** section — executive dashboard: **Today's Work**, **Highlights**, **Recent Activity** with rollups (`build_activity_dashboard`)
- [x] **UTC activity timestamps** — `activity_time.py` (write, parse, normalize, relative display)
- [x] **Weekly Summary** — accomplishment lines from real events
- [x] **App Directory** — 6 apps, themed cards, highlights, Open buttons
- [x] **Deployment & link audit (admin)** expander — secrets probe, Supabase diagnostics, Phase A tables, connection table
- [x] `homepage_sections.py` — import-safe loaders for tests and tooling

### App registry & URLs

- [x] `app_registry.py` — six `AppDefinition` entries with status, GitHub, Streamlit URLs
- [x] `app_urls.py` — verified viewer URLs, deploy paths, `BUILD_VERSION`
- [x] `app_branding.py` — per-app theme colors and emojis
- [x] `verify_connections()` — HTTP live check for Streamlit viewer URLs

### Activity pipeline

- [x] `activity_store.py` — snapshot loading, weekly summary, directory card highlights
- [x] `activity_feed.py` — human-readable messages, noise suppression, dedupe, rollups, highlights
- [x] `activity_feed.py` — `ActivityDashboard` (Today's Work, Highlights, Recent rollups)
- [x] `activity_time.py` — UTC normalization, `sort_key_for_event`, relative display (`format_activity_display_time`)
- [x] `activity_models.py` — `ActivityFeedItem`, `ActivityDashboard` (import-safe types module)
- [x] Supabase `load_events` — filter by `user_id`, order by `timestamp.desc`, normalize timestamps
- [x] SQLite account migrations — `user_id` columns, composite PK/UNIQUE, index-after-migrate fix
- [x] `activity_diagnostics.py` — live pipeline diagnostics for admin panel
- [x] Phase A verification tables: Music, Investment, Baseball, NBA, Applied Intelligence, Future Lens

### Intelligence & continue

- [x] `project_intelligence.py` — project continue cards, cross-app insights, weekly accomplishment lines
- [x] `continue_dashboard.py` — `ContinueCard` builder with resume fallback from `load_current_states()`
- [x] `coach_engine.py` — per-app coach rules (baseball Sunday lineup, music chart follow-ups, etc.)

### Suite storage & cloud

- [x] `suite_storage.py` — unified read API (local JSON + cloud)
- [x] `suite_storage_config.py` — secrets resolution, expected TOML template
- [x] `suite_storage_supabase.py` — PostgREST client for events, current state, resume items
- [x] `suite_activity_client.py` — `record_activity()` write path
- [x] `suite_account.py` — account summary for admin UI
- [x] `suite_user.py` — user id resolution
- [x] Supabase migrations `001`–`003` under `supabase/migrations/`
- [x] Cloud `full_session` persistence helpers (`suite_cloud_state.py`)
- [x] `suite_user_persistence.py` — local disk state, reset controls pattern (synced to apps)
- [x] `suite_deep_links.py` + `suite_resume_launch.py` — Continue URL query param handling

### Scripts & ops

- [x] `scripts/sync_suite_cloud_modules.py` — copy shared modules to 6 sibling repos
- [x] `scripts/verify_account_memory.py`, `verify_live_activity.py`, `verify_imports.py`
- [x] `scripts/migrate_sqlite_to_supabase.py`, `inject_test_music_event.py`
- [x] `scripts/resolve_deploy_urls.py`, `verify_public_apps.py`, `verify_homepage_links.py`
- [x] `scripts/print_suite_secrets_checklist.py`, `setup_homepage_dev.py`
- [x] `scripts/sync_suite_branding.py` + `branding/` pack

### Documentation

- [x] `docs/SUITE_DEV_DEPLOY.md` — secrets, branch `dev`, 7-app matrix
- [x] `docs/SUITE_CLOUD_ACTIVITY.md` — Supabase data model
- [x] `docs/SUITE_ACCOUNT_MEMORY.md`, `ACTIVITY_TRACKING_AUDIT.md`, `DEPLOYMENTS.md`
- [x] `docs/MUSIC_APP_VS_COMMAND_CENTER.md`

### Tests

- [x] Activity feed: noise, priority, executive, music-specific, dashboard (local)
- [x] Phase A: music, investment, baseball activity wiring
- [x] Suite storage, cloud state, account memory, project intelligence
- [x] Import smoke, app branding, homepage sections

### Baseball Stat App — Phase 2 canonical state (2026-06-08)

- [x] **Career Totals** — `career_totals_state.py`; sync trace; force cloud save; phone↔Dell acceptance **PASS** (`be91f64`)
- [x] **Comparison AMI parity** — `apply_comparison_source_state_from_ami`
- [x] **Draft Workflow** — `draft_state.py`; queue + watchlist disk/cloud/AMI; acceptance **PASS** (`a569612`)
- [x] **Historical Explorer** — `historical_state.py`; filters + stat mins; AMI round-trip; acceptance **PASS** (`7647f61`)
- [x] **Valuation + ML Predictions** — `valuation_state.py`, `projections_state.py`; scope/tuning/display/pipeline; AMI insight eligible; acceptance **PASS** (`b29a512`, AMI fix `51df10e`)
- [x] **Fantasy cluster + Leaderboards** — `fantasy_state.py`, `leaderboards_state.py`; AMI eligible + return fix; acceptance **PASS** (`bb9ecb5`, AMI `ab8faef`)
- [x] **Phase 2 final acceptance sweep** — 14/14 pages PASS; protocol + matrix docs; 147 automated tests; **tag `baseball-sync-reference-v1`**

1. **Standalone homepage prototype** — hero + app cards + placeholder-friendly empty states
2. **Real activity ingestion** — SQLite local + Supabase cloud dual mode
3. **Coach + continue intelligence** — no duplicate fact lines in coach section
4. **Account memory + resume** — unified `suite_user_id`, deep links, `suite_resume_launch`
5. **Cloud full_session** — cross-device session persistence contract for sibling apps
6. **Activity executive dashboard (Phase B)** — Today's Work / Highlights / Recent rollups — build `2026-06-03-v30`
7. **Roadmap system** — `cursor-prompts/` + Cursor rule (2026-06-03)
8. **Import hotfix (v31)** — `activity_models.py`; `ActivityFeedItem` imported before `activity_feed`; `activity_time` fallback in `activity_feed`

---

# Notes

- Sibling app features (Music practice studio, Baseball Lahman tools, etc.) are **not** listed here — only Command Center and shared suite modules in this repo.
- Uncommitted locally (separate from Phase B): `suite_cloud_state.py`, `suite_user_persistence.py` restore/debug improvements — sync when ready.
