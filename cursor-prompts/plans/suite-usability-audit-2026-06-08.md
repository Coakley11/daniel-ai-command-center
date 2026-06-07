# Suite usability audit — Continue, persistence, Applied Math quality

**Last updated:** 2026-06-08  
**Status:** Audits complete — **no implementation**  
**Scope:** Command Center classification, Music/NBA/Future Lens persistence, Applied Math quality roadmap

Investment Transparency Phase 1 is **paused** (shipped `76969f4`). Suite-wide reliability and workflow continuity are the next priorities.

---

## Executive summary

| Deliverable | Health | Top action before features |
|-------------|--------|----------------------------|
| **1. Continue vs App Directory** | Classification logic exists but implicit; passive events pollute Continue | Fix placement tags + dedupe before reprioritizing |
| **2. Music persistence** | Strong (50+ keys, page snapshots); minor CPL/widget gaps | Verify cross-device after redeploy; sync `suite_user_persistence.py` |
| **3. NBA persistence** | Narrow (team + page only); sub-page state resets | Remove silent restore failure; persist LGC + Legacy Tracker player |
| **4. Future Lens persistence** | Thin (9 keys); career activity dead; resume URLs incomplete | Enrich deep links; wire or remove career hooks |
| **5. Applied Math quality** | Flow works; analysis often generic | Pass baseball slope/R²; fix AMI preload persistence; store full context |

---

## 1. Command Center — Continue vs App Directory

### How it works today

**Continue** (`project_intelligence.build_project_continue_cards`):
1. Events → `_projects_from_events(snapshot)`
2. Resume items → `load_active_resume_items(limit=30)`
3. Merge by `resume_key` (AMI: `ai:question:{id}`), highest priority wins
4. Sort desc → **top 6**; **14-day stale** cutoff
5. Fallback: `load_current_states()` generic cards

**App Directory** (`activity_store.get_app_directory_card`):
- Fixed **6 apps** from `APP_DEFINITIONS`
- Up to **3 highlight lines** + relative `when` from `ActivitySnapshot`
- Music/Investment use ranked primary lines (`music_directory_rank`, `investment_directory_rank`)

**Key files:** `project_intelligence.py`, `continue_dashboard.py`, `activity_store.py`, `activity_feed.py`, `suite_analytical_question.py`, `ai_command_center.py`

### User intent vs code

| Surface | Should show | Examples |
|---------|-------------|----------|
| **Continue** | Exact resumable workflow | Lorenzo Cain trend chart; Soto vs Piazza comparison; Applied Math question; Perfect practice in D major; Knicks Live Game Center |
| **App Directory** | Durable app identity / project | Turn the Lights Back On (main song); retirement portfolio; Knicks workspace; draft prep workspace; AMI problem-solving workspace |

### Continue → Directory (remove from Continue)

| Workflow | Why | Current |
|----------|-----|---------|
| `song_selected` | Passive catalog pick = state | Continue via `_MUSIC_WORKFLOW_PRIORITY` (61) |
| `holdings_updated` | State change, not review workflow | Continue “Review allocation” (48) |
| `instrument_changed` / `display_key_changed` | Directory already shows instrument/key | Continue via `latest_music_workflow` |
| Weak `bb:proj` fallback | Projection browse ≠ named workflow | Emitted when flag set without compare/trend |

### Directory → Continue (add Continue wiring)

| Workflow | Why | Current |
|----------|-----|---------|
| Future Lens `career_analysis` | Resumable career scenario | `log_career_analysis()` never called |
| `technology_timeline_review` | Resumable timeline session | Feed only |
| `skill_forecast_review` | Skill focus workflow | Feed only |
| NBA `player_comparison` | Meaningful analysis | Counted in weekly stats; no Continue card |
| NBA `playoff_tracker_review` | Resumable review | Feed only |
| Baseball draft room / watchlist | Durable context | Directory shows last chart player only |

### Intentional overlap (tune content, not presence)

| Pair | Continue | Directory |
|------|----------|-----------|
| Music | “Continue {song} practice/chord edits” | Last song, instrument, streak |
| Investment | “Review portfolio health” | Primary health line + goal/holdings |
| NBA live game | Live Game Center card | Last team + last page |
| AMI lesson | “Continue: {lesson}” | Last lesson (no `?`) |

