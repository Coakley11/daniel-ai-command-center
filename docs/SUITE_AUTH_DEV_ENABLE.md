# Enable Real Accounts on dev only (Sprint C/D validation)

**Do not enable on production** until Sprint D gate passes.

## Root cause of “Auth is not configured on this deployment”

The auth **UI** turns on when `suite_auth_enabled = true`. Login/signup also require:

1. Python package **`supabase`** in `requirements.txt` (all suite apps)
2. Existing **`supabase_url`** + **`supabase_key`** (service role — already used for activity/cloud)
3. **`supabase_anon_key`** (public anon key — **new**, required for Auth API)
4. Supabase project **Email** auth provider enabled

Previously, code called `get_supabase_client()` which **did not exist** and `supabase` was not in requirements — the UI showed but the backend always failed.

---

## C2b browser persistence (Streamlit Cloud)

**CookieManager does not work on Streamlit Cloud** — component iframes cannot read/write the parent app cookie jar.

C2b uses:

1. **Opaque session id** in URL: `?suite_sid=<uuid>` via `st.query_params` (survives F5)
2. **Token bundle** in Supabase `suite_saved_items` (`app=_auth_browser`, `item_type=browser_session`)

After login the URL will include `suite_sid=...`. Refresh preserves that param → restore loads tokens from Supabase.

**Security:** URL holds only a random UUID, not JWTs. Logout invalidates the server row and removes the query param.

---

## 1. Supabase project (dashboard)

**Authentication → Providers**

- Enable **Email**
- Optional for dev: disable “Confirm email” to speed up C1 testing
- **Authentication → URL configuration**: add your dev `*.streamlit.app` URLs if redirect errors occur

**C4 password reset (required for live gate):**

1. Run locally (or on deploy with secrets): `python scripts/print_supabase_auth_redirect_checklist.py`
2. Supabase → **Authentication → URL configuration**
   - **Site URL** = Command Center dev URL (same as `auth_password_reset_redirect_url()`)
   - **Redirect URLs** = all suite dev `*.streamlit.app` URLs from the script output
3. Code sends `redirect_to` on `reset_password_email` (defaults to CC dev URL).
4. Reset link lands on CC → **Set new password** panel → update → signed in.

If Site URL is still `http://localhost:3000` (Supabase default), email links show **“This site can't be reached”**.

Optional secrets override:

```toml
suite_auth_redirect_url = "https://daniel-ai-command-center-ion4vh2cvo7bgdnkuktrb3.streamlit.app"
```

**Settings → API**

- Copy **Project URL** → `supabase_url`
- Copy **service_role** → `supabase_key` (server-side PostgREST — already in use)
- Copy **anon public** → `supabase_anon_key` (**required for login**)

---

## 2. Streamlit Cloud secrets (every dev app — identical block)

**Settings → Secrets** — full `[suite_activity]` example:

```toml
[suite_activity]
supabase_url = "https://YOUR_PROJECT_REF.supabase.co"
supabase_key = "YOUR_SERVICE_ROLE_KEY"
supabase_anon_key = "YOUR_ANON_PUBLIC_KEY"
suite_user_id = "daniel"
suite_user_email = "you@example.com"
suite_auth_enabled = true
```

| Key | Required | Purpose |
|-----|----------|---------|
| `supabase_url` | Yes | Supabase project URL |
| `supabase_key` | Yes | Service role — activity, cloud state, PostgREST |
| `supabase_anon_key` | **Yes for auth** | Public anon key — `sign_in_with_password`, sign-up, reset |
| `suite_user_id` | Yes | Legacy secrets identity fallback |
| `suite_user_email` | Recommended | `suite_users` row creation |
| `suite_auth_enabled` | Dev only | Enables auth UI + gate |
| `suite_auth_redirect_url` | Recommended for C4 | Password-reset email landing URL (defaults to CC dev URL) |

### Environment variable fallback (local / CI)

| Variable | Purpose |
|----------|---------|
| `SUITE_SUPABASE_URL` | Same as `supabase_url` |
| `SUITE_SUPABASE_KEY` | Service role key |
| `SUITE_SUPABASE_ANON_KEY` | Anon key for Auth |
| `SUITE_AUTH_ENABLED` | `true` / `1` to enable auth UI |

---

## 3. requirements.txt (every suite app repo)

Add if missing:

```
supabase>=2.0.0
```

Redeploy after changing requirements (push to `dev` or reboot).

---

## 4. Reboot

After secrets or requirements change: **Settings → Reboot app** on each dev deployment.

---

## 5. Validation steps

From Command Center repo (local with secrets.toml) or after deploy:

```bash
python scripts/verify_auth_configuration.py
```

Expected when ready:

- `auth backend ready: True`
- `message: Auth backend ready (C2b query-param + Supabase session storage).`

### C2b — refresh preserves login

1. Log in on CC dev with `?dev=1` optional.
2. Confirm URL contains `suite_sid=<uuid>` after login.
3. Sidebar → **Auth persistence (dev)** — expect:
   - `storage: supabase_query_param`
   - `session_id_present: true`
   - `cloud_payload_present: true`
4. Hard refresh (F5) — should **remain signed in** (URL keeps `suite_sid`).
5. Log out — `suite_sid` removed — refresh shows auth gate.
6. Repeat on one sibling app (separate origin → separate `suite_sid` per app).

---

## 6. Cross-app note

Each `*.streamlit.app` deployment has its own URL and `suite_sid`. Logging in on Command Center does not auto-login Music — log in once per app; refresh then preserves each.

---

## 7. Troubleshooting

| Symptom | Check |
|---------|--------|
| Logged out after F5 | URL missing `suite_sid` → login save failed (check Supabase write) |
| `cloud_payload_present: false` | Row missing in `suite_saved_items` for `_auth_browser` / `browser_session` |
| Auth gate after login | `ensure_user_row` / `auth_user_id` mismatch — see logs |
| Reset link “can't be reached” | Supabase **Site URL** still localhost — run `python scripts/print_supabase_auth_redirect_checklist.py` |
| Reset link loads app but no password form | Redeploy `suite_auth.py` recovery handler; hard refresh after link |

Run: `python scripts/verify_auth_configuration.py`
