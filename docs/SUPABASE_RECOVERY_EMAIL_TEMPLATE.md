# Supabase Recovery Email Template (Streamlit / PKCE)

**Last updated:** 2026-06-19

Streamlit Cloud cannot read URL **hash fragments** (`#access_token=...`). The default Supabase **Reset password** template uses `{{ .ConfirmationURL }}`, which redirects to the **bare Site URL** with no query params — Command Center sees `/` only and C4 fails.

Use a **PKCE-style** link that puts `token_hash` in the **query string** and points at **`{{ .SiteURL }}`** (not ConfirmationURL).

## Dashboard steps

1. Open [Supabase Dashboard](https://supabase.com/dashboard) → your project → **Authentication** → **Email Templates**.
2. Select **Reset password** (Recovery).
3. Replace the **entire** email body with the template below (remove any `{{ .ConfirmationURL }}` link).
4. **Save** — wait for “Saved successfully”.
5. Send a **new** reset email (old emails keep the old link).

## URL configuration (required)

Run locally:

```bash
python scripts/print_supabase_auth_redirect_checklist.py
```

| Setting | Value |
|---------|--------|
| **Site URL** | `https://daniel-ai-command-center-ion4vh2cvo7bgdnkuktrb3.streamlit.app` (base only, no `?`) |
| **Redirect URLs** | Same base URL + all suite dev URLs from script output |

`reset_password_email` sends `redirect_to` as the **base** CC URL (no query). The email template adds `suite_auth_landing`, `token_hash`, and `type`.

## Recovery email body (HTML) — use SiteURL

**Prefer `{{ .SiteURL }}`** so the href works even if `{{ .RedirectTo }}` is empty in the template context.

```html
<h2>Reset password</h2>
<p>Follow this link to reset the password for your user:</p>
<p><a href="{{ .SiteURL }}?suite_auth_landing=recovery&token_hash={{ .TokenHash }}&type=recovery">Reset password</a></p>
```

## Plain-text alternative

```text
Reset password

Follow this link to reset the password for your user:
{{ .SiteURL }}?suite_auth_landing=recovery&token_hash={{ .TokenHash }}&type=recovery
```

## Verify the email href before clicking

Right-click the reset link → **Copy link address**. The copied URL must visibly contain:

- `suite_auth_landing=recovery`
- `token_hash=` (long hash string)
- `type=recovery`

**Expected shape:**

`https://daniel-ai-command-center-ion4vh2cvo7bgdnkuktrb3.streamlit.app?suite_auth_landing=recovery&token_hash=…&type=recovery`

If the href is only the bare Site URL (no `?`) or a `supabase.co/auth/v1/verify?...` link, the template was **not** saved correctly.

## What Supabase sends

| Template | Typical link shape | Works on Streamlit? |
|----------|-------------------|---------------------|
| Default `{{ .ConfirmationURL }}` | verify → redirect to bare Site URL `/` | **No** |
| PKCE with `{{ .SiteURL }}` + token_hash (above) | CC URL with query params | **Yes** |

## Dev diagnostics

| Field | Meaning |
|-------|---------|
| `recovery_bare_site_landing: true` | Browser and server see no recovery query params — email href wrong |
| `query_param_keys: []` | Streamlit server sees `/` only |
| `browser_query_keys: []` | Browser URL also has no recovery params |
| `expected_email_href_prefix` | What the reset email href should start with |
| `reset_redirect_to_sent` | Base URL sent to Supabase API (no `?suite_auth_landing`) |

## Do not use

- `{{ .ConfirmationURL }}` for Streamlit apps.
- Links that only put tokens in `#access_token=...` (hash is lost before Python runs).
