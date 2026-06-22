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

- **Site URL** and **Redirect URLs** must include the Command Center dev URL (base URL, no query string).
- `reset_password_email` sends `redirect_to` as the **base** CC URL (no query params).
- The email template adds `suite_auth_landing`, `token_hash`, and `type` in one query string.

## Recovery email body (HTML)

**Use `?` once** — do **not** append `?token_hash=` to `{{ .RedirectTo }}` if RedirectTo already contains query params.

```html
<h2>Reset password</h2>
<p>Follow this link to reset the password for your user:</p>
<p><a href="{{ .RedirectTo }}?suite_auth_landing=recovery&token_hash={{ .TokenHash }}&type=recovery">Reset password</a></p>
```

## Plain-text alternative

```text
Reset password

Follow this link to reset the password for your user:
{{ .RedirectTo }}?suite_auth_landing=recovery&token_hash={{ .TokenHash }}&type=recovery
```

## What Supabase sends

| Template | Typical link shape | Works on Streamlit? |
|----------|-------------------|---------------------|
| Default `{{ .ConfirmationURL }}` | verify endpoint → hash or empty redirect | **No** |
| Wrong PKCE `{{ .RedirectTo }}?token_hash=...` when RedirectTo already has `?` | `...?suite_auth_landing=recovery?token_hash=...` (malformed) | **No** — stuck on “Processing…” |
| Correct PKCE (above) | `https://<app>?suite_auth_landing=recovery&token_hash=...&type=recovery` | **Yes** |

## C4 PASS criteria

1. Reset email received.
2. Link opens Command Center (no “site can't be reached”).
3. **Set new password** panel appears.
4. New password saves; user is signed in.

## Dev diagnostics

On the recovery wait or failure screen, expand **Auth recovery (dev)** and check:

- `recovery_token_hash_parsed: true` — app extracted token_hash (including malformed-landing fallback).
- `recovery_token_hash_malformed_landing: true` — old template used `?token_hash=` after a RedirectTo that already had `?`; update template and send a new email.
- `recovery_token_hash_in_query: true` — Streamlit saw `token_hash` as its own query param (correct URL shape).
- `recovery_query_promotion_needed: true` — browser URL has `token_hash` but Streamlit `query_params` did not; app rewrites URL client-side.
- `recovery_verify_attempted: true` — `verify_otp` ran once for this link.

## Do not use

- `{{ .ConfirmationURL }}` alone for Streamlit apps.
- `{{ .RedirectTo }}?token_hash=...` when RedirectTo already contains `?suite_auth_landing=recovery`.
- Links that only put tokens in `#access_token=...` (hash is lost before Python runs).
