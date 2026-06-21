# Account / Workspace Phase — Completion Plan (Before AMI Importer)

**Last updated:** 2026-06-21  
**Branch:** `dev`  
**Status:** Sprint B + C **scaffolding shipped** (2026-06-21) — Sprint D manual gate + deploy sync pending. **Do not start AMI Real Problem Importer** until exit criteria pass.

**User goal:** Reliable account foundation for all suite apps — not enterprise auth. Finish this phase, then begin AMI Importer as **architecture + scaffolding only** (prediction-market first; universal routing later).

---

## Executive summary

| Layer | Status | Remaining |
|-------|--------|-----------|
| **Workspace Profiles v1** | ~90% shipped | Manual W1–W8 acceptance |
| **Account Settings UX (Sprint A)** | Shipped in Command Center | — |
| **Account Settings + shell (Sprint B)** | **Code shipped** | Deploy sync, Baseball entry, manual A1–A4 |
| **Real Accounts (Sprint C)** | **Scaffolding shipped** (flag off) | Enable auth on prod, C1–C5, auth UUID mapping |
| **Persistence validation (Sprint D)** | Doc ready | Execute acceptance matrix + Music CPL regression |
| **AMI Real Problem Importer** | Planned only | Blocked until above |

**Today’s identity model:** `suite_user_id` + email from Streamlit secrets / env → `ensure_user_row()` in Supabase. **Not** login-gated. Anyone can switch Daniel/Ariel presets in Command Center.

---

## What is already completed

### Workspace system (Phase 1 foundation)

- [x] `suite_workspace.py` — presets (`daniel`, `ariel`, `guest`, `test_user`), normalization, disk paths, cloud key scoping
- [x] `data/workspaces/{id}/{app}_user_state.json` + legacy migration to `daniel/`
- [x] `scoped_cloud_app_id()` — Daniel keeps legacy keys; others use `music__ariel`, etc.
- [x] `init_suite_workspace(st)` — URL `?suite_workspace=` overrides session + persisted file
- [x] Deep links — `append_suite_workspace_param`, `build_resume_action_url`, `app_registry.get_app_url`
- [x] `sync_workspace_protocol()` — cloud restore, autosave block, resume skip
- [x] CC workspace switcher + activity/resume filtering by workspace namespace
- [x] Validated (automated + user): CC, Investment, Baseball, AMI, Music, **NBA** (2026-06-19)
- [x] FutureLens — code + 10 tests; manual Daniel/Ariel acceptance marked done in tasks

### Account memory & cloud

- [x] `suite_account.py` — saved items, settings, `sync_local_state_to_cloud`
- [x] `suite_storage_supabase.py` — `suite_users`, `suite_user_settings`, `suite_app_current_state`, activity, resume
- [x] `suite_user.py` — email, display name, external id resolution
- [x] Migrations `002_suite_account_memory*.sql`, `003_suite_account_memory_resume.sql`
- [x] Tests: `test_suite_account_memory.py`, `test_workspace_sync_protocol.py`, `test_workspace_cc_activity.py`

### Account Settings UX (Sprint A — Command Center only)

- [x] `suite_account_settings.py` — identity summary, scoped cloud key preview, namespace mismatch warnings
- [x] CC sidebar — `render_global_workspace_badge()`, workspace selector
- [x] CC homepage — Account & workspace panel
- [x] Password reset — intentional stub (“Real Accounts Phase 2”)
- [x] Tests: `test_account_settings_panel.py` (13 tests)

### Music / CPL (persistence — do not regress)

- [x] `prepare_music_workspace()` + workspace-scoped paths (`music_workspace_paths.py`)
- [x] CPL v29k–v29l — source toggle, catalog history, lyrics save (separate track; regression-check during Sprint D)

---

## Remaining gaps (by priority area)

### 1. Account Settings across all apps — **HIGH**

