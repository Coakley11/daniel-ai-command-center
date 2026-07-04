"""Backward-compatible app filter for load_active_resume_items."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from suite_storage import ResumeItem, load_active_resume_items


class TestLoadActiveResumeItemsAppFilter(unittest.TestCase):
    def test_without_app_kwarg_calls_sqlite_loader(self) -> None:
        baseball = ResumeItem(
            app="baseball",
            item_key="draft:1",
            title="Draft",
            subtitle="",
            action_url="",
            updated_at="2026-07-03T10:00:00",
        )
        with patch("suite_storage._use_cloud", return_value=False):
            with patch(
                "suite_storage._sqlite_load_active_resume_items",
                return_value=[baseball],
            ) as mock_sqlite:
                items = load_active_resume_items(limit=30)
        mock_sqlite.assert_called_once_with(limit=30, app=None)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].app, "baseball")

    def test_with_app_music_forwards_filter(self) -> None:
        music = ResumeItem(
            app="music",
            item_key="practice:song1",
            title="Song",
            subtitle="",
            action_url="",
            updated_at="2026-07-03T10:00:00",
        )
        with patch("suite_storage._use_cloud", return_value=False):
            with patch(
                "suite_storage._sqlite_load_active_resume_items",
                return_value=[music],
            ) as mock_sqlite:
                items = load_active_resume_items(limit=40, app="music")
        mock_sqlite.assert_called_once_with(limit=40, app="music")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].app, "music")

    @patch("suite_storage_supabase._scoped_user_id", return_value="uid-1")
    @patch("suite_storage_supabase._request")
    def test_cloud_path_forwards_app_filter(self, mock_req: MagicMock, _uid: MagicMock) -> None:
        mock_req.return_value = [
            {
                "app": "music",
                "item_key": "practice:song1",
                "title": "Song",
                "subtitle": "",
                "action_url": "",
                "updated_at": "2026-07-03T10:00:00",
            }
        ]
        with patch("suite_storage._use_cloud", return_value=True):
            with patch("suite_workspace.scoped_cloud_app_id", return_value="music"):
                items = load_active_resume_items(limit=40, app="music")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].app, "music")
        params = mock_req.call_args.kwargs.get("params") or mock_req.call_args[1].get("params")
        self.assertEqual(params["app"], "in.(music)")

    def test_sqlite_integration_filters_by_app(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            db_path = data_dir / "suite_activity.db"
            with patch("suite_storage.DATA_DIR", data_dir):
                with patch("suite_storage.DB_PATH", db_path):
                    with patch("suite_storage._use_cloud", return_value=False):
                        with patch(
                            "suite_storage._workspace_storage_keys",
                            return_value=frozenset({"music", "baseball"}),
                        ):
                            with patch(
                                "suite_storage._scoped_storage_app",
                                side_effect=lambda app: str(app),
                            ):
                                from suite_storage import _sqlite_upsert_resume_item

                                _sqlite_upsert_resume_item(
                                    "music",
                                    "practice:song1",
                                    title="Music Song",
                                )
                                _sqlite_upsert_resume_item(
                                    "baseball",
                                    "draft:1",
                                    title="Baseball Draft",
                                )

                                all_items = load_active_resume_items(limit=10)
                                music_items = load_active_resume_items(limit=10, app="music")

            self.assertEqual(len(all_items), 2)
            apps = {item.app for item in all_items}
            self.assertEqual(apps, {"music", "baseball"})
            self.assertEqual(len(music_items), 1)
            self.assertEqual(music_items[0].app, "music")
            self.assertEqual(music_items[0].title, "Music Song")


if __name__ == "__main__":
    unittest.main()
