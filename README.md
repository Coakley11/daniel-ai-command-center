# Daniel Cohen AI Command Center

**A portfolio-ready operating layer for a multi-app AI and analytics suite.**

The Command Center is the unified homepage, navigation hub, and cross-app intelligence layer for Daniel Cohen’s personal AI ecosystem. It connects six sibling Streamlit applications — music practice, investment analytics, fantasy baseball, NBA companion, applied mathematical intelligence (AMI), and future-scenario simulation — into one workspace-aware dashboard where users resume real work, move between apps without losing context, and see what they accomplished across domains.

> **Live deployments:** [Production](https://daniel-ai-command-center-dexxnd7bf8jalxzqbyq55i.streamlit.app) · [Dev branch](https://daniel-ai-command-center-ion4vh2cvo7bgdnkuktrb3.streamlit.app)

---

## At a glance

| | |
|---|---|
| **Role** | Suite homepage, Continue/resume hub, activity dashboard, app directory |
| **Stack** | Python 3, Streamlit, Supabase (optional), local SQLite/JSON fallback |
| **Entry point** | `ai_command_center.py` |
| **Connected apps** | Music Practice Coach, Investment Analytics, Baseball Analytics, Basketball Companion, Applied Intelligence, AI Future Simulator |
| **Resume model** | Activity events + `suite_resume_items` → deep links with `suite_resume`, `suite_page`, `suite_workspace` query params |
| **Auth** | Supabase email/password (feature-flagged, off by default) |
| **Workspace** | Preset profiles today; one owned workspace per authenticated account (in progress) |
| **Tests** | 57 test modules, 349 unit tests (`python -m unittest discover -s tests`) |
| **Active branch** | `dev` (daily work); `main` may lag on production deploy |

---

## Why this project matters

Most portfolio apps stand alone. This project demonstrates how to **orchestrate many analytics products as one coherent system**:

- **Resume real workflows**, not just open apps — unfinished drafts, player comparisons, portfolio reviews, and AMI analyses surface as actionable Continue cards.
- **Preserve context across navigation** — workspace IDs and typed resume keys travel in URLs so sibling apps can restore the right page and state.
- **Aggregate cross-app activity** — events from Music, Baseball, Investment, NBA, AMI, and FutureLens feed a single activity store, coach insights, and weekly summaries.
- **Separate concerns cleanly** — **Continue** (top of the homepage) resumes specific workflows; **App Directory** (bottom) launches apps. They are different UI sections with different data sources.
- **Scale toward real accounts** — auth gates, owned workspaces, and cloud persistence are scaffolded without breaking local/offline development.

For employers and reviewers, the Command Center shows product thinking (not just model demos), full-stack integration across repos, and disciplined platform design for a growing app suite.

---

## Key features

### Central dashboard
Single-page homepage (`ai_command_center.py`) with hero, workspace badge, and ordered sections loaded via `homepage_sections.py`.

### Continue — resumable workflows (top of homepage)
The **Continue** row (`continue_dashboard.py`, `project_intelligence.py`) ranks active projects from:
- Meaningful **activity events** (`activity_store.py`; recorded via `suite_activity_client.py` in this repo and sibling apps)
- Persisted **resume items** (`suite_resume_items` / `load_active_resume_items`)
- Fallback **current app state** when no richer signal exists

Cards are workflow-specific (draft room, comparison, portfolio review, AMI question) — not generic app tiles. Links go through `suite_deep_links.py` → `suite_resume_launch.py` in each app.

### Cross-app intelligence
Homepage section order in `ai_command_center.py`: Continue → Recent AMI Questions → Suite focus → Coach Insights → Activity → Weekly summary → App Directory.

- **Recent AMI Questions** (`ami_recent_dashboard.py`) — analytical handoffs from sibling apps
- **Suite focus** (`project_intelligence.generate_cross_app_insights`) — cross-app patterns for the week
- **Coach Insights** (`coach_engine.py`) — prioritized next-step recommendations
- **Activity** (`activity_feed.py`) — **Today’s Work** grouped summaries (meaningful actions, not every click)
- **Weekly summary** — accomplishment lines from real events

### App Directory (bottom of homepage — not Continue)
The **App Directory** (`_render_app_directory` in `ai_command_center.py`) is the project launcher grid at the **bottom** of the page. It lists registered apps with status, branding, and **Open** links only — no resume keys, no workflow restoration. It does not replace Continue cards.

### Deep links and state restoration
Query-parameter contract documented in `suite_deep_links.py`:
- `suite_resume` — typed resume key (e.g. `compare:Juan Soto:Mike Piazza`, `bb:live_draft:ROOM-ABC123`)
- `suite_page` — target page/tab
- `suite_workspace` — active workspace profile
- App-specific params (e.g. `suite_player_a`, `suite_player_b`, `suite_holdings_fp`, music pick keys)

### Shared shell across the suite
`suite_app_shell.py` provides consistent workspace badge, account panel, and Command Center link in sibling apps (synced via `scripts/sync_suite_cloud_modules.py`).

### Deployment visibility
Admin expander verifies live Streamlit URLs, secrets probe, and per-app connection status (`app_registry.verify_connections`, `suite_deploy_marker.py`).

---

## How the Command Center fits into the full app suite

```
┌─────────────────────────────────────────────────────────────────┐
│              Daniel Cohen AI Command Center                      │
│  Continue · AMI · Suite focus · Coach · Activity · App Directory │
└────────────┬────────────────────────────────────────────────────┘
             │ deep links + workspace param
     ┌───────┼───────┬───────────┬──────────┬────────────┐
     ▼       ▼       ▼           ▼          ▼            ▼
  Music   Baseball  Investment   NBA    Applied Intel  FutureLens
```

| App | Registry key | Main file (sibling repo) | Purpose |
|-----|--------------|--------------------------|---------|
| Music Practice Coach | `music` | `streamlit_music_practice_app.py` | Songs, chords, practice logs, backing tracks |
| Baseball Analytics | `baseball` | `streamlit_app.py` | Fantasy lineups, drafts, comparisons, trends |
| Investment Analytics | `investment` | `streamlit_app.py` | Portfolio health, allocation, scenarios |
| Basketball Companion | `nba` | `streamlit_app.py` | Matchups, playoffs, live game center |
| Applied Intelligence | `applied_intelligence` | `streamlit_app.py` | Quantitative reasoning, AMI reports, analytical questions |
| AI Future Simulator | `future_lens` | `streamlit_app.py` | AI transition scenarios across domains |

App metadata lives in `app_registry.py`; public URLs in `app_urls.py`. Shared cloud modules are copied to sibling repos with `scripts/sync_suite_cloud_modules.py`.

---

## Architecture / technical overview

### Homepage data flow

1. `load_activity_snapshot()` — merge Supabase events, local SQLite (`data/suite_activity.db`), or JSON fallback
2. `continue_cards_for_snapshot()` — `build_project_continue_cards()` ranks workflows by priority and recency
3. `generate_coach_insights()` / `generate_cross_app_insights()` — derived recommendations
4. `verify_connections()` — HTTP GET checks on public `*.streamlit.app` URLs

### Core modules

| Module | Responsibility |
|--------|----------------|
| `ai_command_center.py` | Streamlit UI, section renderers, admin panel |
| `homepage_sections.py` | Safe imports for homepage data loading (testable without running Streamlit) |
| `activity_store.py` | Snapshot ingestion, weekly stats, app directory cards |
| `project_intelligence.py` | Workflow detection, Continue card copy, cross-app insights |
| `suite_deep_links.py` | Resume URL builder and page routing by resume key |
| `suite_resume_launch.py` | Query-param consumer in each app (synced to siblings) |
| `suite_storage.py` / `suite_storage_supabase.py` | Dual cloud/local persistence |
| `suite_user.py` / `suite_user_persistence.py` | Identity, scoped disk paths per workspace |
| `suite_auth.py` | Real Accounts gate (Supabase Auth, feature-flagged) |
| `suite_workspace_registry.py` | Owned workspace registry (local JSON; full enforcement in progress) |
| `applied_math_return_insight.py` | AMI insight hydration and return navigation |

### Storage

- **Cloud (optional):** Supabase tables `suite_activity_events`, `suite_app_current_state`, `suite_resume_items`, `suite_saved_items`, `suite_user_settings` — see `docs/SUITE_ACCOUNT_MEMORY.md` and `supabase/migrations/`
- **Local fallback:** `data/suite_activity.db`, `data/suite_activity.json`, per-workspace state under `data/workspaces/{workspace_id}/`

### Multi-repo relationship

This is a **multi-repo suite**, not a monorepo. The Command Center repo is the source of truth for shared suite modules; sibling app repos consume copies via the sync script. Activity is unified when all apps share the same Supabase project and `suite_user_id`.

---

## Auth and workspace model

### Current behavior (Workspace Profiles v1)
- Preset profiles: Daniel, Ariel, Guest, Test User (`suite_workspace.py`)
- Sidebar switcher on Command Center; workspace badge in hero and sibling app shells
- Activity and resume reads filtered by active `workspace_id`
- Cloud app IDs scoped (e.g. `baseball__ariel`) via `scoped_cloud_app_id()`

### Real accounts (scaffolding shipped, feature-flagged off by default)
- `suite_auth.py` — email/password signup, login, logout, password reset via Supabase Auth
- **`SUITE_AUTH_ENABLED`** env var or `suite_auth_enabled` in Streamlit secrets — **disabled by default** on most deployments
- `apply_suite_auth_gate()` wired into Command Center and sibling entry files
- When auth **is** enabled, `enforce_workspace_ownership()` clamps the active workspace to the signed-in account’s allowed presets (non-admin accounts cannot browse parent/child workspaces)

**Not production-complete yet:** enabling auth on production, cross-device persistence validation, and closing the acceptance gate are **in progress** — see `docs/SUITE_ACCOUNT_WORKSPACE_ACCEPTANCE.md` (gate verdict: not closed).

### Owned workspace model (in progress)
- `suite_workspace_registry.py` — local registry scaffolding for one owned workspace slug per authenticated account (`ensure_owned_workspace_for_session`)
- Registry file: `data/workspaces/_ownership_registry.json`
- **Current state:** preset workspace profiles (Daniel, Ariel, Guest, Test User) remain the day-to-day model when auth is off; owned-workspace auto-provisioning and strict isolation are implemented in code but still undergoing manual acceptance
- **Design intent:** private owned workspaces stay separate from future shared/multiplayer features (e.g. Live Draft Room phases 3–4 on the roadmap)
- Deep links append `suite_workspace` so cross-app navigation preserves the active workspace

---

## State restoration / Continue workflows

Continue cards represent **active or recent resumable workflows**, not generic shortcuts. `project_intelligence._projects_from_events()` maps meaningful events to resume keys and deep links.

### Examples (implemented)

| Workflow | Typical resume key | Target app / page |
|----------|-------------------|-------------------|
| Unfinished Live Draft | `bb:live_draft:{room_id}` | Baseball → Live Draft Room |
| Live draft pick in progress | `bb:live_draft:{room_id}` | Baseball → Live Draft Room |
| Draft Simulator / mock draft prep | `bb:draft`, `baseball:draft_prep` | Baseball → Draft Simulation |
| Saved draft review / Draft Lab analysis | `bb:draft_lab:{room_id}`, `bb:draft_lab:team:{room_id}` | Baseball → Draft Simulation Test Mode |
| Player comparison (e.g. Soto vs. Griffey) | `compare:{player_a}:{player_b}` | Baseball → Comparison Tool |
| Trend chart | `trend:{player}` | Baseball → Trend Value |
| Portfolio health review | `portfolio:health` | Investment → Portfolio Health |
| Music practice session | `song:{pick_key}` | Music → practice / log / backing |
| NBA game / matchup | `nba:game:{team}`, `nba:compare:{a}:{b}` | NBA → Live Game Center / Matchup Intelligence |
| AMI analytical question / report | `ai:question:{id}`, `ai:practice_log_analysis:{id}` | Applied Intelligence (may originate from any app) |
| FutureLens simulation | `suite_sim`, domain/area params | Future Lens |

When sibling apps emit `analytical_question` or `practice_log_analysis` events (for example, a baseball page sending a comparison or research question to AMI), Command Center surfaces those as Continue cards with **Open full analysis** actions — covering cross-app analytical workflows such as deep player or career analyses without duplicating AMI’s UI here.

### Fallback
If no ranked project cards exist, `load_current_states()` provides last-known page summaries per app — clearly secondary to event-driven cards.

---

## Local setup

**Requirements:** Python 3.10+ recommended, pip

```bash
git clone https://github.com/Coakley11/daniel-ai-command-center.git
cd daniel-ai-command-center
git checkout dev

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
streamlit run ai_command_center.py
```

Open the URL Streamlit prints (default `http://localhost:8501`).

Without Supabase secrets, the app uses local storage under `data/` — sufficient for UI development and most unit tests.

### Optional: unified cloud activity

1. Create a Supabase project and run migrations in `supabase/migrations/`
2. Add secrets (see below) to `.streamlit/secrets.toml` or Streamlit Cloud
3. Sync shared modules into sibling repos: `python scripts/sync_suite_cloud_modules.py`
4. Record activity from any suite app via `suite_activity_client.record_activity(...)`

---

## Environment variables / secrets

### Streamlit secrets (recommended for deploy)

Generate the canonical TOML block:

```bash
python scripts/print_suite_secrets_checklist.py
```

Typical block (from `suite_storage_config.py`):

```toml
[suite_activity]
supabase_url = "https://YOUR_PROJECT_REF.supabase.co"
supabase_key = "YOUR_SERVICE_ROLE_KEY"
supabase_anon_key = "YOUR_ANON_PUBLIC_KEY"
suite_user_id = "daniel"
suite_user_email = "you@example.com"
# suite_auth_enabled = true   # enable Real Accounts UI (Sprint C/D)
```

| Key | Required | Notes |
|-----|----------|-------|
| `supabase_url` | For cloud mode | Supabase project URL |
| `supabase_key` | For cloud mode | **service_role** — server-side only |
| `supabase_anon_key` | For auth | Public anon key for Supabase Auth sign-in |
| `suite_user_id` | For cloud mode | Same string on **all** suite apps and devices |
| `suite_user_email` | Recommended | Account identity for `suite_users` row |
| `suite_auth_enabled` | Optional | Enables auth gate when `true` |

### Environment variable fallback (local / CI)

| Variable | Purpose |
|----------|---------|
| `SUITE_SUPABASE_URL` | Supabase project URL |
| `SUITE_SUPABASE_KEY` | Service role key |
| `SUITE_SUPABASE_ANON_KEY` | Anon key for auth |
| `SUITE_USER_ID` | Unified account id |
| `SUITE_USER_EMAIL` | Account email |
| `SUITE_AUTH_ENABLED` | `1` / `true` to enable Real Accounts |

Full checklist for all seven Streamlit deployments: `docs/SUITE_DEV_DEPLOY.md`

---

## Testing

The suite uses **`unittest`** (no pytest config). From the repo root:

```bash
# Full suite (349 tests)
python -m unittest discover -s tests -p "test_*.py" -v

# Focused examples
python -m unittest tests.test_suite_deep_links tests.test_homepage_sections tests.test_suite_resume_launch -v
python -m unittest tests.test_workspace_account_ownership tests.test_suite_auth -v
python -m unittest tests.test_baseball_draft_activity tests.test_continue_classification -v
```

Representative coverage areas:

| Area | Test modules |
|------|----------------|
| Continue / deep links | `test_suite_deep_links.py`, `test_continue_classification.py`, `test_load_active_resume_items.py` |
| Workspace / auth | `test_suite_workspace.py`, `test_suite_auth.py`, `test_workspace_account_ownership.py` |
| Activity / feed | `test_activity_dashboard.py`, `test_activity_feed_noise.py`, `test_baseball_draft_activity.py` |
| AMI integration | `test_applied_math_return_insight.py`, `test_ami_recent_dashboard.py` |
| Homepage | `test_homepage_sections.py`, `test_command_center_normal_mode_ui.py` |

Verification scripts (manual / deploy):

```bash
python scripts/verify_homepage_links.py
python scripts/verify_account_memory.py
python scripts/verify_live_activity.py
python scripts/setup_homepage_dev.py
```

---

## Deployment

### Streamlit Cloud

| Environment | URL | Branch |
|-------------|-----|--------|
| **Production** | https://daniel-ai-command-center-dexxnd7bf8jalxzqbyq55i.streamlit.app | `main` |
| **Dev** | https://daniel-ai-command-center-ion4vh2cvo7bgdnkuktrb3.streamlit.app | `dev` |

- **Main file:** `ai_command_center.py`
- **Repository:** `Coakley11/daniel-ai-command-center`
- Daily development targets **`dev`**; merge to `main` for production updates
- Build label shown in footer: `BUILD_VERSION` in `app_urls.py` (e.g. `2026-06-03-v31`)

See `docs/DEPLOYMENTS.md` for sibling app URLs and dev deployment setup. Production may lag `dev` on public app link fixes — the dev homepage typically has the newest `*.streamlit.app` URLs.

### Deploy workflow

1. Push to `origin/dev` → Streamlit Cloud auto-redeploys
2. Ensure identical `[suite_activity]` secrets on Command Center and all sibling apps
3. Run `python scripts/sync_suite_cloud_modules.py` in sibling repos when shared modules change
4. Command Center → **Deployment & link audit (admin)** → confirm secrets probe and live URLs

---

## Screenshots

> Placeholders — add images to `docs/screenshots/` and link here for portfolio polish.

| Section | File (planned) | Description |
|---------|----------------|-------------|
| Homepage hero + Continue | `docs/screenshots/homepage-continue.png` | Continue cards with workspace badge |
| Coach Insights + Activity | `docs/screenshots/coach-activity.png` | Recommendations and recent feed |
| App Directory | `docs/screenshots/app-directory.png` | Lower launch grid, separate from Continue |
| Workspace + Account | `docs/screenshots/workspace-account.png` | Sidebar switcher and auth panel |
| Deep link resume | `docs/screenshots/resume-baseball.png` | Baseball comparison restored via URL params |

---

## Roadmap

Active planning lives in [`cursor-prompts/`](cursor-prompts/) — start with [`cursor-prompts/app_roadmap.md`](cursor-prompts/app_roadmap.md).

### Shipped (highlights)
- Single-page homepage with Continue, Recent AMI Questions, Suite focus, coach, activity, weekly summary, app directory
- Supabase + SQLite dual storage and unified account memory
- Workspace profiles, deep-link resume launch, cross-app project intelligence
- Real Accounts scaffolding (`suite_auth.py`) — off by default until acceptance gate closes
- AMI return navigation and recent analytical questions on homepage

### In progress
- Account / workspace phase completion — manual acceptance (`docs/SUITE_ACCOUNT_WORKSPACE_ACCEPTANCE.md`; gate not closed)
- Enable `SUITE_AUTH_ENABLED` on production with C1–C5 validation
- Owned workspace registry enforcement and cross-device persistence validation
- Baseball Fantasy League Context v1 (sibling `baseball-stat-app` repo)
- Per-app activity coverage expansion; richer Continue when `full_session` metrics grow

### Planned (not started — see backlog)
- **AMI Real Problem Importer** — paste/CSV decision templates with EV/edge analysis
- **Simple Live Draft Room v1** — shared room state (after Real Accounts stable)
- **Advanced Live Draft Room** — private queues, permissions, realtime polish
- **Notifications, tasks, AMI summaries** — cross-app intelligence layer on homepage
- **Mobile-first homepage** — compact Continue row, swipe-friendly cards
- **Operational dashboard** — deploy health and secret rotation in UI

---

## Portfolio / employer note

This repository is best understood as the **platform layer** of a multi-app portfolio, not a standalone demo.

**What it demonstrates**
- **Product architecture** — separating Continue (resumable work) from App Directory (launchers)
- **Cross-repo integration** — shared modules, unified activity schema, consistent deep-link protocol
- **Full-stack delivery** — Streamlit UX, Supabase persistence, auth scaffolding, deploy verification
- **Test discipline** — 349 unit tests around deep links, workspace isolation, activity ingestion, and AMI handoffs
- **Honest iteration** — feature flags, local fallbacks, and documented acceptance gates before enabling production auth

**Sibling repos** (each deploys independently on Streamlit Cloud, branch `dev`):

- [ai-music-practice-coach](https://github.com/Coakley11/ai-music-practice-coach)
- [baseball-stat-app](https://github.com/Coakley11/baseball-stat-app)
- [investment-portfolio-analyzer](https://github.com/Coakley11/investment-portfolio-analyzer)
- [nba-playoff-companion-ai](https://github.com/Coakley11/nba-playoff-companion-ai)
- [Applied-mathematical-intelligence](https://github.com/Coakley11/Applied-mathematical-intelligence)
- [future-lens-ai-transition-simulator](https://github.com/Coakley11/future-lens-ai-transition-simulator)

**Contact / context:** Built by Daniel Cohen as a personal AI command center and analytics portfolio suite. For a live walkthrough, start at the [dev homepage](https://daniel-ai-command-center-ion4vh2cvo7bgdnkuktrb3.streamlit.app), use an app, then return to see Continue and activity update.

---

## Related documentation

| Doc | Topic |
|-----|-------|
| [`docs/DEPLOYMENTS.md`](docs/DEPLOYMENTS.md) | Streamlit URLs and deploy verification |
| [`docs/SUITE_DEV_DEPLOY.md`](docs/SUITE_DEV_DEPLOY.md) | Secrets checklist for all suite apps |
| [`docs/SUITE_ACCOUNT_MEMORY.md`](docs/SUITE_ACCOUNT_MEMORY.md) | Supabase schema and `record_activity` integration |
| [`docs/SUITE_AUTH_DEV_ENABLE.md`](docs/SUITE_AUTH_DEV_ENABLE.md) | Enabling Real Accounts on dev |
| [`cursor-prompts/app_roadmap.md`](cursor-prompts/app_roadmap.md) | Master product roadmap |
