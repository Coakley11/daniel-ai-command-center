"""
Suite activity persistence — Supabase (shared cloud) with SQLite fallback (local).

Public API is unchanged for activity_store and suite_activity_client callers.
When ``SUITE_SUPABASE_URL`` + ``SUITE_SUPABASE_KEY`` (or Streamlit ``[suite_activity]``)
are set, all reads/writes use the same Supabase project across local, dev, and production.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from suite_storage_config import cloud_storage_enabled, get_cloud_config

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


def normalize_app_key(app: str) -> str:
    cleaned = str(app or "").strip()
    if cleaned == "math":
        return "applied_intelligence"
    return cleaned


def _use_cloud() -> bool:
    return cloud_storage_enabled()


# --- SQLite (fallback / local mirror) -------------------------------------------------


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


def _sqlite_user_id() -> str:
    try:
        from suite_user import get_account_user_id

        return get_account_user_id()
    except Exception:
        return "local:default"


def _init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS activity_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'local:default',
            app TEXT NOT NULL,
            event TEXT NOT NULL,
            page TEXT NOT NULL DEFAULT '',
            timestamp TEXT NOT NULL,
            metrics_json TEXT NOT NULL DEFAULT '{}'
        );
        CREATE INDEX IF NOT EXISTS idx_events_user_app_ts ON activity_events(user_id, app, timestamp DESC);

        CREATE TABLE IF NOT EXISTS app_current_state (
            user_id TEXT NOT NULL DEFAULT 'local:default',
            app TEXT NOT NULL,
            page TEXT NOT NULL DEFAULT '',
            summary TEXT NOT NULL DEFAULT '',
            metrics_json TEXT NOT NULL DEFAULT '{}',
            updated_at TEXT NOT NULL,
            PRIMARY KEY (user_id, app)
        );

        CREATE TABLE IF NOT EXISTS resume_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'local:default',
            app TEXT NOT NULL,
            item_key TEXT NOT NULL,
            title TEXT NOT NULL,
            subtitle TEXT NOT NULL DEFAULT '',
            action_url TEXT NOT NULL DEFAULT '',
            valid INTEGER NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL,
            UNIQUE(user_id, app, item_key)
        );
        CREATE INDEX IF NOT EXISTS idx_resume_valid ON resume_items(user_id, valid, updated_at DESC);

        CREATE TABLE IF NOT EXISTS saved_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            app TEXT NOT NULL,
            item_type TEXT NOT NULL DEFAULT 'item',
            item_key TEXT NOT NULL,
            title TEXT NOT NULL,
            payload_json TEXT NOT NULL DEFAULT '{}',
            valid INTEGER NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL,
            UNIQUE(user_id, app, item_type, item_key)
        );
        CREATE INDEX IF NOT EXISTS idx_saved_user_app ON saved_items(user_id, app, valid, updated_at DESC);

        CREATE TABLE IF NOT EXISTS user_settings (
            user_id TEXT NOT NULL,
            app TEXT NOT NULL DEFAULT '_global',
            settings_json TEXT NOT NULL DEFAULT '{}',
            updated_at TEXT NOT NULL,
            PRIMARY KEY (user_id, app)
        );
        """
    )
    _migrate_account_columns(conn)


def _migrate_account_columns(conn: sqlite3.Connection) -> None:
    """Add account columns to DBs created before unified memory."""
    uid = _sqlite_user_id()

    def _has_column(table: str, col: str) -> bool:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return any(str(r[1]) == col for r in rows)

    if _has_column("activity_events", "id") and not _has_column("activity_events", "user_id"):
        conn.execute("ALTER TABLE activity_events ADD COLUMN user_id TEXT NOT NULL DEFAULT 'local:default'")
        conn.execute("UPDATE activity_events SET user_id = ?", (uid,))
    if _has_column("app_current_state", "app") and not _has_column("app_current_state", "user_id"):
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_current_state_v2 (
                user_id TEXT NOT NULL,
                app TEXT NOT NULL,
                page TEXT NOT NULL DEFAULT '',
                summary TEXT NOT NULL DEFAULT '',
                metrics_json TEXT NOT NULL DEFAULT '{}',
                updated_at TEXT NOT NULL,
                PRIMARY KEY (user_id, app)
            )
            """
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO app_current_state_v2 (user_id, app, page, summary, metrics_json, updated_at)
            SELECT ?, app, page, summary, metrics_json, updated_at FROM app_current_state
            """,
            (uid,),
        )
        conn.execute("DROP TABLE app_current_state")
        conn.execute("ALTER TABLE app_current_state_v2 RENAME TO app_current_state")
    if _has_column("resume_items", "app") and not _has_column("resume_items", "user_id"):
        conn.execute("ALTER TABLE resume_items ADD COLUMN user_id TEXT NOT NULL DEFAULT 'local:default'")
        conn.execute("UPDATE resume_items SET user_id = ?", (uid,))


