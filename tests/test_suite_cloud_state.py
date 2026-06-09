"""Cloud session blob helpers."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from suite_cloud_state import (
    FULL_SESSION_KEY,
    has_resume_query_params,
    list_active_resume_query_params,
    pick_newer_session,
    pick_restore_session,
    reconcile_stale_resume_session_flags,
    session_page_summary,
    should_skip_workspace_restore_for_resume,
)


class TestSuiteCloudState(unittest.TestCase):
    def test_has_resume_query_params_suite_page(self) -> None:
        st = MagicMock()
        st.session_state = {}
        st.query_params = {"suite_page": "Comparison Tool"}
        self.assertTrue(has_resume_query_params(st, "baseball"))

    def test_has_resume_query_params_stale_launch_flag_cleared(self) -> None:
        st = MagicMock()
        st.session_state = {"_suite_resume_launch_baseball": True}
        st.query_params = {}
        self.assertFalse(has_resume_query_params(st, "baseball"))
        self.assertNotIn("_suite_resume_launch_baseball", st.session_state)

    def test_reconcile_stale_resume_clears_music_launch_flag(self) -> None:
        st = MagicMock()
        st.session_state = {
            "_suite_resume_launch_music": True,
            "_navigate_to_studio_page": "backing",
        }
        st.query_params = {}
        cleared = reconcile_stale_resume_session_flags(st, "music")
        self.assertIn("_suite_resume_launch_music", cleared)
        self.assertNotIn("_suite_resume_launch_music", st.session_state)
        self.assertNotIn("_navigate_to_studio_page", st.session_state)

    def test_reconcile_clears_stale_ami_preserve_without_url(self) -> None:
        st = MagicMock()
        st.session_state = {
            "_suite_resume_launch_music": True,
            "_ami_insight_return_preserve": True,
        }
        st.query_params = {}
        cleared = reconcile_stale_resume_session_flags(st, "music")
        self.assertIn("_ami_insight_return_preserve", cleared)
        self.assertNotIn("_ami_insight_return_preserve", st.session_state)

    def test_reconcile_keeps_flags_during_live_url_ami_return(self) -> None:
        st = MagicMock()
        st.session_state = {
            "_suite_resume_launch_music": True,
            "_ami_insight_return_preserve": True,
        }
        st.query_params = {"suite_ami_insight": "abc123"}
        cleared = reconcile_stale_resume_session_flags(st, "music")
        self.assertEqual(cleared, [])
        self.assertIn("_suite_resume_launch_music", st.session_state)

    def test_should_skip_false_for_stale_launch_flag_only(self) -> None:
        st = MagicMock()
        st.session_state = {"_suite_resume_launch_music": True, "studio_page": "practice"}
        st.query_params = {}
        self.assertFalse(should_skip_workspace_restore_for_resume(st, "music"))
        self.assertFalse(has_resume_query_params(st, "music"))
        self.assertNotIn("_suite_resume_launch_music", st.session_state)

    def test_should_skip_false_for_suite_pick_key_only(self) -> None:
        st = MagicMock()
        st.session_state = {}
        st.query_params = {"suite_pick_key": "Pop|Perfect"}
        self.assertEqual(
            list_active_resume_query_params(st, "music"),
            ["suite_pick_key"],
        )
        self.assertFalse(should_skip_workspace_restore_for_resume(st, "music", reconcile_first=False))
        self.assertFalse(has_resume_query_params(st, "music"))

    def test_should_skip_true_for_suite_page_on_music(self) -> None:
        st = MagicMock()
        st.session_state = {}
        st.query_params = {"suite_page": "backing", "suite_pick_key": "Pop|Perfect"}
        self.assertTrue(should_skip_workspace_restore_for_resume(st, "music", reconcile_first=False))

    def test_list_active_resume_query_params_music(self) -> None:
        st = MagicMock()
        st.session_state = {}
        st.query_params = {"suite_page": "backing", "suite_ami_insight": "abc"}
        self.assertEqual(
            list_active_resume_query_params(st, "music"),
            ["suite_page", "suite_ami_insight"],
        )

    def test_has_resume_query_params_false_after_ami_consumed(self) -> None:
        st = MagicMock()
        st.session_state = {
            "_suite_resume_launch_baseball": True,
            "_ami_resume_consumed_baseball": True,
        }
        st.query_params = {"suite_page": "Trend Value", "suite_ami_insight": "ins1"}
        self.assertFalse(has_resume_query_params(st, "baseball"))

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
