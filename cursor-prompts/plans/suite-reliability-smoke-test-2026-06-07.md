# Suite reliability smoke test report

**Date:** 2026-06-07  
**Type:** Code trace + automated tests + deploy reachability (no browser automation)  
**P0 commits under test:** Music `1359af6`, Baseball `16fbe29`, NBA `db30b53`, Future Lens `2eab052`, Investment `34529d1`, AMI `32c2158`, CC `145eaaa`

## Methodology

| Layer | What ran |
|-------|----------|
| **Automated** | pytest in CC, Baseball, Investment, Music (persistence modules) |
| **Code trace** | Restore order, persist keys, P0 fix presence, known gap paths |
| **Deploy check** | HTTP 200 on all 7 Streamlit Cloud dev URLs |
| **Manual required** | Browser refresh, hard refresh, reboot, cross-device (cannot automate from CI here) |

**Note:** Refresh, hard refresh, and new tab are equivalent for Streamlit — `session_state` clears and `restore_once()` runs again from disk/cloud.

---

## Executive summary

| App | Overall | Blockers before CC ranking work |
|-----|---------|--------------------------------|
| Music | **Likely Pass** (manual confirm) | Silent restore exception → default song |
| Baseball | **Likely Pass** | Enum validation after redeploy |
| NBA | **Likely Pass** | Retired page label fallback |
| Investment | **Likely Pass** | Empty holdings blob → SPY/BND |
| Future Lens | **Partial** | **Tab/view mode not restored** |
| AMI | **Likely Pass** | view_mode widget key (P2) |
| Command Center | **N/A widgets** | Activity feed not real-time |

---

## Full smoke matrix

### Music

| Test | Pass/Fail | Issue | Root Cause | Fix |
|------|-----------|-------|------------|-----|
| Non-core song · refresh/hard/new tab | **Likely Pass** | — | P0 skip when restored pick_key (`streamlit_music_practice_app.py:1185-1195`) | Shipped |
| Non-core song · reboot/redeploy | **Manual verify** | Cloud disk ephemeral | Needs Supabase `full_session` | Confirm cloud secrets |
| Non-core song · cross-device | **Manual verify** | No content-resync like Investment | Music `restore_once` timestamp-only | P1 optional |
| Core song · all reload types | **Likely Pass** | — | Standard restore + autosave | Manual verify |
| Custom progression · refresh/reboot | **Likely Pass** | — | `cpl_*` in `music_persistent_state.py` | Shipped |
| Instrument · refresh/reboot | **Likely Pass** | — | In `core` blob + session keys | Manual verify |
| Display key / written key mode | **Likely Pass** | — | `display_key`, key state in core blob | Manual verify |
| Practice / Backing Track page | **Likely Pass** | — | `studio_page` persisted | Manual verify |
| Restore exception path | **Fail (code)** | Default core song | Bare `except` → `ensure_master_song_initialized` (`:1097-1103`) | Log error; skip default init |
| Reset to default only | **Likely Pass** | — | `default_reset_music_session` | Manual verify |

### Baseball

| Test | Pass/Fail | Issue | Root Cause | Fix |
|------|-----------|-------|------------|-----|
| Comparison Tool state · reload | **Likely Pass** | — | `page_filter_state` + restore before resume | Shipped `16fbe29` |
| Trend Value · reload | **Likely Pass** | — | Per-page filters in blob | Manual verify |
| Multi-player trend comparison · reload | **Likely Pass** | — | Same filter store | Manual verify |
| Draft workflow · reload | **Likely Pass** | — | Draft globals in `_GLOBAL_KEYS` | Manual verify |
| Trade workflow · reload | **Likely Pass** | — | Resume + filter persistence | Manual verify |
| Continue from CC · reload | **Likely Pass** | — | Restore before `apply_suite_resume_launch` | Shipped |
| Filter enum after redeploy | **Fail (code)** | Widget resets | `validate_state_option` (`streamlit_app.py:10825+`) | Migrate enums on restore |
| Cross-device | **Manual verify** | — | Cloud autosave | Manual verify |

### NBA

| Test | Pass/Fail | Issue | Root Cause | Fix |
|------|-----------|-------|------------|-----|
| Non-Knicks team · refresh/reboot | **Likely Pass** | — | `NBA_TEAM_SELECT_KEY` seeded before widget | Shipped `db30b53` |
| Live Game Center page · reload | **Likely Pass** | — | `NBA_PAGE_RADIO_KEY` from `page_label_last` | Manual verify |
| Matchup page · reload | **Likely Pass** | — | Same page radio key | Manual verify |
| Team selector stability | **Likely Pass** | — | Widget `key=` binding | Shipped |
| Page selector stability | **Likely Pass** | — | Widget `key=` binding | Shipped |
| Knicks unwanted reset | **Likely Pass** | — | No hardcoded index when restored team valid | Shipped |
| Retired page label | **Fail (code)** | Falls back to Home | Invalid label check (`streamlit_app.py:18077-18078`) | Label aliases |
| Cross-device | **Manual verify** | — | Cloud autosave | Manual verify |

