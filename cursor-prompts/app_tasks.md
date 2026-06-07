# Current Tasks — Daniel AI Command Center

**Last updated:** 2026-06-07

Actionable work items. Master context: [app_roadmap.md](./app_roadmap.md).

---

# Project Description

Central hub repo (`daniel-ai-command-center`) for suite homepage, activity aggregation, Supabase account memory, and shared modules synced to sibling apps.

---

# Current Priorities

**Focus: reliability and usefulness — no new features until stable.**

### P1 — Command Center quality filtering (Continue vs App Directory)

- [x] Workflow classification audit — [plans/command-center-workflow-classification-audit.md](./plans/command-center-workflow-classification-audit.md)
- [ ] User review classification table before ranking changes
- [ ] Implement event-type tags (Continue / Directory / Both / Neither)
- [ ] Fix top misclassifications: `song_selected`, `holdings_updated`, Future Lens/NBA gaps
- [ ] Enrich Directory with durable state from cloud `full_session`

### P2 — Persistence reliability

- [x] Deep audit — [plans/suite-session-persistence-audit.md](./plans/suite-session-persistence-audit.md)
- [x] Baseball restore-before-resume (shipped `16fbe29`)
- [x] AMI cloud reset (shipped `32c2158`)
- [ ] P0 fixes: Music non-core override, Future Lens early restore + `_suite_fl_sim`, NBA team widget
- [ ] P1: Music custom progression keys, Investment cloud_resync promotion
- [ ] E2E smoke: refresh / reboot / cross-device per app

### P3 — Investment UI transparency (audit first, no formula changes)

- [x] Calculation audit — [plans/investment-macro-return-volatility-audit.md](./plans/investment-macro-return-volatility-audit.md)
- [x] Wording mockups — [plans/investment-ui-transparency-mockups.md](./plans/investment-ui-transparency-mockups.md)
- [ ] User review mockups (inline captions vs banners, label renames)
- [ ] Implement approved copy only — no formula changes

### P4 — Future work (not now)

- Applied Math solving quality
- Future Lens analytical question support
- Music → Applied Math support
- Command Center coaching improvements
- Investment forward-looking modeling improvements

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

*See [app_roadmap.md](./app_roadmap.md) and [app_feature_backlog.md](./app_feature_backlog.md).*

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

### Active plans

| Plan | Status |
|------|--------|
| [plans/README.md](./plans/README.md) | Folder ready — add plans as work starts |
| [plans/command-center-workflow-classification-audit.md](./plans/command-center-workflow-classification-audit.md) | P1 — Continue vs Directory |
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
