# Suite Account / Workspace Acceptance Matrix

**Last updated:** 2026-06-21 (post-auth enable + wiring fix audit)  
**Full report:** [SPRINT_D_GATE_REPORT.md](./SPRINT_D_GATE_REPORT.md)

## Gate verdict: **NOT CLOSED**

User enabled `suite_auth_enabled = true` on dev secrets (all apps). Auth-gate wiring audit **PASS** on all entry files. NBA/FutureLens SyntaxError fixes deployed (`9efece3`, `4139b52`).

---

## Workspace isolation

| # | Scenario | Result | Notes |
|---|----------|--------|-------|
| W1 | Switch profile in CC; open Music | **MANUAL PENDING** | Browser sign-off required |
| W2 | Switch profile; open AMI | **MANUAL PENDING** | Browser sign-off required |
| W3 | Switch profile; open Baseball | **N/A** | Entry shell not wired |
| W4 | Switch profile; open Investment | **MANUAL PENDING** | Browser sign-off required |
| W5 | Switch profile; open NBA | **MANUAL PENDING** | Wiring fixed; confirm in browser |
| W6 | Switch profile; open FutureLens | **MANUAL PENDING** | Wiring fixed; confirm in browser |
| W7 | CC activity feed workspace isolation | **PASS** | `test_workspace_cc_activity.py` |
| W8 | Continue cards include `?suite_workspace=` | **PASS** | Audit tests + `continue_dashboard` |

## Account shell (Sprint B)

| # | Scenario | Result | Notes |
|---|----------|--------|-------|
| A1 | Workspace badge in every app sidebar | **MANUAL PENDING** | Verify in browser after auth reboot |
| A2 | Account & workspace expander in sidebars | **MANUAL PENDING** | Same |
| A3 | Command Center link preserves workspace param | **PASS** | Automated audit |
| A4 | Namespace mismatch warning when URL ≠ profile | **PASS (logic)** | Unit test; live banner **MANUAL PENDING** |

## Real Accounts (Sprint C — auth enabled on dev)

| # | Scenario | Result | Notes |
|---|----------|--------|-------|
| C1 | Create account (email/password) | **MANUAL PENDING** | Auth enabled; complete in browser on CC dev |
| C2 | Log in | **MANUAL PENDING** | CC + one sibling app |
| C2b | **Browser refresh (F5) preserves login** | **MANUAL PENDING** | Cookie + `restore_auth_session()` — login → F5 → still signed in |
| C3 | Log out | **MANUAL PENDING** | Session + browser cookie cleared |
| C4 | Password reset email | **MANUAL PENDING** | Supabase Auth email delivery |
| C5 | Ariel account cannot access Daniel workspace | **PASS (unit)** | `test_enforce_workspace_ownership_clamps_profile`; live **MANUAL PENDING** |

## Persistence / cross-device

| # | Scenario | Result | Notes |
|---|----------|--------|-------|
| P1 | Music CPL active song phone → Dell | **MANUAL PENDING** | |
| P2 | Music custom lyrics phone → Dell | **MANUAL PENDING** | |
| P3 | AMI UI state phone → Dell | **MANUAL PENDING** | |
| P4 | Baseball draft queue phone → Dell | **MANUAL PENDING** | |
| P5 | Direct app open shows correct badge | **MANUAL PENDING** | |

## Music CPL regression

| # | Scenario | Result | Notes |
|---|----------|--------|-------|
| M1 | Custom ↔ catalog source toggle | **MANUAL PENDING** | |
| M2 | Recently Selected catalog history | **MANUAL PENDING** | |
| M3 | Custom song library selector | **MANUAL PENDING** | |
| M4 | Display key sync | **MANUAL PENDING** | |
| M5 | Backing defaults unchanged | **MANUAL PENDING** | |

## Gate checklist

- [ ] All W1–W8 PASS (W3 N/A OK)
- [ ] All A1–A4 PASS
- [ ] C1–C5 PASS on dev (include **C2b** refresh persistence)
- [ ] P1–P5 PASS
- [ ] M1–M5 PASS

**Signed off by:** _______________ **Date:** _______________
