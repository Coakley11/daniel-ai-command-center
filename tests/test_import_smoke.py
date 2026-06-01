"""Smoke tests: catch broken cross-module imports before deploy."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMMAND_CENTER = ROOT / "ai_command_center.py"

# Names imported from activity_store in ai_command_center.py (keep in sync).
ACTIVITY_STORE_IMPORTS = (
    "ActivitySnapshot",
    "get_app_directory_card",
    "get_weekly_summary",
    "load_activity_snapshot",
    "load_all_events",
)


def _activity_store_names_imported_by_command_center() -> tuple[str, ...]:
    tree = ast.parse(COMMAND_CENTER.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "activity_store":
            return tuple(alias.name for alias in node.names)
    return ()


class TestImportSmoke(unittest.TestCase):
    def test_activity_store_exports_match_command_center(self) -> None:
        imported = _activity_store_names_imported_by_command_center()
        self.assertEqual(imported, ACTIVITY_STORE_IMPORTS)

        import activity_store

        for name in ACTIVITY_STORE_IMPORTS:
            self.assertTrue(
                hasattr(activity_store, name),
                f"activity_store missing {name!r} (imported by ai_command_center.py)",
            )
            self.assertIn(name, activity_store.__all__)

    def test_activity_feed_import(self) -> None:
        from activity_feed import build_activity_feed

        self.assertTrue(callable(build_activity_feed))

    def test_targeted_activity_store_import(self) -> None:
        from activity_store import (
            ActivitySnapshot,
            get_app_directory_card,
            get_weekly_summary,
            load_activity_snapshot,
            load_all_events,
        )

        snap = load_activity_snapshot()
        self.assertIsInstance(snap, ActivitySnapshot)
        self.assertIsInstance(get_weekly_summary(snap).has_any, bool)
        self.assertIsInstance(get_app_directory_card(snap, "music").highlights, tuple)
        self.assertIsInstance(load_all_events(limit=5), list)

    def test_command_center_compiles(self) -> None:
        source = COMMAND_CENTER.read_text(encoding="utf-8")
        ast.parse(source, filename=str(COMMAND_CENTER))


if __name__ == "__main__":
    unittest.main()
