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

## 1. Supabase project (dashboard)

**Authentication → Providers**

- Enable **Email**
- Optional for dev: disable “Confirm email” to speed up C1 testing
- **Authentication → URL configuration**: add your dev `*.streamlit.app` URLs if redirect errors occur

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
- `message: Auth backend ready.`

Then manual C1–C5 on CC dev:

| # | Check |
|---|-------|
| C1 | Create account (email/password) |
| C2 | Log in on CC + one sibling app |
| C3 | Log out |
| C4 | Password reset email |
| C5 | Ariel account clamped to Ariel workspace |

Login errors should now show Supabase messages (invalid password, etc.), **not** “Auth is not configured”.

---

## 6. Roll back

Set `suite_auth_enabled = false` or remove it; reboot. Apps revert to secrets-based Workspace Profiles v1.
