# Daniel AI Command Center — Master Roadmap

**Last updated:** 2026-06-08 · **Branch:** `dev` · **Entry app:** `ai_command_center.py` · **Build:** `2026-06-03-v30`

This is the master planning document. Related files:

| File | Purpose |
|------|---------|
| [app_tasks.md](./app_tasks.md) | Active work and near-term execution |
| [app_feature_backlog.md](./app_feature_backlog.md) | Queued ideas and enhancements |
| [app_completed_features.md](./app_completed_features.md) | Shipped capabilities by area |

---

# Project Description

**Daniel Cohen AI Command Center** is the suite homepage and cross-app dashboard for the Daniel AI ecosystem. It aggregates real activity from six sibling Streamlit apps (Music, Investment, Baseball, NBA, Applied Intelligence, Future Lens), surfaces actionable coach recommendations, resume/continue deep links, and an app launcher — without duplicating each app's full UX.

**Stack:** Python 3, Streamlit, optional Supabase (PostgREST), local SQLite fallback, shared suite modules copied to sibling repos via `scripts/sync_suite_cloud_modules.py`.

**Deployment:** Daily work on `origin/dev` (Streamlit Cloud dev homepage). Production `main` may lag; see [docs/DEPLOYMENTS.md](../docs/DEPLOYMENTS.md) and [docs/SUITE_DEV_DEPLOY.md](../docs/SUITE_DEV_DEPLOY.md).

---

# Current Priorities

1. **Baseball Phase 2 — Full page audit (P0)** — Canonical state modules for all 14 pages; reference impl before suite port. [plans/2026-06-08-baseball-phase-2-page-audit.md](./plans/2026-06-08-baseball-phase-2-page-audit.md)
2. **Continue vs App Directory (P1)** — Classification audit complete; fix placement before ranking. [plans/suite-usability-audit-2026-06-08.md](./plans/suite-usability-audit-2026-06-08.md) §1
3. **Music persistence (P2)** — Broad coverage; verify cross-device + CPL gaps. §2
4. **NBA persistence (P3)** — Team/page fixed; LGC + Legacy Tracker sub-state gaps. §3
5. **Future Lens persistence (P4)** — Thin vs peers; career activity dead; resume URLs incomplete. §4
6. **Applied Math quality roadmap (P5)** — Context gaps; no implementation yet. §5
7. **Investment** — Transparency Phase 1 shipped (`76969f4`); formulas/macro **paused** until suite stable.

---

# Next Features

- **Baseball reference protocol** — After Phase 2 acceptance, port ownership/sync to Music, NBA, Investment, Applied Intelligence.
- Ship Activity Feed Phase B to `origin/dev` with tests (`test_activity_dashboard.py`, `test_activity_time.py`).
- Per-app activity coverage expansion (Applied Intelligence, Future Lens Phase A tables in admin panel).
- Smarter Continue cards when `full_session` cloud state is richer across apps.
- Optional user-facing filter (hide noise events) without breaking coach logic.
- Homepage dev/prod URL auto-discovery refresh (`scripts/resolve_deploy_urls.py`).

---

# Long-Term Vision

- Unified **suite identity** — one `suite_user_id`, consistent resume URLs, session sync on every app (Investment pattern).
- **AI command layer** — LLM-generated weekly narrative from real events (not placeholder coach strings).
- **Mobile-first homepage** — compact continue row, swipe-friendly app cards.
- **Operational dashboard** — deploy health, last event per app, secret rotation checklist in UI.
- **Teacher/coach mode** — share read-only activity summaries (future).

---

# Completed Features

See [app_completed_features.md](./app_completed_features.md) for the full shipped list. Highlights:

- Single-page homepage with six major sections + admin expander
- Supabase + SQLite dual storage for events and resume state
- Phase A activity verification per app in admin diagnostics
- Account memory migrations and deep-link resume launch helpers
- Cross-app project intelligence and accomplishment weekly lines

---

# Notes

- Command Center does **not** host Baseball/Music/etc. UIs — it links out via `app_registry.py` / `app_urls.py`.
- README still says "placeholder data" — outdated; activity can be live when Supabase is configured.
- Uncommitted local work (as of roadmap creation): activity feed Phase B files — track in [app_tasks.md](./app_tasks.md).

---

## Current application status

**Product:** Streamlit-wide homepage prototype evolved into a **live cross-app hub** when Supabase secrets are configured; falls back to local `data/suite_activity.json` for development.

**Registered suite apps (6):**

