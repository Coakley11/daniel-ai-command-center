# Sprint D Manual Validation Results

**Tester:** Daniel  
**Date started:** 2026-06-21  
**Date completed:** _in progress — Session A done_

**Instructions:** Mark each row `PASS`, `FAIL`, or `N/A`. Add notes for any FAIL.  
**Do not start Importer Phase 0 until gate is closed.**

---

## Already validated (do not re-test unless regression)

| Row | Result | Date | Notes |
|-----|--------|------|-------|
| C1 | PASS | 2026-06-21 | Account created on dev |
| C2b | PASS | 2026-06-21 | suite_sid + F5 preserved login |
| Egress | PASS | 2026-06-21 | suite_app_current_state ~1.9 KB on CC |
| W7 | PASS | automated | |
| W8 | PASS | automated | |
| A3 | PASS | automated | |
| C5 unit | PASS | automated | |
| W1 fix | PASS | 2026-06-21 | CC `3fea2a4` + selector `8111c34` |

---

## Session A — Workspace + shell

**Completed:** 2026-06-21 · Deploy baseline CC `8111c34`

| Row | Result | Notes |
|-----|--------|-------|
| W1 | PASS | CC → Music as Ariel; `?suite_workspace=ariel` |
| W2 | PASS | CC → AMI as Ariel |
| W4 | PASS | CC → Investment as Ariel |
| W5 | PASS | CC → NBA as Ariel |
| W6 | PASS | CC → FutureLens as Ariel |
| A1 | PASS | Ariel badge visible in all tested app sidebars |
| A2 | PASS | Account & workspace expander visible in all tested apps |
| A4 live | PASS | Namespace mismatch warning when URL ≠ session profile |

---

## Session B — Auth

| Row | Result | Notes |
|-----|--------|-------|
| C2 | | Sibling app login (Music or AMI) |
| C3 | | Logout + F5 → auth gate |
| C4 | PARTIAL | Email PASS; redirect PASS; recovery panel pending retest after 221ab44+ fix |
| C5 live | | Ariel cannot stay on Daniel workspace |

---

## Session C — Cross-device

| Row | Result | Notes |
|-----|--------|-------|
| P1 | | Music active song phone → Dell |
| P2 | | Music custom lyrics phone → Dell |
| P3 | | AMI UI state phone → Dell |
| P4 | | Baseball draft queue phone → Dell |
| P5 | | Direct app open badge |

---

## Session D — Music CPL

| Row | Result | Notes |
|-----|--------|-------|
| M1 | | Custom ↔ catalog toggle |
| M2 | | Recently Selected |
| M3 | | Custom song library |
| M4 | | Display key sync |
| M5 | | Backing defaults |

---

## Gate sign-off

- [ ] All rows above PASS or N/A (W3 N/A OK)
- [ ] No open P0/P1 defects from FAIL rows
- [ ] [SUITE_ACCOUNT_WORKSPACE_ACCEPTANCE.md](./SUITE_ACCOUNT_WORKSPACE_ACCEPTANCE.md) signed
- [ ] [SPRINT_D_GATE_REPORT.md](./SPRINT_D_GATE_REPORT.md) updated: Gate closed YES

**Signed off by:** _______________ **Date:** _______________
