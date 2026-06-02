"""Supabase storage routing (mocked HTTP)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from suite_storage_config import SuiteCloudConfig, reset_cloud_config_cache


class TestSuiteCloudStorage(unittest.TestCase):
    def tearDown(self) -> None:
        reset_cloud_config_cache()

    @patch(
        "suite_storage_supabase._cloud_user_id",
        return_value="11111111-1111-1111-1111-111111111111",
    )
    @patch("suite_storage_supabase._request")
    @patch("suite_storage_config.get_cloud_config")
    def test_record_activity_uses_cloud_when_configured(
        self, mock_cfg: MagicMock, mock_req: MagicMock, _uid: MagicMock
    ) -> None:
        mock_cfg.return_value = SuiteCloudConfig(url="https://test.supabase.co", key="secret")
        from suite_storage_supabase import record_activity

        record_activity(
            "music",
            "verified_chart_saved",
            metrics={"song": "Test", "artist": "Artist", "edited_fields": ["chords"]},
            summary="Saved",
            resume_key="song:test",
            resume_title="Continue: Test",
        )
        self.assertGreaterEqual(mock_req.call_count, 1)
        first_path = mock_req.call_args_list[0][0][1]
        self.assertEqual(first_path, "suite_activity_events")
        event_body = mock_req.call_args_list[0][1]["json_body"]
        self.assertIn("user_id", event_body)

    @patch("suite_storage_supabase._request")
    @patch("suite_user.get_external_user_id", return_value="daniel")
    @patch("suite_user.get_user_email", return_value="daniel@example.com")
    @patch("suite_user.get_display_name", return_value="Daniel")
    @patch("suite_storage_config.get_cloud_config")
    def test_ensure_user_row_returns_uuid(
        self,
        mock_cfg: MagicMock,
        _dn: MagicMock,
        _em: MagicMock,
        _ext: MagicMock,
        mock_req: MagicMock,
    ) -> None:
        mock_cfg.return_value = SuiteCloudConfig(url="https://test.supabase.co", key="secret")
        mock_req.side_effect = [
            [{"id": "11111111-1111-1111-1111-111111111111"}],
        ]
        from suite_storage_supabase import ensure_user_row

        uid = ensure_user_row("daniel", email="daniel@example.com", display_name="Daniel")
        self.assertEqual(uid, "11111111-1111-1111-1111-111111111111")

    @patch("suite_storage.cloud_storage_enabled", return_value=False)
    def test_load_events_sqlite_when_no_cloud(self, _mock: MagicMock) -> None:
        from suite_storage import load_events

        events = load_events(limit=5)
        self.assertIsInstance(events, list)


if __name__ == "__main__":
    unittest.main()