| Gap | Severity | Notes |
|-----|----------|-------|
| `suite_account_settings.py` not synced to sibling repos | **High** | In sync script list; Music has no copy on disk |
| No Account page/panel outside Command Center | **High** | Users opening Music/Baseball directly never see account context |
| No consistent nav to account/workspace | **High** | CC-only switcher; siblings rely on URL param or local JSON |
| `suite_account.py` drift (email in summary) | **Low** | CC has email; Music copy may lag after sync |

### 2. Workspace system polish — **HIGH**

| Gap | Severity | Notes |
|-----|----------|-------|
| Global workspace badge not in sibling sidebars | **High** | P1b backlog |
| Workspace selector not in sibling apps | **Medium** | Read-only badge + link to CC acceptable for v1 |
| Deep-link audit incomplete | **High** | Not every Open/Continue URL verified for `?suite_workspace=` |
| Cross-device workspace choice | **Medium** | Profile is per-deployment `suite_active_workspace.json` unless URL param used |
| Namespace mismatch on write vs read | **Medium** | Diagnostics exist in CC; banner in siblings missing |
| Activity sync audit (all apps → CC) | **Medium** | AMI partial; full six-app pass pending |

### 3. Real account foundation — **BLOCKER for Importer**

| Capability | Status |
|------------|--------|
| Email-based account model | **Partial** — email in secrets only, not verified login |
| Account creation | **Missing** |
| Login | **Missing** |
| Logout | **Missing** |
| Password reset | **Stub UI only** |
| User profile storage | **Partial** — `suite_users` row via `external_id`; no auth-linked profile fields |
| User preferences storage | **Shipped** — `suite_user_settings` via `save_settings` / `load_settings` |
| Workspace ownership model | **Partial** — preset profiles, not tied to authenticated user |

**Important:** This is **not** enterprise SSO. Target: **Supabase Auth** (email/password) + map `auth.users.id` → `suite_users` + session cookie/token in Streamlit session state.

### 4. Persistence validation — **HIGH (gate)**

| Check | Status |
|-------|--------|
| Account/workspace disk paths | Automated tests pass |
| Cloud `full_session` restore | Automated + Music/AMI manual paths |
| Cross-device (phone ↔ Dell) | Validated per-app ad hoc; no single matrix sign-off |
| CPL / Music regression on workspace switch | v29k/v29l shipped; re-verify in Sprint D |
| Direct app open without `?suite_workspace=` | **Risk** — defaults to Daniel or local persisted file |

---

## Recommended implementation plan

### Sprint B — Account Settings + workspace polish (1–2 weeks)

**Goal:** Same account/workspace UX everywhere; no auth yet.

1. **Sync shared modules**
   - Run `python scripts/sync_suite_cloud_modules.py` from Command Center
   - Commit sibling repos (Music, Baseball, NBA, Investment, AMI, FutureLens)

2. **Wire sibling app shell (each app)**
   - Call `init_suite_workspace(st)` at startup (audit — Music has it via `apply_suite_resume_launch`; verify others)
   - Sidebar: `render_global_workspace_badge(st)` on every page
   - Sidebar or Settings page: `render_account_settings_panel(st, expanded=False)` (compact expander)
   - Link: “Manage workspace in Command Center” → CC URL with `?suite_workspace={active}`

3. **Deep-link audit**
   - Grep all `get_app_url`, Open buttons, Continue cards, manual bookmarks
   - Fix any URL missing `suite_workspace`
   - Add test: `test_all_app_urls_include_workspace_param`

4. **Namespace warnings**
   - Reuse `detect_account_settings_issues()` from `suite_account_settings.py`
   - Show compact warning banner in sibling sidebars when query param ≠ active workspace

5. **Activity sync audit**
   - Confirm each app writes `workspace_id` + scoped `app` key on activity and analytical events

**Exit criteria Sprint B:**
- Open any suite app → see workspace badge matching CC selection
- Account expander shows email, ids, scoped cloud keys
- Open Music from CC as Ariel → URL has `?suite_workspace=ariel` → Ariel disk/cloud keys active

