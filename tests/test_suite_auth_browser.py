"""CookieManager bootstrap behavior for C2b."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from suite_auth_browser import (
    COOKIE_BOOTSTRAP_KEY,
    COOKIE_NAME,
    COOKIE_SYNC_PENDING_KEY,
    init_browser_auth_storage,
    save_browser_auth_tokens,
)


class TestBrowserAuthStorageInit(unittest.TestCase):
    def _st(self) -> MagicMock:
        st = MagicMock()
        st.session_state = {}
        return st

    @patch("suite_auth_browser._cookie_manager")
    def test_first_run_returns_wait(self, mock_mgr_fn: MagicMock) -> None:
        mock_mgr_fn.return_value = MagicMock(get_all=MagicMock(return_value={}))
        st = self._st()
        self.assertEqual(init_browser_auth_storage(st), "wait")
        self.assertTrue(st.session_state.get(COOKIE_BOOTSTRAP_KEY))

    @patch("suite_auth_browser._cookie_manager")
    def test_second_run_returns_ready(self, mock_mgr_fn: MagicMock) -> None:
        mock_mgr_fn.return_value = MagicMock(get_all=MagicMock(return_value={}))
        st = self._st()
        st.session_state[COOKIE_BOOTSTRAP_KEY] = True
        self.assertEqual(init_browser_auth_storage(st), "ready")

    @patch("suite_auth_browser._cookie_manager")
    def test_sync_pending_until_cookie_readable(self, mock_mgr_fn: MagicMock) -> None:
        mgr = MagicMock()
        mgr.get.return_value = None
        mgr.get_all.return_value = {}
        mock_mgr_fn.return_value = mgr
        st = self._st()
        st.session_state[COOKIE_BOOTSTRAP_KEY] = True
        st.session_state[COOKIE_SYNC_PENDING_KEY] = True
        self.assertEqual(init_browser_auth_storage(st), "sync_pending")

        mgr.get.return_value = '{"access_token":"a","refresh_token":"r","expires_at":1}'
        self.assertEqual(init_browser_auth_storage(st), "ready")
        self.assertNotIn(COOKIE_SYNC_PENDING_KEY, st.session_state)

    @patch("suite_auth_browser._cookie_manager")
    def test_save_sets_sync_pending(self, mock_mgr_fn: MagicMock) -> None:
        mgr = MagicMock()
        mock_mgr_fn.return_value = mgr
        st = self._st()
        st.session_state[COOKIE_BOOTSTRAP_KEY] = True
        save_browser_auth_tokens(
            st,
            {"access_token": "a", "refresh_token": "r", "expires_at": 123},
        )
        mgr.set.assert_called_once()
        self.assertTrue(st.session_state.get(COOKIE_SYNC_PENDING_KEY))
        _, kwargs = mgr.set.call_args
        self.assertEqual(kwargs.get("same_site"), "lax")
        self.assertEqual(kwargs.get("secure"), True)
        self.assertEqual(mgr.set.call_args[0][0], COOKIE_NAME)


if __name__ == "__main__":
    unittest.main()
