# Suite session persistence audit

**Last updated:** 2026-06-07  
**Status:** Read-only audit — no major fixes implemented in this pass

## Rule

Only **Reset to default** should restore factory defaults. Reboot, redeploy, refresh, or reopen should restore the latest saved state (local disk + Supabase `full_session` when configured).

## Per-app report

| App | Persists correctly | Still resets incorrectly | Cause | Proposed fix |
|-----|-------------------|--------------------------|-------|--------------|
| **Music** | Song context (pick_key, instrument, studio page, focus), filters, favorites, karaoke queue, page snapshots — `music_persistent_state.py` + cloud | Non–trusted-core song replaced with first default core song on refresh | After restore, `streamlit_music_practice_app.py` ~L1174–1183 forces `DEFAULT_SONG_RECORDS[0]` when `chart_library_mode == core` and song not trusted | Skip override when restored `pick_key` or `SUITE_LOCAL_STATE_RESTORED_KEY` is set |
| **Music** | Cloud/disk session | Default song if restore fails silently | Bare `except` around restore (~L1095–1100); falls through to `ensure_master_song_initialized` | Surface restore errors; avoid silent fallback |
| **Investment** | Mode, tab, holdings, dates, macro sliders, goals, workflow blob, health summary — richest persistence | Beginner/Advanced mode drift phone↔laptop | `restore_once` skips re-apply when already restored and cloud not newer | Use `investment_cloud_resync_needed()`; verify matching `suite_user_id` |
| **Investment** | Most fields | Default SPY/BND when blob has no `holdings_df` | `apply_investment_disk_state` fallback | Intentional; ensure autosave always writes holdings |
| **Baseball** | `active_page`, draft room, full `page_filter_state` (trends, comparison, etc.) | *(Fixed)* page/filters lost on Continue reopen | Resume launch ran before restore | **Fixed:** restore → then `apply_suite_resume_launch` |
| **Baseball** | Per-page filters | Invalid restored enum → widget fallback | `validate_state_option` / `validate_multiselect_options` | Expected validation; update option catalogs if enums change |
| **NBA** | Team (`favorite_team`), page override, sidebar prefs — `nba_persistent_state.py` | Knicks on first paint if restore fails | `_nba_restore_team` one-shot index; no stable widget key on team selectbox | Seed selectbox key from restored team |
| **AMI** | `view_mode`, `ps_area_id`, `ps_library_problem` | Suite AI preload cleared on normal reopen | Preload keys intentionally excluded; autosave skips during `_suite_ai_question` | By design for CC cross-app questions |
| **Future Lens** | Wizard fields, sim year, `_suite_fl_view` | Simulation name/project (`_suite_fl_sim`) | Not in `_SESSION_KEYS` / `build_future_lens_disk_state` | Add `_suite_fl_sim` to persist keys |
| **Future Lens** | Wizard on cold start | Restore runs in sidebar after factory defaults | `restore_future_lens_state_once` at ~L490 after defaults loop ~L129 | Move restore to top of `streamlit_app.py` (after `set_page_config`) |
| **Command Center** | Activity feed, Continue cards, coach insights (cloud/SQLite read) | No Streamlit widget/session restore | Dashboard aggregator, not a suite app | N/A — reads sibling state via `activity_store.py` |

## Restore order (entry files)

| App | Order | OK? |
|-----|-------|-----|
| Baseball | restore → resume (`streamlit_app.py`) | Yes (fixed) |
| NBA | restore → resume | Yes |
| Investment | resume → restore; tab applied inside restore | Yes for direct open |
| AMI | restore → resume | Yes |
| Future Lens | resume → defaults → sidebar restore | Fragile |
| Music | resume → catalog load → restore → finalize resume → song init | Yes by design |
| Command Center | none | N/A |

## Shared mechanism

All suite apps (except CC) use `suite_user_persistence.py`:
- `restore_once()` — disk + cloud (newer wins); skipped on Continue query params, local dirty flag, or already-restored-with-stale-cloud
- `autosave_if_changed()` — fingerprint-based disk + Supabase write at end of run
- `finalize_suite_reset()` — only path that clears cloud and writes factory defaults

## Verification checklist

1. Change state → browser refresh → state returns
2. Reboot Streamlit Cloud → same state (matching `suite_user_id` in secrets)
3. Reset to default → factory state only
4. Continue deep link → resume after restore without wiping unrelated state
5. Cross-device (Investment): mode sync phone ↔ laptop
