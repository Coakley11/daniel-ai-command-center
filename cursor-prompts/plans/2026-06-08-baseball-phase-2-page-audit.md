# Baseball Phase 2 — Full Page Audit & Canonical State

**Last updated:** 2026-06-08  
**Status:** Active — reference implementation before suite-wide port  
**Repos:** `baseball-stat-app` (primary), `daniel-ai-command-center` (shared suite modules)  
**Branch:** `dev`

---

## Goal

Turn Baseball into the **reference implementation** for page ownership, cross-device sync, cloud restore, navigation, and Applied Math Insight (AMI) returns — then port the same protocol to Music, NBA, Investment, and Applied Intelligence.

**Exit gate:** All major Baseball pages pass acceptance tests A–E before any cross-app port begins.

---

## Reference architecture (Trend + Comparison)

These two pages are the canonical model. Every complex page should converge on this pattern.

### Lifecycle

```
prepare_*_page()           # before widgets render
  → gather from canonical blob / widget keys / page_filter_state / pending_*
  → write_canonical_*_state()  # mirror widgets + page_filter_state block
  → if user edit: mark_*_local_edit()

On sidebar leave:  page_state.save_page_state → page_filter_state[page]
On sidebar return: restore_*_page_filters() — blocked if dirty
On cloud restore:  apply_baseball_disk_state → write_canonical + clear dirty (if allowed)
On widget change: sync_* → write_canonical(..., local_edit=True)
On AMI return:     apply_*_source_state_from_ami() — canonical write, no re-nav after consume
```

### Required module API

Each canonical page-state module must export:

| Function | Purpose |
|----------|---------|
| `prepare_*_page(session)` | Seed widgets from canonical/disk/cloud; respect dirty flag |
| `write_canonical_*_state(session, ..., reason=, local_edit=)` | Single write path to canonical blob + widget mirrors |
| `restore_*_page_filters(session, snapshot)` | Restore from `page_filter_state`; return `False` if dirty |
| `is_*_locally_dirty(session)` | Dirty ownership check |
| `mark_*_local_edit(session)` / `clear_*_local_edit(session)` | Local edit beats restore |
| `apply_*_source_state_from_ami(session, source_state)` | AMI return restore without page lock |
| `apply_cloud_*_state_if_allowed(session, cloud_blob)` | Cloud newer protection |
| `render_*_state_debug(session)` | `?dev=1` diagnostics panel |

### Ownership rules (global)

| Rule | Behavior |
|------|----------|
| **Local user edit** | Beats restore on same device (`*_state_dirty` blocks overwrite) |
| **Newer cloud** | Beats stale disk/default (`pick_restore_session`, `cloud_newer_than_applied`) |
| **Manual page nav** | Beats cloud page mismatch (`claim_user_page_ownership`, `_suite_user_owned_page`) |
| **AMI return** | Hydrates once, consumes resume, never forces navigation again |
| **Insight rendering** | Only on normalized `source_page`; never forces `active_page` after consume |

### Shared infrastructure (already shipped)

- `baseball_persistent_state.py` — `build_baseball_disk_state`, `apply_baseball_disk_state`, `prepare_baseball_workspace`
- `suite_user_persistence.py` — `sync_workspace_protocol`, `claim_user_page_ownership`, page-change cloud save
- `applied_math_return_insight.py` — insight hydrate, consume, scope-by-page
- `applied_math_context.py` — `build_source_state`, `apply_source_state_to_session`
- `page_state.py` — `PAGE_STATE_REGISTRY`, generic save/restore for non-canonical pages

---

## Sidebar inventory (14 pages)

| # | Page | Canonical module | AMI insight eligible | Contextual transfer |
|---|------|------------------|---------------------|---------------------|
| 1 | Historical Explorer | `historical_state.py` (new) | Yes | No |
| 2 | Career Totals | `career_totals_state.py` (new) | No | No |
| 3 | Leaderboards | `leaderboards_state.py` (new) | No | No |
| 4 | Comparison Tool | `comparison_state.py` ✅ | Yes | Yes |
| 5 | Trend Value | `trend_state.py` ✅ | Yes | Yes |
| 6 | Valuation | `valuation_state.py` (new) | No | Yes |
| 7 | ML Predictions | `projections_state.py` (new) | No | No |
| 8 | Fantasy Sleepers & Busts | `fantasy_state.py` (new) | No | No |
| 9 | Draft Room Simulator | `draft_state.py` (new) | Yes | No |
| 10 | Draft Assistant Simulator | `draft_state.py` (shared) | Yes | No |
| 11 | Draft Simulation Test Mode | `draft_state.py` (shared) | Yes | No |
| 12 | Live Draft Room | `draft_state.py` (shared) | Yes | No |
| 13 | Fantasy Standings Tracker | `fantasy_state.py` (shared) | No | No |
| 14 | Fantasy Lineup Assistant | `fantasy_state.py` (shared) | No | No |