def ensure_storage() -> None:
    if _use_cloud():
        return
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
    uid = _sqlite_user_id()
    for row in raw[-500:]:
        if not isinstance(row, dict):
            continue
        conn.execute(
            """
            INSERT INTO activity_events (user_id, app, event, page, timestamp, metrics_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                uid,
                str(row.get("app", "")),
                str(row.get("event", "")),
                str(row.get("page") or ""),
                str(row.get("timestamp") or _now_iso()),
                json.dumps(row.get("metrics") or {}, ensure_ascii=False),
            ),
        )


def _sqlite_append_event(
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
    uid = _sqlite_user_id()
    ensure_storage()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO activity_events (user_id, app, event, page, timestamp, metrics_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (uid, app_key, event, page, ts, json.dumps(payload, ensure_ascii=False)),
        )
        conn.execute(
            "DELETE FROM activity_events WHERE id NOT IN (SELECT id FROM activity_events ORDER BY id DESC LIMIT ?)",
            (MAX_EVENTS,),
        )


def _sqlite_save_current_state(
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


def _sqlite_upsert_resume_item(
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
    uid = _sqlite_user_id()
    ensure_storage()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO resume_items (user_id, app, item_key, title, subtitle, action_url, valid, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
            ON CONFLICT(user_id, app, item_key) DO UPDATE SET
                title=excluded.title,
                subtitle=excluded.subtitle,
                action_url=excluded.action_url,
                valid=1,
                updated_at=excluded.updated_at
            """,
            (uid, app_key, key, title_clean, subtitle, action_url, ts),
        )


def _sqlite_invalidate_resume_item(app: str, item_key: str) -> None:
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


def _sqlite_invalidate_app_resume_items(app: str) -> None:
    app_key = normalize_app_key(app)
    if not app_key:
        return
    ensure_storage()
    with _connect() as conn:
        conn.execute(
            "UPDATE resume_items SET valid=0, updated_at=? WHERE app=?",
            (_now_iso(), app_key),
        )


def _sqlite_load_events(limit: int = MAX_EVENTS) -> list[dict[str, Any]]:
    uid = _sqlite_user_id()
    ensure_storage()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT app, event, page, timestamp, metrics_json
            FROM activity_events
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (uid, limit),
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


def _sqlite_load_current_states() -> dict[str, dict[str, Any]]:
    uid = _sqlite_user_id()
    ensure_storage()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT app, page, summary, metrics_json, updated_at FROM app_current_state WHERE user_id = ?",
            (uid,),
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


