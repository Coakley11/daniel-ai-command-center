# Account Settings → Workspace Polish → Real Problem Importer

**Last updated:** 2026-06-19  
**Branch:** `dev`  
**Status:** Approved direction — do not start Real Problem Importer until Account Settings + workspace polish foundations land

---

## Summary

Shift suite roadmap after AMI persistence/workspace sync stabilization. **Account Settings UX** (not full login/auth) comes before **Real Problem Importer**. Kalshi/prediction-market coach is Phase 4 specialization on top of a manual-field importer MVP.

**Hard gate:** Close Workspace Profiles P0 validation (FutureLens + final CC isolation pass) in parallel with Account Settings design — do not defer isolation work.

---

## Recommended implementation order

| Order | Track | Size | Depends on |
|-------|-------|------|------------|
| 0 | Workspace P0 exit (FutureLens + CC final validation) | Small | AMI persistence shipped (`87d2785`) |
| 1 | **Account Settings** (profile page, identity diagnostics) | Medium | `suite_user.py`, `suite_workspace.py`, `suite_account.py` |
| 2 | **Workspace & account polish** | Medium | Account Settings shell |
| 3 | **Real Problem Importer MVP** (manual fields + EV math) | Medium | Polish + AMI persist keys |
| 4 | **Kalshi / prediction-market coach** | Medium | Importer MVP |
| 5 | **Additional real-life templates** | Large | Importer framework |
| 6 | **Real Accounts / auth** (roadmap Phase 2) | Large | All above stable |

**Defer (not cancelled):** P1 AMI Baseball Draft Intelligence — resume after Importer v1 or run narrow parallel fixes only when draft season blocks.

---

## Phase 1 — Account Settings

**Goal:** User always knows account + workspace; Daniel/Ariel never feel ambiguous.

**Scope (v1 — no full auth):**
- Command Center **Account Settings** page/section (sidebar or hero expander → dedicated panel)
- Display: `suite_user_id`, Supabase `user_id`, email (from secrets), display name, cloud mode
- Workspace: active profile, label, cloud namespace sample (`applied_intelligence__ariel`)
- Switch workspace (reuse `render_workspace_selector_sidebar` or link to CC)
- Diagnostics: same fields as AMI/CC persistence panels (read-only)
- Password reset: **“Coming with Real Accounts”** unless Supabase Auth added — do not fake reset

**Shared module:** `suite_account_settings.py` (new, synced to siblings)

**Exit criteria:** Daniel opens Settings → sees Daniel workspace + unscoped keys; Ariel → `__ariel` keys; no edit actions that cross profiles.

---

## Phase 2 — Workspace & account polish

- Global workspace badge in every app sidebar (not CC-only)
- `init_suite_workspace(st)` at top of every sibling app (audit NBA/FutureLens/Music)
- App open URLs always append `?suite_workspace=` (`app_registry.get_app_url`)
- Namespace mismatch banner when activity write key ≠ active workspace
- CC activity sync: session_activity + analytical_question (shipped `a14d9be` / `790fc0e`) — extend to all apps audit

---

## Phase 3 — Real Problem Importer MVP

**Goal:** Paste or type a real decision; app fills EV math — not gambling advice.

**v1 scope (do NOT overbuild):**
- New AMI section: **“Analyze a real decision”** (view mode or tab under Solve a Problem)
- **Manual form** only (no HTML/CSV parse, no LLM extract in v1):
  - Question, market price / implied prob, cost, payout, horizon, user prob, notes
- Pure functions: implied prob, break-even, EV, profit/loss, edge, Kelly-lite or fixed-fraction sizing cap
- Reuse `idea_interactives._play_ev` math extracted to `decision_math.py`
- Editable sliders after prefill; persist under `dec_*` keys in `_ami_ui_state`
- Activity: `analytical_question` + `session_activity` scoped to workspace
- Disclaimer: educational decision analysis, not financial/gambling advice

**Exit criteria:** Daniel pastes Kalshi-like numbers manually → EV + edge shown → refresh restores → CC shows activity under Daniel only.

---

## Phase 4 — Kalshi Decision Coach

- Template preset “Prediction market”
- Sections: Market Data | My estimate | EV | Risk/size | Explanation | Summary
- Optional paste helper (regex/structured text parse) — still no scrape
- Confidence tiers adjust position cap
- Scenario: “What prob makes this negative EV?”

---

## Phase 5 — More templates

- Investing, sports, business, cost-benefit, portfolio, time — each adds template id + field schema + solver hook
- Shared `decision_templates.py` registry

---

## Tests (by phase)

| Phase | Tests |
|-------|--------|
| 1 | `test_account_settings_panel.py` — summary fields, workspace ids |
| 2 | `test_workspace_deep_links.py`, namespace mismatch detector |
| 3 | `test_decision_math.py`, `test_decision_importer_persist.py`, workspace isolation |
| 4 | Kalshi template parse unit tests (golden paste samples) |
| 5 | Per-template smoke tests |

---

## Risks

| Risk | Mitigation |
|------|------------|
| Daniel/Ariel state leak on imported problems | `dec_*` in `_ami_ui_state`; scoped cloud keys; tests per workspace |
| AMI default workspace `daniel` on direct open | Settings + app links require `?suite_workspace=`; badge visible |
| Overbuilding AI parse before manual form | Phase 3 = form only; Phase 4 = optional parse |
| Legal/regulatory framing | Static disclaimer; “based on your assumptions” copy |
| Real Accounts collision | User Phase 1 = **Settings UX**; roadmap Phase 2 = **auth** — separate names in docs |
| Persistence regression | Reuse `maybe_persist` / one-shot reapply patterns; don’t add second restore path |

---

## Key files (Command Center)

- `ai_command_center.py` — Account Settings section
- `suite_account_settings.py` (new)
- `suite_user.py`, `suite_account.py`, `suite_workspace.py`
- `activity_diagnostics.py`, `app_registry.py`

## Key files (AMI)

- `components/decision_importer.py` (new)
- `decision_math.py` (new, pure)
- `content/decision_templates.py` (Phase 4+)
- `applied_intelligence_persistent_state.py` — `dec_` prefix
- `applied_intelligence_activity.py` — import events
- `streamlit_app.py` — nav entry
