# Command Center Sprint 1 — Continue Deep Links

**Goal:** Continue buttons restore exact app context (song + key + page, portfolio + tab, player comparison, NBA team + Live Game Center).

**Status:** Implementing  
**Next after this:** Music coaching v1 (Priority 2)

---

## Acceptance criteria

| App | Continue action | Expected restore |
|-----|-----------------|------------------|
| Music | Continue Perfect practice | Perfect, correct display key, Practice studio page |
| Investment | Continue portfolio health | Same portfolio session + Portfolio Health tab |
| Baseball | Continue Soto vs Piazza | Comparison Tool with both players loaded |
| NBA | Continue Knicks Live Game Center | New York Knicks selected + Live Game Center page |

---

## Root causes (pre-fix)

1. **`activity_store._sync_disk_user_states_to_storage()`** used `get_app_url()` — no query params.
2. **`continue_dashboard` fallback** used plain app URLs when event-derived cards were empty.
3. **`project_intelligence.build_project_continue_cards()`** passed `subtitle` as `page` and omitted `metrics`.
4. **`suite_deep_links.py`** missing `suite_display_key`, `suite_holdings_fp`, `suite_player_a`/`suite_player_b`.
5. **`suite_resume_launch.py`** did not apply display key, compare players, or investment tab.
6. **Investment app** never consumed `_suite_investment_page` → `investment_active_tab`.

---

## Implementation steps

### Step 1 — `suite_deep_links.py` (Command Center, then sync)

- Add query params: `suite_display_key`, `suite_holdings_fp`, `suite_player_a`, `suite_player_b`.
- Normalize Music pages (`Practice Log` → `practice`, `Backing Track Studio` → `backing`).
- Parse `compare:{a}:{b}` resume keys for baseball player params.
- Parse `portfolio:health` + holdings fingerprint for investment.

### Step 2 — `suite_resume_launch.py` (Command Center, then sync)

- **Music:** set `PENDING_DISPLAY_KEY` from `suite_display_key`; normalize studio page.
- **Baseball:** accept `resume` key; set `pending_sig_player_a/b` + `pending_compare_players`; navigate to Comparison Tool.
- **Investment:** set `_suite_investment_page` + optional `_suite_holdings_fp`.
- **NBA:** unchanged path (team + `page_override` already work).

### Step 3 — Command Center consumers

| File | Change |
|------|--------|
| `activity_store.py` | `_disk_resume_from_block` enriched per app; `_sync_disk_user_states_to_storage` uses `build_resume_action_url()` |
| `project_intelligence.py` | Event scan stores metrics; emit baseball compare + NBA game cards; build URLs with `page` + `metrics`; rebuild resume-item URLs from `item_key` |
| `continue_dashboard.py` | Fallback path builds deep links from `load_current_states()` metrics |

### Step 4 — App-specific hooks (sibling repos)

| App | File | Change |
|-----|------|--------|
| Investment | `streamlit_app.py` or `investment_persistent_state.py` | Apply `_suite_investment_page` → `investment_active_tab` after disk restore |
| Music | `streamlit_music_practice_app.py` | Include `pick_key` in practice-log `record_activity` metrics |

### Step 5 — Sync + deploy

```bash
python scripts/sync_suite_cloud_modules.py
```

Reboot Streamlit Cloud dev deployments for Command Center + all suite apps.

---

## Tests

- `tests/test_suite_deep_links.py` — URL building for all four acceptance scenarios.
- Existing `test_import_smoke` / `test_project_intelligence` must pass.

---

## Out of scope (Sprint 2+)

- Intent logging, entity-aware summaries, action coordinator.
- Music coaching refactor (Priority 2).
- Holdings fingerprint mismatch warnings in Investment UI.
