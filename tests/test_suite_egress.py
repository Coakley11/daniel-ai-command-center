"""Supabase egress reduction and instrumentation tests."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from suite_storage_config import SuiteCloudConfig, reset_cloud_config_cache


class TestSuiteEgress(unittest.TestCase):
    def tearDown(self) -> None:
        reset_cloud_config_cache()

    @patch("suite_storage_supabase._cloud_user_id", return_value="uid-1")
    @patch("suite_storage_supabase._request")
    @patch("suite_storage_config.get_cloud_config")
    def test_load_current_states_default_skips_metrics(
        self, mock_cfg: MagicMock, mock_req: MagicMock, _uid: MagicMock
    ) -> None:
        mock_cfg.return_value = SuiteCloudConfig(url="https://test.supabase.co", key="secret")
        mock_req.return_value = [
            {
                "app": "music",
                "page": "Song Editor",
                "summary": "Working on chords",
                "updated_at": "2026-06-19T12:00:00",
            }
        ]
        with patch(
            "suite_workspace.workspace_storage_app_keys",
            return_value=frozenset({"music"}),
        ):
            from suite_storage_supabase import load_current_states

            states = load_current_states()
        self.assertEqual(states["music"]["page"], "Song Editor")
        self.assertEqual(states["music"]["metrics"], {})
        params = mock_req.call_args.kwargs["params"]
        self.assertEqual(params["select"], "app,page,summary,updated_at")

    @patch("suite_storage_supabase._cloud_user_id", return_value="uid-1")
    @patch("suite_storage_supabase._request")
    @patch("suite_storage_config.get_cloud_config")
    def test_load_current_state_for_app_single_row(
        self, mock_cfg: MagicMock, mock_req: MagicMock, _uid: MagicMock
    ) -> None:
        mock_cfg.return_value = SuiteCloudConfig(url="https://test.supabase.co", key="secret")
        mock_req.return_value = [
            {
                "app": "music",
                "page": "Song Editor",
                "summary": "Working on chords",
                "metrics": {"full_session": {"song": "Test"}, "pick_key": "abc"},
                "updated_at": "2026-06-19T12:00:00",
            }
        ]
        with patch(
            "suite_workspace.workspace_storage_app_keys",
            return_value=frozenset({"music"}),
        ):
            from suite_storage_supabase import load_current_state_for_app

            row = load_current_state_for_app("music")
        self.assertIn("full_session", row["metrics"])
        params = mock_req.call_args.kwargs["params"]
        self.assertIn("metrics", params["select"])
        self.assertIn("limit", params)

    @patch("suite_storage_supabase._cloud_user_id", return_value="uid-1")
    @patch("suite_storage_supabase._request")
    @patch("suite_storage_config.get_cloud_config")
    def test_load_current_state_meta_for_app_no_metrics(
        self, mock_cfg: MagicMock, mock_req: MagicMock, _uid: MagicMock
    ) -> None:
        mock_cfg.return_value = SuiteCloudConfig(url="https://test.supabase.co", key="secret")
        mock_req.return_value = [
            {
                "app": "music",
                "page": "Song Editor",
                "summary": "Working on chords",
                "updated_at": "2026-06-19T12:00:00",
            }
        ]
        with patch(
            "suite_workspace.workspace_storage_app_keys",
            return_value=frozenset({"music"}),
        ):
            from suite_storage_supabase import load_current_state_meta_for_app

            meta = load_current_state_meta_for_app("music")
        self.assertEqual(meta["page"], "Song Editor")
        params = mock_req.call_args.kwargs["params"]
        self.assertNotIn("metrics", params["select"])

    @patch("suite_storage_supabase.get_cloud_config")
    def test_request_get_cache_reuses_response(self, mock_cfg: MagicMock) -> None:
        mock_cfg.return_value = SuiteCloudConfig(url="https://test.supabase.co", key="secret")
        bucket: dict = {}
        fake_st = MagicMock()
        fake_st.session_state = {"_suite_supabase_get_cache": bucket}

        response = MagicMock()
        response.status_code = 200
        response.content = b'[{"ok": true}]'
        response.json.return_value = [{"ok": True}]

        with patch("requests.request", return_value=response) as mock_http:
            with patch("streamlit.st", fake_st, create=True):
                from suite_storage_supabase import _request

                first = _request("GET", "suite_app_current_state", params={"select": "app"})
                second = _request("GET", "suite_app_current_state", params={"select": "app"})
        self.assertEqual(first, second)
        self.assertEqual(mock_http.call_count, 1)

    def test_record_egress_tracks_table_and_source(self) -> None:
        from suite_egress_trace import EgressRunSummary, egress_source, record_egress

        summary = EgressRunSummary()
        with patch("suite_egress_trace._session_bucket", return_value=summary):
            with egress_source("load_current_state_for_app"):
                record_egress(method="GET", path="suite_app_current_state", bytes_in=4096)
        self.assertEqual(summary.reads, 1)
        self.assertEqual(summary.bytes_in, 4096)
        self.assertIn("suite_app_current_state", summary.by_table)
        self.assertIn("load_current_state_for_app", summary.by_source)

    @patch("suite_storage_config.cloud_storage_enabled", return_value=True)
    @patch("suite_cloud_state._import_storage")
    def test_load_cloud_full_session_uses_single_app_fetch(
        self, mock_import: MagicMock, _cloud: MagicMock
    ) -> None:
        storage = MagicMock()
        storage.normalize_app_key.return_value = "music"
        storage.load_current_state_meta_for_app.return_value = {
            "updated_at": "2026-06-19T12:00:00",
        }
        storage.load_current_state_for_app.return_value = {
            "updated_at": "2026-06-19T12:00:00",
            "metrics": {"full_session": {"view_mode": "editor"}},
        }
        mock_import.return_value = (storage, "suite_storage")
        from suite_cloud_state import load_cloud_full_session

        blob, ts = load_cloud_full_session("music")
        self.assertEqual(blob.get("view_mode"), "editor")
        self.assertEqual(ts, "2026-06-19T12:00:00")
        storage.load_current_states.assert_not_called()
        storage.load_current_state_for_app.assert_called_once()


if __name__ == "__main__":
    unittest.main()
