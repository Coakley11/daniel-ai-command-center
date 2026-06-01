"""Supabase storage routing (mocked HTTP)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from suite_storage_config import SuiteCloudConfig, reset_cloud_config_cache


class TestSuiteCloudStorage(unittest.TestCase):
    def tearDown(self) -> None:
        reset_cloud_config_cache()

    @patch("suite_storage_supabase._request")
    @patch("suite_storage_config.get_cloud_config")
    def test_record_activity_uses_cloud_when_configured(
        self, mock_cfg: MagicMock, mock_req: MagicMock
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

    @patch("suite_storage.cloud_storage_enabled", return_value=False)
    def test_load_events_sqlite_when_no_cloud(self, _mock: MagicMock) -> None:
        from suite_storage import load_events

        events = load_events(limit=5)
        self.assertIsInstance(events, list)


if __name__ == "__main__":
    unittest.main()
