#!/usr/bin/env python3
"""Run before push: verify Command Center import surface matches activity_store."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.test_import_smoke import ACTIVITY_STORE_IMPORTS  # noqa: E402


def main() -> int:
    try:
        import activity_store
        from activity_feed import build_activity_feed
    except ImportError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    missing = [name for name in ACTIVITY_STORE_IMPORTS if not hasattr(activity_store, name)]
    if missing:
        print(f"FAIL: activity_store missing: {', '.join(missing)}", file=sys.stderr)
        return 1

    if not callable(build_activity_feed):
        print("FAIL: build_activity_feed is not callable", file=sys.stderr)
        return 1

    from activity_store import (
        ActivitySnapshot,
        get_app_directory_card,
        get_weekly_summary,
        load_activity_snapshot,
        load_all_events,
    )

    snap = load_activity_snapshot()
    _ = get_weekly_summary(snap)
    _ = get_app_directory_card(snap, "music")
    _ = load_all_events(limit=3)

    import py_compile

    py_compile.compile(str(ROOT / "ai_command_center.py"), doraise=True)

    print("OK: imports and py_compile passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
