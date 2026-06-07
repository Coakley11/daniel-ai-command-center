# Suite session persistence audit (deep)

**Last updated:** 2026-06-07  
**Status:** P0 fixes implemented — pending deploy verification

## Rule

Apps must **never** revert to defaults unless **Reset to Default** is pressed. Applies to: refresh, reopen, reboot, redeploy, cross-device restore.

---

## Per-app report

| App | Persists correctly | Still resets incorrectly | Cause | Exact fix required |
|-----|-------------------|--------------------------|-------|-------------------|
| **Music** | Song, CPL, filters | **Fixed** non-core override + CPL keys | was `:1174–1183` | **Shipped** — skip override when restored pick_key |
| **Music** | Custom progression | **Fixed** CPL persist | missing keys | **Shipped** — `cpl_*` in disk blob |
| **Music** | Cloud sync when configured | Default song on silent restore failure | Bare `except` at `:1095–1100` → `ensure_master_song_initialized` | Log/surface errors; no default init after partial restore |
| **Baseball** | Page, draft room, `page_filter_state` | Invalid filter enum → widget default | `streamlit_app.py:10825+` `validate_state_option` | Migrate enums on restore or extend catalogs (expected after redeploy) |
| **Baseball** | *(was Continue wipe)* | **Fixed** | Resume before restore | Shipped — QA only |
| **NBA** | Team, page | **Fixed** Knicks reset | hardcoded index, no widget key | **Shipped** — stable selectbox/radio keys |
| **Future Lens** | Wizard, sim | **Fixed** restore order + `_suite_fl_sim` | late sidebar restore | **Shipped** — restore at startup |
| **Investment** | Cross-device mode | **Fixed** cloud drift guard | EOR autosave + timestamp skip | **Shipped** — reconcile + block EOR clobber |
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
