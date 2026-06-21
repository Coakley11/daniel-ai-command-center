# Suite Account / Workspace Acceptance Matrix

**Last updated:** 2026-06-21  
**Phase:** Sprint D gate before AMI Importer Phase 0

Mark each row **PASS** / **FAIL** / **N/A** with date, device, and notes.

## Workspace isolation

| # | Scenario | Daniel | Ariel | Notes |
|---|----------|--------|-------|-------|
| W1 | Switch profile in Command Center; open Music | | | |
| W2 | Switch profile; open AMI | | | |
| W3 | Switch profile; open Baseball | | | |
| W4 | Switch profile; open Investment | | | |
| W5 | Switch profile; open NBA | | | |
| W6 | Switch profile; open FutureLens | | | |
| W7 | CC activity feed shows only active workspace events | | | |
| W8 | Continue cards include `?suite_workspace=` | | | |

## Account shell (Sprint B)

| # | Scenario | Pass | Notes |
|---|----------|------|-------|
| A1 | Workspace badge visible in every app sidebar | | |
| A2 | Account & workspace expander in every app sidebar | | |
| A3 | Command Center link preserves workspace param | | |
| A4 | Namespace mismatch warning when URL ≠ profile | | |

## Real Accounts (Sprint C — when `SUITE_AUTH_ENABLED=true`)

| # | Scenario | Pass | Notes |
|---|----------|------|-------|
| C1 | Create account (email/password) | | |
| C2 | Log in | | |
| C3 | Log out | | |
| C4 | Password reset email | | |
| C5 | Ariel account cannot access Daniel workspace data | | |

## Persistence / cross-device

| # | Scenario | Pass | Notes |
|---|----------|------|-------|
| P1 | Music CPL active song phone → Dell | | |
| P2 | Music custom lyrics save phone → Dell | | |
| P3 | AMI UI state phone → Dell | | |
| P4 | Baseball draft queue phone → Dell | | |
| P5 | Direct app open shows correct workspace badge | | |

## Music CPL regression (required)

| # | Scenario | Pass | Notes |
|---|----------|------|-------|
| M1 | Custom ↔ catalog source toggle | | |
| M2 | Recently Selected catalog history | | |
| M3 | Custom song library selector | | |
| M4 | Display key sync | | |
| M5 | Backing defaults unchanged | | |

## Gate

Importer Phase 0 (`decision_templates`, `decision_router`, `decision_math`, `decision_registry`) starts only when:

- [ ] All W1–W8 PASS
- [ ] All A1–A4 PASS
- [ ] C1–C5 PASS or documented N/A with auth disabled on prod
- [ ] P1–P5 PASS
- [ ] M1–M5 PASS

**Signed off by:** _______________ **Date:** _______________
