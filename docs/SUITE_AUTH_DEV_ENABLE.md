# Enable Real Accounts on dev only (Sprint C validation)

**Do not enable on production** until Sprint D gate passes.

## 1. Supabase Auth

In Supabase project → **Authentication** → **Providers**:

- Enable **Email** provider
- Configure site URL / redirect URLs for your `*.streamlit.app` dev URLs if required
- Optional: disable email confirmation for dev testing (project policy)

## 2. Streamlit Cloud secrets (dev deployments only)

For each **dev** app (Command Center + Music + AMI + Investment + NBA + FutureLens + Baseball dev):

**Settings → Secrets** — add under existing `[suite_activity]` block:

```toml
[suite_activity]
# ... existing supabase_url, supabase_key, suite_user_id, suite_user_email ...
suite_auth_enabled = true
```

Or set environment variable on the deployment: `SUITE_AUTH_ENABLED=true`

## 3. Reboot

After saving secrets: **Settings → Reboot app** on each dev deployment.

Push-to-`dev` redeploys code but **does not** apply secret changes until reboot.

## 4. Validate C1–C5

| # | Check |
|---|-------|
| C1 | Create test account (email/password) on CC dev |
| C2 | Log in on CC + one sibling app |
| C3 | Log out clears session |
| C4 | Password reset email arrives |
| C5 | Ariel test account stays clamped to Ariel workspace (cannot persist Daniel profile data) |

## 5. Roll back

Remove `suite_auth_enabled` or set `false`; reboot. Apps revert to secrets-based identity (Workspace Profiles v1).
