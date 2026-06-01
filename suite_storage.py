"""
SQLite persistence for the Daniel AI suite.

Three layers:
  - activity_events  — append-only history log
  - app_current_state — latest snapshot per app (what exists now)
  - resume_items — active "continue" cards (valid=1 only on dashboard)

Designed for local/shared-disk use today; swap backend for Supabase/Firebase later
by replacing this module's public functions without changing activity_store callers.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

DATA_DIR = Path(__file__).resolve().parent / "data"
DB_PATH = DATA_DIR / "suite_activity.db"
LEGACY_JSON = DATA_DIR / "suite_activity.json"

MAX_EVENTS = 2000
ACTIVE_APP_KEYS = frozenset(
    {
        "music",
        "investment",
        "baseball",
        "nba",
        "applied_intelligence",
        "future_lens",
    }
)


@dataclass(frozen=True)
class ResumeItem:
    app: str
    item_key: str
    title: str
    subtitle: str
    action_url: str
    updated_at: str


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS activity_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app TEXT NOT NULL,
            event TEXT NOT NULL,
            page TEXT NOT NULL DEFAULT '',
            timestamp TEXT NOT NULL,
            metrics_json TEXT NOT NULL DEFAULT '{}'
        );
        CREATE INDEX IF NOT EXISTS idx_events_app_ts ON activity_events(app, timestamp DESC);

        CREATE TABLE IF NOT EXISTS app_current_state (
            app TEXT PRIMARY KEY,
            page TEXT NOT NULL DEFAULT '',
            summary TEXT NOT NULL DEFAULT '',
            metrics_json TEXT NOT NULL DEFAULT '{}',
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS resume_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app TEXT NOT NULL,
            item_key TEXT NOT NULL,
            title TEXT NOT NULL,
            subtitle TEXT NOT NULL DEFAULT '',
            action_url TEXT NOT NULL DEFAULT '',
            valid INTEGER NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL,
            UNIQUE(app, item_key)
        );
        CREATE INDEX IF NOT EXISTS idx_resume_valid ON resume_items(valid, updated_at DESC);
        """
    )


def ensure_storage() -> None:
    with _connect() as conn:
        _init_db(conn)
        _migrate_legacy_json(conn)