**Not in sidebar but needs persistence:** Watchlist (`workflow_favorite_targets`, `draft_assistant_focus_players`), Draft Queue (`draft_queue`) — currently session-only via `workflow_sidebar.py`.

---

## Per-page state classification template

For each page, audit and document:

| Field / widget group | Local-only | Cross-device | Cloud blob key | AMI source_state | AMI return restore | Notes |
|---------------------|------------|--------------|----------------|------------------|-------------------|-------|
| *(fill per page)* | | | | | | |

### Classification legend

- **Local-only** — ephemeral, derived, or too large (e.g. `ml_predictions_df`)
- **Cross-device** — must survive phone ↔ Dell refresh
- **Cloud-persisted** — in `full_session` via `build_baseball_disk_state`
- **AMI source_state** — captured by `build_source_state(page, session)`
- **Page restore** — restored on sidebar return or disk/cloud apply

---

## Page-by-page audit checklist

### Priority 1 — Career Totals

**Registry keys** (`page_state.py`): `career_year*`, `career_sort*`, `career_bats`, `career_pos*`, `career_team`, `career_by_team_toggle`

| Task | Status |
|------|--------|
| Inventory widget keys vs registry (grep `streamlit_app.py` Career section) | ☐ |
| Create `career_totals_state.py` with canonical pattern | ☐ |
| Add `career_state` to disk blob + `baseball_workspace_state` envelope | ☐ |
| Wire `prepare_career_totals_page` before widgets | ☐ |
| Dirty flag + cloud restore protection | ☐ |
| AMI: extend `build_source_state` with filter snapshot | ☐ |
| Acceptance A–E | ☐ |

### Priority 2 — Draft / Draft Queue

**Pages:** Draft Room Simulator, Draft Assistant, Draft Sim Test Mode, Live Draft Room  
**Registry keys:** `draft_*`, `room_*`, `live_draft_*`, `live_slot_*`  
**Global keys in disk blob:** `draft_room_table`, `room_your_team`, `room_team_count`, `room_rounds`, `room_format`

| Task | Status |
|------|--------|
| Fix envelope mismatch: `"Draft Room"` vs `"Draft Room Simulator"` in `_build_workspace_envelope` | ☐ |
| Create `draft_state.py` (shared across 4 draft pages) | ☐ |
| Persist `draft_queue` + watchlist keys in disk/cloud blob | ☐ |
| `apply_draft_source_state_from_ami` for queue restore | ☐ |
| Add Draft Room to `PAGE_STATE_DEBUG_PREFIXES` | ☐ |
| Acceptance A–E on Draft Room + Live Draft | ☐ |

### Priority 3 — Watchlist

**Keys:** `draft_assistant_focus_players`, `workflow_favorite_targets` (from `workflow_sidebar.py`)

| Task | Status |
|------|--------|
| Create `watchlist_state.py` or fold into `draft_state.py` | ☐ |
| Add to `build_baseball_disk_state` | ☐ |
| Cross-device acceptance B | ☐ |

### Priority 4 — Player pages / Historical Explorer

**Historical Explorer** has partial AMI support (`_ami_historical_snapshot`) but no canonical module.

| Task | Status |
|------|--------|
| Create `historical_state.py` | ☐ |
| Promote snapshot to canonical blob | ☐ |
| Acceptance A–E | ☐ |

### Priority 5 — Fantasy / Projection pages

**Pages:** Valuation, ML Predictions, Fantasy Sleepers, Standings, Lineup  
**Note:** `ml_predictions_df` intentionally excluded from persistence (large derived data)

| Task | Status |
|------|--------|
| Create `projections_state.py` (ML Predictions + Valuation shared chart keys) | ☐ |
| Create `fantasy_state.py` (Sleepers, Standings, Lineup) | ☐ |
| Document which derived keys stay local-only | ☐ |
| Acceptance A–E per page | ☐ |