---

### Sprint C — Real Accounts foundation (2–3 weeks)

**Goal:** Success criteria auth flows without overbuilding.

**Stack:** Supabase Auth (email/password) + existing `suite_users` / `suite_user_settings`.

| Task | Detail |
|------|--------|
| **Auth module** | New `suite_auth.py` — signup, login, logout, session restore, password reset email |
| **UI** | `render_auth_panel(st)` — login/signup forms; replace secrets-only identity when auth enabled |
| **User row mapping** | On first login: `ensure_user_row(external_id=auth.uid or email)`; store `auth_user_id` on `suite_users` |
| **Profile** | Display name + email from auth; optional `suite_user_settings` `_global` profile keys |
| **Logout** | Clear Streamlit session + auth token; redirect to login or guest read-only mode |
| **Password reset** | Supabase `resetPasswordForEmail`; wire existing stub button when `password_auth_available=True` |
| **Workspace ownership** | v1: authenticated user **selects** workspace preset (same as today); v1.1: map `user_id → allowed workspace_ids` (Daniel admin sees all; Ariel sees `ariel` only) |
| **Feature flag** | `SUITE_AUTH_ENABLED` secret — dev can run secrets mode until auth deployed |
| **All apps** | Shared auth gate at top of each `streamlit_*.py` (or shared `suite_app_bootstrap.py`) |

**Explicitly out of scope (Sprint C):**
- Google OAuth (optional fast-follow)
- Enterprise SSO, MFA, org admin
- Billing / subscriptions

**Exit criteria Sprint C:**
- Create account → login → see profile in Account Settings
- Logout → session cleared
- Reset password email flow works (Supabase)
- Daniel and Ariel can each log in (or share deployment with role flags) and see isolated workspace data

---

### Sprint D — Persistence validation matrix (1 week, parallel with C tail)

Manual + automated acceptance. **Do not break Music CPL.**

| Scenario | Apps | Pass criteria |
|----------|------|---------------|
| Workspace switch | All 6 | Daniel action invisible in Ariel feed/state |
| Deep link | CC → each app | Correct workspace without manual switch |
| Cloud restore | Music, AMI, Baseball | Phone edit → Dell shows same state (same profile + auth user) |
| Direct open | Music, AMI | Badge shows active workspace; warning if mismatch |
| Auth + workspace | All | Login → workspace selection persists in `suite_active_workspace.json` per user |
| CPL regression | Music | Custom/catalog toggle, lyrics save, display key sync still pass |

Document results in `docs/SUITE_ACCOUNT_WORKSPACE_ACCEPTANCE.md`.

**Exit criteria Sprint D:** Matrix signed off; no P0/P1 open items.

---

### Gate — AMI Real Problem Importer (after B + C + D)

**Do not implement full importer yet.** First deliverable is **architecture + scaffolding only**.

**Product vision:** AMI as a router for real-world decisions — not only calculators.

```
Real market page / problem text
  → Importer (paste/CSV/manual v1; screenshot/URL later)
  → Extract key fields
  → Classify (e.g. Prediction Market / Betting EV)
  → Route to AMI section (Betting / Expected Value for v1)
  → Prefill existing fields
  → User adjusts assumptions
  → AMI explains math and decision support
```

**V1 concrete use case:** Kalshi-style prediction-market import.

**Extract (Kalshi example):** market question, YES price, NO price, contract side, cost, payout, expiration, metadata, source text.

**Calculate:** implied probability, break-even probability, expected value, edge, risk/reward, profit/loss, conservative position size.

**Framing:** mathematical decision-analysis — not gambling advice. Disclaimer on user assumptions, fees, liquidity, jurisdiction, risk tolerance.

**Future routing registry (backlog):**

