# Suite Account / Workspace Acceptance Matrix

**Last updated:** 2026-06-21  
**Phase:** Sprint D gate before AMI Importer Phase 0  
**Deploy:** Command Center `4044ee1` pushed to `dev`; sibling sync commits pushed 2026-06-21

Mark each row **PASS** / **FAIL** / **PENDING** / **N/A** with date, device, and notes.

## Deploy log (2026-06-21)

| Step | Status | Notes |
|------|--------|-------|
| Push CC `4044ee1` | **DONE** | `origin/dev` |
| `sync_suite_cloud_modules.py` | **DONE** | All 6 sibling repos |
| Commit/push sibling repos | **DONE** | Music `a0979f1`, AMI `6e3144c`, Investment `60b122e`, NBA `0f119df`, FutureLens `07777a5`, Baseball `4864a59` |
| Streamlit Cloud redeploy | **TRIGGERED** | Auto on push; allow 5–15 min |
| Manual reboot | **PENDING** | Required after `suite_auth_enabled` secret change only |
| `SUITE_AUTH_ENABLED` on dev | **PENDING** | Requires Streamlit Cloud secrets — see [SUITE_AUTH_DEV_ENABLE.md](./SUITE_AUTH_DEV_ENABLE.md) |
| Automated tests (CC) | **PASS** | 70 passed (workspace + audit + auth scaffolding) |

## Workspace isolation

| # | Scenario | Daniel | Ariel | Result | Notes |
|---|----------|--------|-------|--------|-------|
| W1 | Switch profile in Command Center; open Music | | | **PENDING** | Manual browser — deploy redeploy in progress |
| W2 | Switch profile; open AMI | | | **PENDING** | Manual browser |
| W3 | Switch profile; open Baseball | | | **N/A** | Local `streamlit_app.py` empty; shell not wired in entry |
| W4 | Switch profile; open Investment | | | **PENDING** | Manual browser |
| W5 | Switch profile; open NBA | | | **PENDING** | Manual browser |
| W6 | Switch profile; open FutureLens | | | **PENDING** | Manual browser |
| W7 | CC activity feed shows only active workspace events | | | **PASS (auto)** | `test_workspace_cc_activity.py` |
| W8 | Continue cards include `?suite_workspace=` | | | **PASS (auto)** | `test_suite_sprint_b_audit.py` + `continue_dashboard` fix |

## Account shell (Sprint B)

| # | Scenario | Result | Notes |
|---|----------|--------|-------|
| A1 | Workspace badge visible in every app sidebar | **PENDING** | Code wired; verify in browser after redeploy (Streamlit sidebar not in static HTML probe) |
| A2 | Account & workspace expander in every app sidebar | **PENDING** | Same — manual sign-off |
| A3 | Command Center link preserves workspace param | **PASS (auto)** | `audit_command_center_link_url` |
| A4 | Namespace mismatch warning when URL ≠ profile | **PENDING** | Manual — open app with mismatched `?suite_workspace=` |

## Real Accounts (Sprint C — when `SUITE_AUTH_ENABLED=true`)

| # | Scenario | Result | Notes |
|---|----------|--------|-------|
| C1 | Create account (email/password) | **BLOCKED** | Enable `suite_auth_enabled = true` on dev secrets + reboot |
| C2 | Log in | **BLOCKED** | Same |
| C3 | Log out | **BLOCKED** | Same |
| C4 | Password reset email | **BLOCKED** | Supabase Auth email + secrets |
| C5 | Ariel account cannot access Daniel workspace data | **PASS (auto)** | `test_enforce_workspace_ownership_clamps_profile`; live test **BLOCKED** until auth enabled |

## Persistence / cross-device

| # | Scenario | Result | Notes |
|---|----------|--------|-------|
| P1 | Music CPL active song phone → Dell | **PENDING** | Manual phone + Dell |
| P2 | Music custom lyrics save phone → Dell | **PENDING** | Manual |
| P3 | AMI UI state phone → Dell | **PENDING** | Manual |
| P4 | Baseball draft queue phone → Dell | **PENDING** | Manual |
| P5 | Direct app open shows correct workspace badge | **PENDING** | Manual |

## Music CPL regression (required)

| # | Scenario | Result | Notes |
|---|----------|--------|-------|
| M1 | Custom ↔ catalog source toggle | **PENDING** | Manual (v29k) |
| M2 | Recently Selected catalog history | **PENDING** | Manual (v29k) |
| M3 | Custom song library selector | **PENDING** | Manual (v29l) |
| M4 | Display key sync | **PENDING** | Manual |
| M5 | Backing defaults unchanged | **PENDING** | Manual |

## Gate

Importer Phase 0 (`decision_templates`, `decision_router`, `decision_math`, `decision_registry`) starts only when:

- [ ] All W1–W8 PASS
- [ ] All A1–A4 PASS
- [ ] C1–C5 PASS (auth enabled on dev)
- [ ] P1–P5 PASS
- [ ] M1–M5 PASS

**Gate status (2026-06-21):** **NOT PASSED** — automated subset green; manual browser, cross-device, CPL, and auth validation remain.

**Signed off by:** _______________ **Date:** _______________
