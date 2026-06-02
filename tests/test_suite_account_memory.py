"""Unified account memory — SQLite scoping by suite_user_id."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import suite_storage as storage


class TestSuiteAccountMemory(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self._db = Path(self._tmpdir.name) / "suite_activity.db"
        storage.DATA_DIR = Path(self._tmpdir.name)
        storage.DB_PATH = self._db
        os.environ["SUITE_USER_ID"] = "test-phone"
        from suite_user import reset_account_cache

        reset_account_cache()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()
        os.environ.pop("SUITE_USER_ID", None)
        from suite_user import reset_account_cache

        reset_account_cache()

    def test_events_scoped_by_user(self) -> None:
        storage.append_event("baseball", "player_comparison", metrics={"player": "Judge"})
        events = storage.load_events(limit=10)
        self.assertEqual(len(events), 1)

        os.environ["SUITE_USER_ID"] = "other-laptop"
        from suite_user import reset_account_cache

        reset_account_cache()
        self.assertEqual(storage.load_events(limit=10), [])

    def test_saved_items_and_invalidate(self) -> None:
        storage.upsert_saved_item(
            "music", "song", "autumn-leaves", title="Autumn Leaves", payload={"key": "Am"}
        )
        rows = storage.load_saved_items(app="music")
        self.assertEqual(len(rows), 1)
        storage.invalidate_saved_item("music", "song", "autumn-leaves")
        self.assertEqual(storage.load_saved_items(app="music"), [])

    def test_user_settings_round_trip(self) -> None:
        storage.save_user_settings("music", {"instrument": "guitar"})
        self.assertEqual(storage.load_user_settings("music")["instrument"], "guitar")

    def test_account_summary(self) -> None:
        from suite_account import account_summary

        summary = account_summary()
        self.assertEqual(summary["external_id"], "test-phone")
        self.assertTrue(summary["user_id"].startswith("local:"))


if __name__ == "__main__":
    unittest.main()
