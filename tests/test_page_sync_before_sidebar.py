"""Page-first cloud workspace sync before sidebar."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from suite_user_persistence import sync_cloud_workspace_before_sidebar


class TestPageSyncBeforeSidebar(unittest.TestCase):
    def test_applies_cloud_when_page_mismatch_and_cloud_newer(self) -> None:
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
            return_value=(cloud_state, "2026-06-08T14:00:00+00:00"),
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

    def test_skips_page_mismatch_when_cloud_not_newer(self) -> None:
        st = MagicMock()
        st.session_state = {
            "active_page": "Comparison Tool",
            "main_sidebar_page": "Comparison Tool",
            "_suite_applied_cloud_ts::baseball": "2026-06-08T14:00:00+00:00",
            "_suite_last_persisted_page": "Comparison Tool",
        }
        cloud_state = {"active_page": "Trend Value", "page_filter_state": {}}
        applied: list[dict] = []

        with patch("suite_cloud_state.has_resume_query_params", return_value=False), patch(
            "suite_cloud_state.load_cloud_full_session",
            return_value=(cloud_state, "2026-06-08T12:00:00+00:00"),
        ), patch(
            "suite_user_persistence._load_raw",
            return_value=({"active_page": "Comparison Tool"}, None, "2026-06-08T13:00:00+00:00"),
        ):
            ok = sync_cloud_workspace_before_sidebar(
                st,
                "baseball",
                apply_state=lambda _s, _d: applied.append(_d),
                cloud_first=True,
            )

        self.assertFalse(ok)
        self.assertEqual(applied, [])

    def test_skips_page_mismatch_apply_when_user_navigated(self) -> None:
        st = MagicMock()
        st.session_state = {
            "active_page": "Trend Value",
            "main_sidebar_page": "Comparison Tool",
            "_suite_page_user_nav": True,
            "_suite_applied_cloud_ts::baseball": "2026-06-08T12:00:00+00:00",
        }
        cloud_state = {
            "active_page": "Trend Value",
            "page_filter_state": {},
        }
        disk_state = {"active_page": "Comparison Tool", "page_filter_state": {}}
        applied: list[dict] = []

        def apply_state(_st: MagicMock, state: dict) -> None:
            applied.append(state)

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

        self.assertFalse(ok)
        self.assertEqual(len(applied), 0)


if __name__ == "__main__":
    unittest.main()
