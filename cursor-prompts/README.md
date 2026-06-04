# Cursor prompts & product docs

Planning documents for **Daniel Cohen AI Command Center** — the suite homepage and cross-app hub. Cursor agents should keep these updated per `.cursor/rules/command-center-roadmap-docs.mdc`.

| File | Role |
|------|------|
| [app_roadmap.md](./app_roadmap.md) | **Master** status, sections, bugs, AI ideas, technical debt |
| [app_tasks.md](./app_tasks.md) | Active priorities, deployment checks, testing |
| [app_feature_backlog.md](./app_feature_backlog.md) | Future ideas not yet scheduled |
| [app_completed_features.md](./app_completed_features.md) | Shipped capabilities by area |

## Product areas documented

- Homepage sections (hero, continue, coach, activity, weekly, app directory)
- Activity feed (Today's Work, Highlights, Recent Activity, rollups)
- Suite storage (SQLite local, Supabase cloud, account memory, resume items)
- Cross-app intelligence (coach insights, project continue cards, suite focus)
- Admin diagnostics (deployment & link audit expander)
- Shared modules synced to sibling suite apps

## Plans folder

Large implementation plans are saved under [`plans/`](./plans/) and linked from `app_tasks.md`.
