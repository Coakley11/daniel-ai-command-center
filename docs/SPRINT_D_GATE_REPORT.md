# Sprint D Gate Report — Account / Workspace Foundation

**Date:** 2026-06-21  
**Deploy baseline:** Command Center `4044ee1` + docs `0f19d20`; sibling sync commits on `origin/dev`  
**Importer Phase 0:** **BLOCKED** — do not start until this gate closes

---

## Executive recommendation

**Gate status: NOT CLOSED**

The Account/Workspace foundation is **deployed and code-validated**, but the Sprint D gate **cannot be officially closed** until:

1. **You enable auth on dev** (`suite_auth_enabled = true` in Streamlit Cloud secrets + reboot on all 7 dev apps) — see [SUITE_AUTH_DEV_ENABLE.md](./SUITE_AUTH_DEV_ENABLE.md)
2. **You complete live browser sign-off** (W1–W2, W4–W6, A1–A2 UI visibility)
3. **You complete cross-device + Music CPL manual rows** (P1–P5, M1–M5)
4. **You validate C1–C5 end-to-end** after auth is enabled

Automated headless browser checks against Streamlit Cloud **cannot reliably render** app UI (WebSocket client shell only). Failures from `run_sprint_d_live_validation.py` are **inconclusive**, not proof of regressions.

---

## Automated validation (Command Center repo)

| Check | Result | Evidence |
|-------|--------|----------|
| Sprint B deep-link audit | **PASS** | `test_suite_sprint_b_audit.py` |
| Account shell wiring (unit) | **PASS** | `test_suite_app_shell.py` |
| Auth scaffolding | **PASS** | `test_suite_auth.py` |
| Account settings + namespace | **PASS** | `test_account_settings_panel.py` |
| Workspace profiles | **PASS** | `test_suite_workspace.py` |
| CC activity isolation | **PASS** | `test_workspace_cc_activity.py` |
| **Total automated** | **PASS (60/60)** | pytest 2026-06-21 |

---

## Acceptance matrix — final status

### Workspace isolation

| # | Scenario | Result | Notes |
|---|----------|--------|-------|
| W1 | CC → Music (Ariel profile) | **MANUAL PENDING** | Shell wired on `origin/dev` (`a0979f1`); browser sign-off required |
| W2 | CC → AMI | **MANUAL PENDING** | Shell wired (`6e3144c`) |
| W3 | CC → Baseball | **N/A** | No local entry wiring; modules synced only (`4864a59`) |
| W4 | CC → Investment | **MANUAL PENDING** | Shell wired (`60b122e`) |
| W5 | CC → NBA | **MANUAL PENDING** | Shell wired (`0f119df`) |
| W6 | CC → FutureLens | **MANUAL PENDING** | Shell wired (`07777a5`) |
| W7 | CC activity feed workspace isolation | **PASS** | Automated |
| W8 | Continue/Open URLs include `?suite_workspace=` | **PASS** | Automated audit + `continue_dashboard` fix |

### Account shell (Sprint B)

| # | Scenario | Result | Notes |
|---|----------|--------|-------|
| A1 | Workspace badge in every app sidebar | **MANUAL PENDING** | Code present; Streamlit UI requires browser verification |
| A2 | Account & workspace expander in sidebars | **MANUAL PENDING** | Same |
| A3 | Command Center link preserves workspace param | **PASS** | Automated audit |
| A4 | Namespace mismatch warning (URL ≠ profile) | **PASS (logic)** | `test_query_param_mismatch_raises_error_issue`; live banner **MANUAL PENDING** |

### Real Accounts (Sprint C)

| # | Scenario | Result | Notes |
|---|----------|--------|-------|
| C1 | Create account | **BLOCKED** | Auth not enabled on Streamlit Cloud dev secrets |
| C2 | Log in | **BLOCKED** | Same |
| C3 | Log out | **BLOCKED** | Same |
| C4 | Password reset email | **BLOCKED** | Same + Supabase Auth email config |
| C5 | Ariel cannot access Daniel workspace | **PASS (unit)** | `test_enforce_workspace_ownership_clamps_profile`; live **BLOCKED** until auth enabled |

### Persistence / cross-device

| # | Scenario | Result | Notes |
|---|----------|--------|-------|
| P1 | Music CPL active song phone → Dell | **MANUAL PENDING** | Requires your devices |
| P2 | Music custom lyrics phone → Dell | **MANUAL PENDING** | Same |
| P3 | AMI UI state phone → Dell | **MANUAL PENDING** | Same |
| P4 | Baseball draft queue phone → Dell | **MANUAL PENDING** | Same |
| P5 | Direct app open shows correct badge | **MANUAL PENDING** | Same |

### Music CPL regression

| # | Scenario | Result | Notes |
|---|----------|--------|-------|
| M1 | Custom ↔ catalog source toggle | **MANUAL PENDING** | v29k behavior |
| M2 | Recently Selected catalog history | **MANUAL PENDING** | v29k |
| M3 | Custom song library selector | **MANUAL PENDING** | v29l |
| M4 | Display key sync | **MANUAL PENDING** | |
| M5 | Backing defaults unchanged | **MANUAL PENDING** | |

---

## Auth enablement (step 1 — user action required)

This agent **cannot** modify Streamlit Cloud secrets. To unblock C1–C5:

1. Supabase → Authentication → enable Email provider
2. For **each dev deployment** (7 apps): Settings → Secrets → add under `[suite_activity]`:
   ```toml
   suite_auth_enabled = true
   ```
3. **Reboot app** on each deployment (secrets do not apply until reboot)
4. Re-run C1–C5 manually on CC dev first, then one sibling app

Roll back: remove flag or set `false`; reboot.

---

## Remaining defects / blockers

| # | Severity | Issue | Owner |
|---|----------|-------|-------|
| D1 | **P0** | Auth not enabled on dev Streamlit secrets | User (Streamlit Cloud dashboard) |
| D2 | **P0** | Live acceptance rows not signed off (W/A/P/M browser + devices) | User |
| D3 | **P2** | Baseball app entry has no shell wiring | Dev (when `streamlit_app.py` restored) |
| D4 | **P3** | Headless Playwright cannot validate Streamlit Cloud UI | Tooling limitation (use manual checklist) |

---

## Gate checklist (all must be true to close)

- [ ] W1–W8 PASS (W3 N/A acceptable)
- [ ] A1–A4 PASS
- [ ] C1–C5 PASS on dev with auth enabled
- [ ] P1–P5 PASS
- [ ] M1–M5 PASS
- [ ] Signed off in [SUITE_ACCOUNT_WORKSPACE_ACCEPTANCE.md](./SUITE_ACCOUNT_WORKSPACE_ACCEPTANCE.md)

**Current:** 4 automated PASS rows · 5 BLOCKED (auth) · 16 MANUAL PENDING · 1 N/A

---

## After gate closes — Importer Phase 0 only

Architecture modules in AMI repo (no OCR, URL, screenshot, or full UI):

- `decision_registry.py`
- `decision_router.py`
- `decision_templates.py`
- `decision_math.py`

First workflow target: Kalshi-style prediction market → Betting / Expected Value routing.

---

**Signed off by:** _pending_  
**Gate closed:** **NO**
