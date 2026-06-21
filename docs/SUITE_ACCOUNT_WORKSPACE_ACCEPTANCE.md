# Suite Account / Workspace Acceptance Matrix

**Last updated:** 2026-06-21  
**Phase:** Sprint D gate before AMI Importer Phase 0  
**Full report:** [SPRINT_D_GATE_REPORT.md](./SPRINT_D_GATE_REPORT.md)

## Gate verdict: **NOT CLOSED**

---

## Workspace isolation

| # | Scenario | Result | Notes |
|---|----------|--------|-------|
| W1 | Switch profile in CC; open Music | **MANUAL PENDING** | Deploy wired (`a0979f1`); browser sign-off |
| W2 | Switch profile; open AMI | **MANUAL PENDING** | Deploy wired (`6e3144c`) |
| W3 | Switch profile; open Baseball | **N/A** | Entry shell not wired |
| W4 | Switch profile; open Investment | **MANUAL PENDING** | Deploy wired (`60b122e`) |
| W5 | Switch profile; open NBA | **MANUAL PENDING** | Deploy wired (`0f119df`) |
| W6 | Switch profile; open FutureLens | **MANUAL PENDING** | Deploy wired (`07777a5`) |
| W7 | CC activity feed workspace isolation | **PASS** | `test_workspace_cc_activity.py` |
| W8 | Continue cards include `?suite_workspace=` | **PASS** | Audit tests + `continue_dashboard` |

## Account shell (Sprint B)

| # | Scenario | Result | Notes |
|---|----------|--------|-------|
| A1 | Workspace badge in every app sidebar | **MANUAL PENDING** | Code deployed; verify in browser |
| A2 | Account & workspace expander in sidebars | **MANUAL PENDING** | Same |
| A3 | Command Center link preserves workspace param | **PASS** | Automated audit |
| A4 | Namespace mismatch warning when URL ≠ profile | **PASS (logic)** | Unit test; live banner **MANUAL PENDING** |

## Real Accounts (Sprint C — `SUITE_AUTH_ENABLED=true`)

| # | Scenario | Result | Notes |
|---|----------|--------|-------|
| C1 | Create account | **BLOCKED** | Enable `suite_auth_enabled=true` on dev secrets + reboot |
| C2 | Log in | **BLOCKED** | Same |
| C3 | Log out | **BLOCKED** | Same |
| C4 | Password reset email | **BLOCKED** | Same + Supabase Auth email |
| C5 | Ariel cannot access Daniel workspace | **PASS (unit)** | Ownership clamp test; live **BLOCKED** until auth on |

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
- [ ] C1–C5 PASS on dev
- [ ] P1–P5 PASS
- [ ] M1–M5 PASS

**Signed off by:** _______________ **Date:** _______________