| Problem | Route |
|---------|-------|
| Car lease / purchase | Financial Decisions / Major Purchase Analysis |
| Compare two cars | Financial Decisions / Major Purchase Comparison |
| Cell phone purchase | Consumer Purchase Comparison |
| Job offers | Career / Job Offer Decision Analysis |
| Business deal | Cost-Benefit Analysis |
| Single stock / short-term trade | Trade / Risk-Reward Decision |
| Prediction market / bet | Betting / Expected Value |
| Treatment decision | Risk-Benefit Analysis |

**Phase 0 (Importer scaffolding — 1 week):**
- `decision_templates.py` — registry: `id`, `label`, `fields[]`, `solver`, `route_target`
- `decision_router.py` — `classify(text) → template_id` (rule-based v1; LLM later)
- `decision_math.py` — EV, break-even, edge (extract from existing AMI interactives where possible)
- `decision_registry.py` — route target → AMI module/section mapping
- AMI UI: empty “Analyze a real decision” section with template picker only (no Kalshi math UI yet)
- Tests: `test_decision_math.py`, workspace isolation for `dec_*`
- **No OCR, URL parsing, screenshot processing, or large UI build in Phase 0**

**Phase 1 (Importer MVP — after scaffolding review):**
- Paste/CSV/manual prediction-market import → prefill Betting/EV → disclaimer → workspace-scoped persist → activity → Command Center

---

## Success criteria (full Account / Workspace phase)

A user can:

- [ ] Create an account (email)
- [ ] Log in / log out
- [ ] Reset password
- [ ] View Account Settings in **any** suite app
- [ ] See consistent workspace badge and cloud namespace
- [ ] Own/use workspace profiles with isolation (Daniel vs Ariel)
- [ ] Move between apps preserving workspace (and after Sprint C, auth) context
- [ ] Rely on cloud restore cross-device without CPL/state regressions

---

## Risk register

| Risk | Mitigation |
|------|------------|
| Auth breaks existing secrets-based deploys | Feature flag; secrets mode fallback |
| Streamlit session + auth token expiry | Document refresh behavior; restore from Supabase session on rerun |
| Workspace preset vs authenticated user confusion | Settings copy: “Workspace profile” until multi-tenant workspaces |
| Sync script not run | CI check: hash compare CC vs sibling `suite_*.py` |
| Importer started too early | Hard gate in `app_tasks.md`; no `dec_*` code until Sprint D pass |
| Music CPL regression | Sprint D explicit row; run Music test suite on auth PRs |

---

## Test coverage today vs needed

| Area | Existing | Needed |
|------|----------|--------|
| Workspace | `test_suite_workspace.py`, `test_workspace_*` | Deep-link all-apps test |
| Account Settings | `test_account_settings_panel.py` | Sibling wiring smoke (import + render callable) |
| Auth | None | `test_suite_auth.py` (mock Supabase) |
| Persistence | `test_workspace_sync_protocol.py` | Acceptance doc + optional e2e script |
| Importer | None | Phase 0 unit tests only |

---

## Immediate next actions (this week)

1. Run `sync_suite_cloud_modules.py`; wire Music sidebar badge + account expander (first sibling pilot)
2. Complete deep-link audit checklist (spreadsheet or test file)
3. Draft `suite_auth.py` API sketch + Supabase Auth enablement checklist
4. **Do not** start Importer UI or Kalshi template until Sprint B exit + Sprint C login/logout demo

---

## Related docs

- [2026-06-19-account-settings-real-problem-importer-roadmap.md](./2026-06-19-account-settings-real-problem-importer-roadmap.md) — superseded order for Importer gate; auth moved before Importer
- [2026-06-19-workspace-profiles-real-accounts-live-draft-room.md](./2026-06-19-workspace-profiles-real-accounts-live-draft-room.md) — long-range auth + Live Draft Room
- [../app_tasks.md](../app_tasks.md) — active checklist
- [../../docs/SUITE_ACCOUNT_MEMORY.md](../../docs/SUITE_ACCOUNT_MEMORY.md) — storage schema