### Duplicates

**Within Continue:**
- Multiple cards per song — different merge keys (`song:{pick}` vs `music:practice:{song}` vs `music:workflow:{song}`)
- Event + resume item duplicate only dedupes when **same** `resume_key`

**Across sections:**
- Baseball “Last player” in Directory = last chart touch, not durable project (misleading vs Continue trend card)
- AMI questions correctly **Continue-only** (Directory blocks `?` in lesson text)

### Recommendations (before ranking changes)

1. Add explicit tags: `CONTINUE_ONLY`, `DIRECTORY_ONLY`, `BOTH`, `NEITHER` per event type
2. Remove passive events from Continue: `song_selected`, `holdings_updated`
3. Normalize music merge keys → **one card per song** (highest-priority workflow wins)
4. Wire missing Continue candidates (Future Lens career/timeline/skill; NBA comparison/playoff tracker)
5. Enrich Directory from cloud `full_session` (draft room, watchlist, favorite team) — not “last metric”
6. Validate with Developer Mode diagnostics (`diagnose_continue_workflow_candidates`) before priority tweaks
7. Align logging at source apps: `record_activity` + consistent `resume_key` across events vs resume_items vs disk sync

**Related:** [command-center-workflow-classification-audit.md](./command-center-workflow-classification-audit.md)

---

## 2. Music persistence audit

**Repo:** `ai-music-practice-coach`  
**Stack:** `suite_user_persistence.restore_once` + `data/music_user_state.json` + Supabase `metrics.full_session`

### Persisted today

| Feature | Keys / mechanism | Module |
|---------|------------------|--------|
| Active song | `core.pick_key`, `active_catalog_pick_key` | `songs/state.py`, `music_persistent_state.py` |
| Instrument | `core.instrument` | `songs/state.py` |
| Key (display) | `core.display_key` → `PENDING_DISPLAY_KEY` | `songs/key_state.py` |
| Practice page | `core.studio_page` + `_studio_page_snapshots` | `studio_page_persistence.py` |
| Section focus | `core.practice_focus_section` + practice snapshot | same |
| Backing Track | `backing_track_*`, page snapshots (not audio cache) | `music_persistent_state.py` |
| Karaoke | `karaoke_queue`, countdown, auto-advance | `music_persistent_state.py` |
| Custom progression | `cpl_active_progression`, `cpl_saved_progressions` | `music_persistent_state.py` |
| Practice history | Separate `practice_history.json` | `streamlit_music_practice_app.py` |

**Restore flow:** `apply_suite_resume_launch` → `restore_music_disk_state_once` → `finalize_suite_resume_launch` → skip default song if restored → `autosave_music_state` EOR

### Gaps

| ID | Gap | Severity |
|----|-----|----------|
| M-1 | CPL widget-only keys (`cpl_finished`, bar widgets) not in disk blob | P2 |
| M-2 | Backing WAV/cache not persisted (by design — regenerated) | Info |
| M-3 | Cross-device uses timestamp-only pick (no content fingerprint) | P2 |
| M-4 | `suite_user_persistence.py` not in `sync_suite_cloud_modules.py` — hub/apps drift | P2 |
| M-5 | Missing catalog song → recovery notice + default song | P1 UX |

### Verification checklist

1. Non-core song + CPL + Backing page → F5 → same song/page/progression
2. Reboot Streamlit → same (requires Supabase on Cloud)
3. Phone ↔ Dell with same `suite_user_id` → cloud restore
4. Reset → factory defaults only

**Goal met?** Mostly yes for song/instrument/key/page/section/CPL. CPL bar widgets and cloud fingerprint are the main gaps.

---

## 3. NBA persistence audit

**Repo:** `nba-playoff-companion-ai`  
**Module:** `nba_persistent_state.py`

### Persisted today

