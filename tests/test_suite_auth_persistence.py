"""C2b — auth session persistence across browser refresh."""

from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

from suite_auth import (
    AUTH_SESSION_KEY,
    AUTH_TOKENS_KEY,
    AUTH_USER_EMAIL_KEY,
    _apply_authenticated_user,
    _clear_auth_session,
    _tokens_from_auth_response,
    _tokens_from_session_obj,
    is_authenticated,
    logout,
    restore_auth_session,
)


class _FakeUser:
    def __init__(self, *, uid: str = "uid-1", email: str = "daniel@example.com") -> None:
        self.id = uid
        self.email = email


class _FakeSession:
    def __init__(self) -> None:
        self.access_token = "access-token-abc"
        self.refresh_token = "refresh-token-xyz"
        self.expires_at = 4102444800
        self.user = _FakeUser()


class _FakeAuthResponse:
    def __init__(self) -> None:
        self.user = _FakeUser()
        self.session = _FakeSession()


class TestAuthTokenHelpers(unittest.TestCase):
    def test_tokens_from_session_obj(self) -> None:
        tokens = _tokens_from_session_obj(_FakeSession())
        self.assertEqual(tokens["access_token"], "access-token-abc")

    def test_tokens_from_auth_response(self) -> None:
        tokens = _tokens_from_auth_response(_FakeAuthResponse())
        self.assertIn("access_token", tokens)


class TestRestoreAuthSession(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop("SUITE_AUTH_ENABLED", None)

    @patch("suite_auth.is_auth_enabled", return_value=True)
    @patch("suite_auth._auth_api")
    def test_restore_from_session_state_tokens(self, mock_auth_api: MagicMock, _enabled: MagicMock) -> None:
        auth = MagicMock()
        auth.set_session.return_value = _FakeAuthResponse()
        auth.get_user.return_value = MagicMock(user=_FakeUser())
        mock_auth_api.return_value = auth

        session_state = {
            AUTH_TOKENS_KEY: {
                "access_token": "access-token-abc",
                "refresh_token": "refresh-token-xyz",
                "expires_at": 4102444800,
            }
        }
        self.assertTrue(restore_auth_session(session_state))
        self.assertTrue(is_authenticated(session_state))

    @patch("suite_auth.is_auth_enabled", return_value=True)
    @patch("suite_auth_browser.load_browser_auth_tokens")
    @patch("suite_auth._auth_api")
    def test_restore_from_browser_storage(
        self, mock_auth_api: MagicMock, mock_browser: MagicMock, _enabled: MagicMock
    ) -> None:
        auth = MagicMock()
        auth.set_session.return_value = _FakeAuthResponse()
        auth.get_user.return_value = MagicMock(user=_FakeUser())
        mock_auth_api.return_value = auth
        mock_browser.return_value = {
            "access_token": "access-token-abc",
            "refresh_token": "refresh-token-xyz",
            "expires_at": 4102444800,
        }

        session_state: dict = {}
        st = MagicMock()
        self.assertTrue(restore_auth_session(session_state, st=st))
        mock_browser.assert_called_once_with(st)


class TestLogoutPersistence(unittest.TestCase):
    @patch("suite_auth._auth_api")
    def test_logout_clears_tokens(self, mock_auth_api: MagicMock) -> None:
        auth = MagicMock()
        mock_auth_api.return_value = auth
        session_state = {
            AUTH_SESSION_KEY: True,
            AUTH_TOKENS_KEY: {"access_token": "a", "refresh_token": "r"},
        }
        st = MagicMock()
        with patch("suite_auth_browser.clear_browser_auth_tokens") as mock_clear:
            logout(session_state, st=st)
        self.assertNotIn(AUTH_SESSION_KEY, session_state)
        mock_clear.assert_called_once_with(st)


class TestApplyAuthenticatedUser(unittest.TestCase):
    def test_apply_sets_external_id_for_ariel(self) -> None:
        session_state: dict = {}
        _apply_authenticated_user(
            session_state,
            _FakeUser(email="ariel@example.com"),
            tokens={"access_token": "a", "refresh_token": "r"},
        )
        self.assertEqual(session_state["_suite_auth_external_id"], "ariel")


if __name__ == "__main__":
    unittest.main()
