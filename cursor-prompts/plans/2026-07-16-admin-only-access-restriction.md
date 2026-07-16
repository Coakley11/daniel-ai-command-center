# Security — Admin-only production access restriction (2026-07-16)

## Goal

Every suite app (Command Center, Baseball, Music, NBA, Investment / Portfolio Hub, AMI, Future Lens, and future apps) must behave like a normal production product for standard users. Only authorized owner accounts may access developer, debugging, diagnostic, deployment, or administrative functionality.

## Authorized admin accounts

| Identity form | Notes |
|---------------|--------|
| `coakley11` | Email local-part (immutable authenticated identity) |
| `daniel.cohen11` | Email local-part (immutable authenticated identity) |

Resolved suite external_id / workspace preset `daniel` is **not** an admin grant. It only describes the profile id inferred for `daniel.cohen11@…`. Workspace ids, display names, account slugs, query params, and forged session `external_id` values never grant admin.

## Authorization model

- **Source of truth:** `suite_workspace_registry.ADMIN_ACCOUNTS` + `is_admin_user()`
- **Server-side only** — based on authenticated account identity (or secrets `suite_user_id` when Real Accounts auth is off)
- **Not granted by:** workspace ownership alone, league ownership, invites, client toggles, or `?dev=1` without admin identity
- **Fail-safe:** if auth/identity cannot be determined → standard user (hide all admin/dev tools). Never default to admin.

## What is gated

All surfaces that already used `can_show_developer_tools()` now require **admin identity AND** explicit Developer Mode (`?dev=1` or session toggle), including:

- Developer Mode toggle (Command Center Advanced)
- Debug / diagnostics / resume / auth / workspace / cloud / egress panels
- Deploy markers, build/commit footers, Deployment & link audit
- Full Account & Workspace identity diagnostics

Shared modules (`suite_app_shell`, `suite_account_settings`, `suite_auth`, `suite_workspace`, `suite_egress_trace`) are synced to sibling apps via `scripts/sync_suite_cloud_modules.py`.

## Regular user experience

Non-admins see only production UX: fantasy/draft/research/music/analytics tools and end-user account features (email + logout). No developer-facing controls, internal IDs, build metadata, or diagnostics.

## Sensitive information

Do not expose secrets, API keys, tokens, credentials, env vars, auth metadata, admin internal IDs, or infrastructure paths to non-admins. Auth recovery JSON diagnostics are admin-only (no `force=` bypass).

## Streamlit Cloud Manage / Reboot

Streamlit Cloud **Manage app** / **Reboot** / Secrets / Logs are platform-owner controls on streamlit.io — they cannot be gated by in-app `is_admin_user()`. In-app CSS may hide MainMenu/footer chrome; Cloud dashboard access remains with the Streamlit account that owns the deploy.

## Deploy steps

1. Merge/push Command Center `dev` with updated shared modules
2. Run `python scripts/sync_suite_cloud_modules.py` (or existing sync workflow) to sibling repos
3. Reboot each Streamlit Cloud app after sync
4. Verify: sign in as non-admin → no Advanced/Developer Mode/diagnostics; sign in as `coakley11` or `daniel.cohen11` → Developer Mode available
