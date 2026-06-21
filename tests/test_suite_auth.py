"""Sprint C — Real Accounts foundation scaffolding."""

from __future__ import annotations

import os
import unittest
import unittest.mock

from suite_auth import (
    AUTH_EXTERNAL_ID_KEY,
    AUTH_SESSION_KEY,
    allowed_workspaces_for_user,
    enforce_workspace_ownership,
    is_auth_enabled,
    is_authenticated,
    login_with_email,
    logout,
    password_auth_available,
)
from suite_workspace import SESSION_KEY


class TestSuiteAuth(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop("SUITE_AUTH_ENABLED", None)
        from suite_storage_config import reset_cloud_config_cache

        reset_cloud_config_cache()

    def test_auth_disabled_by_default(self) -> None:
        os.environ.pop("SUITE_AUTH_ENABLED", None)
        self.assertFalse(is_auth_enabled())
        self.assertFalse(password_auth_available())

    def test_auth_enabled_via_env(self) -> None:
        os.environ["SUITE_AUTH_ENABLED"] = "true"
        self.assertTrue(is_auth_enabled())

    def test_unauthenticated_when_auth_enabled(self) -> None:
        os.environ["SUITE_AUTH_ENABLED"] = "true"
        session = {}
        self.assertFalse(is_authenticated(session))

    def test_logout_clears_session(self) -> None:
        session = {AUTH_SESSION_KEY: True, "_suite_auth_user_email": "a@b.com"}
        logout(session)
        self.assertNotIn(AUTH_SESSION_KEY, session)

    def test_allowed_workspaces_for_ariel(self) -> None:
        self.assertEqual(allowed_workspaces_for_user("ariel"), ("ariel",))

    def test_enforce_workspace_ownership_clamps_profile(self) -> None:
        os.environ["SUITE_AUTH_ENABLED"] = "true"
        session = {
            AUTH_SESSION_KEY: True,
            AUTH_EXTERNAL_ID_KEY: "ariel",
            SESSION_KEY: "daniel",
        }
        with unittest.mock.patch("suite_auth.is_auth_enabled", return_value=True):
            with unittest.mock.patch("suite_auth.is_authenticated", return_value=True):
                enforce_workspace_ownership(session)
        self.assertEqual(session.get(SESSION_KEY), "ariel")

    def test_login_requires_supabase_when_enabled(self) -> None:
        os.environ["SUITE_AUTH_ENABLED"] = "true"
        session = {}
        ok, msg = login_with_email(session, email="test@example.com", password="secret")
        self.assertFalse(ok)
        self.assertTrue(
            any(
                phrase in msg.lower()
                for phrase in ("not configured", "supabase", "anon", "missing", "installed")
            ),
            msg,
        )

    def test_auth_backend_status_when_enabled_without_secrets(self) -> None:
        os.environ["SUITE_AUTH_ENABLED"] = "true"
        from suite_auth import auth_backend_status

        status = auth_backend_status()
        self.assertTrue(status["auth_ui_enabled"])
        self.assertFalse(status["ready"])


if __name__ == "__main__":
    unittest.main()
