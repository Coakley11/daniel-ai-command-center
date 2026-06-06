# Suite workflow coverage audit

**Last updated:** 2026-06-06  
**Goal:** Every meaningful workflow (10+ seconds of analysis) should be **logged**, **Continue-eligible** (or explicitly excluded), and **restorable** where applicable.

Legend:
- **Continue?** — appears in Command Center Continue when recent + high enough priority
- **App Directory?** — drives `get_app_directory_card()` highlights (Music/Investment have rank functions; Baseball/NBA use snapshot + disk state)
- **Restore?** — deep link / resume launch returns to same page + context

---

## Baseball Stat App

| Workflow | Logged? | event_type | Continue? | App Directory? | Priority | Restore? | Notes |
|----------|---------|------------|-----------|----------------|----------|----------|-------|
| Single-player trend chart | ✅ | `player_trend_viewed` | ✅ | Partial (snapshot) | 58 | ✅ `trend:{player}` | Fires after dashboard chart render |
| Multi-player trend comparison | ✅ | `trend_comparison_viewed` | ✅ | Partial | 59 | ✅ `trendcompare:A:B` | **Continue wired 2026-06-06** |
| Player comparison (Comparison Tool) | ✅ | `player_comparison` | ✅ | Partial | 59 | ✅ `compare:A:B` | Stat sig / compare page — not Trends |
| Trade analysis | ✅ | `trade_analysis` | ✅ | Partial | 54 | ✅ `bb:trade` | Fantasy Lineup Assistant |
| Draft simulation prep | ✅ | `draft_prep` | ✅ | Partial | 56 | ✅ `bb:draft` | Draft Simulation Test Mode lab |
| Live draft / roster build | ✅ | `roster_build` | Partial | Partial | ~35 via resume | Partial | Logged when lab completes with team |
| Draft queue edits | ❌ | — | ❌ | ❌ | — | Session only | **Excluded:** sidebar MRU; use draft_prep when sim completes |
| Watchlist additions | ❌ | — | ❌ | ❌ | — | Session only | **Excluded:** low signal; would spam Continue |
| Breakout / decline lists | ✅ | `breakout_analysis` | Weak | Partial | 35 | Partial `baseball:breakouts` | Filter-driven, not player-specific |
| Sleeper / bust research | ✅ | `sleeper_research` | Partial | Partial | ~35 | Partial | Fantasy Market table |
| ML projection report | ✅ | `projection_report` | Partial | Partial | ~48 | Partial `baseball:projections` | Logged on ML run; not always latest baseball workflow |
| Trend filter change only | ✅ | `trend_filter_changed` | ❌ | ❌ | — | — | **Excluded:** aggregate filter tweak, no named workflow |
| Player insight row (trend/market/draft/ML) | ❌ | — | ❌ | ❌ | — | — | **Excluded:** widget selection; no analysis completed |
| Feature-importance / ML insight drill-down | ❌ | — | ❌ | ❌ | — | — | **Excluded:** not wired — **P1 backlog** |
| Valuation table analysis | ❌ | — | ❌ | ❌ | — | Disk state | **P1 backlog:** user spends time on Valuation page |
| Live Draft Room picks | ❌ | — | ❌ | ❌ | — | Disk state | **P1 backlog:** log on pick commit or export |
| Custom / saved rankings | ❌ | — | ❌ | ❌ | — | — | No dedicated rankings builder page found |
| Team builder | ❌ | — | ❌ | ❌ | — | — | No standalone "Team Builder" page — draft room serves this |

**Baseball gaps (recommended P1 logging):** Valuation review, Live Draft pick, ML insight player selected, draft queue milestone (optional).

---

## Music Practice Coach

| Workflow | Logged? | event_type | Continue? | App Directory? | Priority | Restore? | Notes |
|----------|---------|------------|-----------|----------------|----------|----------|-------|
| Song selected | ✅ | `song_selected` | ✅ | ✅ rank 55 | 55 | ✅ `song:{pick}` | Via songs/state |
| Verified chart saved | ✅ | `verified_chart_saved` | ✅ | ✅ rank high | 58+ | ✅ | Chord/chart edits |
| Practice log saved | ✅ | `practice` | ✅ | ✅ | 65 | ✅ | Practice Log tab |
| Display key changed | ✅ | `display_key_changed` | ✅ | ❌ | 62 | ✅ | |
| Instrument changed | ✅ | `instrument_changed` | ✅ | ❌ | 60 | ✅ | |
| Studio page entered | ✅ | `studio_page_entered` | ✅ | ❌ | 58 | ✅ | practice/backing/recording |
| Backing track started | ✅ | `backing_track_started` | ✅ | ✅ | 70 | ✅ `backing:{pick}` | |
| Backing track completed | ✅ | `backing_track_completed` | ✅ | ✅ | 68 | ✅ | |
| Recording upload | ✅ | `video_uploaded` / `audio_uploaded` | ✅ | ✅ | 55 | ✅ | |
| Recording reviewed | ✅ | `recording_reviewed` | Partial | Partial | 52 | ✅ | |
| Catalog favorites toggle | ❌ | — | ❌ | ❌ | — | Disk | **Excluded:** preference only |
| Practice log coach refresh | ❌ | — | ❌ | ❌ | — | — | **Excluded:** derived UI |