| Key | Name | Status | Main file (sibling repo) |
|-----|------|--------|--------------------------|
| `music` | Music Practice Coach | Active | `streamlit_music_practice_app.py` |
| `investment` | Investment Analytics | Active | `streamlit_app.py` |
| `baseball` | Baseball Analytics | Active | `streamlit_app.py` |
| `nba` | Basketball Companion | Active | `streamlit_app.py` |
| `applied_intelligence` | Applied Intelligence | Active | `streamlit_app.py` |
| `future_lens` | AI Future Simulator | Active | `streamlit_app.py` |

---

## Key pages and workflows (homepage sections)

Rendered top-to-bottom in `ai_command_center.py`:

| Section | Purpose | Primary modules |
|---------|---------|-----------------|
| **Hero** | Welcome, build version, live vs waiting tag | `ai_command_center.py`, `activity_store.py` |
| **Continue where you left off** | Resume cards + deep links | `continue_dashboard.py`, `project_intelligence.py`, `suite_storage.py` |
| **Suite focus** | Cross-app weekly patterns | `project_intelligence.py` |
| **Coach Insights** | Actionable next steps (not fact repetition) | `coach_engine.py` |
| **Activity** | Today's Work → Highlights → Recent Activity | `activity_feed.py`, `activity_time.py` |
| **Weekly Summary** | Accomplishment counts this week | `activity_store.py`, `project_intelligence.py` |
| **App Directory** | Themed cards + Open buttons | `app_registry.py`, `app_branding.py` |
| **Deployment & link audit (admin)** | Secrets probe, Supabase diagnostics, Phase A tables | `activity_diagnostics.py`, `suite_account.py` |

**User workflow:** Open Command Center → scan continue/coach → review activity → launch app via Open/Continue → sibling app applies `suite_resume_launch` query params.

---

## High-priority future enhancements

- Finish and deploy Activity Feed Phase B (executive dashboard UX).
- Real-time or near-real-time activity refresh (today: load on page render).
- Expand coach insights to use cloud `full_session` summaries per app.
- Automated deploy URL verification in CI (`scripts/verify_public_apps.py`).
- Document and enforce reset-to-default pattern across all suite apps from Command Center checklist.

---

## Known bugs

| Issue | Area | Notes |
|-------|------|-------|
| README claims "placeholder data" | Docs | Misleading when Supabase is live |
| Cloud deploy lag | Activity feed | Confirm Streamlit dev shows build `2026-06-03-v30` |
| `APP_BRANCH` shows `DEV` not `dev` | `app_urls.py` | Display string only; Streamlit uses `dev` |
| Coach insights can be empty with sparse events | Coach | Expected empty state; not a crash |
| Connection probe timeouts | App registry | `verify_connections()` HTTP GET can false-negative |
| Sibling apps out of sync | Shared modules | Must run `sync_suite_cloud_modules.py` manually |
| Baseball pages without canonical state | Baseball | Only Trend + Comparison have full ownership modules; 12 pages on generic `page_state` |
| Reset button hidden if import fails | Sibling apps | `try/except: pass` in app entrypoints |

---

## UI/UX improvement opportunities

- Sidebar or sticky quick-launch strip for frequent apps.
- Collapse admin expander behind role flag or `?admin=1` query param.
- Stronger visual distinction between Highlights vs Recent Activity.
- Empty-state CTAs that deep-link into a suggested first action per app.
- Dark mode / reduced-motion theme tokens in hero CSS.
- Show relative timestamps consistently (depends on Phase B deploy).

---

## AI enhancement opportunities

- LLM weekly digest from `load_all_events()` → narrative paragraph in Suite focus.
- Personalized continue ranking (ML or heuristic) beyond `project_intelligence` rules.
- Anomaly detection ("you haven't practiced in 5 days") with coach priority boost.
- Natural-language search over activity history.
- Suggested next app based on time-of-day and past patterns.

---

## Technical debt items

| Item | Notes |
|------|-------|
| Duplicate test paths (`tests\` vs `tests/`) | Windows path artifacts |
| `homepage_sections.py` vs inline renderers | Partial abstraction; not all sections use HOMEPAGE_RENDERERS |
| Legacy SQLite + cloud dual write paths | Documented in `docs/SUITE_CLOUD_ACTIVITY.md` |
| Manual module sync to 6 repos | No CI gate on drift |
| Large `activity_feed.py` | Candidate for split (rollup vs highlight vs today) |
| Phase A diagnostics tables duplicated per app | Could be data-driven from config |