def _sqlite_load_active_resume_items(limit: int = 8) -> list[ResumeItem]:
    uid = _sqlite_user_id()
    ensure_storage()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT app, item_key, title, subtitle, action_url, updated_at
            FROM resume_items
            WHERE user_id = ? AND valid=1 AND app IN ({})
            ORDER BY updated_at DESC
            LIMIT ?
            """.format(",".join("?" * len(ACTIVE_APP_KEYS))),
            (uid, *sorted(ACTIVE_APP_KEYS), limit),
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


def _mirror_sqlite_write(
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
    """Optional local cache when cloud is primary (offline dev without credentials)."""
    try:
        _sqlite_append_event(app, event, page=page, metrics=metrics)
        if summary or page or metrics:
            _sqlite_save_current_state(app, page=page, summary=summary, metrics=metrics)
        if resume_key and resume_title:
            _sqlite_upsert_resume_item(
                app,
                resume_key,
                title=resume_title,
                subtitle=resume_subtitle,
                action_url=action_url,
            )
    except OSError:
        pass


# --- Public API -----------------------------------------------------------------------


def append_event(
    app: str,
    event: str,
    *,
    page: str = "",
    metrics: dict[str, Any] | None = None,
) -> None:
    if _use_cloud():
        import suite_storage_supabase as cloud

        cloud.append_event(app, event, page=page, metrics=metrics)
        _mirror_sqlite_write(app, event, page=page, metrics=metrics)
        return
    _sqlite_append_event(app, event, page=page, metrics=metrics)


def save_current_state(
    app: str,
    *,
    page: str = "",
    summary: str = "",
    metrics: dict[str, Any] | None = None,
) -> None:
    if _use_cloud():
        import suite_storage_supabase as cloud

        cloud.save_current_state(app, page=page, summary=summary, metrics=metrics)
        try:
            _sqlite_save_current_state(app, page=page, summary=summary, metrics=metrics)
        except OSError:
            pass
        return
    _sqlite_save_current_state(app, page=page, summary=summary, metrics=metrics)


def upsert_resume_item(
    app: str,
    item_key: str,
    *,
    title: str,
    subtitle: str = "",
    action_url: str = "",
) -> None:
    if _use_cloud():
        import suite_storage_supabase as cloud

        cloud.upsert_resume_item(
            app, item_key, title=title, subtitle=subtitle, action_url=action_url
        )
        try:
            _sqlite_upsert_resume_item(
                app, item_key, title=title, subtitle=subtitle, action_url=action_url
            )
        except OSError:
            pass
        return
    _sqlite_upsert_resume_item(
        app, item_key, title=title, subtitle=subtitle, action_url=action_url
    )


def invalidate_resume_item(app: str, item_key: str) -> None:
    if _use_cloud():
        import suite_storage_supabase as cloud

        cloud.invalidate_resume_item(app, item_key)
        try:
            _sqlite_invalidate_resume_item(app, item_key)
        except OSError:
            pass
        return
    _sqlite_invalidate_resume_item(app, item_key)


def invalidate_app_resume_items(app: str) -> None:
    if _use_cloud():
        import suite_storage_supabase as cloud

        cloud.invalidate_app_resume_items(app)
        try:
            _sqlite_invalidate_app_resume_items(app)
        except OSError:
            pass
        return
    _sqlite_invalidate_app_resume_items(app)


def load_events(limit: int = MAX_EVENTS) -> list[dict[str, Any]]:
    if _use_cloud():
        import suite_storage_supabase as cloud

        try:
            return cloud.load_events(limit=limit)
        except Exception:
            return _sqlite_load_events(limit=limit)
    return _sqlite_load_events(limit=limit)


def load_current_states() -> dict[str, dict[str, Any]]:
    if _use_cloud():
        import suite_storage_supabase as cloud

        try:
            return cloud.load_current_states()
        except Exception:
            return _sqlite_load_current_states()
    return _sqlite_load_current_states()


def load_active_resume_items(limit: int = 8) -> list[ResumeItem]:
    if _use_cloud():
        import suite_storage_supabase as cloud

        try:
            rows = cloud.load_active_resume_items(limit=limit)
            return [
                ResumeItem(
                    app=str(r["app"]),
                    item_key=str(r["item_key"]),
                    title=str(r["title"]),
                    subtitle=str(r["subtitle"]),
                    action_url=str(r["action_url"]),
                    updated_at=str(r["updated_at"]),
                )
                for r in rows
            ]
        except Exception:
            return _sqlite_load_active_resume_items(limit=limit)
    return _sqlite_load_active_resume_items(limit=limit)


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
    if _use_cloud():
        import suite_storage_supabase as cloud

        cloud.record_activity(
            app,
            event,
            page=page,
            metrics=metrics,
            summary=summary,
            resume_key=resume_key,
            resume_title=resume_title,
            resume_subtitle=resume_subtitle,
            action_url=action_url,
        )
        _mirror_sqlite_write(
            app,
            event,
            page=page,
            metrics=metrics,
            summary=summary,
            resume_key=resume_key,
            resume_title=resume_title,
            resume_subtitle=resume_subtitle,
            action_url=action_url,
        )
        return
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


def _sqlite_upsert_saved_item(
    app: str,
    item_type: str,
    item_key: str,
    *,
    title: str,
    payload: dict[str, Any] | None = None,
) -> None:
    app_key = normalize_app_key(app)
    key = str(item_key or "").strip()
    title_clean = str(title or "").strip()
    itype = str(item_type or "item").strip() or "item"
    if not app_key or not key or not title_clean:
        return
    uid = _sqlite_user_id()
    ts = _now_iso()
    ensure_storage()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO saved_items (user_id, app, item_type, item_key, title, payload_json, valid, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
            ON CONFLICT(user_id, app, item_type, item_key) DO UPDATE SET
                title=excluded.title,
                payload_json=excluded.payload_json,
                valid=1,
                updated_at=excluded.updated_at
            """,
            (uid, app_key, itype, key, title_clean, json.dumps(payload or {}, ensure_ascii=False), ts),
        )


