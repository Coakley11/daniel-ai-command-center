# Feature Backlog — Daniel AI Command Center

**Last updated:** 2026-06-03

Ideas not yet scheduled. Active work: [app_tasks.md](./app_tasks.md).

---

# Project Description

Queued enhancements for the suite homepage and shared infrastructure — not sibling app feature work (track those in each app's `cursor-prompts/`).

---

# Current Priorities

*None in backlog — see [app_tasks.md](./app_tasks.md) for scheduled work.*

---

# Next Features

### Near-term (next 1–2 sprints)

- Activity feed: user-toggle "show all events" vs executive summary only
- Continue card thumbnails or app-color badges by project type
- Export weekly summary as markdown/email draft
- Pin favorite app to top of App Directory
- Command Center sidebar mini-nav (jump to section anchors)

### Nice-to-have

- Sparkline of events per day in Weekly Summary
- Search box over Recent Activity
- "Last synced" timestamp when reading from Supabase
- Integrate `scripts/probe_public_urls.py` results into admin panel automatically
- Branding sync status indicator (last `sync_suite_branding.py` run)

---

# Long-Term Vision

- **Unified notifications** — browser/email when milestone events fire (chart saved, portfolio check, etc.)
- **Multi-user / family mode** — separate `suite_user_id` profiles on one deployment
- **Public share links** — read-only activity week for coach/teacher
- **Graph view** — nodes = apps, edges = correlated activity sessions
- **Embedded mini-widgets** — iframe or API snippets for single-app status on external sites
- **CLI / SDK homepage** — `cursor-sdk` agent reads suite state for automation

---

# Completed Features

*Shipped items live in [app_completed_features.md](./app_completed_features.md).*

---

# Notes

- Experimental: LLM-generated coach insights (needs API key policy across suite)
- Experimental: Real-time Supabase subscription instead of poll-on-load
- Do not backlog duplicate features already owned by sibling apps (e.g. Music practice UI) — link out instead

---

## Future enhancements (detail)

| Idea | Value | Complexity |
|------|-------|------------|
| LLM weekly narrative | High engagement | Medium (API + prompt) |
| Per-app health badges on directory cards | Quick deploy status | Low |
| Activity export CSV | Personal analytics | Low |
| Config-driven app registry | Add apps without code edit | Medium |
| Rate-limited public homepage | Demo mode | Medium |

---

## Experimental ideas

- Voice summary of today's work (TTS)
- Calendar integration (Google) for "lineup day" coach hints
- GitHub commit activity correlated with dev app usage
- A/B test hero copy for onboarding