def _migrate_legacy_json(conn: sqlite3.Connection) -> None:
    if not LEGACY_JSON.is_file():
        return
    count = conn.execute("SELECT COUNT(*) FROM activity_events").fetchone()[0]
    if count:
        return
    try:
        raw = json.loads(LEGACY_JSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    if not isinstance(raw, list):
        return
    for row in raw[-500:]:
        if not isinstance(row, dict):
            continue
        conn.execute(
            """
            INSERT INTO activity_events (app, event, page, timestamp, metrics_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                str(row.get("app", "")),
                str(row.get("event", "")),
                str(row.get("page") or ""),
                str(row.get("timestamp") or _now_iso()),
                json.dumps(row.get("metrics") or {}, ensure_ascii=False),
            ),
        )


def normalize_app_key(app: str) -> str:
    cleaned = str(app or "").strip()
    if cleaned == "math":
        return "applied_intelligence"
    return cleaned


def append_event(
    app: str,
    event: str,
    *,
    page: str = "",
    metrics: dict[str, Any] | None = None,
) -> None:
    app_key = normalize_app_key(app)
    if not app_key:
        return
    payload = metrics or {}
    ts = _now_iso()
    ensure_storage()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO activity_events (app, event, page, timestamp, metrics_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (app_key, event, page, ts, json.dumps(payload, ensure_ascii=False)),
        )
        conn.execute(
            "DELETE FROM activity_events WHERE id NOT IN (SELECT id FROM activity_events ORDER BY id DESC LIMIT ?)",
            (MAX_EVENTS,),
        )


def save_current_state(
    app: str,
    *,
    page: str = "",
    summary: str = "",
    metrics: dict[str, Any] | None = None,
) -> None:
    app_key = normalize_app_key(app)
    if app_key not in ACTIVE_APP_KEYS:
        return
    ts = _now_iso()
    ensure_storage()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO app_current_state (app, page, summary, metrics_json, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(app) DO UPDATE SET
                page=excluded.page,
                summary=excluded.summary,
                metrics_json=excluded.metrics_json,
                updated_at=excluded.updated_at
            """,
            (app_key, page, summary, json.dumps(metrics or {}, ensure_ascii=False), ts),
        )


def upsert_resume_item(
    app: str,
    item_key: str,
    *,
    title: str,
    subtitle: str = "",
    action_url: str = "",
) -> None:
    app_key = normalize_app_key(app)
    key = str(item_key or "").strip()
    title_clean = str(title or "").strip()
    if not app_key or not key or not title_clean:
        return
    if app_key not in ACTIVE_APP_KEYS:
        return
    ts = _now_iso()
    ensure_storage()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO resume_items (app, item_key, title, subtitle, action_url, valid, updated_at)
            VALUES (?, ?, ?, ?, ?, 1, ?)
            ON CONFLICT(app, item_key) DO UPDATE SET
                title=excluded.title,
                subtitle=excluded.subtitle,
                action_url=excluded.action_url,
                valid=1,
                updated_at=excluded.updated_at
            """,
            (app_key, key, title_clean, subtitle, action_url, ts),
        )


def invalidate_resume_item(app: str, item_key: str) -> None:
    app_key = normalize_app_key(app)
    key = str(item_key or "").strip()
    if not app_key or not key:
        return
    ensure_storage()
    with _connect() as conn:
        conn.execute(
            "UPDATE resume_items SET valid=0, updated_at=? WHERE app=? AND item_key=?",
            (_now_iso(), app_key, key),
        )


def invalidate_app_resume_items(app: str) -> None:
    app_key = normalize_app_key(app)
    if not app_key:
        return
    ensure_storage()
    with _connect() as conn:
        conn.execute(
            "UPDATE resume_items SET valid=0, updated_at=? WHERE app=?",
            (_now_iso(), app_key),
        )


def load_events(limit: int = MAX_EVENTS) -> list[dict[str, Any]]:
    ensure_storage()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT app, event, page, timestamp, metrics_json
            FROM activity_events
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    out: list[dict[str, Any]] = []
    for row in reversed(rows):
        try:
            metrics = json.loads(row["metrics_json"] or "{}")
        except json.JSONDecodeError:
            metrics = {}
        out.append(
            {
                "app": row["app"],
                "event": row["event"],
                "page": row["page"],
                "timestamp": row["timestamp"],
                "metrics": metrics,
            }
        )
    return out


def load_current_states() -> dict[str, dict[str, Any]]:
    ensure_storage()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT app, page, summary, metrics_json, updated_at FROM app_current_state"
        ).fetchall()
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        app = str(row["app"])
        if app not in ACTIVE_APP_KEYS:
            continue
        try:
            metrics = json.loads(row["metrics_json"] or "{}")
        except json.JSONDecodeError:
            metrics = {}
        out[app] = {
            "page": row["page"],
            "summary": row["summary"],
            "metrics": metrics,
            "updated_at": row["updated_at"],
        }
    return out


def load_active_resume_items(limit: int = 8) -> list[ResumeItem]:
    ensure_storage()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT app, item_key, title, subtitle, action_url, updated_at
            FROM resume_items
            WHERE valid=1 AND app IN ({})
            ORDER BY updated_at DESC
            LIMIT ?
            """.format(",".join("?" * len(ACTIVE_APP_KEYS))),
            (*sorted(ACTIVE_APP_KEYS), limit),
        ).fetchall()
    return [
        ResumeItem(
            app=str(row["app"]),
            item_key=str(row["item_key"]),
            title=str(row["title"]),
            subtitle=str(row["subtitle"] or ""),
            action_url=str(row["action_url"] or ""),
            updated_at=str(row["updated_at"]),
        )
        for row in rows
    ]


def record_activity(
    app: str,
    event: str,
    *,
    page: str = "",
    metrics: dict[str, Any] | None = None,
    summary: str = "",
    resume_key: str = "",
    resume_title: str = "",
    resume_subtitle: str = "",
    action_url: str = "",
) -> None:
    """Log history, refresh current state, and optionally upsert a resume card."""
    append_event(app, event, page=page, metrics=metrics)
    if summary or page or metrics:
        save_current_state(app, page=page, summary=summary, metrics=metrics)
    if resume_key and resume_title:
        upsert_resume_item(
            app,
            resume_key,
            title=resume_title,
            subtitle=resume_subtitle,
            action_url=action_url,
        )
