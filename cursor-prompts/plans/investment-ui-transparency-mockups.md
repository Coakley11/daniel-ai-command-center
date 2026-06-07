# Investment UI transparency — proposed wording (mockups)

**Last updated:** 2026-06-07  
**Status:** Mockups for review — **no formula changes, no implementation yet**

Existing reference: `investment-portfolio-analyzer/components/calculation_transparency.py` (Advanced expanders). This doc proposes **inline captions** visible without opening expanders.

---

## Design principles

1. **Historical vs forward** must be visually distinct on every metric
2. **Date range** shown wherever historical metrics appear
3. **Macro effect** callout on Portfolio Health — what changes vs what does not
4. Beginner and Advanced share the same definitions; Beginner uses shorter copy

---

## Mockup 1 — Overview metrics row (Advanced)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Portfolio Overview          Period: Jan 2019 – Dec 2024  (5 years)    │
├──────────────┬──────────────┬──────────────┬──────────────────────────┤
│ Annual Return│  Volatility  │ Sharpe Ratio │ Max Drawdown             │
│    8.2%      │    12.4%     │    0.52      │   −18.3%                 │
│ Historical   │ Historical   │ Historical   │ Historical               │
│ annualized   │ annualized   │ over same    │ peak-to-trough           │
│ over selected│ over selected│ period       │ in selected period       │
│ date range   │ date range   │              │                          │
└──────────────┴──────────────┴──────────────┴──────────────────────────┘

ℹ️ These metrics use price history for your current holdings in the date
   range above. Macro settings do not change these numbers.
```

**Caption under row (single line):**
> Historical metrics · Based on **Jan 2019 – Dec 2024** · Current portfolio weights · Not macro-adjusted

---

## Mockup 2 — Overview metrics row (Beginner)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Your Portfolio at a Glance                                             │
├──────────────┬──────────────┬──────────────┬──────────────────────────┤
│ Average      │ How Bumpy    │ Risk/Reward  │ Worst Drop               │
│ Yearly Return│ (Volatility) │ Score        │                          │
│    8.2%      │    12.4%     │    0.52      │   −18.3%                 │
└──────────────┴──────────────┴──────────────┴──────────────────────────┘

Plain English: These numbers describe how your portfolio behaved in the
past (about the last 5 years), not a prediction of next year.
```

**Shorter variant:**
> Past performance · Last ~5 years · Your current mix of investments

---

## Mockup 3 — Portfolio Health macro panel

```
┌─ Macro assumptions ─────────────────────────────────────────────────────┐
│  Recession probability: 35%    Rate environment: Rising                 │
│  Inflation: Moderate           Valuation: Fair                          │
│  Economic regime: Normal                                                │
├─────────────────────────────────────────────────────────────────────────┤
│  What macro settings affect:                                            │
│  ✓ Health score (Macro Regime Fit — up to 10 points)                    │
│  ✓ Forward projections (Forward Macro, Monte Carlo forward mode)      │
│  ✓ Recommendations when rules trigger (e.g. high recession + equity)    │
│  ✗ Historical return, volatility, Sharpe, or drawdown on Overview       │
└─────────────────────────────────────────────────────────────────────────┘
```

**One-line callout (below macro sliders):**
> Macro assumptions affect **forward projections**, **health score**, and **recommendations**. They do **not** change historical return or volatility on Overview.

---

## Mockup 4 — Forward Macro Analysis tab

```
┌─ Forward projection ────────────────────────────────────────────────────┐
│  Forward Return        Forward Volatility      Forward Sharpe           │
│      6.1%                    14.8%                  0.31                │
│  Macro-adjusted        Macro-adjusted          Macro-adjusted           │
│  (not the same as      (not the same as        (uses forward           │
│   Overview return)      Overview volatility)    return & vol above)     │
├─────────────────────────────────────────────────────────────────────────┤
│  Baseline: historical return/vol from Jan 2019 – Dec 2024, then         │
│  adjusted for your macro assumptions (recession 35%, rising rates, …).  │
└─────────────────────────────────────────────────────────────────────────┘
```

**Forward Max Drawdown caption:**
> Stress-adjusted estimate: historical max drawdown × recession stress factor. Not a simulated forward path.

---

## Mockup 5 — Health score card

```
┌─ Portfolio Health Score ────────────────────────────────────────────────┐
│                         72 / 100                                        │
│  Based on historical metrics (Jan 2019 – Dec 2024) + objective fit +    │
│  macro regime fit (10 pts max).                                         │
│                                                                         │
│  [Expand breakdown]                                                     │
│    Return vs Benchmark ........ 8 pts                                   │
│    Volatility Level ........... 7 pts                                   │
│    Sharpe Ratio ............... 6 pts                                   │
│    Max Drawdown ............... 5 pts                                   │
│    Diversification ............ 9 pts                                   │
│    Concentration Risk ......... 8 pts                                   │
│    Objective Alignment ........ 10 pts                                  │
│    Macro Regime Fit ........... 7 pts  ← changes when macro sliders move│
└─────────────────────────────────────────────────────────────────────────┘

⚠️ Health analysis may be outdated — macro or objective settings changed.
   Click Analyze Portfolio to refresh.
```

---

## Mockup 6 — Stale settings banner (existing pattern, clarified copy)

**Current (paraphrased):** "Health analysis may be outdated — objective or macro settings changed."

**Proposed:**
> **Settings changed since last analysis.** Macro assumptions or portfolio objective differ from the last health run. Historical Overview metrics are unchanged; click **Analyze Portfolio** to update health score and recommendations.

---

## Label rename proposal (Advanced)

| Current label | Proposed label | Tooltip |
|---------------|----------------|---------|
| Annual Return | **Annual Return (historical)** | Mean daily return × 252 over selected dates |
| Volatility | **Volatility (historical)** | Daily std × √252 over selected dates |
| Sharpe Ratio | **Sharpe Ratio (historical)** | (Return − risk-free) / volatility |
| Max Drawdown | **Max Drawdown (historical)** | Largest peak-to-trough in period |
| Forward Return | **Forward Return (macro-adjusted)** | Historical baseline + macro shifts |
| Forward Volatility | **Forward Volatility (macro-adjusted)** | Historical vol × macro multipliers |

## Label rename proposal (Beginner)

| Current label | Proposed subtitle |
|---------------|-------------------|
| Average Yearly Return | "How your portfolio grew on average in the past" |
| How Bumpy (Volatility) | "How much it went up and down in the past" |
| Risk/Reward Score | "Return compared to risk in the past" |
| Worst Drop | "Biggest drop from a high point in the past" |

---

## Placement map (where to add copy)

| Location | File (approx.) | Mockup |
|----------|----------------|--------|
| Overview metrics row | `streamlit_app.py` `metrics_row_primary()` | 1, 2 |
| Portfolio Health macro expander | `streamlit_app.py` health section | 3 |
| Forward Macro tab | Forward projection section | 4 |
| Health score card | `beginner_coach.py`, `streamlit_app.py` | 5 |
| Stale banner | Existing warning blocks | 6 |

---

## Out of scope (this pass)

- Formula changes
- Monte Carlo / Optimizer methodology rewrites (already in `calculation_transparency.py` expanders)
- New metrics or date-range picker UX

## Review questions for user

1. Prefer **inline captions** under every metric vs **one banner** per section?
2. Show exact dates (`Jan 2019 – Dec 2024`) or relative (`~5 years`) in Beginner mode?
3. Rename labels (historical/forward suffix) or keep labels and rely on captions only?
4. Add macro callout to Overview tab or Portfolio Health only?