def _sqlite_invalidate_saved_item(app: str, item_type: str, item_key: str) -> None:
    app_key = normalize_app_key(app)
    key = str(item_key or "").strip()
    itype = str(item_type or "item").strip() or "item"
    if not app_key or not key:
        return
    uid = _sqlite_user_id()
    ensure_storage()
    with _connect() as conn:
        conn.execute(
            """
            UPDATE saved_items SET valid=0, updated_at=?
            WHERE user_id=? AND app=? AND item_type=? AND item_key=?
            """,
            (_now_iso(), uid, app_key, itype, key),
        )


def _sqlite_load_saved_items(
    *,
    app: str | None = None,
    item_type: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    uid = _sqlite_user_id()
    ensure_storage()
    query = """
        SELECT app, item_type, item_key, title, payload_json, updated_at
        FROM saved_items
        WHERE user_id = ? AND valid = 1
    """
    params: list[Any] = [uid]
    if app:
        query += " AND app = ?"
        params.append(normalize_app_key(app))
    if item_type:
        query += " AND item_type = ?"
        params.append(item_type)
    query += " ORDER BY updated_at DESC LIMIT ?"
    params.append(limit)
    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        try:
            payload = json.loads(row["payload_json"] or "{}")
        except json.JSONDecodeError:
            payload = {}
        out.append(
            {
                "app": row["app"],
                "item_type": row["item_type"],
                "item_key": row["item_key"],
                "title": row["title"],
                "payload": payload,
                "updated_at": row["updated_at"],
            }
        )
    return out


def _sqlite_save_user_settings(app: str, settings: dict[str, Any]) -> None:
    app_key = str(app or "_global").strip() or "_global"
    uid = _sqlite_user_id()
    ts = _now_iso()
    ensure_storage()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO user_settings (user_id, app, settings_json, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, app) DO UPDATE SET
                settings_json=excluded.settings_json,
                updated_at=excluded.updated_at
            """,
            (uid, app_key, json.dumps(settings or {}, ensure_ascii=False), ts),
        )


def _sqlite_load_user_settings(app: str = "_global") -> dict[str, Any]:
    app_key = str(app or "_global").strip() or "_global"
    uid = _sqlite_user_id()
    ensure_storage()
    with _connect() as conn:
        row = conn.execute(
            "SELECT settings_json FROM user_settings WHERE user_id = ? AND app = ?",
            (uid, app_key),
        ).fetchone()
    if not row:
        return {}
    try:
        raw = json.loads(row["settings_json"] or "{}")
        return raw if isinstance(raw, dict) else {}
    except json.JSONDecodeError:
        return {}


def upsert_saved_item(
    app: str,
    item_type: str,
    item_key: str,
    *,
    title: str,
    payload: dict[str, Any] | None = None,
) -> None:
    if _use_cloud():
        import suite_storage_supabase as cloud

        cloud.upsert_saved_item(app, item_type, item_key, title=title, payload=payload)
        try:
            _sqlite_upsert_saved_item(app, item_type, item_key, title=title, payload=payload)
        except OSError:
            pass
        return
    _sqlite_upsert_saved_item(app, item_type, item_key, title=title, payload=payload)


def invalidate_saved_item(app: str, item_type: str, item_key: str) -> None:
    if _use_cloud():
        import suite_storage_supabase as cloud

        cloud.invalidate_saved_item(app, item_type, item_key)
        try:
            _sqlite_invalidate_saved_item(app, item_type, item_key)
        except OSError:
            pass
        return
    _sqlite_invalidate_saved_item(app, item_type, item_key)


def load_saved_items(
    *,
    app: str | None = None,
    item_type: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    if _use_cloud():
        import suite_storage_supabase as cloud

        try:
            return cloud.load_saved_items(app=app, item_type=item_type, limit=limit)
        except Exception:
            return _sqlite_load_saved_items(app=app, item_type=item_type, limit=limit)
    return _sqlite_load_saved_items(app=app, item_type=item_type, limit=limit)


def save_user_settings(app: str, settings: dict[str, Any]) -> None:
    if _use_cloud():
        import suite_storage_supabase as cloud

        cloud.save_user_settings(app, settings)
        try:
            _sqlite_save_user_settings(app, settings)
        except OSError:
            pass
        return
    _sqlite_save_user_settings(app, settings)


def load_user_settings(app: str = "_global") -> dict[str, Any]:
    if _use_cloud():
        import suite_storage_supabase as cloud

        try:
            return cloud.load_user_settings(app)
        except Exception:
            return _sqlite_load_user_settings(app)
    return _sqlite_load_user_settings(app)


def cloud_ping() -> bool:
    if not _use_cloud():
        return False
    import suite_storage_supabase as cloud

    return cloud.ping()
