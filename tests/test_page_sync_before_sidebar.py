"""Page-first cloud workspace sync before sidebar."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from suite_user_persistence import sync_cloud_workspace_before_sidebar


class TestPageSyncBeforeSidebar(unittest.TestCase):
    def test_applies_cloud_when_page_mismatch_even_if_applied_ts_current(self) -> None:
        st = MagicMock()
        st.session_state = {
            "active_page": "Trend Value",
            "main_sidebar_page": "Trend Value",
            "_suite_applied_cloud_ts::baseball": "2026-06-08T12:00:00+00:00",
        }
        cloud_state = {
            "active_page": "Historical Explorer",
            "page_filter_state": {},
        }
        disk_state = {"active_page": "Trend Value", "page_filter_state": {}}
        applied: list[dict] = []

        def apply_state(_st: MagicMock, state: dict) -> None:
            applied.append(state)
            _st.session_state["active_page"] = state.get("active_page")
            _st.session_state["main_sidebar_page"] = state.get("active_page")

        with patch("suite_cloud_state.has_resume_query_params", return_value=False), patch(
            "suite_cloud_state.load_cloud_full_session",
            return_value=(cloud_state, "2026-06-08T12:00:00+00:00"),
        ), patch(
            "suite_user_persistence._load_raw",
            return_value=(disk_state, None, "2026-06-08T11:00:00+00:00"),
        ), patch("suite_user_persistence.save_user_state", return_value=True):
            ok = sync_cloud_workspace_before_sidebar(
                st,
                "baseball",
                apply_state=apply_state,
                cloud_first=True,
            )

        self.assertTrue(ok)
        self.assertEqual(len(applied), 1)
        self.assertEqual(applied[0].get("active_page"), "Historical Explorer")
        self.assertTrue(st.session_state.get("_suite_persist_restore_applied"))
        self.assertEqual(st.session_state.get("_suite_cloud_target_page"), "Historical Explorer")


if __name__ == "__main__":
    unittest.main()
