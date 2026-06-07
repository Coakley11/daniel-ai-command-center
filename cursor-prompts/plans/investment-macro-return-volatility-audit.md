# Investment calculation audit (code-level)

**Last updated:** 2026-06-07  
**Status:** Audit complete — **no formula changes** until user approves UI/recommendations

Repo: `investment-portfolio-analyzer`

---

## Naming note

There is **no metric named "Macro Score"**. Closest equivalent: **Macro Regime Fit** (`s_macro`, 0–10 pts of 100) inside `evaluate_portfolio_health()`.

**Market outlook** maps to **Valuation Environment** (`health_valuation` → `ForwardMacroAssumptions.valuation`).

---

## Per-metric audit

### Expected Return

| Question | Answer |
|----------|--------|
| **Functions** | Historical: `annualized_return()` → `compute_extended_metrics()` (`portfolio_core.py`). Forward: `compute_forward_projection_with_profile()` → `adj_return`; orchestrated by `get_forward_projection()` (`components/macro_engine.py`). |
| **Historical or forward** | **Both.** Overview = historical. Forward Macro / MC / Optimizer / Frontier (forward mode) = macro-adjusted forward. |
| **Date range affects?** | **Yes (historical).** `settings["start"]`/`["end"]` → `load_market_data()` → daily returns → `compute_extended_metrics()`. Forward baseline uses that historical `metrics.annual_return`. |
| **Macro affects?** | **Forward only (real math).** `ret_shift` from `_rate_environment_effects`, `_inflation_effects`, `_valuation_effects`, `_economic_regime_effects`, recession terms. Overview return **not** macro-adjusted. |
| **Beginner = Advanced?** | **Same value.** Labels differ: "Average Yearly Return" vs "Annual Return" (`metrics_row_primary()` in `streamlit_app.py`). |
| **UI pages** | Overview, Portfolio Analytics export, Forward Macro ("Forward Return"), Monte Carlo (forward), Optimization (forward), Efficient Frontier (forward), sidebar Metrics CSV. |

### Volatility

| Question | Answer |
|----------|--------|
| **Functions** | Historical: `annualized_volatility()` → `compute_extended_metrics()`. Forward: `adj_vol = max(0.001, metrics.volatility * vol_mult)` in `compute_forward_projection_with_profile()`. |
| **Historical or forward** | **Both.** |
| **Date range affects?** | **Yes (historical).** Std of daily returns in window × √252. |
| **Macro affects?** | **Forward only.** `vol_mult` = product of rate/inflation/valuation/regime multipliers × `(1 + recession_prob × 0.75)`. |
| **Beginner = Advanced?** | **Same value.** "How Bumpy (Volatility)" vs "Volatility". |
| **UI pages** | Overview, Analytics export, Risk Analysis vol ranking, Forward Macro, MC/Optimizer/Frontier (forward), guided-adjustment preview (historical only). |

### Sharpe Ratio

| Question | Answer |
|----------|--------|
| **Functions** | `sharpe_ratio(ann_return, ann_vol, risk_free_rate)` in `portfolio_core.py`; called from `compute_extended_metrics()` and `compute_forward_projection_with_profile()`. |
| **Historical or forward** | **Both.** Health uses **historical** sharpe for `s_sharpe` component (`clip(sharpe × 10, 0, 15)`). |
| **Date range affects?** | **Yes (historical).** Via return and vol in window. |
| **Macro affects?** | **Forward Sharpe only** (derived from macro-adjusted return/vol). Health component uses historical sharpe. |
| **Beginner = Advanced?** | **Same value.** "Risk/Reward Score" vs "Sharpe Ratio". |
| **UI pages** | Overview, Analytics export, Forward Macro, Optimizer comparison, Risk Analysis macro-regime table, guided preview. |

### Drawdown

| Question | Answer |
|----------|--------|
| **Functions** | Historical: `maximum_drawdown(port_rets)` → `compute_extended_metrics()`. Forward stress: `adj_dd = metrics.max_drawdown * (1 + recession_prob × 0.90)` in `compute_forward_projection_with_profile()`. Per-asset: `_drawdown_contribution_df()`. |
| **Historical or forward** | Historical = peak-to-trough in date window. "Forward Max Drawdown" = **scaled historical**, not forward path simulation (`calculation_transparency.py`, `docs/MODEL_ASSUMPTIONS.md`). |
| **Date range affects?** | **Yes (historical).** |
| **Macro affects?** | **Recession probability** scales forward drawdown only. Health "Max Drawdown" component uses **historical** `metrics.max_drawdown`. |
| **Beginner = Advanced?** | **Same value.** "Worst Drop" vs "Max Drawdown". |
| **UI pages** | Overview extended metrics, Analytics export, Forward Macro, Portfolio Health advanced charts, Risk Analysis narrative. |

