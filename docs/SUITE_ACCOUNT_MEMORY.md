# Unified account memory (cross-device)

One personal account ties together Music, Baseball, Investment, NBA, Applied Intelligence, Future Lens, and Command Center. Activity on your phone appears on your laptop when both use the **same Supabase project** and **`suite_user_id`**.

## Schema (Supabase)

| Logical name | Physical table | Purpose |
|--------------|----------------|---------|
| `users` | `suite_users` | Account (`external_id` = your `suite_user_id`) |
| `app_activity` | `suite_activity_events` | Meaningful events (scoped by `user_id`) |
| `app_state` | `suite_app_current_state` | Last page, summary, metrics per app |
| `saved_items` | `suite_saved_items` | Songs, players, portfolios, simulations |
| `user_settings` | `suite_user_settings` | Per-app or `_global` JSON settings |

Also: `suite_resume_items` (Continue cards), invalidated when items are deleted.

## Setup

1. Run `supabase/migrations/001_suite_activity.sql` (if new project).
2. Run `supabase/migrations/002_suite_account_memory_paste.sql` in Supabase SQL Editor (copy from the file in GitHub; do not copy from chat markdown).
3. Add to **every** Streamlit app (identical block):

```toml
[suite_activity]
supabase_url = "https://xxxx.supabase.co"
supabase_key = "YOUR_SERVICE_ROLE_KEY"
suite_user_id = "daniel"
suite_user_email = "you@example.com"
```

4. Sync shared modules into sibling repos:

```bash
python scripts/sync_suite_cloud_modules.py
```

5. Redeploy all apps.

## App integration

### Activity + state (existing)

```python
from suite_activity_client import record_activity

record_activity(
    "baseball",
    "player_comparison",
    metrics={"player_a": "Judge", "player_b": "Soto"},
    summary="Compared Judge vs Soto",
    resume_key="compare:Judge:Soto",
    resume_title="Continue player comparison",
    local_state={"page": "Comparison", "team": "NYY"},
)
```

### Saved items

```python
from suite_account import remember_saved_item, forget_saved_item

remember_saved_item("music", "song", "autumn-leaves", title="Autumn Leaves", payload={"key": "Am"})
forget_saved_item("music", "song", "old-song-id")  # hides from active dashboard
```

Or via metrics on `record_activity`:

```python
metrics={
    "saved_item_type": "player",
    "saved_item_key": "aaron-judge",
    "saved_item_title": "Aaron Judge",
}
```

### Settings

```python
from suite_account import save_settings, load_settings

save_settings("music", {"instrument": "guitar", "capo": 2})
prefs = load_settings("_global")
```

## Command Center

- **Continue**, **Recent Activity**, and **Coach** read account-scoped data automatically.
- Admin panel shows account id and sync mode when diagnostics are open.
- Deleted items: call `forget_saved_item` or `invalidate_resume_item` from the app when user deletes.

## Local fallback

Without Supabase secrets, data stays in `data/suite_activity.db` keyed by `local:{suite_user_id}` (same machine only).
