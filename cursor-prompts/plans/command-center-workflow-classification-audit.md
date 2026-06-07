# Command Center workflow classification audit

**Last updated:** 2026-06-07  
**Status:** Audit complete — **no ranking/filter changes implemented yet**

## Goal

Separate **Continue Where You Left Off** (resume active workflow) from **App Directory** (durable app state).

**Rules:**
- Continue = most recent meaningful workflow the user would resume
- App Directory = long-term work, current song/portfolio/team/simulation/lesson
- Applied Math questions = **Continue only** (never App Directory)

## How surfaces are built today

| Surface | Source | Limit |
|---------|--------|-------|
| **Continue** | `project_intelligence._projects_from_events` + `load_active_resume_items` → merge by key, sort priority, top **6** | 14-day stale cutoff |
| **App Directory** | `activity_store.get_app_directory_card(snapshot, app_key)` from `ActivitySnapshot` | 3 highlight lines per app |
| **Activity logging** | `suite_activity_client.record_activity` → events + optional `suite_resume_items` | Per-app `*_activity.py` hooks |

Key files: `project_intelligence.py`, `continue_dashboard.py`, `activity_store.py`, `activity_feed.py`, `suite_analytical_question.py`.

---

## Master classification table

**Legend:** ✅ = recommended placement | ⚠️ = current misclassification

### Cross-app

| Workflow | Continue | App Directory | Both | Neither | Current | Notes |
|----------|:--------:|:-------------:|:----:|:-------:|---------|-------|
| Applied Math question (Baseball/NBA/Investment → AMI) | ✅ | | | | **Continue** | ✅ Correct — Directory filters `?` text |

### Music

| Workflow | Continue | App Directory | Both | Neither | Current | Notes |
|----------|:--------:|:-------------:|:----:|:-------:|---------|-------|
| Song practice session (`practice`) | ✅ | | ✅ | | Both | Session = Continue; song identity = Directory |
| Verified chord/chart save | ✅ | | ✅ | | Both | Edit work = Continue |
| Verified lyrics save | ✅ | | ✅ | | Both | Same |
| Backing track session | ✅ | | | | Continue | Active session |
| Recording upload / review | ✅ | | | | Continue | Active workflow |
| Studio page entered | ✅ | | | | Continue | e.g. Piano, Eb Major page |
| Display key / capo change | ✅ | | | | Continue | Resume exact key context |
| **Current song selected** (`song_selected`) | | ✅ | | | **Both** ⚠️ | Should be **Directory only** |
| Instrument switch | | ✅ | | | Continue + Directory partial | Instrument = Directory state |
| New song added to catalog | | ✅ | | | Directory partial | Long-term catalog |
| Instrument-only navigation | | | | ✅ | Neither | Too lightweight for Continue |

### Investment

| Workflow | Continue | App Directory | Both | Neither | Current | Notes |
|----------|:--------:|:-------------:|:----:|:-------:|---------|-------|
| Portfolio Health review | ✅ | | ✅ | | Both | Matches user example |
| Monte Carlo / scenario run | ✅ | | | | Continue | Transient analysis |
| Allocation drift review | ✅ | | | | Continue | |
| Rebalance guidance review | ✅ | | | | Continue | |
| Optimizer run | ✅ | | | | Continue partial | |
| **Holdings updated** | | ✅ | | | **Continue** ⚠️ | Should be **Directory only** (portfolio state) |
| Portfolio created | | ✅ | | | Directory | Long-term setup |
| Goal selected | | ✅ | | | Directory | |
| Risk profile changed | | ✅ | | | Directory | |
| Macro environment applied | | | | ✅ | Neither | Settings change, not workflow |
| Ticker analyzed | | | | ✅ | Neither | Light lookup |
| Efficient frontier viewed | | | | ✅ | Neither | Feed suppressed |

### Baseball