### Portfolio Health Score

| Question | Answer |
|----------|--------|
| **Functions** | `evaluate_portfolio_health()` (`portfolio_core.py`); cache: `evaluate_portfolio_health_if_needed()`, `cache_health_summary()`, `get_health_cache_status()` (`streamlit_app.py`). Display: `render_health_score_card()` (Advanced), `_render_health_score_card()` (`components/beginner_coach.py`). |
| **Historical or forward** | **Historical metrics + macro-fit sub-score.** Eight components; macro only via `s_macro` (0–10 pts) and rule-based text/recommendations. |
| **Date range affects?** | **Yes.** All metric inputs from selected historical window. |
| **Macro affects?** | **Partially (real scoring).** `s_macro` adjusted by rate env, inflation vs long bonds, recession vs equity/tbills, regime. Does **not** macro-adjust return/vol/sharpe/drawdown inputs. |
| **Beginner = Advanced?** | **Same `health.score`.** Advanced shows breakdown dataframe; Beginner hides sub-scores. |
| **UI pages** | Portfolio Health tab, Overview health snapshot, header badge, Analyze beginner results, action plan. |

**Breakdown keys:** Return vs Benchmark, Volatility Level, Sharpe Ratio, Max Drawdown, Diversification, Concentration Risk, Objective Alignment, **Macro Regime Fit**.

### Recommendations

| Question | Answer |
|----------|--------|
| **Functions** | `evaluate_portfolio_health()` → `recommendation_details` / `recommendations`; display via `render_recommendations_panel()` (`components/decision_coach.py`). Separate: `recommend_portfolio()` (age/horizon/objective — **no macro**). |
| **Historical or forward** | **Historical metrics + macro assumption checks.** Not forward-projected returns. |
| **Date range affects?** | **Indirectly** via historical metrics in triggers. |
| **Macro affects?** | **Yes — real rules + text.** Macro rules: `recession_prob > 0.50` + equity > 70%; `inflation == "High Inflation"` + long-duration bonds > 20%. Rebalance drift uses historical optimizer (`optimize_max_sharpe` on historical mean/cov). `macro_fit` list is **text only**. |
| **Beginner = Advanced?** | **Same `health.recommendation_details`.** Beginner gets plainer copy. |
| **UI pages** | Portfolio Health Recommendations, Overview Recommendations, Analyze beginner "Why?", Rebalancing/Guided Adjustment, workflow checklist. |

### Macro Score (= Macro Regime Fit)

| Question | Answer |
|----------|--------|
| **Functions** | `s_macro` block in `evaluate_portfolio_health()` (`portfolio_core.py` ~1807–1825). Reference heatmap: `_macro_heatmap_df()` (not user score). Scenario table: `macro_regime_analysis()` (fixed presets, **not** user sliders). |
| **Historical or forward** | **Neither** — heuristic fit of macro assumptions × portfolio profile. |
| **Date range affects?** | **No** directly. |
| **Macro affects?** | **Yes — this IS the macro score.** |
| **Beginner = Advanced?** | **Same value** in total score; Advanced shows 0–10 in breakdown; Beginner macro panel text only. |
| **UI pages** | Portfolio Health advanced breakdown, `macro_fit` commentary, beginner "Overall Environment" text (text only). |

---

## Macro dependency map

