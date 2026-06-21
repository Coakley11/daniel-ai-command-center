"""Query-param + Supabase browser auth persistence (C2b)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from suite_auth_browser import (
    SESSION_QUERY_PARAM,
    SESSION_STATE_SID_KEY,
    clear_browser_auth_tokens,
    load_browser_auth_tokens,
    save_browser_auth_tokens,
)


class _FakeQueryParams(dict):
    def get(self, key, default=None):  # type: ignore[override]
        return super().get(key, default)


class TestBrowserAuthStorage(unittest.TestCase):
    def _st(self, *, query: dict | None = None) -> MagicMock:
        st = MagicMock()
        st.session_state = {}
        st.query_params = _FakeQueryParams(query or {})
        return st

    @patch("suite_storage_supabase.load_browser_auth_session")
    def test_load_reads_query_param(self, mock_load: MagicMock) -> None:
        mock_load.return_value = {"access_token": "a", "refresh_token": "r", "expires_at": 1}
        st = self._st(query={SESSION_QUERY_PARAM: "sid-123"})
        tokens = load_browser_auth_tokens(st)
        self.assertEqual(tokens["access_token"], "a")
        mock_load.assert_called_once_with("sid-123")

    @patch("suite_storage_supabase.save_browser_auth_session")
    def test_save_writes_query_param(self, mock_save: MagicMock) -> None:
        st = self._st()
        save_browser_auth_tokens(
            st,
            {"access_token": "a", "refresh_token": "r", "expires_at": 1},
            auth_user_id="user-uuid",
        )
        mock_save.assert_called_once()
        sid = mock_save.call_args[0][0]
        self.assertEqual(st.query_params[SESSION_QUERY_PARAM], sid)

    @patch("suite_storage_supabase.invalidate_browser_auth_session")
    def test_clear_removes_query_param(self, mock_inv: MagicMock) -> None:
        st = self._st(query={SESSION_QUERY_PARAM: "sid-123"})
        clear_browser_auth_tokens(st)
        mock_inv.assert_called_once_with("sid-123")
        self.assertNotIn(SESSION_QUERY_PARAM, st.query_params)


if __name__ == "__main__":
    unittest.main()
