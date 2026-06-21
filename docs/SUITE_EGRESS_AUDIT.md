# Supabase egress audit (Daniel AI Suite)

**Last updated:** 2026-06-19

## Problem

Supabase dashboard showed ~**7.2 GB egress** against a **5 GB free tier** limit while database storage was only ~**40 MB**. That ratio means the apps were **re-downloading the same data repeatedly**, not storing too much.

## Root causes

| Cause | Impact |
|-------|--------|
| `load_cloud_full_session()` called `load_current_states()` | Downloaded **every app’s `metrics.full_session` blob** to restore **one** app (on every startup / sync) |
| `load_current_states()` default select included `metrics` | Command Center Continue + activity snapshot pulled all workspace blobs each run |
| Streamlit reruns | Same cloud GETs repeated many times per browser session with no cache |
| `probe_cloud_restore_diagnostics()` | Also used full multi-app state fetch |
| `load_events(limit=2000)` | Large activity feed payload on CC homepage (expected but measurable) |

**Rough math:** If six apps each store ~500 KB–2 MB in `full_session`, one `load_current_states()` is ~3–12 MB. Ten Streamlit reruns × six apps × several call sites ≈ hundreds of MB per session → multi‑GB over daily multi-app / multi-device use.

## Fixes shipped

### 1. Targeted reads (`suite_storage_supabase.py`)

- `load_current_state_meta_for_app(app)` — `page`, `summary`, `updated_at` only (no metrics)
- `load_current_state_for_app(app)` — **one row** including `metrics` / `full_session`
- `load_current_states_summary()` — all workspace apps **without** metrics
- `load_current_states(include_metrics=False)` — **default is summary-only**; pass `include_metrics=True` only when shallow resume hints inside metrics are required

### 2. Session-level GET cache

Identical Supabase GET requests within a Streamlit browser session are cached in `st.session_state`. Writes invalidate cache for that table.

### 3. `full_session` restore cache (`suite_cloud_state.py`)

- `load_cloud_full_session()` checks lightweight metadata first
- Skips re-download when `updated_at` matches session cache
- Uses single-app fetch instead of all apps
- `invalidate_cloud_full_session_cache()` after cloud saves

### 4. Call-site updates

- **Activity snapshot:** summary states + lazy single-app fetch for Applied Intelligence when `page` column empty
- **Continue dashboard fallback:** uses summary-only `load_current_states()` (resume deep links from project intelligence / resume items first)
- **Probe diagnostics:** meta + single-app row instead of all apps

### 5. Instrumentation (`suite_egress_trace.py`)

Hooked from `suite_storage_supabase._request`:

- Read / write counts per browser session
- Bytes downloaded per request
- Breakdown by **table** and **source** (e.g. `load_cloud_full_session`, `load_events`)
- Dev sidebar panel when `?dev=1` (via `can_show_developer_tools`) — **Supabase egress (dev)** expander

## Tables to watch

| Table | Typical payload | When read |
|-------|-----------------|----------|
| `suite_app_current_state` | **Largest** — `metrics.full_session` blobs | App restore, CC state fallback |
| `suite_activity_events` | Medium — up to 2000 rows with metrics | CC activity feed |
| `suite_resume_items` | Small | Continue cards |
| `suite_saved_items` | Small–medium | Saved charts / items |
| `suite_user_settings` | Small | Account / workspace settings |

## Verification

1. Open any suite app with `?dev=1` on dev deployment.
2. Sidebar → **Supabase egress (dev)** — note reads and download size on first load vs after widget interactions (reruns should show **cached** hits, near-zero new bytes).
3. Open Baseball / Music / AMI — first load should show **one** `suite_app_current_state` read for that app, not six.
4. Command Center homepage — `load_current_states` should **not** download metrics unless explicitly needed.
5. Re-check Supabase dashboard egress after 24–48 h of normal use.

## Remaining optimizations (if egress still high)

- Debounce autosave / cloud sync in `suite_user_persistence.py`
- Trim `full_session` payload size per app
- Paginate or window `load_events()` for CC (e.g. 500 + “load more”)
- Avoid `_merge_state_metrics()` GET-before-POST on every save when incoming already includes full_session
- Compress large blobs or split page snapshots from session state

## Sync

Run from Command Center repo:

```bash
python scripts/sync_suite_cloud_modules.py
```

Includes `suite_egress_trace.py`, updated `suite_storage_supabase.py`, `suite_cloud_state.py`, `suite_app_shell.py`. Reboot each Streamlit Cloud app after deploy.
