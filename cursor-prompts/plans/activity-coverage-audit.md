# Activity Coverage Audit — Continue vs App Directory

**Date:** 2026-06-06  
**Goal:** Continue = most recent meaningful **workflow**. App Directory = most recent **app state**.

---

## Two concepts (must stay separate)

| Concept | Purpose | Opens to |
|---------|---------|----------|
| **Continue** | Exact workflow resume | Same page + entity + context (key, players, portfolio) |
| **App Directory** | App home summary | App homepage with session restored (song loaded, portfolio on disk) |

---

## Music Practice Coach

### Currently logged → activity event → resume item → Continue card

| Action | Logged? | Event | Resume item | Continue card | App Directory |
|--------|---------|-------|-------------|---------------|---------------|
| Song selected (picker) | ✅ | `song_selected` | ✅ `song:{pick_key}` | ✅ via events | ✅ rank 1 |
| Practice log saved | ✅ | `practice` | ✅ | ✅ | ✅ rank 3 |
| Chart/lyrics verified | ✅ | `verified_chart_saved` | ✅ | ✅ edit card | ✅ rank 4 |
| Display key changed | ✅ (fixed) | `display_key_changed` | ✅ (now with key+page) | ✅ (fixed) | ❌ |
| Instrument changed | ✅ (new) | `instrument_changed` | ✅ | ✅ (fixed) | ❌ |
| Studio page (practice/backing) | ✅ (new) | `studio_page_entered` | ✅ | ✅ (fixed) | ❌ |
| Backing track generated | ✅ (new wire) | `backing_track_started` | ✅ `backing:{pick}` | ✅ (fixed) | rank 2 |
| Recording upload/review | ✅ | `video_uploaded` / `recording_reviewed` | ✅ | partial | rank 2 |

### Missing before this pass (now addressed)

- Key changes did not update Continue subtitle/URL with `display_key`
- Instrument changes not logged
- Backing Track work not logged (`log_backing_*` existed but was never called)
- Studio page navigation not logged
- `display_key_changed` used hardcoded page "Practice Studio"

### Still not logged (minor / future)

- Section focus changes alone
- Focus/level widget tweaks
- Column sort / filter toggles (correct — skip)

### App Directory behavior

- Driven by `music_directory_rank()` — prefers verified chart > practice > backing > song_selected
- Disk sync via `_disk_resume_from_block` restores song + `display_key` + `studio_page`
- **Does not** need to open Backing page — only load song state

---

## Baseball Stat App

### Currently logged

| Action | Event | Continue | Notes |
|--------|-------|----------|-------|
| Player comparison (2 selected) | `player_comparison` | ✅ `compare:A:B` | Works |
| Draft prep | `draft_prep` | ✅ `baseball:draft` | |
| Trade analysis | `trade_analysis` | ✅ | |
| Projection report | `projection_report` | ✅ | |
| Sleeper research | `sleeper_research` | partial | |
| Trend filter change (aggregate) | `trend_analysis` (no player) | ❌ weak | Logged on filter sig only |
| Single-player trend chart | — | ❌ **was missing** | **Fixed:** logs `trend_analysis` with `player` |

### Lorenzo Cain scenario (root cause)

- `log_trend_analysis()` was called **without player name** when lag/position filters changed
- Single-player dashboard chart never called `log_trend_analysis(player=...)`
- `project_intelligence` treated all `trend_analysis` as generic projection — no Continue card with player

### Fixed in this pass

- Log player name when single-player trend chart renders
- Continue card: `trend:{player}` → Trend Value + `suite_trend_player` deep link

---

## Investment Portfolio Analyzer

| Action | Event | Continue | App Directory |
|--------|-------|----------|---------------|
| Goal selected | `investment_goal_selected` | partial | ✅ |
| Portfolio created | `portfolio_created` | ✅ | ✅ |
| Holdings updated | `holdings_updated` | ✅ | ✅ |
| Health check | `portfolio_health_checked` | ✅ + fingerprint | ✅ rank 5 |
| Scenario / rebalance | various | partial | ✅ |

App Directory restores portfolio via disk/cloud — does not force Health tab (correct).

---

## NBA Playoff Companion

| Action | Event | Continue |
|--------|-------|----------|
| Live Game Center | `game_outlook` | ✅ `nba:game:{team}` |
| Matchup / injury / playoff | various | ✅ |
| Team select alone | ❌ | via disk state only |

---

## Command Center routing

| Source | Feeds Continue | Feeds App Directory | Feeds Recent Activity |
|--------|----------------|---------------------|----------------------|
| `record_activity` → resume_items | ✅ | ❌ | ✅ |
| `project_intelligence._projects_from_events` | ✅ | ❌ | ❌ |
| `_sync_disk_user_states_to_storage` | ✅ fallback | ✅ current_states | ❌ |
| `activity_feed.build_today_summaries` | ❌ | ❌ | ✅ (generic — P2) |
| `get_app_directory_card` | ❌ | ✅ | ❌ |

---

## Recommended next steps (after this pass)

1. Reboot Streamlit Cloud apps; retest Turn the Lights Back On + Lorenzo Cain flows
2. P2: entity-aware Today's Work copy (not activity logging)
3. P3: `action_coordinator.py` to unify Continue + Coach + Highlights
4. Music: log section focus changes when user jumps sections (optional)
