# Sprint 1 Reliability Fixes — Post-Deploy (2026-06-06)

## Root causes found in testing

### Music Continue opened Say (wrong song)

1. `apply_suite_resume_launch` set `active_catalog_pick_key` **before** the catalog loaded.
2. `ensure_master_song_initialized` only checked `selected_song` — not the pending pick key — and fell back to the **first trusted-core song (Say)**.
3. Disk/cloud restore via `apply_music_disk_state` seeded `session_state["pick_key"]` (wrong key) instead of calling `apply_pick_key`.

### Music reboot lost last song

Same disk restore bug: `data/music_user_state.json` / cloud `full_session.core` had the right `pick_key`, but it was never committed to `selected_song` / `active_catalog_pick_key`.

### Baseball Lorenzo Cain trend missing from Continue

1. `log_trend_analysis(player=...)` only ran inside `if not selected_player_summary.empty` — chart could render without logging.
2. Continue deep link stored plain `Lorenzo Cain` but the selectbox needs `Lorenzo Cain (years)` — widget state was cleared.
3. `suite_instrument` was not in Continue URLs (music subtitle showed Piano but URL did not restore it).

## Fixes applied

| Area | Fix |
|------|-----|
| Music | `finalize_suite_resume_launch()` after catalog load → `apply_pick_key` |
| Music | `apply_saved_music_context()` shared by disk + activity restore |
| Music | `apply_music_disk_state` applies core via `apply_pick_key` |
| Music | `ensure_master_song_initialized` respects pending `active_catalog_pick_key` |
| CC/Music URLs | `suite_instrument` query param |
| Baseball | Trend log fires on player select (not only when summary table renders) |
| Baseball | Resolve `pending_trend_player` / plain names to full trend labels |
| CC | `has_resume_query_params` expanded for music + baseball |
| CC | `baseball_compare` uses latest timestamp (not first only) |

## Suite-wide Continue vs App Directory

| App | Continue (meaningful workflow) | App Directory (state on open) | Gaps |
|-----|-------------------------------|------------------------------|------|
| **Music** | song/backing + key + instrument + page | song/instrument/key via disk/cloud | Fixed resume + persistence |
| **Baseball** | compare, trend (player), draft, trade | page + filters via disk/cloud | Trend logging fixed |
| **Investment** | health, scenario, allocation | portfolio/goal via disk/cloud | Generally OK from Sprint 1 |
| **NBA** | live game, matchup, playoff | team via disk/cloud | Team-only select not a Continue card (by design) |
| **Future Lens** | simulation workflow | sim state via disk/cloud | Partial — needs smoke test |
| **Applied Intelligence** | lesson/lab workflow | lesson via disk/cloud | Partial — needs smoke test |

**Rule:** Only **Reset to default** should return an app to factory defaults. Continue skips cloud restore; normal open uses newer of cloud vs disk.

## Retest after reboot

### Music Continue
1. Turn the Lights Back On → Piano → Eb → Practice or Backing
2. Command Center Continue → click
3. Expect: same song, key, instrument, page — **not Say**

### Music persistence
1. Work on Turn the Lights Back On
2. Reboot Streamlit app (or new browser session)
3. Expect: Turn the Lights Back On still loaded

### Baseball trend
1. Trends → Lorenzo Cain → view dashboard
2. Command Center → Continue Lorenzo Cain trend chart
3. Expect: Trend Value with Lorenzo Cain loaded
