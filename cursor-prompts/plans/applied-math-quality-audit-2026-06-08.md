# Applied Math quality audit — Priority D (2026-06-08)

**Status:** Roadmap only — **no implementation approved yet**

**Workflow:** Source app → Command Center (`analytical_question` event) → Applied Intelligence (resume URL + first-pass analysis)

**Goal:** Document what numerical context actually reaches Applied Intelligence (AMI), what is missing, and what would most improve analysis quality.

---

## Architecture (current)

```
Source app sidebar
  └─ render_applied_math_sidebar_entry()
       └─ build_context_from_session(source_app, page, session_state)
       └─ submit_analytical_question(context=ctx)
            ├─ record_activity("analytical_question", metrics=context_json)
            ├─ upsert_resume_item("applied_intelligence", …)
            └─ build_applied_math_resume_url(payload)
                 └─ suite_ai_context = context_json[:800]   ← URL cap
```

**Key modules (Command Center hub, synced to siblings):**

| Module | Role |
|--------|------|
| `suite_analytical_question.py` | `build_context_from_session`, `_PUBLIC_CONTEXT_KEYS`, submit + resume |
| `suite_deep_links.py` | URL params; `suite_ai_context` truncated to **800 chars** |
| `Applied-mathematical-intelligence/components/applied_math_first_pass_analysis.py` | Rule-based first pass; consumes full `context` dict when present |

**Storage:** Resume item subtitle embeds `__ctx_json__:{…[:1200]}` for rebuild; URL carries truncated JSON.

---

## 1. What data is currently being sent?

### Baseball

| Category | Sent today? | Source session keys | Notes |
|----------|-------------|---------------------|-------|
| Player name(s) | ✓ | `single_trend_dashboard_player`, `trend_players_multi`, draft queue | Up to 6 names on trend compare |
| Metric names | ✓ | `trend_plot_stat`, `single_trend_dashboard_stats` | Names only — e.g. HR, OPS |
| Workflow label | ✓ | Derived from page | "Player trend analysis", "Fantasy draft", etc. |
| Draft round / pick | ✓ | `draft_room_state.current_pick_index` | When on draft pages |
| Trend direction | Partial | `_ami_trend_direction`, `trend_direction_label` | **Almost never set** — keys exist in builder but baseball app never writes them |
| Trend slope | ✗ | Computed in `_trend_slope_r2`, `classify_player_trend_from_series` | Not passed to AMI |
| R² | ✗ | Same | Not passed |
| Recent slope | ✗ | `Recent Slope` in trend classifier | Not passed |
| Volatility / consistency | ✗ | Trend classifier output | Not passed |
| Year-over-year deltas | ✗ | Trend tables on page | Not passed |
| Rolling averages | ✗ | Trend dashboard | Not passed |
| Comparison stat lines | ✗ | Comparison Tool page | Only player names |
| Projection / next-year estimate | ✗ | Trend page estimates | Not passed |

**Baseball AMI entry:** Global sidebar call with `source_page=active_page` only — no `context_extra`. Trend page computes rich numerics but sidebar never receives them.

### NBA

| Category | Sent today? | Source session keys | Notes |
|----------|-------------|---------------------|-------|
| Team | ✓ | `_nba_persist_team`, `favorite_team`, `context_extra.team` | Reliable |
| Opponent | Partial | `playoff_team_state.current_opponent` | Only when playoff state populated |
| Win probability | Partial | `live_win_prob_display`, `_last_win_prob` | Live/game pages only |
| Series probability | Partial | `playoff_team_state.series_win_probability` | When bracket state exists |
| Page / workflow | ✓ | `page_label_last`, derived workflow string | Generic labels |
| Matchup metrics | ✗ | Matchup intel caches (`load_matchup_intel_*`) | Not in context builder |
| Injury assumptions | ✗ | ESPN injury report, impact notes | Not passed |
| Simulation outputs | ✗ | Fan sim, swing states, LGC overrides | Not passed |
| Statistical gaps (e.g. rebound catch-up) | ✗ | Legacy tracker totals | AMI expects `stat_gap` — **never set** |
| Player comparison focus | ✗ | Player comparison page selections | Not wired to AMI |