```
Macro session keys (health_rate_env, health_inflation, health_recession,
                    health_valuation, health_regime)
        │
        ▼
macro_assumptions_from_session()                    [macro_engine.py]
        │
        ├─► REAL CALCULATION (forward μ, σ, drawdown scale)
        │   compute_forward_projection_with_profile() [portfolio_core.py]
        │     ├─ _rate_environment_effects()
        │     ├─ _inflation_effects()
        │     ├─ _valuation_effects()
        │     ├─ _economic_regime_effects()
        │     └─ recession_prob → ret_shift, vol_mult, drawdown_mult, corr_stress
        │   get_forward_projection() [cached]
        │     → Forward Macro tab, Monte Carlo (forward), Optimizer/Frontier (forward)
        │
        ├─► HEALTH SCORE (partial macro)
        │   evaluate_portfolio_health()
        │     ├─ s_macro (Macro Regime Fit) — REAL ± points
        │     ├─ 7 other components — historical only
        │     ├─ recommendation_details — macro-triggered rules
        │     └─ macro_fit / whats_working / whats_not — TEXT
        │
        └─► TEXT ONLY
            macro_assumption_summary(), beginner_friendly_labels(),
            generate_portfolio_explanation().macro_sensitivity
```

### Cards/pages affected when macro changes

| Page | What changes |
|------|--------------|
| **Overview** historical metrics | **Nothing** (until dates/holdings change) |
| **Portfolio Health** score | **Changes after Refresh** — `s_macro`, macro rules, text |
| **Forward Macro Analysis** | **Real recalc** of Forward Return/Vol/Sharpe/Drawdown |
| **Monte Carlo** (forward mode) | **Real recalc** of simulation μ/σ |
| **Optimization / Frontier** (forward mode) | **Real recalc** of mean/cov inputs |
| **Risk Analysis → Macro Regime Engine** | **Unchanged** by user sliders — fixed presets |

---

## Specific macro-change answers

### Recession probability

**Real (after refresh/run):** Forward ret/vol/drawdown/corr; health `s_macro` (+1.0 if p≥0.5 and equity≤55%; −2.0 if p≥0.5 and equity>70%); recommendation if p>0.50 and equity>70%; action plan text if p≥0.45.

**Does NOT change:** cached health until refresh; **historical** Overview return/vol/sharpe/drawdown.

### Rate outlook (`health_rate_env`)

**Real:** `_rate_environment_effects()` on forward metrics; health `s_macro` ±1.5 for falling/rising/high-rate fits.

**Does NOT change:** historical Overview metrics; no dedicated rate-only recommendation rule.

### Summary table

| Macro change | Historical return/vol (Overview) | Forward return/vol | Health score | Recommendations |
|--------------|----------------------------------|--------------------|--------------|-----------------|
| Recession % | **No** | **Yes (real)** | **Yes** (after refresh) | **Yes** if p>50% & equity>70% |
| Rate outlook | **No** | **Yes (real)** | **Yes** (s_macro) | Text only |
| Inflation | **No** | **Yes (real)** | **Yes** (+ rule if High Inflation + long bonds) | **Yes** if High Inflation + long bonds >20% |
| Economic regime | **No** | **Yes (real)** | **Yes** (s_macro) | Text (macro_fit) |
| Valuation / market outlook | **No** | **Yes (real)** | **No** in s_macro | Text (macro_fit) |

**Real calculation vs text:** Forward Macro / MC / Optimizer / Frontier = **real math**. Health `s_macro` and macro-triggered recommendation rules = **real scoring**. `macro_fit`, forward insights, beginner environment copy = **text only**.

---

## Key files

| File | Role |
|------|------|
| `portfolio_core.py` | Metric formulas, health scoring, forward projection, recommendations |
| `components/macro_engine.py` | Session → assumptions, cache, forward wrapper |
| `components/macro_data.py` | Live FRED → session keys (Beginner) |
| `streamlit_app.py` | UI orchestration, caching, tabs |
| `components/beginner_coach.py` | Beginner health display |
| `components/decision_coach.py` | Recommendations panel |
| `investment_persistent_state.py` | Persists dates, macro keys, holdings |

---

## Recommended UI fixes (not implemented)

1. Label "Annual Return (historical, selected period)" vs "Forward expected return (macro-adjusted)"
2. Show active date range on every metrics card
3. Macro callout on Portfolio Health: macro adjusts Macro Regime Fit + forward sections only
4. Align beginner "expected return" copy with historical definition
5. Surface `settings_stale` when macro fingerprint changes

---

## Verification steps

1. SPY 100%, dates 2019–2024 → note Overview return & vol
2. Change to 1-year window → return/vol change
3. Recession 25% → 60% → health score changes after Refresh; Overview return/vol unchanged
4. Forward Macro tab → recession slider → Forward Return/Vol change
5. Beginner vs Advanced health score match for same holdings/settings
