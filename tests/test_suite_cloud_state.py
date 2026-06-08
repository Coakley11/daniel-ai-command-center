"""Cloud session blob helpers."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from suite_cloud_state import (
    FULL_SESSION_KEY,
    has_resume_query_params,
    pick_newer_session,
    pick_restore_session,
    session_page_summary,
)


class TestSuiteCloudState(unittest.TestCase):
    def test_has_resume_query_params_suite_page(self) -> None:
        st = MagicMock()
        st.session_state = {}
        st.query_params = {"suite_page": "Comparison Tool"}
        self.assertTrue(has_resume_query_params(st, "baseball"))

    def test_has_resume_query_params_launch_flag(self) -> None:
        st = MagicMock()
        st.session_state = {"_suite_resume_launch_baseball": True}
        st.query_params = {}
        self.assertTrue(has_resume_query_params(st, "baseball"))

    def test_pick_newer_prefers_cloud(self) -> None:
        cloud = {"active_page": "Trending"}
        disk = {"active_page": "Historical Explorer"}
        picked = pick_newer_session(cloud, "2026-06-01T12:00:00", disk, "2026-05-01T12:00:00")
        self.assertEqual(picked["active_page"], "Trending")

    def test_pick_restore_cloud_first_over_disk_newer(self) -> None:
        cloud = {"active_page": "Comparison Tool", "page_filter_state": {"Comparison Tool": {"sig_player_a_clean": "Juan Soto"}}}
        disk = {"active_page": "Trend Value"}
        picked = pick_restore_session(
            cloud,
            "2026-06-01T10:00:00",
            disk,
            "2026-06-01T12:00:00",
            local_dirty=False,
            cloud_first=True,
        )
        self.assertEqual(picked.source, "cloud")
        self.assertEqual(picked.state.get("active_page"), "Comparison Tool")

    def test_pick_restore_local_dirty_keeps_disk(self) -> None:
        cloud = {"active_page": "Comparison Tool"}
        disk = {"active_page": "Trend Value"}
        picked = pick_restore_session(
            cloud,
            "2026-06-01T12:00:00",
            disk,
            "2026-06-01T10:00:00",
            local_dirty=True,
            cloud_first=True,
        )
        self.assertEqual(picked.source, "disk")
        self.assertEqual(picked.reason, "local unsaved edits")

    def test_session_page_summary_baseball(self) -> None:
        page, summary = session_page_summary("baseball", {"active_page": "Comparison Tool"})
        self.assertEqual(page, "Comparison Tool")
        self.assertEqual(summary, "Comparison Tool")

    def test_full_session_key_constant(self) -> None:
        self.assertEqual(FULL_SESSION_KEY, "full_session")

    @patch("suite_storage_config.cloud_storage_enabled", return_value=True)
    def test_save_cloud_full_session_uses_supabase(self, _enabled: MagicMock) -> None:
        mock_storage = MagicMock()
        mock_storage.normalize_app_key.return_value = "baseball"
        with patch("suite_cloud_state._import_storage", return_value=(mock_storage, "suite_storage_supabase")):
            from suite_cloud_state import save_cloud_full_session

            ok = save_cloud_full_session(
                "baseball",
                {"active_page": "Comparison Tool", "page_filter_state": {}},
                page="Comparison Tool",
                summary="Comparison Tool",
            )
        self.assertTrue(ok)
        mock_storage.save_current_state.assert_called_once()
        metrics = mock_storage.save_current_state.call_args.kwargs.get("metrics") or {}
        self.assertIn("full_session", metrics)


if __name__ == "__main__":
    unittest.main()
