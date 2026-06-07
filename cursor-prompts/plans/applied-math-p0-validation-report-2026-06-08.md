# Applied Math P0 — Quality Validation Report

**Date:** 2026-06-08  
**Scope:** Verify richer context arrives at Applied Intelligence and improves first-pass answers. No new product features (diagnostics only).

---

## Executive summary

| Source app | Context pipeline | Answer uses context | Live quality (1–10) |
|------------|------------------|---------------------|---------------------|
| Baseball — Historical Explorer | **Partial** (snapshot only after table renders) | **Weak** (player name only, not table stats) | **6** |
| Baseball — Trend Value | **Strong** (slope, R², delta when intel runs) | **Strong** | **9** |
| Baseball — Comparison | **Strong** (both players + diffs after intel table) | **Good** (names + slope diffs when present) | **8** |
| NBA — Matchup | **Partial** (team/opponent only; no matchup metrics hook) | **Weak** | **5** |
| NBA — Live / Probability | **Strong** (win + series probability) | **Strong** | **9** |
| NBA — Legacy Tracker | **Missing** (no `_ami_legacy_context` / stat-gap hooks) | **N/A without hooks** | **3** |
| Investment — Portfolio Health | **Strong** | **Good** (health, holdings, Sharpe) | **8** |
| Investment — Rebalance | **Missing** (`rebalance_drift` never populated in UI) | **Partial** (health only if on tab) | **4** |
| Investment — Macro | **Strong** (macro + forward/historical labels) | **Good** | **8** |

**Command Center:** Continue cards remain clean (question only) — verified by automated test.

**Developer diagnostics:** Added to Applied Intelligence (Developer Mode sidebar toggle → **Context received** expander).

---

## Baseball

### Test 1 — Historical Explorer

**Example question:** “Is Mike Trout's 2019 season an outlier in this table?”

**What arrives (after table renders):**
- ✅ `filters_applied` (year range, sort stat)
- ✅ `metrics` (sort stat)
- ✅ `historical_snapshot` (top 5 rows, sort_stat, year_range, top_players)
- ⚠️ `player` — only if user selected a player (`historical_selected_player`); otherwise top_players from snapshot

**What is missing if user sends before table loads:**
- ❌ `historical_snapshot` (cached at end of page render)
- ❌ Visible stat values in answer

**Example answer (first-pass):** Generic decision framework anchored on player name — does **not** cite HR 45 or table rows from snapshot.

**Quality rating:** **6/10** (context good when snapshot cached; answer does not yet use table numbers)

---

### Test 2 — Trend Value

**Example question:** “Is Lorenzo Cain's HR trend meaningful?”

**What arrives:**
- ✅ `player`, `metrics`
- ✅ `trend_summary.slope`, `.r2`, `.delta`, `.summary` (after Advanced Trend Intelligence runs)

**Example answer:** “Estimated slope: **1.2** per season. Fit (R²): **0.64**…”

**Quality rating:** **9/10**

---

### Test 3 — Comparison Tool

**Example question:** “Is Piazza better than Bagwell for my league?”

**What arrives:**
- ✅ `player_a`, `player_b`, `players`
- ✅ `comparison_differences` (after Advanced Trend Intelligence on comparison page)

**Example answer:** References both players; includes slope snippets from diffs when present.

**Quality rating:** **8/10**

---

## NBA

### Test 1 — Matchup

**Example question:** “How much does the injury gap matter?”

**What arrives:**
- ✅ `team`, `opponent`, `workflow`
- ❌ Matchup-specific metrics (`_ami_matchup_context` never written in `streamlit_app.py`)

**Example answer:** Generic rate × minutes framework — does not use injury or gap metrics.

**Quality rating:** **5/10**

---

### Test 2 — Probability (Live Game Center)

**Example question:** “Is 62% win probability reasonable?”

**What arrives:**
- ✅ `team`, `opponent`
- ✅ `win_probability`, `series_probability`

**Example answer:** “For New York Knicks: if **62%** is far from a simple strength model…”

**Quality rating:** **9/10**

---

### Test 3 — Legacy Tracker

**Example question:** “Will Jalen Brunson pass Allan Houston in playoff rebounds?”

**What arrives (live):**
- ✅ `team`, `workflow`
- ❌ `player`, `stat_gap`, `current_value`, `target_value`, `gap`, `games_remaining`, `rate_needed`

**Note:** Extractor reads `_ami_legacy_context` / `_ami_stat_gap_context` but **no page hooks populate them**.

**Example answer (with full fixture context):** References gap, games remaining, rate needed — **works when context is manually present**.

**Quality rating:** **3/10 live** / **9/10 with populated hooks**

---

## Investment

### Test 1 — Portfolio Health

**Example question:** “Is my portfolio too risky?”

**What arrives:**
- ✅ `holdings`, `current_weights`
- ✅ `health_score`, `sharpe_ratio`, `max_drawdown`, `expected_return`, `volatility`
- ✅ `context_note_historical`

**Example answer:** Cites health score and holdings.

**Quality rating:** **8/10**

---

### Test 2 — Rebalance

**Example question:** “Should I rebalance now?”

**What arrives (live):**
- ✅ Health metrics if `health_result` in session
- ❌ `rebalance_drift`, rebalance recommendation (no session hook)

**Quality rating:** **4/10**

---

### Test 3 — Macro

**Example question:** “How does recession risk affect my portfolio?”

**What arrives:**
- ✅ `macro_outlook`, `macro_summary`
- ✅ `context_note_forward` (macro → forward projections)
- ✅ `context_note_historical` (return/vol are historical)

**Example answer:** Assumptions mention forward macro; answer body includes historical note.

**Quality rating:** **8/10**

---

## Command Center

- Continue cards show: **App name**, **question**, **Continue in Applied Mathematics** only.
- No raw context on cards — confirmed by `test_command_center_card_stays_clean`.

---

## Developer diagnostics (Applied Intelligence)

Enable **Developer Mode** in AMI sidebar when debugging a Continue flow:

- Question ID
- Source app / page
- Fields received vs expected-for-page missing list
- Context JSON size + hydration hint
- Raw context JSON (truncated display)

---

## Recommended P1 fixes (after this validation pass)

1. **NBA Legacy / stat-gap:** Populate `_ami_stat_gap_context` on Legacy Tracker when showing leader/challenger totals.
2. **NBA Matchup:** Populate `_ami_matchup_context` with injury summary and key gaps.
3. **Investment Rebalance:** Cache `rebalance_drift` + recommendation when drift analysis runs.
4. **Baseball Historical:** First-pass branch using `historical_snapshot.top_rows` stat values.
5. **NBA Matchup first-pass:** Reference team/opponent and any matchup metrics in answer.

---

## Tests added

- `Applied-mathematical-intelligence/tests/test_applied_math_quality_validation.py` (4 tests, all passing)
- `Applied-mathematical-intelligence/applied_math_quality_validation.py` (scenario fixtures + rating)
- `Applied-mathematical-intelligence/components/applied_math_context_diagnostics.py`

Run: `python -m unittest tests.test_applied_math_quality_validation -v` from AMI repo root.
