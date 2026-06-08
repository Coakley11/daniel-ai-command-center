# Sprint 7 — Suite Port (Baseball Reference → Sibling Apps)

**Last updated:** 2026-06-08  
**Status:** Active  
**Reference:** Baseball tagged `baseball-sync-reference-v1` on `dev`  
**Protocol:** `baseball-stat-app/docs/BASEBALL_PAGE_STATE_PROTOCOL.md`  
**Matrix template:** `baseball-stat-app/docs/BASEBALL_ACCEPTANCE_MATRIX.md`

**Rule:** No new product features during port. Architecture migration only.

---

## Port order

| # | App | Repo | APP_ID |
|---|-----|------|--------|
| 1 | Music Practice Coach | `ai-music-practice-coach` | `music` |
| 2 | NBA Playoff Companion | `nba-playoff-companion-ai` | `nba` |
| 3 | Investment App | `investment-portfolio-analyzer` | `investment` |
| 4 | Applied Intelligence / Calculus | `Applied-mathematical-intelligence` | `applied_intelligence` or app-specific |

---

## Per-app phases (repeat for each app)

### Phase A — Acceptance audit

- [ ] Page inventory (sidebar / tabs / major views)
- [ ] State inventory (widget keys, session keys, disk blob shape)
- [ ] AMI inventory (eligible pages, `build_source_state`, apply paths)
- [ ] Navigation inventory (sidebar ownership, cloud page mismatch, resume URLs)
- [ ] Gap doc: canonical vs generic-only vs local-only keys

### Phase B — Shared suite modules

Sync from Command Center via `scripts/sync_suite_cloud_modules.py`:

- [ ] `suite_user_persistence.py`
- [ ] `suite_cloud_state.py`
- [ ] `applied_math_return_insight.py`
- [ ] `suite_analytical_question.py`
- [ ] `suite_deep_links.py`
- [ ] `suite_resume_launch.py`

Verify after sync:

- [ ] Force-save bypass reasons for app-specific `*_edit` reasons
- [ ] `claim_user_page_ownership` intact (no accidental strip)
- [ ] App boots with `prepare_*_workspace()` before sidebar

### Phase C — Canonical page-state modules

For each major page/cluster:

- [ ] `{page}_state.py` (or `{app}_persistent_state.py` envelope)
- [ ] Local edit > restore (`*_state_dirty`)
- [ ] Newer cloud > stale disk (`apply_cloud_*_if_allowed`)
- [ ] Manual nav > cloud mismatch (`claim_user_page_ownership`)
- [ ] AMI hydrate once (`consume_ami_return_resume`)
- [ ] Insight only on source page (`INSIGHT_ELIGIBLE_PAGES`)
- [ ] Tests A–E per module (`tests/test_*_state.py`)

### Phase D — Manual acceptance

- [ ] Phone ↔ Dell sync (filters / selections)
- [ ] AMI send → return → insight on source page only
- [ ] Dismiss insight cross-device
- [ ] No page bounce after AMI consume
- [ ] Final acceptance matrix (PASS/FAIL by page)

---

## App-specific starting points

### 1. Music Practice Coach

**Likely first canonical modules:** studio session state, song catalog / CPL bar, non-core song selection.

**Existing:** partial persistence (`_cpl_widget_state`), cloud sync, non-core override fix.

**Audit focus:** song selection ownership, studio widget keys, AMI from practice/analysis pages.

### 2. NBA Playoff Companion

**Likely first modules:** Legacy Tracker player, Live Game Center team, LGC manual/matchup keys.

**Existing:** team widget persistence, `_nba_restore_error`, LGC dynamic keys.

**Audit focus:** Knicks default guard, cross-page player focus, AMI from matchup/legacy pages.

### 3. Investment App

**Likely first modules:** Portfolio health tab, holdings, scenario/macro inputs.

**Existing:** cloud drift reconcile, EOR autosave guard, holdings persistence.

**Audit focus:** tab ownership, macro assumption keys, AMI from health/analytics pages.

### 4. Applied Intelligence / Calculus

**Likely first modules:** lesson session, question bank progress, calculator inputs.

**Audit focus:** session vs lesson state, AMI from lesson/question pages.

---

## Shared modules reference (auto-sync)

See `BASEBALL_PAGE_STATE_PROTOCOL.md` § Suite port — modules by app.

## Exit criteria (Sprint 7 complete)

- [ ] All four apps: Phase A–D complete
- [ ] Per-app `{APP}_PAGE_STATE_PROTOCOL.md` or pointer to baseball reference
- [ ] Per-app acceptance matrix
- [ ] Command Center roadmap updated