| Feature | Status |
|---------|--------|
| Team | ✅ `favorite_team_sidebar`, widget key `NBA_TEAM_SELECT_KEY` seeded before selectbox |
| Page | ✅ `page_label_last`, `page_override` → `NBA_PAGE_RADIO_KEY` |
| Sidebar toggles | ✅ demo backup, bracket API, QA, manual live enabled |
| **Live Game Center sub-state** | ❌ manual scores, what-if sliders, `_live_gc_*` |
| **Legacy Tracker player** | ❌ defaults Jalen Brunson every refresh |
| **Matchup / Playoff Tracker depth** | ❌ page label only |
| **Bracket** | ❌ API-derived, not user state |

### Knicks/Home revert — status

**Fixed (P0 `db30b53`):** Stable widget keys; team/page seeded before widgets.

**Remaining revert paths:**

| Condition | Fallback |
|-----------|----------|
| First run, no saved state | New York Knicks |
| Invalid/retired page label | 🏠 Home Dashboard |
| Silent restore failure (`except: pass` in `main()`) | Knicks |
| LGC emergency route | `index=` radio, minimal restore |

### Gaps

| ID | Gap | Severity |
|----|-----|----------|
| N-1 | Bare `except: pass` on restore → silent Knicks default | **P1** |
| N-2 | Legacy Tracker player not in `_PERSIST_KEYS` | P2 |
| N-3 | LGC manual overrides / game selection not saved | P2 |
| N-4 | Retired page emoji labels → Home fallback (no alias) | P2 |
| N-5 | `playoff_team_state` read by AMI but never persisted | P3 |

### Verification checklist

1. Non-Knicks + Live Game Center → F5 → same team + page ✅ (when restore succeeds)
2. Legacy Tracker: pick non-Brunson → F5 → **expect Brunson** (gap)
3. LGC manual score edits → F5 → **expect reset** (gap)
4. Reset → Knicks + Home + default toggles

---

## 4. Future Lens persistence audit

**Repo:** `future-lens-ai-transition-simulator`  
**Persisted keys (9):** `broad_domain`, `area`, `specific_skill`, `sim_year`, `timeline_year`, `wizard_complete`, `_suite_fl_view`, `_suite_fl_sim`, `future_project`

### Feature matrix

| Feature | Persists | Gap |
|---------|----------|-----|
| Career simulations | No dedicated mode | `log_career_analysis()` defined, **never called** |
| Timeline mode | `timeline_year` + view | Resume URL lacks `timeline_year` |
| Skill mode | Alias for Future Advice tab | No distinct skill workflow state |
| Saved scenario | Not implemented | No scenario library |
| Active simulation | `sim_year` + skill hint | Deep link passes `suite_sim` only; `wizard_complete` never set |

### vs suite peers

| App | Persist surface |
|-----|-----------------|
| Music | 50+ keys + `core` blob + page snapshots |
| Investment | 40+ keys + holdings + health |
| NBA | ~12 keys + team/page widgets |
| **Future Lens** | 9 wizard/tab keys only — no computed artifacts |

### Gaps

| ID | Gap |
|----|-----|
| FL-1 | Career activity dead — CC handlers exist, no producer |
| FL-2 | No saved-scenario model |
| FL-3 | Resume URL missing domain/area/year/timeline_year |
| FL-4 | `wizard_complete` in persist list but never assigned |
| FL-5 | Drivers tab — no persist hook |
| FL-6 | Only 3 tab/view tests vs Music/Investment depth |
| FL-7 | Activity dedupe sigs session-only — re-log on fresh session |

### Verification checklist

1. Wizard + Simulation + `sim_year=2050` → F5 → same tab/year/skill
2. CC Continue with `suite_sim` only → confirm partial wizard restore
3. Cross-device → cloud summary includes view + skill + year

---

## 5. Applied Math quality audit (roadmap only)

**Flow:** Source app sidebar → `build_context_from_session` → `submit_analytical_question` → CC activity/resume → `suite_ai_*` URL → AMI preloaded branch → rule-based first pass + static worked examples

**Wired sources:** Baseball, NBA, Investment. **Not wired:** Music, Future Lens.

### Context sent vs missing

**Whitelist** (`suite_analytical_question.py`): players, team, metrics, draft fields, health_score, holdings (≤8 tickers), expected_return, volatility, macro_summary, win/series probability.

