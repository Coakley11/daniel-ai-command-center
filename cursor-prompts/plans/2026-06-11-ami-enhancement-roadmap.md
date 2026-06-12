# AMI Enhancement Roadmap + Cross-Device Sync Audit

**Last updated:** 2026-06-11  
**Priority:** AMI improvements first; optional sync enhancements later  
**Repos:** `daniel-ai-command-center`, `Applied-mathematical-intelligence`, `ai-music-practice-coach`, `baseball-stat-app`

---

## Part 1 — Sync Audit Summary

### Music App (`ai-music-practice-coach`)

| Item | Status | Mechanism | Effort to improve |
|------|--------|-----------|-------------------|
| Active song selection | **Syncs well** | `active_song_state.py` + cloud `full_session` | Easy (maintenance) |
| Instrument / key / level | **Syncs well** | Same canonical module; Test D passed | Easy |
| Practice filters | **Syncs well** | `practice_state.py` (Test B) | Easy |
| Backing filters | **Syncs well** | `backing_track_state.py` (Test C) | Easy |
| Studio page nav | **Syncs well** | `studio_nav_state.py` (Test A) | Easy |
| User chart overrides | **Does not sync** | `data/user_chart_overrides.json` local | Medium (1–3h metadata) / Large (1–2d if full chart JSON) |
| Creative Lab state | **Partial** | `_PERSIST_KEYS` + page snapshots; no `creative_state.py` | Medium (3–8h) |
| Recording / analysis prefs | **Partial** | Analysis page snapshots; multitrack settings mostly missing | Small (1–3h) |
| AI analysis results | **Partial** | `last_analysis_result` in snapshot; `ai_performance_history.json` local | Medium (3–8h) |
| Practice logs | **Does not sync** | `practice_history.json` local file | Medium (3–8h) |
| Uploaded audio/video | **Does not sync** | Blobs excluded; no object storage | Major (multi-day) |
| Karaoke queue | **Partial** | `karaoke_queue` in global list; no `karaoke_state.py` | Medium (3–8h) |

**Small high-impact sync win (optional):** Persist `practice_history.json` + `ai_performance_history.json` to Supabase `suite_saved_items` — **Medium (3–8h)**, no blob storage required.

### Baseball App (`baseball-stat-app`)

| Item | Status | Mechanism | Effort to improve |
|------|--------|-----------|-------------------|
| Watchlists / draft queue | **Syncs well** | `draft_state.py` canonical + `draft_edit` force-save | Easy (optional flush polish) |
| Comparisons | **Syncs well** | `comparison_state.py` reference impl | Done |
| Sleeper filters | **Syncs well** | `fantasy_state.sleepers` canonical | Done |
| Fantasy standings/lineup filters | **Syncs well** | `fantasy_state` canonical | Done |
| Draft room board | **Partial** | `draft_room_table` global; delayed save until nav/autosave | Small–Medium (0.5–1d force-save; 1–2d canonical) |
| Live draft in progress | **Partial** | `live_draft_room` page-scoped snapshot only | Medium (1–2d promote to canonical/global) |
| League settings (draft) | **Partial** | Split across global keys + page registry | Medium (1–2d consolidate `draft_state`) |
| Uploaded fantasy rosters | **Does not sync** | `fantasy_current_roster_stats` intentionally local | Large (1–2d if product wants persistence) |
| Draft recommendations | **Does not sync** | Recomputed each render (by design) | N/A |
| Sleeper result tables | **Does not sync** | Recomputed (by design) | Small (1d optional cache) |

**Small high-impact sync win (optional):** Draft Room `on_change` + immediate `force_save_baseball_state(reason="draft_edit")` on board edits — **Small (1–3h)** per acceptance matrix P1-1.

---

## Part 2 — AMI Architecture (current state)

**Pipeline:** Source app → `suite_analytical_question` → CC activity + Supabase blob → AMI hydrate → **rule-based** router/solvers → return insight → source app restore.

**Not OpenAI today** for suite AMI path (except separate in-app coaches). Context = JSON dict + `source_state` snapshot.

### Gaps by app

