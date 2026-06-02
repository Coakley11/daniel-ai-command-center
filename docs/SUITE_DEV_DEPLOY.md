# Suite dev deploy — account memory + Supabase

After migration `002_suite_account_memory_paste.sql` succeeds in Supabase:

## 1. Streamlit secrets (every app)

Paste **the same block** into Streamlit Cloud → **Settings → Secrets** for each deployment, then **Reboot app**.

| Streamlit app | Repository | Branch | Main file |
|---------------|------------|--------|-----------|
| Daniel Cohen AI Command Center | `Coakley11/daniel-ai-command-center` | `dev` | `ai_command_center.py` |
| Music Practice Coach | `Coakley11/ai-music-practice-coach` | `dev` | `streamlit_music_practice_app.py` |
| Baseball Analytics | `Coakley11/baseball-stat-app` | `dev` | `streamlit_app.py` |
| Basketball Companion | `Coakley11/nba-playoff-companion-ai` | `dev` | `streamlit_app.py` |
| Investment Analytics | `Coakley11/investment-portfolio-analyzer` | `dev` | `streamlit_app.py` |
| Applied Intelligence | `Coakley11/applied-mathematical-intelligence` | `dev` | `streamlit_app.py` |
| AI Future Simulator | `Coakley11/future-lens-ai-transition-simulator` | `dev` | `streamlit_app.py` |

### Required secrets (TOML)

```toml
[suite_activity]
supabase_url = "https://YOUR_PROJECT.supabase.co"
supabase_key = "YOUR_SERVICE_ROLE_KEY"
suite_user_id = "daniel"
suite_user_email = "you@example.com"
```

| Key | Required | Notes |
|-----|----------|--------|
| `supabase_url` | Yes | Project URL from Supabase → Settings → API |
| `supabase_key` | Yes | **service_role** key (server-side only; never expose in UI) |
| `suite_user_id` | Yes | Same string on **all** apps and devices (your account id) |
| `suite_user_email` | Recommended | Used when creating `suite_users` row |

Optional env fallback (local/CI): `SUITE_SUPABASE_URL`, `SUITE_SUPABASE_KEY`, `SUITE_USER_ID`, `SUITE_USER_EMAIL`.

## 2. Sync shared Python modules

From `daniel-ai-command-center`:

```bash
python scripts/sync_suite_cloud_modules.py
```

Commit copied files in each sibling repo when they change.

## 3. Push `dev` (triggers Streamlit redeploy)

Each repo should track branch **`dev`** on Streamlit Cloud. Pushing to `origin/dev` redeploys automatically.

## 4. Verify

1. Command Center → expand **Deployment & link audit (admin)**  
   - `suite_activity section found` = true  
   - `cloud_connected` / account mode = cloud  
2. Use Music on Cloud → save a chart → refresh Command Center → event appears under your `suite_user_id`.  
3. `python scripts/verify_live_activity.py` (with local secrets.toml if testing locally)

## App wiring (already in code)

Each app calls `record_activity()` via its `*_activity.py` module. Music also passes `local_state` and resume keys. No fake placeholder events — only real user actions.