### Priority 6 — Remaining pages

**Leaderboards** — small filter set; candidate for lightweight `leaderboards_state.py` or enhanced registry only.

**Comparison gap:** Add `apply_comparison_source_state_from_ami` (Trend parity — today uses `pending_compare_players` only).

---

## Cross-device acceptance tests (per page)

Run on phone + Dell after each page module ships.

### A. Local persistence
1. Edit filters/selections on page
2. Rerun (F5)
3. **Pass:** values remain

### B. Cross-device
1. Edit on phone
2. Refresh Dell (or vice versa)
3. **Pass:** same state restored from cloud

### C. Cloud protection
1. Cloud has newer state than local disk
2. Open app with stale local defaults
3. **Pass:** cloud wins; local blank state cannot erase cloud players/filters

### D. Navigation
1. Open app → navigate to page under test
2. Switch to 2 other pages and back
3. **Pass:** no bounce, no page lock, `final_page` matches selection

### E. Applied Math (eligible pages only)
1. Configure page state → send AMI question
2. Return to Baseball
3. **Pass:** state preserved, insight visible only on source page, sidebar nav free after first render

---

## Implementation sprints

### Sprint 1 — Foundation (shipped 2026-06-08)
- [x] Page navigation ownership (`claim_user_page_ownership`, reconcile stale nav)
- [x] Cloud insight hydrate no longer forces page
- [x] AMI return consume on page match
- [x] Baseball sidebar wired

### Sprint 2 — Career Totals + Comparison AMI parity (shipped 2026-06-08)
- [x] `career_totals_state.py`
- [x] `apply_comparison_source_state_from_ami`
- [x] Tests: `test_career_totals_state.py`, extend `test_comparison_state.py`
- [ ] Manual acceptance A–E on phone + Dell

### Sprint 3 — Draft cluster
- [ ] `draft_state.py` + watchlist/queue persistence
- [ ] Fix Draft Room envelope key
- [ ] Tests + manual acceptance

### Sprint 4 — Historical + Valuation + ML
- [ ] `historical_state.py`, `valuation_state.py`, `projections_state.py`
- [ ] Tests + manual acceptance

### Sprint 5 — Fantasy cluster + Leaderboards
- [ ] `fantasy_state.py`, `leaderboards_state.py`
- [ ] Full Baseball acceptance matrix sign-off

### Sprint 6 — Reference doc + suite port plan
- [ ] Document final architecture in `docs/BASEBALL_PAGE_STATE_PROTOCOL.md` (baseball repo)
- [ ] Port checklist for Music / NBA / Investment / Applied Intelligence

---

## Suite port gate (do not start until Baseball passes)

| App | Port when | Notes |
|-----|-----------|-------|
| Music Practice Coach | Baseball Sprint 6 complete | Studio pages + song catalog state |
| NBA Companion | Baseball Sprint 6 complete | Team, LGC, Legacy Tracker sub-state |
| Investment Analyzer | Baseball Sprint 6 complete | Portfolio health, holdings |
| Applied Intelligence | Baseball Sprint 6 complete | Lesson/question session state |

Shared modules to extend during port: `suite_user_persistence.py`, `suite_cloud_state.py`, `applied_math_return_insight.py` — app-specific `*_state.py` modules live in each sibling repo.

---

## Known gaps from Phase 1 inventory

1. **Watchlist / draft queue** — not in disk blob
2. **Draft Room envelope** — key name mismatch
3. **Comparison AMI restore** — no canonical applier (Trend has one)
4. **ML Predictions df** — intentionally local-only; document in audit
5. **Generic-only pages** — registry may drift from actual widget keys in `streamlit_app.py`

---

## Files to create (baseball-stat-app)

```
career_totals_state.py
draft_state.py
watchlist_state.py
historical_state.py
valuation_state.py
projections_state.py
fantasy_state.py
leaderboards_state.py
tests/test_career_totals_state.py
tests/test_draft_state.py
tests/test_historical_state.py
docs/BASEBALL_PAGE_STATE_PROTOCOL.md
```

---

## Sync workflow

After any `suite_*` or `applied_math_return_insight.py` change in command center:

```bash
python scripts/sync_suite_cloud_modules.py
```

Commit both repos; reboot Streamlit Cloud dev deployments.