**NBA AMI entry:** `context_extra={"team": favorite_team}` only.

### Investment

| Category | Sent today? | Source session keys | Notes |
|----------|-------------|---------------------|-------|
| Tab / workflow | ✓ | `investment_active_tab` | Overview, Health, Macro, etc. |
| Health score | ✓ | `health_result.score` | Single scalar when computed |
| Expected return | Partial | `portfolio_expected_return`, `health_result.expected_return` | When health run exists |
| Volatility | Partial | `portfolio_volatility`, `health_result.volatility` | When health run exists |
| Portfolio value | ✓ | `sidebar_portfolio_value` | Formatted dollar string |
| Preset name | ✓ | `portfolio_preset`, `asset_preset` | Label only |
| Objective | ✓ | `portfolio_objective` | Text goal |
| Holdings tickers | Partial | `holdings_df.Ticker` | **Up to 8 tickers, no weights** |
| Macro summary | ✓ | `macro_assumption_summary()` | Text blob from macro engine |
| Weights | ✗ | `holdings_df.Weight` | Not passed |
| Portfolio drift | ✗ | Rebalance / drift views | Not passed |
| Risk metrics (Sharpe, max drawdown, etc.) | ✗ | Health panel internals | Not passed |
| Monte Carlo / scenario outputs | ✗ | Scenario tabs | Not passed |
| Efficient frontier point | ✗ | Frontier tab | Not passed |
| Correlation / concentration | ✗ | Health breakdown | Not passed |

**Investment AMI entry:** No `context_extra`; relies entirely on `build_context_from_session`.

### Cross-cutting (all apps)

| Field | Sent? | Notes |
|-------|-------|-------|
| `trend_summary` (dict) | Rarely | Builder supports `{direction, slope, r2, stat}` but `_PUBLIC_CONTEXT_KEYS` **excludes** it from display lines; still in `context_json` if set |
| Full `context_json` in URL | Truncated | **800 char max** in `suite_deep_links.py` |
| Full context in resume storage | Partial | Subtitle embed **1200 chars** of JSON |
| Quant area | ✓ | `sports` / `forecasting` / `abstract` |

---

## 2. What data is missing?

### High-impact gaps (by app)

**Baseball**

1. Slope, R², recent slope, volatility for selected player + stat
2. Trend window (years) and minimum games filter
3. Next-year projection delta vs baseline
4. Comparison Tool: side-by-side rate stats for A vs B
5. Trade analysis: players + category impact direction

**NBA**

1. Win/series probability with **model source** and timestamp
2. Matchup intel summary (pace, ORtg diff, injury-adjusted minutes)
3. Named injury list affecting probability
4. Legacy tracker / counting-record **gap** numbers (`stat_gap`)
5. Simulation slider settings when user asks about fan scenarios

**Investment**

1. Holdings **with weights** (top 8–12)
2. Drift from target allocation (%)
3. Health sub-scores (diversification, concentration flags)
4. Risk metrics already on screen (not recomputing formulas — **display values only**)
5. Active macro scenario assumptions (rates, inflation path) as structured fields

---

## 3. What would most improve analysis quality?

Ranked by impact vs implementation cost:

| Priority | Change | Why |
|----------|--------|-----|
| **P0** | Baseball: pass `trend_summary` with slope, R², direction, window from Trend Value page via `context_extra` | AMI first-pass already reads `trend_summary.slope/r2`; today it always falls back to "methodological" answer |
| **P0** | Expand `_PUBLIC_CONTEXT_KEYS` to include `trend_summary`, `stat_gap`, `weights`, `drift` | Human-readable context lines + dedupe |
| **P1** | NBA: pass win/series prob + opponent + `stat_gap` from active page via `context_extra` | Enables catch-up probability and probability reasonableness paths |
| **P1** | Investment: pass tickers **with weights** + drift % from health result | Rebalance questions need weights, not ticker list alone |
| **P2** | Baseball Comparison: pass rate-stat snapshot for A/B | Compare workflow currently name-only |
| **P2** | NBA: injury summary string (top 3 OUT/GTD) | Matchup questions reference injuries verbally |
| **P3** | Structured macro fields (rate, inflation) vs free-text only | Better macro reasoning without formula changes |

**Explicitly out of scope (user):** formula redesign, MC/frontier/optimizer/health score/macro model changes. Pass **existing computed display values** only.

---

## 4. What context is lost due to URL limits?

| Limit | Location | Effect |
|-------|----------|--------|
| **800 chars** | `suite_deep_links.py` → `suite_ai_context` | Long holdings lists, multi-player trends, macro text truncated mid-JSON → AMI preload may parse incomplete JSON |
| **1200 chars** | `analytical_question_storage_subtitle` | Resume rebuild from storage may lose tail of context |
| **500 chars** | `suite_ai_question` | Long user questions truncated |
| Query param encoding | All `suite_*` params | Special characters in player names / questions |

**Typical loss scenarios:**

- Investment: 8 tickers + macro_summary + health fields → JSON often **>800 chars**
- Baseball trend compare: 6 players × multiple metrics → names survive, numerics never sent anyway
- NBA: injury paragraph + probabilities → would truncate if added without server storage

**Mitigation options (roadmap — not implemented):**

1. **Server-side context blob** (Supabase) keyed by `question_id` — URL carries id only
2. **Resume item metrics** full `context` dict (already stored in activity; AMI should read from CC resume fetch, not URL alone)
3. **Tiered context**: URL = summary hash + id; AMI hydrates from Supabase on load

---

## 5. Should context move to server-side storage?

**Recommendation: Yes, for P0 quality work — phased.**

| Phase | Approach |
|-------|----------|
| **Phase 1 (quick win)** | AMI on load: prefer resume item / activity `metrics.context` over URL `suite_ai_context` parse |
| **Phase 2** | On submit: `upsert` full context to `suite_app_current_state` or dedicated `suite_ami_context` table keyed by `question_id` |
| **Phase 3** | URL carries only `suite_ai_qid={question_id}`; drop 800-char JSON from URL |

**Why:**

- URL limits are the binding constraint for Investment + multi-player Baseball
- Command Center already stores `context_json` in activity metrics and resume subtitle
- Duplicating truncated JSON in URL is redundant and lossy

**Risk:** AMI opened without CC session must still work → keep URL summary fallback until Phase 3 proven.

---

## Proposed implementation order (after user approval)

1. **Baseball P0** — Trend Value page sets `context_extra.trend_summary` from computed slope/R²/direction (no formula changes)
2. **AMI preload** — Read full context from resume metrics before URL parse
3. **NBA P1** — Page-specific `context_extra` for live/playoff/matchup pages
4. **Investment P1** — Weights + drift from existing health/holdings display
5. **Server-side context store** — Phase 2–3 if URL truncation still bites after 1–4

---

## Verification plan (post-implementation)

1. Trend Value: send question → inspect activity `metrics.context_json` contains slope + R²
2. AMI first pass: answer cites numeric slope/R², not "methodological" fallback
3. Investment: rebalance question includes weight percentages in context display
4. NBA playoff: series probability appears in AMI assumptions
5. Deliberately long context → confirm server hydrate works when URL truncated

---

## Related docs

- Suite usability audit §5 — [suite-usability-audit-2026-06-08.md](./suite-usability-audit-2026-06-08.md)
- Command Center tasks — [app_tasks.md](../app_tasks.md) P5

**Last updated:** 2026-06-08