| App | Sent | Missing (available in session) |
|-----|------|--------------------------------|
| Baseball | Workflow, players, draft round | **slope/R²** (computed in `_trend_slope_r2` but not sent), ADP/VORP, stat deltas |
| NBA | Team, opponent, win % | Player totals, stat_gap, games remaining, injuries |
| Investment | Health score, tickers, return/vol, macro | Weight drift, health components, MC percentiles |

**Transport limits:** URL context **800 chars**; resume subtitle JSON **1200 chars** → holdings/metrics truncated.

**Display gap:** `trend_summary` not in `_PUBLIC_CONTEXT_KEYS` — user cannot see numeric context AMI receives.

### Analysis quality

**Engine:** `applied_math_first_pass_analysis.py` — keyword routing + rule templates.

| When | Behavior |
|------|----------|
| Context fields present (slope, health_score, stat_gap) | **Data-driven** answer |
| Fields missing | **Methodological** answer + `data_needed` list |
| No app match | Generic “define variable, baseline, threshold” |

**Critical gap:** Baseball trend computes slope/R² but AMI receives only `{direction, stat}` and `_ami_trend_direction` is **never set** → trend questions always methodological.

**AMI persistence drift:** Tests expect `_suite_ai_question` to survive refresh; `applied_intelligence_persistent_state.py` **skips autosave** when preload active — CC question lost on refresh.

### Roadmap (no implementation)

#### P0 — unlock existing code paths

1. Pass baseball `{slope, r2, n_seasons, direction}` from Trends page into `build_context_from_session`
2. Fix AMI preload persistence (align code with tests OR document intentional skip)
3. Store full context in resume item / Supabase metrics; URL as pointer only

#### P1 — richer context per app

| App | Add to context | Enables |
|-----|----------------|---------|
| Baseball | season_values[], adp, vorp, scoring weights | Draft EV, numeric trend significance |
| NBA | player, stat_totals, games_remaining, injury_status[] | Catch-up probability with numbers |
| Investment | current/target weights, max_drift, health_components, mc_percentiles | Actionable rebalance answers |

#### P1 — visibility

- Add `trend_summary`, `stat_gap`, `weight_drift` to `_PUBLIC_CONTEXT_KEYS`
- CC Continue subtitle from stored `metrics.context`, not truncated `__ctx_json__`

#### P2 — depth

- Second-pass numeric functions in AMI using attached series (not LLM)
- Extend pipeline to Future Lens + Music
- Coach insights: surface `data_needed` when context incomplete

**Related:** [cross-app-analytical-questions-v1.md](./cross-app-analytical-questions-v1.md)

---

## Recommended implementation order (after user review)

| Phase | Work | Formula/feature changes? |
|-------|------|--------------------------|
| **A** | Continue classification fixes (tags, passive event removal, music dedupe) | No |
| **B** | NBA P1: silent restore logging + Legacy Tracker player + LGC sub-state | No |
| **C** | Future Lens P0: resume URL enrichment + career activity wire/remove | No |
| **D** | Applied Math P0: baseball slope/R² + AMI preload persistence | No |
| **E** | Music P2: CPL widget keys + sync script for `suite_user_persistence.py` | No |
| **F** | Directory enrichment from `full_session` (Baseball draft, NBA workspace) | No |

**Do not start until:** Investment smoke test on Transparency Phase 1 + user approves classification table.

---

## Key code references

| Area | Path |
|------|------|
| Continue builder | `daniel-ai-command-center/project_intelligence.py` |
| App Directory | `daniel-ai-command-center/activity_store.py` |
| Music persist | `ai-music-practice-coach/music_persistent_state.py` |
| NBA persist | `nba-playoff-companion-ai/nba_persistent_state.py` |
| Future Lens persist | `future-lens-ai-transition-simulator/future_lens_persistent_state.py` |
| AMI context | `daniel-ai-command-center/suite_analytical_question.py` |
| AMI analysis | `Applied-mathematical-intelligence/components/applied_math_first_pass_analysis.py` |
| Shared persist | `suite_user_persistence.py` (each app + CC — sync gap) |
