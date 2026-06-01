# Shared cloud activity backend

## Recommendation: Supabase (PostgreSQL + PostgREST)

| Criterion | Supabase | Firebase | Custom API |
|-----------|----------|----------|------------|
| Fit for append-only event log + upserts | Excellent (SQL) | Good (Firestore) | Good |
| Streamlit integration | REST + `requests` (no extra deps) | Admin SDK + rules | You maintain hosting |
| Expected cost (personal suite) | **$0** on Free tier | **$0** Spark | $5–20/mo VPS or serverless |
| Complexity | **Low** — 3 tables, one secrets block | Medium — security rules | **High** — deploy + auth |
| Migration from SQLite | Straightforward SQL import | Document reshaping | Custom |

**Chosen:** Supabase with **service_role** key in Streamlit secrets (same block on every app).

### Expected cost

- **Free tier:** 500 MB database, 50k monthly active users (API requests) — more than enough for one user across ~6 apps.
- **Paid:** Pro ~$25/mo only if you exceed free limits or need daily backups on Pro features.
- **Realistic for Daniel AI suite:** **$0/month** for years at personal usage.

### Complexity

- **Setup:** ~30 minutes (create project, run SQL migration, paste secrets into 7 Streamlit apps).
- **Code:** `suite_storage_config.py` + `suite_storage_supabase.py` behind existing `suite_storage` / `suite_activity_client` APIs.
- **Ongoing:** Run `python scripts/sync_suite_cloud_modules.py` after changing shared client modules.

---

## Data model

### `suite_activity_events` (append-only)

| Column | Type | Notes |
|--------|------|--------|
| id | bigint | PK |
| app | text | `music`, `baseball`, `nba`, … |
| event | text | `verified_chart_saved`, `practice`, `song_selected`, … |
| page | text | UI context |
| timestamp | timestamptz | ISO from apps |
| metrics | jsonb | `song`, `artist`, `edited_fields`, etc. |

### `suite_app_current_state` (one row per app)

| Column | Type |
|--------|------|
| app | text PK |
| page, summary | text |
| metrics | jsonb |
| updated_at | timestamptz |

### `suite_resume_items` (Continue cards)

| Column | Type |
|--------|------|
| app, item_key | unique |
| title, subtitle, action_url | text |
| valid | boolean |
| updated_at | timestamptz |

---

## Migration plan

1. **Create Supabase project** at [supabase.com](https://supabase.com).
2. **Run** `supabase/migrations/001_suite_activity.sql` in SQL Editor.
3. **Copy** Project URL + **service_role** key (Settings → API).
4. **Add secrets** to every Streamlit Cloud app (identical block):

   ```toml
   [suite_activity]
   supabase_url = "https://xxxx.supabase.co"
   supabase_key = "eyJ...service_role..."
   ```

5. **Deploy** Command Center + Music + Baseball + NBA + Investment + Applied Intelligence + Future Lens (each repo must include synced cloud modules).
6. **Optional:** `python scripts/migrate_sqlite_to_supabase.py` to upload existing local `data/suite_activity.db`.
7. **Verify:** Command Center admin → *Cross-app activity trace* → `cloud_connected: true`, verified saves after Music save on Cloud.

### Rollout phases

| Phase | Behavior |
|-------|----------|
| No secrets | SQLite / JSON fallback (today’s local-only behavior) |
| Secrets set | Cloud primary; SQLite mirror on Command Center machine only |
| All apps on secrets | Identical behavior local, dev, production |

---

## Event types tracked (unchanged hooks)

| App | Example events |
|-----|----------------|
| Music | `verified_chart_saved`, `lyrics_saved`, `practice`, `song_selected`, `backing_track`, `song_added` |
| Baseball | `comparison`, `lineup_review`, `trade_eval`, `page_view` |
| NBA | `page_view` |
| Investment | `portfolio_check` |
| Applied Intelligence | `analysis`, `page_view` |
| Future Lens | `simulation` |

Command Center reads via `activity_store.load_activity_snapshot()` → `suite_storage.load_events()` (cloud when configured).

---

## Setup checklist

- [ ] Supabase project + migration SQL
- [ ] `[suite_activity]` secrets on Command Center Cloud
- [ ] Same secrets on Music / Baseball / NBA / Investment / Applied Intelligence / Future Lens Cloud apps
- [ ] `python scripts/sync_suite_cloud_modules.py` committed copies in each app repo (or CI step)
- [ ] Save verified chart on Music Cloud → appears on Command Center Cloud within one refresh
