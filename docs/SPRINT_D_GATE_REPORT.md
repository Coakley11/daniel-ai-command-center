# Sprint D Gate Report — Account / Workspace Foundation

**Date:** 2026-06-21 (Session A live PASS)  
**Deploy baseline:** CC `8111c34`; W1 `3fea2a4`; selector snap-back `8111c34`; auth persistence `c085957` (`suite_sid` + Supabase)  
**Importer Phase 0:** **BLOCKED** — do not start until this gate closes

---

## Executive recommendation

**Gate status: NOT CLOSED** — **no remaining P0 auth/code defects**

Infrastructure blockers are **resolved**:

| Area | Status |
|------|--------|
| Auth gate wiring (SyntaxError) | **FIXED** |
| Supabase Auth backend (`supabase_anon_key`) | **FIXED** |
| Supabase egress (full_session blobs) | **ACCEPTED** — user verified ~1.9 KB `suite_app_current_state` on CC |
| C2b refresh persistence | **PASS** — user verified `suite_sid` + Supabase row + F5 |

**Gate remains open** because **14 manual acceptance rows** remain (Session B auth, Session C cross-device, Session D Music CPL).

**Recommendation:** Complete Session B using [SPRINT_D_MANUAL_VALIDATION_RUNBOOK.md](./SPRINT_D_MANUAL_VALIDATION_RUNBOOK.md). Record results in [SPRINT_D_MANUAL_RESULTS.md](./SPRINT_D_MANUAL_RESULTS.md). Preflight: `python scripts/sprint_d_manual_preflight.py`. Then Sessions C–D, sign acceptance matrix, and **CLOSE gate** to unblock Importer Phase 0.

---

## User-validated (live)

| # | Result | Evidence |
|---|--------|----------|
| C1 | **PASS (live)** | User created Real Account on dev (prior session) |
| C2b | **PASS (live)** | `session_id_present`, `query_param_present`, `cloud_payload_present`; F5 preserved login |
| Egress | **ACCEPTED** | CC refresh/login: `suite_app_current_state` ~1.9 KB; no multi-app blob download |
| W1–W6 | **PASS (live)** | Session A 2026-06-21; Ariel deep links from CC App Directory |
| A1–A2 | **PASS (live)** | Ariel badge + Account expander in all tested sibling sidebars |
| A4 | **PASS (live)** | Namespace mismatch warning when URL ≠ session profile |

---

## Fixes completed (Sprint D)

| Issue | Status | Commit / note |
|-------|--------|---------------|
| NBA / FutureLens auth-gate SyntaxError | **FIXED** | `9efece3`, `4139b52`, CC `0eb640e` |
| Supabase Auth backend | **FIXED** | `a77dfa0` — `get_supabase_client`, anon key |
| Supabase egress (full_session) | **FIXED** | `0cab55d` — targeted reads, session cache |
| C2b CookieManager (failed on Cloud) | **SUPERSEDED** | `c085957` — `suite_sid` query param + Supabase `suite_saved_items` |
| W1 App Directory workspace param | **FIXED** | `3fea2a4` — Daniel admin profile switching + deep links |
| Workspace selector snap-back | **FIXED** | `8111c34` — selectbox no longer reset before user input |
| Auth-gate wiring (7 entry files) | **PASS** | `scripts/audit_auth_gate_wiring.py` |

---

## Automated validation (Command Center repo)

| Check | Result | Evidence |
|-------|--------|----------|
| Sprint B deep-link audit | **PASS** | `test_suite_sprint_b_audit.py` |
| Account shell wiring | **PASS** | `test_suite_app_shell.py` |
| Auth + C2b persistence | **PASS** | `test_suite_auth.py`, `test_suite_auth_persistence.py`, `test_suite_auth_browser.py` |
| Supabase egress | **PASS** | `test_suite_egress.py` |
| Workspace + CC activity | **PASS** | `test_suite_workspace.py`, `test_workspace_cc_activity.py` |
| Auth-gate compile audit | **PASS** | `scripts/audit_auth_gate_wiring.py` |

---

## Acceptance matrix — current status

### Workspace isolation

| # | Result | Notes |
|---|--------|-------|
| W1 | **PASS (live)** | CC → Music as Ariel; 2026-06-21 |
| W2 | **PASS (live)** | CC → AMI |
| W3 | **N/A** | Baseball entry shell not wired |
| W4 | **PASS (live)** | CC → Investment |
| W5 | **PASS (live)** | CC → NBA |
| W6 | **PASS (live)** | CC → FutureLens |
| W7 | **PASS** | Automated |
| W8 | **PASS** | Automated |