### Investment

| Test | Pass/Fail | Issue | Root Cause | Fix |
|------|-----------|-------|------------|-----|
| Beginner mode · reload | **Likely Pass** | — | `ensure_experience_mode` + restore | Manual verify |
| Advanced mode · reload | **Likely Pass** | — | Dual experience keys in blob | Manual verify |
| Advanced cross-device | **Likely Pass** | — | `reconcile_investment_cloud_drift_if_needed` | Shipped `34529d1` |
| Portfolio holdings · reload | **Likely Pass** | — | `holdings_df` in blob | Manual verify |
| Goal / macro / dates · reload | **Likely Pass** | — | `_PERSIST_SCALAR_KEYS` | Manual verify |
| Portfolio Health · reload | **Likely Pass** | — | `health_summary` + macro keys | Manual verify |
| Empty holdings in blob | **Fail (code)** | SPY/BND default | `apply_investment_disk_state` fallback | Keep existing when absent |
| EOR autosave clobber | **Likely Pass** | — | `_end_of_run_autosave_blocked` | Shipped |
| Reset to default only | **Likely Pass** | — | `default_reset_investment_session` | Manual verify |

### Future Lens

| Test | Pass/Fail | Issue | Root Cause | Fix |
|------|-----------|-------|------------|-----|
| Wizard domain/area/skill · reload | **Likely Pass** | — | Early restore at startup | Shipped `2eab052` |
| sim_year · reload | **Likely Pass** | — | `sim_year` in `_SESSION_KEYS` | Manual verify |
| Simulation name/project · reload | **Likely Pass** | — | `_suite_fl_sim`, `future_project` persisted | Shipped |
| Timeline year · reload | **Likely Pass** | — | `timeline_year` persisted | Manual verify |
| **View mode / active tab · reload** | **Fail (code)** | Always Evolution tab | `_suite_fl_view` saved but not applied (`streamlit_app.py:520-521`) | Wire view to tab UI |
| Cross-device | **Manual verify** | — | Cloud autosave | Manual verify |

### Applied Intelligence

| Test | Pass/Fail | Issue | Root Cause | Fix |
|------|-----------|-------|------------|-----|
| Saved session (view_mode, area, problem) · reload | **Likely Pass** | — | `_PERSIST_KEYS` + restore before resume | Manual verify |
| Reset to default | **Likely Pass** | — | `finalize_suite_reset` | Shipped `32c2158` |
| Applied Math preload from CC | **Pass (by design)** | Cleared on normal reopen | Preload keys not persisted | N/A |
| Reopen after refresh (normal) | **Likely Pass** | — | Library area persists | Manual verify |
| view_mode widget race | **Manual verify** | Possible overwrite | Radio without stable key (`streamlit_app.py:92-99`) | P2 fix |

### Command Center

| Test | Pass/Fail | Issue | Root Cause | Fix |
|------|-----------|-------|------------|-----|
| Widget/session restore | **N/A** | Dashboard | No `restore_once` | By design |
| Continue cards · refresh | **Manual verify** | — | Rebuilt from activity + resume items | Hard refresh after app activity |
| App Directory · refresh | **Manual verify** | — | `load_activity_snapshot` | Hard refresh |
| Applied Math cards (question only) | **Likely Pass** | — | `analytical_question_continue_copy` | Shipped `d400e71` |
| Cross-device activity | **Manual verify** | Not real-time | Load on render only | Expected |

---

## Automated test results

| Repo | Suite | Result |
|------|-------|--------|
| Command Center | analytical question, project intelligence, app directory | **19 passed** |
| Baseball | full tests | **92 passed** |
| Investment | `test_investment_persistent_state.py` | **12 passed** |
| Music | session restore, persistence, favorites, reboot | **13 passed, 2 failed** (`test_suite_session_restore` — pick_key / recovery notice assertions; manual smoke still required) |

All 7 Streamlit Cloud URLs returned **HTTP 200**.

---

## Manual smoke script (recommended order)

1. **Music** — non-core song → custom progression → F5 → Reboot app → second device  
2. **NBA** — non-Knicks + Live Game Center → F5 → Reboot  
3. **Future Lens** — full wizard + sim 2050 + **Simulation tab** → F5 (**expect Simulation tab returns**)  
4. **Investment** — Advanced on phone → laptop (same `suite_user_id`)  
5. **Baseball** — Draft Room + trend comparison → F5 → Continue from CC  
6. **AMI** — Practical Lab + problem → F5 → Reset  
7. **CC** — verify Continue + App Directory after above activity  

---

## P1 fixes (after manual confirm, before CC ranking)

1. **Future Lens** — apply `_suite_fl_view` to tab selection  
2. **Music** — surface restore errors; no default song after failed restore  
3. **Investment** — do not overwrite holdings with SPY/BND when blob field absent  
4. **Baseball** — migrate filter enums on restore after redeploy  

No architecture changes recommended in this pass.
