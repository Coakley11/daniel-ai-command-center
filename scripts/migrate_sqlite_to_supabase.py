#!/usr/bin/env python3
"""One-time upload of local suite_activity.db into Supabase."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from suite_storage_config import cloud_storage_enabled, get_cloud_config
from suite_storage_supabase import append_event, record_activity, save_current_state, upsert_resume_item


def main() -> None:
    if not cloud_storage_enabled():
        print("Set SUITE_SUPABASE_URL and SUITE_SUPABASE_KEY (or Streamlit secrets) first.")
        sys.exit(1)

    db = ROOT / "data" / "suite_activity.db"
    if not db.is_file():
        print(f"No database at {db}")
        sys.exit(1)

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    events = conn.execute(
        "SELECT app, event, page, timestamp, metrics_json FROM activity_events ORDER BY id ASC"
    ).fetchall()
    states = conn.execute(
        "SELECT app, page, summary, metrics_json, updated_at FROM app_current_state"
    ).fetchall()
    resumes = conn.execute(
        """
        SELECT app, item_key, title, subtitle, action_url
        FROM resume_items WHERE valid=1
        """
    ).fetchall()
    conn.close()

    print(f"Uploading {len(events)} events...")
    for row in events:
        import json

        try:
            metrics = json.loads(row["metrics_json"] or "{}")
        except json.JSONDecodeError:
            metrics = {}
        append_event(row["app"], row["event"], page=row["page"], metrics=metrics)

    for row in states:
        import json

        try:
            metrics = json.loads(row["metrics_json"] or "{}")
        except json.JSONDecodeError:
            metrics = {}
        save_current_state(
            row["app"],
            page=row["page"],
            summary=row["summary"],
            metrics=metrics,
        )

    for row in resumes:
        upsert_resume_item(
            row["app"],
            row["item_key"],
            title=row["title"],
            subtitle=row["subtitle"] or "",
            action_url=row["action_url"] or "",
        )

    cfg = get_cloud_config()
    print(f"Migration complete → {cfg.url if cfg else 'supabase'}")


if __name__ == "__main__":
    main()
