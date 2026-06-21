# Supabase Recovery Email Template (Streamlit / PKCE)

**Last updated:** 2026-06-19

Streamlit Cloud cannot read URL **hash fragments** (`#access_token=...`). The default Supabase **Reset password** template uses `{{ .ConfirmationURL }}`, which often lands users on Command Center **without** query or hash tokens the app can consume.

Use a **PKCE-style** link that puts `token_hash` in the **query string** instead.

## Dashboard steps

1. Open [Supabase Dashboard](https://supabase.com/dashboard) → your project → **Authentication** → **Email Templates**.
2. Select **Reset password** (Recovery).
3. Replace the link in the body with the template below.
4. Save.
5. Send a **new** reset email (old emails keep the old link).

## URL configuration (unchanged)

Run locally:

```bash
python scripts/print_supabase_auth_redirect_checklist.py
```

- **Site URL** and **Redirect URLs** must include the Command Center dev URL.
- `redirect_to` in code appends `?suite_auth_landing=recovery` so the app can detect a reset landing even before tokens arrive.

## Recovery email body (HTML)

```html
<h2>Reset password</h2>
<p>Follow this link to reset the password for your user:</p>
<p><a href="{{ .RedirectTo }}?token_hash={{ .TokenHash }}&type=recovery">Reset password</a></p>
```

## Plain-text alternative

```text
Reset password

Follow this link to reset the password for your user:
{{ .RedirectTo }}?token_hash={{ .TokenHash }}&type=recovery
```

## What Supabase sends

| Template | Typical link shape | Works on Streamlit? |
|----------|-------------------|---------------------|
| Default `{{ .ConfirmationURL }}` | `https://<project>.supabase.co/auth/v1/verify?token=...&type=recovery&redirect_to=<app>` → may redirect with hash or nothing | Often **no** |
| PKCE `token_hash` (above) | `https://<app>?suite_auth_landing=recovery&token_hash=...&type=recovery` | **Yes** |

## C4 PASS criteria

1. Reset email received.
2. Link opens Command Center (no “site can't be reached”).
3. **Set new password** panel appears.
4. New password saves; user is signed in.

## Dev diagnostics

On the recovery wait or failure screen, expand **Auth recovery (dev)** and check:

- `configured_reset_redirect_to` — must match Supabase redirect allow-list.
- `client_landing_snapshot` — `th:1` means `token_hash` reached the browser query string.
- `recovery_token_hash_in_query` — `true` when server sees `token_hash`.
- `email_template_action_required` — `true` when landing hint is present but no token shape was detected.

## Do not use

- `{{ .ConfirmationURL }}` alone for Streamlit apps.
- Links that only put tokens in `#access_token=...` (hash is lost before Python runs).