---

## Investment Portfolio Analyzer

| Workflow | Logged? | event_type | Continue? | App Directory? | Priority | Restore? | Notes |
|----------|---------|------------|-----------|----------------|----------|----------|-------|
| Portfolio health check | ✅ | `portfolio_health_checked` | ✅ | ✅ rank 5 | 58 | ✅ fingerprint | Requires explicit completion flow |
| Portfolio created / confirmed | ✅ | `portfolio_created` | ✅ | ✅ | 48 | ✅ | Beginner "Use this portfolio" |
| Holdings updated | ✅ | `holdings_updated` | ✅ | ✅ | 48 | ✅ | |
| Goal selected | ✅ | `investment_goal_selected` | Partial | ✅ | low | Partial | |
| Efficient frontier viewed | ✅ | `frontier_viewed` | Partial | Partial | — | Partial | Logged; weak Continue mapping |
| Scenario / Monte Carlo | ✅ | `scenario_run` | ✅ | Partial | 50 | ✅ `inv:scenario` | Hook exists; verify UI calls it |
| Rebalance reviewed | ✅ | `rebalance_reviewed` | Partial | Partial | — | Partial | |
| Ticker analyzed | ✅ | `ticker_analyzed` | ❌ | ❌ | — | — | **Excluded:** light lookup |
| Optimizer run | ✅ | `optimizer_run` | Partial | Partial | — | Partial | |
| Risk profile changed | ✅ | `risk_profile_changed` | ❌ | ❌ | — | — | Feed only |
| Macro environment | ✅ | `macro_environment_applied` | ❌ | ❌ | — | — | **P2** |

---

## NBA Playoff Companion

| Workflow | Logged? | event_type | Continue? | App Directory? | Priority | Restore? | Notes |
|----------|---------|------------|-----------|----------------|----------|----------|-------|
| Live Game Center outlook | ✅ | `game_outlook` | ✅ | Disk team | 60 | ✅ `nba:game:{team}` | |
| Matchup analysis | ✅ | `matchup_analysis` | ✅ | Partial | 56 | ✅ | Page-context hook |
| Injury analysis | ✅ | `injury_analysis` | ✅ | Partial | 50 | ✅ | |
| Playoff simulation | ✅ | `playoff_simulation` | ✅ | Partial | 54 | ✅ | |
| Player comparison | Partial | `player_comparison` | Partial | ❌ | — | — | Verify if wired in UI |
| Team select alone | ❌ | — | ❌ | Disk | — | Disk | **Excluded:** navigation |

---

## Future Lens AI Transition Simulator

| Workflow | Logged? | event_type | Continue? | App Directory? | Priority | Restore? | Notes |
|----------|---------|------------|-----------|----------------|----------|----------|-------|
| Simulation completed | ✅ | `simulation_completed` | ✅ | Partial | 50 | ✅ `sim:{name}` | Verify UI calls hook |
| Career analysis | ✅ | `career_analysis` | ✅ | Partial | 54 | ✅ | |
| Skill forecast review | ✅ | `skill_forecast_review` | Partial | Partial | — | Partial | |
| Technology timeline | ✅ | `technology_timeline_review` | Partial | Partial | — | ✅ `timeline:` | |

**Gap:** Confirm each simulation UI path calls `future_lens_activity` (not just module exists).

---

## Applied Mathematical Intelligence

| Workflow | Logged? | event_type | Continue? | App Directory? | Priority | Restore? | Notes |
|----------|---------|------------|-----------|----------------|----------|----------|-------|
| Lesson completed | ✅ | `lesson_completed` | ✅ | Partial | 48 | ✅ | |
| Problem solved | ✅ | `problem_solved` | ✅ | Partial | 48 | ✅ | |
| Case study completed | ✅ | `case_study_completed` | ✅ | Partial | — | ✅ | |
| Module completed | ✅ | `module_completed` | Partial | Partial | — | ✅ | |
| Reasoning exercise | ✅ | `reasoning_exercise_completed` | Partial | Partial | — | ✅ | |
| Concept explored | ❌ | — | ❌ | ❌ | — | — | **P2 backlog** |

---

## Command Center routing summary

| Layer | Role |
|-------|------|
| App `*_activity.py` hooks | Write events + resume_key |
| `suite_activity_client` | Supabase / SQLite / fallback |
| `activity_feed` | Human-readable Recent Activity |
| `project_intelligence._projects_from_events` | Continue card candidates |
| `build_project_continue_cards` | Merge events + resume_items, rank, limit 6 |
| `get_app_directory_card` | Per-app homepage summary (Music/Investment ranked) |
| `suite_deep_links` + `suite_resume_launch` | Restore page + context |

---

## Implementation status (2026-06-06)

- ✅ Lorenzo Cain single-player trend pipeline proven
- ✅ Multi-player trend logging (`trend_comparison_viewed`)
- ✅ Continue card for `trend_comparison_viewed` (priority 59, same tier as player comparison)
- 📋 P1: Baseball Valuation, Live Draft, ML insight hooks
- 📋 P2: Cross-app verification that Future Lens / Applied Math UI calls existing hooks

See also: `baseball-stat-app/docs/baseball_workflow_activity_audit.md`