| Workflow | Continue | App Directory | Both | Neither | Current | Notes |
|----------|:--------:|:-------------:|:----:|:-------:|---------|-------|
| Player trend chart (`player_trend_viewed`) | ✅ | | | | Continue | e.g. Lorenzo Cain trend |
| Trend comparison (`trend_comparison_viewed`) | ✅ | | | | Continue | Multi-player trends |
| Player comparison (`player_comparison`) | ✅ | | | | Continue | e.g. Soto vs Piazza |
| Trade analysis | ✅ | | | | Continue | |
| Fantasy draft prep | ✅ | | | | Continue | |
| ML projection report | ✅ | | | | Continue partial | |
| Breakout/decline list | ✅ | | | | Continue weak | Low priority |
| **Last player in Directory** | | ✅ | | | **Directory** ⚠️ | Shows transient chart player, not durable context |
| Current draft room state | | ✅ | | | Partial | Should surface draft/watchlist in Directory |
| Roster build / sleeper research | | | | ✅ | Neither / resume only | Not active resume workflow |
| Trend filter change only | | | | ✅ | Neither | Correctly excluded |

### NBA

| Workflow | Continue | App Directory | Both | Neither | Current | Notes |
|----------|:--------:|:-------------:|:----:|:-------:|---------|-------|
| Live Game Center (`game_outlook`) | ✅ | | ✅ | | Both partial | Game = Continue; team = Directory |
| Matchup analysis | ✅ | | | | Continue | |
| Injury report analysis | ✅ | | | | Continue | |
| Playoff simulation | ✅ | | | | Continue | |
| **Current team** | | ✅ | | | Directory | e.g. Knicks |
| **Last page viewed** | | ✅ | | | Directory | e.g. Live Game Center |
| Player comparison | ✅ | | | | **Neither** ⚠️ | Logged but no Continue candidate |
| Playoff tracker review | | ✅ | | | **Neither** ⚠️ | Feed only — consider Directory |

### Applied Intelligence

| Workflow | Continue | App Directory | Both | Neither | Current | Notes |
|----------|:--------:|:-------------:|:----:|:-------:|---------|-------|
| Applied Math question (suite) | ✅ | | | | Continue | Never Directory |
| Lesson completed | ✅ | | ✅ | | Both | Lesson = Directory if short, no `?` |
| Problem solved (library) | ✅ | | ✅ | | Both | Questions with `?` blocked from Directory |
| Case study / module / reasoning | ✅ | | ✅ | | Both partial | |

### Future Lens

| Workflow | Continue | App Directory | Both | Neither | Current | Notes |
|----------|:--------:|:-------------:|:----:|:-------:|---------|-------|
| Simulation completed | ✅ | | ✅ | | Both | Sim name = Directory |
| Career transition analysis | ✅ | | ✅ | | **Neither** ⚠️ | Logged but not in `_projects_from_events` |
| Technology timeline review | ✅ | | | | **Neither** ⚠️ | Feed only |
| Skill forecast review | | ✅ | | | **Neither** ⚠️ | Long-term skill focus → Directory |

---

## Top misclassifications (fix order)

1. **`song_selected` → Continue** — passive catalog pick should be Directory only (current song/instrument/key)
2. **`holdings_updated` → Continue** — portfolio state belongs in Directory; Continue only after explicit allocation/rebalance review
3. **Future Lens career/timeline/skill** — events log but no Continue wiring in `_projects_from_events`
4. **NBA `player_comparison` / `playoff_tracker_review`** — logged, no Continue candidate
5. **Baseball Directory "Last player"** — reflects last chart, not durable draft/watchlist/comparison project
6. **Applied Math guard** — keep Continue-only; watch AMI `problem_solved` text without `?` leaking to Directory

## Structural constraints

- Only **6** Continue cards shown — lower-priority workflows dropped silently
- **14-day stale** cutoff hides older workflows
- Dual paths: events + `resume_items` + `load_current_states` fallback can disagree
- Ranking changes should follow this classification table, not ad hoc priority tweaks

## Proposed next steps (after approval)

1. Add `CONTINUE_ONLY` / `DIRECTORY_ONLY` / `BOTH` / `NEITHER` tags per event type in `project_intelligence.py`
2. Remove `song_selected` and `holdings_updated` from `_projects_from_events` Continue path
3. Wire missing Future Lens + NBA events into Continue candidates
4. Enrich Baseball/NBA Directory with durable state (draft, watchlist, team) from `full_session` cloud blobs
5. Deep-link resume must restore exact page/entity (already partially wired via `suite_resume_launch`)

## Verification (before/after changes)

1. Log each workflow in source app → confirm event in storage
2. Command Center Continue top 6 matches classification table
3. App Directory shows durable state only — no analytical questions
4. Applied Math question: Continue only, opens AMI with full context
