# Suite session persistence audit (deep)

**Last updated:** 2026-06-07  
**Status:** Read-only audit — fixes prioritized, not implemented (except Baseball restore order + AMI reset, shipped `16fbe29` / `32c2158`)

## Rule

Apps must **never** revert to defaults unless **Reset to Default** is pressed. Applies to: refresh, reopen, reboot, redeploy, cross-device restore.

---

## Per-app report

| App | Persists correctly | Still resets incorrectly | Cause | Exact fix required |
|-----|-------------------|--------------------------|-------|-------------------|
| **Music** | Song pick_key, instrument, studio page, filters, favorites, snapshots | **Non-core song → first core default** | `streamlit_music_practice_app.py:1174–1183` trusted-core guard after restore | Skip override when `SUITE_LOCAL_STATE_RESTORED_KEY` or restored `pick_key` is set |
| **Music** | `active_music_source` | **Custom progression name/sections lost** | `cpl_active_progression` / `cpl_saved_progressions` not in `music_persistent_state.py` persist keys; re-seeded at `:1168–1171` | Add CPL keys to disk/cloud blob; apply before CPL init |
| **Music** | Cloud sync when configured | Default song on silent restore failure | Bare `except` at `:1095–1100` → `ensure_master_song_initialized` | Log/surface errors; no default init after partial restore |
| **Baseball** | Page, draft room, `page_filter_state` | Invalid filter enum → widget default | `streamlit_app.py:10825+` `validate_state_option` | Migrate enums on restore or extend catalogs (expected after redeploy) |
| **Baseball** | *(was Continue wipe)* | **Fixed** | Resume before restore | Shipped — QA only |
| **NBA** | Team on disk (`favorite_team`), page prefs | **Knicks when restore fails** | `:17951` hardcoded Knicks index; `:17905` silent restore failure | Fail loudly; fallback to last saved team not Knicks |
| **NBA** | `_nba_persist_team` at autosave | **Team selectbox not stably bound** | `:17995–18000` no widget `key=`; `_nba_restore_team` one-shot pop | Add `key="nba_favorite_team_sidebar"`; seed session state before render |
| **NBA** | Page override | Helpers assume Knicks | `:5858` `favorite_team` never written to session (only `_nba_persist_team`) | Set `session_state["favorite_team"]` after selectbox |
| **Investment** | Holdings, dates, macro, goals, workflow | **Cross-device Beginner/Advanced drift** | `restore_once` timestamp skip; only Investment has `cloud_resync_needed` | Sync content-resync pattern to all apps; verify `suite_user_id` |
| **Investment** | Most scalars | **EOR autosave may clobber cloud mode** | `streamlit_app.py:2940` end-of-run autosave | Guard when in-memory mode ≠ cloud without local edit |
| **Investment** | | Default SPY/BND if blob empty | `investment_persistent_state.py:421–422` | Keep existing holdings when field absent |
| **AMI** | `view_mode`, `ps_area_id`, `ps_library_problem` | AI preload cleared on reopen | Preload keys not persisted (by design) | OK for CC questions |
| **AMI** | | `view_mode` overwritten by sidebar radio | `streamlit_app.py:99` after restore `:38` | Seed widget key from restore before radio |
| **Future Lens** | Wizard fields, `_suite_fl_view` (saved) | **Wizard → factory defaults on refresh** | Defaults loop `:129–138` before sidebar restore `:490` | Move restore to top after `set_page_config` |
| **Future Lens** | | **`_suite_fl_sim` / sim name lost** | Set by `suite_resume_launch.py:238–243`; not in persist keys; never read in app | Persist + apply `_suite_fl_sim`; map to wizard or sim selector |
| **Future Lens** | | **Tab view not restored** | `_suite_fl_view` persisted but tabs hard-coded `:512–521` | Apply restored view to active tab |
| **Command Center** | Activity, Continue, coach (cloud read) | No widget session restore | Dashboard aggregator | N/A |

---

## Scenario matrix

| Scenario | Music | Baseball | NBA | Investment | AMI | Future Lens |
|----------|-------|----------|-----|------------|-----|-------------|
| **Refresh** | ⚠️ non-core override | ✅ | ⚠️ team widget | ⚠️ mode drift | ✅ | ⚠️ restore order |
| **Reopen tab** | Same as refresh | ✅ | ⚠️ | ⚠️ | ✅ | ⚠️ |
| **Reboot/redeploy** | ⚠️ + cloud | ✅ | ⚠️ | ⚠️ cloud sync | ✅ | ⚠️ |
| **Cross-device** | ⚠️ if cloud OK | ✅ | ⚠️ | ⚠️ primary risk | ✅ | ⚠️ |
| **Reset to default** | ✅ clears | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## Fix priority (reliability pass)

| Priority | App | Fix | Effort |
|----------|-----|-----|--------|
| P0 | Music | Skip trusted-core override after restore | Small |
| P0 | Future Lens | Early restore + persist `_suite_fl_sim` | Medium |
| P0 | NBA | Stable team selectbox key + session binding | Small |
| P1 | Music | Persist custom progression blob keys | Small |
| P1 | Investment | Guard EOR autosave; promote cloud_resync | Medium |
| P2 | AMI | Widget key seed for view_mode | Small |
| P2 | Shared | Sync `suite_user_persistence.py` via sync script | Medium |

---

## Shared architecture notes

- `suite_user_persistence.restore_once()` — skipped on Continue query params, local dirty, already-restored + stale cloud timestamp
- **Investment-only** `cloud_resync_needed()` compares content fingerprint, not just timestamp
- `scripts/sync_suite_cloud_modules.py` does **not** sync `suite_user_persistence.py` — apps can diverge

---

## Verification checklist

1. Non-core song (Music) → refresh → same song
2. Custom progression (Music) → refresh → same sections
3. Non-Knicks team (NBA) → refresh + reboot → same team everywhere
4. Future Lens wizard + sim year → refresh → same domain/area/skill/year/tab
5. Investment Advanced on phone → laptop → Advanced (check diagnostics)
6. Reset to default → factory only
7. Continue deep link → target state without wiping unrelated fields
