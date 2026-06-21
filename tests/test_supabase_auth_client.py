"""Supabase Auth client wiring."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from suite_storage_config import SuiteCloudConfig


class TestSupabaseAuthClient(unittest.TestCase):
    @patch("supabase.create_client")
    @patch("suite_storage_supabase.get_auth_api_key", return_value="anon-key")
    @patch(
        "suite_storage_supabase.get_cloud_config",
        return_value=SuiteCloudConfig(url="https://x.supabase.co", key="service-key"),
    )
    def test_get_supabase_client_creates_client(self, _cfg, _auth_key, mock_create) -> None:
        from suite_storage_supabase import get_supabase_client, reset_supabase_client_cache

        reset_supabase_client_cache()
        mock_create.return_value = MagicMock()
        client = get_supabase_client()
        mock_create.assert_called_once_with("https://x.supabase.co", "anon-key")
        self.assertIs(client, mock_create.return_value)


if __name__ == "__main__":
    unittest.main()
