"""Smoke tests: catch broken cross-module imports before deploy."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path
from unittest.mock import patch

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
        from activity_feed import ActivityFeedItem, build_activity_dashboard, build_activity_feed
        from activity_models import ActivityFeedItem as FeedItemModel

        self.assertIs(ActivityFeedItem, FeedItemModel)
        self.assertTrue(callable(build_activity_feed))
        self.assertTrue(callable(build_activity_dashboard))

    def test_command_center_phase_b_imports(self) -> None:
        tree = ast.parse(COMMAND_CENTER.read_text(encoding="utf-8"))
        import_from = {
            (node.module, tuple(alias.name for alias in node.names))
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        self.assertIn(("activity_models", ("ActivityFeedItem",)), import_from)
        self.assertIn(("activity_feed", ("build_activity_dashboard",)), import_from)

    @patch("activity_store._sync_disk_user_states_to_storage")
    def test_targeted_activity_store_import(self, _sync) -> None:
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

    @patch("activity_store._sync_disk_user_states_to_storage")
    def test_build_continue_cards_accepts_snapshot(self, _sync) -> None:
        import inspect

        from continue_dashboard import build_continue_cards, continue_cards_for_snapshot
        from activity_store import ActivitySnapshot, load_activity_snapshot

        sig = inspect.signature(build_continue_cards)
        self.assertIn("snapshot", sig.parameters)

        snap = load_activity_snapshot()
        self.assertIsInstance(snap, ActivitySnapshot)
        cards_kw = build_continue_cards(limit=3, snapshot=snap)
        cards_fn = continue_cards_for_snapshot(snap, limit=3)
        self.assertIsInstance(cards_kw, list)
        self.assertIsInstance(cards_fn, list)


if __name__ == "__main__":
    unittest.main()