### Account shell

| # | Result | Notes |
|---|--------|-------|
| A1 | **PASS (live)** | Workspace badge in every tested app sidebar |
| A2 | **PASS (live)** | Account & workspace expander |
| A3 | **PASS** | Automated |
| A4 | **PASS (live)** | Namespace mismatch banner in browser |

### Real Accounts

| # | Result | Notes |
|---|--------|-------|
| C1 | **PASS (live)** | Account created on dev |
| C2 | **MANUAL PENDING** | Log in on **one sibling app** (CC implied by C2b) |
| C2b | **PASS (live)** | F5 preserves login via `suite_sid` |
| C3 | **MANUAL PENDING** | Log out; F5 shows auth gate; `suite_sid` cleared |
| C4 | **PARTIAL (live)** | Email delivery PASS; reset link FAIL — Supabase Site URL + redirect_to fix pending |
| C5 | **PASS (unit)** / live **MANUAL PENDING** | Ariel cannot stay on Daniel workspace (browser) |

### Persistence / Music CPL

| # | Result |
|---|--------|
| P1–P5 | **MANUAL PENDING** (phone + Dell) |
| M1–M5 | **MANUAL PENDING** (Music CPL regression) |

---

## Remaining blockers (non-P0)

| # | Severity | Issue | Owner |
|---|----------|-------|-------|
| D1 | ~~P0~~ | Auth + egress + C2b | **Resolved** |
| D2 | ~~P1~~ | W1–W6, A1–A2, A4 live | **Resolved** (Session A 2026-06-21) |
| D3 | **P1** | C2 sibling, C3, C4, C5 live | User (browser) — **Session B next** |
| D4 | **P1** | P1–P5 phone↔Dell | User (devices) |
| D5 | **P1** | M1–M5 Music CPL | User (phone) |
| D6 | **P2** | Baseball shell not wired | Dev (post-gate OK) |

---

## Remaining manual validation checklist (gate closure)

**Runbook:** [SPRINT_D_MANUAL_VALIDATION_RUNBOOK.md](./SPRINT_D_MANUAL_VALIDATION_RUNBOOK.md)  
**Results tracker:** [SPRINT_D_MANUAL_RESULTS.md](./SPRINT_D_MANUAL_RESULTS.md)  
**Preflight:** `python scripts/sprint_d_manual_preflight.py`

Complete in order. Mark PASS/FAIL in the results file.

### Session A — Workspace + shell ✓ COMPLETE (2026-06-21)

All rows PASS. See [SPRINT_D_MANUAL_RESULTS.md](./SPRINT_D_MANUAL_RESULTS.md).

### Session B — Auth completion (~15 min) ← **NEXT**

4. **C2:** Log in on **Music** (or AMI) dev — separate origin; confirm `suite_sid` in URL.
5. **C3:** Log out on CC — URL loses `suite_sid`; F5 shows auth gate.
6. **C4:** Password reset — email received (Supabase Auth).
7. **C5 (live):** Log in as **Ariel** — cannot remain on Daniel workspace (clamped to Ariel).

### Session C — Cross-device (~30 min, phone + Dell)

8. **P1–P2:** Music CPL active song + custom lyrics — phone save → Dell shows same state.
9. **P3:** AMI UI state phone → Dell.
10. **P4:** Baseball draft queue phone → Dell (if baseball dev reachable).
11. **P5:** Open app directly (not via CC) — correct workspace badge.

### Session D — Music CPL regression (~20 min, phone)

12. **M1–M5:** Custom/catalog toggle, Recently Selected, custom library, display key sync, backing defaults.

### Sign-off

- [ ] All rows PASS or N/A (W3)
- [ ] Sign acceptance matrix
- [ ] Update this report: **Gate closed: YES**

---

## Gate checklist summary

| Section | PASS | Pending | N/A |
|---------|------|---------|-----|
| W1–W8 | 7 | 0 | 1 |
| A1–A4 | 4 | 0 | 0 |
| C1–C5 + C2b | 3 (C1, C2b, C5 unit) | 4 | 0 |
| P1–P5 | 0 | 5 | 0 |
| M1–M5 | 0 | 5 | 0 |

**Total manual rows remaining: 14** (Session B: 4 · Session C: 5 · Session D: 5)

---

## After gate closes — Importer Phase 0 only

Architecture-only: `decision_registry.py`, `decision_router.py`, `decision_templates.py`, `decision_math.py` — no OCR, URL, screenshot, or full UI.

---

**Signed off by:** _pending_  
**Gate closed:** **NO** (awaiting manual matrix sign-off)
