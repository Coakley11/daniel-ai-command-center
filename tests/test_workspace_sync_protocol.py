"""Authoritative workspace sync protocol (single blob, post-restore autosave block)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from suite_user_persistence import (
    autosave_if_changed,
    clear_workspace_autosave_block,
    force_autosave,
    sync_workspace_protocol,
)


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

    def test_cloud_newer_than_disk_applies_even_if_already_synced(self) -> None:
        st = MagicMock()
        st.session_state = {
            "active_page": "Trend Value",
            "main_sidebar_page": "Trend Value",
            "compare_players": [],
            "_suite_workspace_synced::baseball": True,
            "_suite_applied_cloud_ts::baseball": "2026-06-08T12:00:00+00:00",
        }
        cloud_state = {
            "active_page": "Comparison Tool",
            "comparison_state": {"players": ["Francisco Lindor", "Aaron Judge"]},
            "page_filter_state": {
                "Comparison Tool": {
                    "compare_players": ["Francisco Lindor", "Aaron Judge"],
                }
            },
        }
        applied: list[dict] = []

        def apply_state(_st: MagicMock, state: dict) -> None:
            applied.append(state)
            _st.session_state["active_page"] = state.get("active_page")

        with patch("suite_cloud_state.has_resume_query_params", return_value=False), patch(
            "suite_cloud_state.probe_cloud_restore_diagnostics",
            return_value={"cloud_has_full_session": True, "suite_user_id": "user-1"},
        ), patch(
            "suite_cloud_state.load_cloud_full_session",
            return_value=(cloud_state, "2026-06-08T15:00:00+00:00"),
        ), patch(
            "suite_user_persistence._load_raw",
            return_value=({"active_page": "Trend Value"}, None, "2026-06-08T12:00:00+00:00"),
        ), patch("suite_user_persistence.save_user_state", return_value=True):
            ok = sync_workspace_protocol(
                st, "baseball", apply_state=apply_state, cloud_first=True,
            )

        self.assertTrue(ok)
        self.assertEqual(applied[0]["active_page"], "Comparison Tool")
        self.assertEqual(st.session_state.get("_suite_restore_decision"), "applied")
        self.assertIn("cloud_newer_than_disk", st.session_state.get("_suite_restore_apply_reason", ""))

    def test_skips_when_local_dirty(self) -> None:
        st = MagicMock()
        st.session_state = {"_suite_persist_local_dirty::baseball": True}
        applied: list[dict] = []

        def apply_state(_st: MagicMock, state: dict) -> None:
            applied.append(state)

        with patch("suite_cloud_state.has_resume_query_params", return_value=False), patch(
            "suite_cloud_state.load_cloud_full_session",
            return_value=({"active_page": "Trend Value"}, "2026-06-08T12:00:00+00:00"),
        ), patch(
            "suite_user_persistence._load_raw",
            return_value=({"active_page": "Trend Value"}, None, "2026-06-08T13:00:00+00:00"),
        ):
            ok = sync_workspace_protocol(
                st,
                "baseball",
                apply_state=apply_state,
                cloud_first=True,
            )

        self.assertFalse(ok)
        self.assertEqual(applied, [])

    def test_local_dirty_allows_sync_when_cloud_newer_than_disk(self) -> None:
        st = MagicMock()
        st.session_state = {
            "_suite_persist_local_dirty::baseball": True,
            "active_page": "Trend Value",
        }
        cloud_state = {
            "active_page": "Comparison Tool",
            "comparison_state": {"players": ["Francisco Lindor", "Aaron Judge"]},
        }
        applied: list[dict] = []

        def apply_state(_st: MagicMock, state: dict) -> None:
            applied.append(state)

        with patch("suite_cloud_state.has_resume_query_params", return_value=False), patch(
            "suite_cloud_state.probe_cloud_restore_diagnostics",
            return_value={"cloud_has_full_session": True},
        ), patch(
            "suite_cloud_state.load_cloud_full_session",
            return_value=(cloud_state, "2026-06-08T15:00:00+00:00"),
        ), patch(
            "suite_user_persistence._load_raw",
            return_value=({"active_page": "Trend Value"}, None, "2026-06-08T12:00:00+00:00"),
        ), patch("suite_user_persistence.save_user_state", return_value=True):
            ok = sync_workspace_protocol(st, "baseball", apply_state=apply_state)

        self.assertTrue(ok)
        self.assertEqual(len(applied), 1)


    def test_resume_params_still_apply_workspace_sync(self) -> None:
        st = MagicMock()
        st.session_state = {
            "active_page": "Trend Value",
            "main_sidebar_page": "Trend Value",
        }
        cloud_state = {
            "active_page": "Comparison Tool",
            "comparison_state": {"players": ["Francisco Lindor", "Aaron Judge"]},
        }
        applied: list[dict] = []

        def apply_state(_st: MagicMock, state: dict) -> None:
            applied.append(state)

        with patch("suite_cloud_state.has_resume_query_params", return_value=True), patch(
            "suite_cloud_state.probe_cloud_restore_diagnostics",
            return_value={"cloud_has_full_session": True},
        ), patch(
            "suite_cloud_state.load_cloud_full_session",
            return_value=(cloud_state, "2026-06-08T15:00:00+00:00"),
        ), patch(
            "suite_user_persistence._load_raw",
            return_value=({"active_page": "Trend Value"}, None, "2026-06-08T12:00:00+00:00"),
        ), patch("suite_user_persistence.save_user_state", return_value=True):
            ok = sync_workspace_protocol(st, "baseball", apply_state=apply_state)

        self.assertTrue(ok)
        self.assertEqual(len(applied), 1)
        self.assertTrue(st.session_state.get("_suite_resume_insight_hydration_only"))
        self.assertNotIn("_suite_workspace_sync_skipped_no_apply", st.session_state)

    def test_restore_skipped_blocks_autosave(self) -> None:
        st = MagicMock()
        st.session_state = {"_suite_persist_local_dirty::baseball": True}
        build = MagicMock(return_value={"active_page": "Trend Value"})

        with patch("suite_cloud_state.has_resume_query_params", return_value=False), patch(
            "suite_cloud_state.load_cloud_full_session",
            return_value=({"active_page": "Trend Value"}, "2026-06-08T12:00:00+00:00"),
        ), patch(
            "suite_user_persistence._load_raw",
            return_value=({"active_page": "Trend Value"}, None, "2026-06-08T13:00:00+00:00"),
        ):
            sync_workspace_protocol(st, "baseball", apply_state=lambda _s, _d: None)

        with patch("suite_user_persistence.save_user_state") as save_disk:
            autosave_if_changed(st, "baseball", build_state=build)
        save_disk.assert_not_called()
        self.assertTrue(st.session_state.get("_suite_workspace_sync_skipped_no_apply"))

    def test_blank_comparison_cannot_overwrite_cloud(self) -> None:
        st = MagicMock()
        st.session_state = {
            "active_page": "Comparison Tool",
            "comparison_state": {"players": []},
        }
        cloud_state = {
            "active_page": "Comparison Tool",
            "comparison_state": {"players": ["Francisco Lindor", "Aaron Judge"]},
        }
        build = MagicMock(
            return_value={
                "active_page": "Comparison Tool",
                "comparison_state": {"players": []},
                "page_filter_state": {"Comparison Tool": {"compare_players": []}},
            }
        )

        with patch(
            "suite_cloud_state.load_cloud_full_session",
            return_value=(cloud_state, "2026-06-08T15:00:00+00:00"),
        ), patch("suite_cloud_state.save_cloud_full_session", return_value=True) as save_cloud, patch(
            "suite_user_persistence.save_user_state", return_value=True
        ):
            force_autosave(st, "baseball", build_state=build, reason="autosave")

        save_cloud.assert_not_called()
        self.assertEqual(
            st.session_state.get("_suite_autosave_cloud_blocked_reason"),
            "blank_comparison_would_erase_cloud",
        )


if __name__ == "__main__":
    unittest.main()
