# Daniel AI Suite — Streamlit Deployments

Last verified: 2026-05-31 (build 2026-05-31-v6 on branch `dev`)

## Homepage deployments

| Environment | URL | Git branch | Status |
|---|---|---|---|
| **Production** | https://daniel-ai-command-center-dexxnd7bf8jalxzqbyq55i.streamlit.app | `main` | Deployed |
| **Dev** | *(not created yet)* | `dev` | **Missing — create manually** |

### Create Homepage Dev deployment

Streamlit Cloud does not allow creating apps via git push alone. One-time setup:

1. Open [share.streamlit.io](https://share.streamlit.io) (same account as your other apps).
2. Click **Create app**.
3. Repository: `Coakley11/daniel-ai-command-center`
4. Branch: **`dev`**
5. Main file: **`ai_command_center.py`**
6. Deploy — copy the new `*.streamlit.app` URL into `app_urls.py` as `HOMEPAGE_DEV_URL`.

## App launch URLs (used by App Directory buttons)

| App | Branch | Public URL |
|---|---|---|
| Music Practice Coach | DEV | https://ai-music-practice-coach-6szqxqxqrqxdmryyewk8sq.streamlit.app |
| Investment Analytics | DEV | https://investment-portfolio-analyzer-ty2sbzumvxsqwbqhkvf6rz.streamlit.app |
| Baseball Analytics | MAIN | https://baseball-stat-app-bwx4bawvayxbsbxqbqmfws.streamlit.app |
| Basketball Companion | DEV | https://nba-playoff-companion-ai-gd4sx677quejdfkvappv6o.streamlit.app |
| AI Future Simulator | DEV | https://future-lens-ai-transition-simulator-m6n4kaku28ztzlxfts2xt6.streamlit.app |

## Why links were broken on Production

Production (`main`) previously used `share.streamlit.io/...` URLs. Those open Streamlit’s owner portal and show “You do not have access.”

The fix (public `*.streamlit.app` URLs) lives on branch **`dev`**. Merge `dev` → `main` and redeploy Production to apply.

## Verify deployed build

The homepage footer shows `build 2026-05-31-v6`. If you see an older build or `share.streamlit.io` links, Production has not redeployed yet.

Check Homepage Dev status:

```bash
python scripts/setup_homepage_dev.py
```

Run locally:

```bash
python scripts/verify_homepage_links.py
python scripts/resolve_deploy_urls.py
```
