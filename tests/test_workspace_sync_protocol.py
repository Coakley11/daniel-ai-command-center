"""Authoritative workspace sync protocol (single blob, post-restore autosave block)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from suite_user_persistence import autosave_if_changed, clear_workspace_autosave_block, sync_workspace_protocol


class TestWorkspaceSyncProtocol(unittest.TestCase):
    def test_first_sync_applies_cloud_and_blocks_autosave(self) -> None:
        st = MagicMock()
        st.session_state = {
            "active_page": "Trend Value",
            "main_sidebar_page": "Trend Value",
        }
        cloud_state = {
            "active_page": "Comparison Tool",
            "page_filter_state": {
                "Comparison Tool": {
                    "compare_players": ["Miguel Cabrera (DET)", "Juan Soto (NYY)"],
                }
            },
            "baseball_workspace_state": {
                "page": "Comparison Tool",
                "comparison_players": ["Miguel Cabrera (DET)", "Juan Soto (NYY)"],
            },
        }
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
            return_value=({"active_page": "Trend Value"}, None, "2026-06-08T12:00:00+00:00"),
        ), patch("suite_user_persistence.save_user_state", return_value=True):
            ok = sync_workspace_protocol(
                st,
                "baseball",
                apply_state=apply_state,
                cloud_first=True,
            )

        self.assertTrue(ok)
        self.assertEqual(len(applied), 1)
        self.assertEqual(applied[0]["active_page"], "Comparison Tool")
        self.assertTrue(st.session_state.get("_suite_autosave_blocked::baseball"))
        self.assertTrue(st.session_state.get("_cloud_workspace_restored_this_run"))
        self.assertTrue(st.session_state.get("_suite_workspace_apply_success"))

    def test_autosave_blocked_after_restore(self) -> None:
        st = MagicMock()
        st.session_state = {"_suite_autosave_blocked::baseball": True}
        build = MagicMock(return_value={"active_page": "Trend Value"})
        with patch("suite_user_persistence.save_user_state") as save_disk:
            autosave_if_changed(st, "baseball", build_state=build)
        save_disk.assert_not_called()
        build.assert_not_called()
        self.assertTrue(st.session_state.get("_suite_autosave_blocked_after_restore"))

    def test_clear_autosave_block_end_of_run(self) -> None:
        st = MagicMock()
        st.session_state = {
            "_suite_autosave_blocked::baseball": True,
            "_cloud_workspace_restored_this_run": True,
        }
        clear_workspace_autosave_block(st, "baseball")
        self.assertNotIn("_suite_autosave_blocked::baseball", st.session_state)
        self.assertNotIn("_cloud_workspace_restored_this_run", st.session_state)

    def test_skips_when_local_dirty(self) -> None:
        st = MagicMock()
        st.session_state = {"_suite_persist_local_dirty::baseball": True}
        applied: list[dict] = []

        def apply_state(_st: MagicMock, state: dict) -> None:
            applied.append(state)

        with patch("suite_cloud_state.has_resume_query_params", return_value=False):
            ok = sync_workspace_protocol(
                st,
                "baseball",
                apply_state=apply_state,
                cloud_first=True,
            )

        self.assertFalse(ok)
        self.assertEqual(applied, [])


if __name__ == "__main__":
    unittest.main()