| App | Restore | Answer quality |
|-----|---------|----------------|
| Baseball | Strong on canonical pages; Phase 2 gaps on 14-page parity | 9/10 Trend, 8/10 Compare when `_ami_*` hooks run; weak without hooks |
| Music | **Strong** (Test E return restore) | **Weak** — no music router; falls to `GENERIC_INTERACTIVE` |
| NBA | Partial | 3–5/10 without live stat-gap/matchup hooks |
| Investment | Partial | 4/10 rebalance without drift hooks |
| Applied Math | Core solvers work | Needs teaching-framed explanations + interactive what-if |

### Cross-cutting gap

URL `suite_ai_context` truncated to 400 chars when `question_id` present. Full context should always load from Supabase blob by `question_id` first.

---

## Part 3 — Recommended AMI Implementation Order

### Phase 0 — Foundation (1–2 days) — **All apps**

1. AMI hydrate: **blob-by-question_id first**, URL fallback second
2. Developer diagnostics: fields received vs `expected_fields_for_page` on every solve
3. Teaching response template: problem → analyst frame → variables → tradeoffs → decision

**Effort:** Easy–Small per item; **1–2 days** total

### Phase 1 — Baseball AMI depth (3–5 days P0; 2–3 weeks full)

1. Ensure every AMI-eligible page populates `_ami_*` / `context_extra_builder` before send
2. Wire `trend_summary`, `comparison_differences`, `historical_snapshot`, `draft_projection`
3. Answer framing: analyst + projection-system reasoning; assumptions explicit
4. Complete Phase 2 canonical `*_state.py` for remaining pages (longer arc)

**Effort:** **Small–Medium** for hooks; **Large** for full 14-page canonical

### Phase 2 — Music AMI coach (1–2 weeks)

1. Expand send context: song title/artist, section, BPM/groove, mission, analysis summary, practice history snippet
2. Add `music` router branch + domain solvers OR OpenAI music-coach prompt packer (product decision)
3. Teaching outputs: chord function, rhythm, harmony, ear-training, practice steps
4. Use `source_state.widget_params` for answer context (not just minimal send whitelist)
5. Add music keys to `_PUBLIC_CONTEXT_KEYS`

**Effort:** **Medium** context (2–3d); **Large** solvers (1w); **Major** if OpenAI coach (2w)

### Phase 3 — Applied Mathematics teaching layer (1 week)

1. Structured 5-step reasoning template in solver UI
2. Sliders / scenario comparison where router supports interactive partial models
3. NBA stat-gap + matchup hooks; Investment rebalance drift hooks
4. Historical: surface `top_rows` numbers in answer body

**Effort:** **Medium** per domain (~3–5d each)

---

## Part 4 — Effort Summary (AMI focus)

| Workstream | Effort | Notes |
|------------|--------|-------|
| Cross-cutting hydration + teaching template | **1–2 days** | Unblocks all apps |
| Baseball AMI contextual transfer (P0 pages) | **3–5 days** | Highest ROI for sports |
| Baseball Phase 2 canonical (14 pages) | **2–3 weeks** | Parallel with AMI if needed |
| Music AMI context + rule-based music domain | **1–1.5 weeks** | Restore already strong |
| Music AMI OpenAI coach (optional) | **+1–2 weeks** | If rule solvers insufficient |
| Applied Math teaching + interactive UX | **1 week** | NBA + Investment hooks |
| **Total AMI program (sequential P0–P2)** | **~3–4 weeks** | Excludes optional OpenAI music |

---

## Part 5 — Optional sync (defer unless small win)

| Item | Effort | Impact |
|------|--------|--------|
| Baseball draft board immediate force-save | Small (1–3h) | High for draft cross-device |
| Music practice log + analysis history → Supabase | Medium (3–8h) | High for coach continuity |
| Music `creative_state.py` canonical | Medium (3–8h) | Medium |
| Uploaded media blob storage | Major | Only if product requires cross-device recordings |

---

## Verification

- Music: Tests A–D regression unchanged after any sync work
- Baseball: `test_draft_state`, `test_comparison_state`, `test_fantasy_state` green
- AMI: Developer Mode shows full context after send; Music/Baseball answers use domain fields not generic template
