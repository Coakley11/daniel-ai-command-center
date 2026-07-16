"""Admin-only access model — authorized accounts and fail-safe defaults."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from suite_auth import AUTH_EXTERNAL_ID_KEY, AUTH_SESSION_KEY, AUTH_USER_EMAIL_KEY
from suite_workspace import can_show_developer_tools, set_active_workspace_id
from suite_workspace_registry import (
    ADMIN_ACCOUNTS,
    ADMIN_EMAIL_LOCAL_PARTS,
    can_switch_workspaces,
    is_admin_account,
    is_admin_user,
)


class TestAdminAllowlist(unittest.TestCase):
    def test_allowlist_is_email_local_parts_only(self) -> None:
        self.assertEqual(ADMIN_ACCOUNTS, ADMIN_EMAIL_LOCAL_PARTS)
        self.assertIn("coakley11", ADMIN_EMAIL_LOCAL_PARTS)
        self.assertIn("daniel.cohen11", ADMIN_EMAIL_LOCAL_PARTS)
        self.assertNotIn("daniel", ADMIN_EMAIL_LOCAL_PARTS)

    def test_coakley11_external_id_is_admin(self) -> None:
        self.assertTrue(is_admin_user(external_id="coakley11"))
        self.assertTrue(is_admin_account(external_id="coakley11"))

    def test_bare_daniel_external_id_is_not_admin(self) -> None:
        self.assertFalse(is_admin_user(external_id="daniel"))
        self.assertFalse(is_admin_account(external_id="daniel"))

    def test_email_local_part_daniel_cohen11_is_admin(self) -> None:
        self.assertTrue(is_admin_user(email="daniel.cohen11@example.com"))

    def test_email_local_part_coakley11_is_admin(self) -> None:
        self.assertTrue(is_admin_user(email="coakley11@aol.com"))

    def test_non_admin_external_id_denied(self) -> None:
        self.assertFalse(is_admin_user(external_id="ariel"))
        self.assertFalse(is_admin_user(external_id="jordan99"))
        self.assertFalse(is_admin_user(external_id="default"))

    def test_empty_identity_denied(self) -> None:
        with patch("suite_user.get_external_user_id", return_value="default"), patch(
            "suite_user.get_user_email", return_value=""
        ):
            self.assertFalse(is_admin_user())


class TestDanielAliasNotSpoofable(unittest.TestCase):
    """Bare ``daniel`` must never grant admin without daniel.cohen11 email proof."""

    def test_forged_session_external_id_daniel_denied(self) -> None:
        session = {
            AUTH_SESSION_KEY: True,
            AUTH_EXTERNAL_ID_KEY: "daniel",
            AUTH_USER_EMAIL_KEY: "jordan99@example.com",
            "_suite_active_workspace_id": "daniel",
        }
        with patch("suite_auth.is_auth_enabled", return_value=True), patch(
            "suite_auth.is_authenticated", return_value=True
        ):
            self.assertFalse(is_admin_user(session_state=session))
            self.assertFalse(can_switch_workspaces(session_state=session))

    def test_workspace_id_daniel_does_not_grant_admin(self) -> None:
        class FakeState(dict):
            pass

        session = FakeState(
            {
                AUTH_SESSION_KEY: True,
                AUTH_EXTERNAL_ID_KEY: "jordan99",
                AUTH_USER_EMAIL_KEY: "jordan99@example.com",
            }
        )
        st = type("St", (), {"session_state": session, "query_params": {"dev": "1", "suite_workspace": "daniel"}})()
        set_active_workspace_id(st, "daniel")
        with patch("suite_auth.is_auth_enabled", return_value=True), patch(
            "suite_auth.is_authenticated", return_value=True
        ), patch("suite_workspace.is_admin_session", wraps=__import__("suite_workspace").is_admin_session):
            self.assertFalse(is_admin_user(session_state=session))
            self.assertFalse(can_show_developer_tools(st=st))

    def test_display_name_daniel_does_not_grant_admin(self) -> None:
        session = {
            AUTH_SESSION_KEY: True,
            AUTH_EXTERNAL_ID_KEY: "guest",
            AUTH_USER_EMAIL_KEY: "guest@example.com",
            "display_name": "Daniel",
            "suite_user_display_name": "Daniel Cohen",
        }
        with patch("suite_auth.is_auth_enabled", return_value=True), patch(
            "suite_auth.is_authenticated", return_value=True
        ):
            self.assertFalse(is_admin_user(session_state=session))

    def test_account_slug_daniel_without_admin_email_denied(self) -> None:
        session = {
            AUTH_SESSION_KEY: True,
            AUTH_EXTERNAL_ID_KEY: "daniel",
            AUTH_USER_EMAIL_KEY: "daniel@evil.example",
            "_suite_owned_workspace_id": "daniel",
        }
        with patch("suite_auth.is_auth_enabled", return_value=True), patch(
            "suite_auth.is_authenticated", return_value=True
        ):
            self.assertFalse(is_admin_user(session_state=session))

    def test_unsigned_demo_workspace_daniel_denied(self) -> None:
        session = {
            AUTH_SESSION_KEY: True,
            AUTH_EXTERNAL_ID_KEY: "test_user",
            AUTH_USER_EMAIL_KEY: "test_user@example.com",
            "_suite_active_workspace_id": "daniel",
        }
        with patch("suite_auth.is_auth_enabled", return_value=True), patch(
            "suite_auth.is_authenticated", return_value=True
        ):
            self.assertFalse(is_admin_user(session_state=session))

    def test_query_param_dev_and_daniel_workspace_denied_for_non_admin(self) -> None:
        class FakeState(dict):
            pass

        session = FakeState(
            {
                AUTH_SESSION_KEY: True,
                AUTH_EXTERNAL_ID_KEY: "ariel",
                AUTH_USER_EMAIL_KEY: "ariel@example.com",
                "cc_developer_mode": True,
            }
        )
        st = type(
            "St",
            (),
            {"session_state": session, "query_params": {"dev": "1", "suite_workspace": "daniel"}},
        )()
        set_active_workspace_id(st, "daniel")
        with patch("suite_auth.is_auth_enabled", return_value=True), patch(
            "suite_auth.is_authenticated", return_value=True
        ):
            self.assertFalse(can_show_developer_tools(st=st))

    def test_secrets_suite_user_id_daniel_alone_denied(self) -> None:
        with patch("suite_auth.is_auth_enabled", return_value=False), patch(
            "suite_user.get_external_user_id", return_value="daniel"
        ), patch("suite_user.get_user_email", return_value=""):
            self.assertFalse(is_admin_user(session_state={}))

    def test_secrets_email_daniel_cohen11_grants_admin(self) -> None:
        with patch("suite_auth.is_auth_enabled", return_value=False), patch(
            "suite_user.get_external_user_id", return_value="daniel"
        ), patch("suite_user.get_user_email", return_value="daniel.cohen11@example.com"):
            self.assertTrue(is_admin_user(session_state={}))


class TestAdminSessionAuth(unittest.TestCase):
    def test_authenticated_coakley11_is_admin(self) -> None:
        session = {
            AUTH_SESSION_KEY: True,
            AUTH_EXTERNAL_ID_KEY: "coakley11",
            AUTH_USER_EMAIL_KEY: "coakley11@aol.com",
        }
        with patch("suite_auth.is_auth_enabled", return_value=True), patch(
            "suite_auth.is_authenticated", return_value=True
        ):
            self.assertTrue(is_admin_user(session_state=session))
            self.assertTrue(can_switch_workspaces(session_state=session))

    def test_authenticated_daniel_cohen11_email_is_admin(self) -> None:
        session = {
            AUTH_SESSION_KEY: True,
            AUTH_EXTERNAL_ID_KEY: "daniel",
            AUTH_USER_EMAIL_KEY: "daniel.cohen11@example.com",
        }
        with patch("suite_auth.is_auth_enabled", return_value=True), patch(
            "suite_auth.is_authenticated", return_value=True
        ):
            self.assertTrue(is_admin_user(session_state=session))
            self.assertTrue(can_switch_workspaces(session_state=session))

    def test_authenticated_ariel_is_not_admin(self) -> None:
        session = {
            AUTH_SESSION_KEY: True,
            AUTH_EXTERNAL_ID_KEY: "ariel",
            AUTH_USER_EMAIL_KEY: "ariel@example.com",
        }
        with patch("suite_auth.is_auth_enabled", return_value=True), patch(
            "suite_auth.is_authenticated", return_value=True
        ):
            self.assertFalse(is_admin_user(session_state=session))
            self.assertFalse(can_switch_workspaces(session_state=session))

    def test_auth_enabled_but_signed_out_is_not_admin(self) -> None:
        session = {
            AUTH_EXTERNAL_ID_KEY: "daniel",
            AUTH_USER_EMAIL_KEY: "daniel.cohen11@example.com",
        }
        with patch("suite_auth.is_auth_enabled", return_value=True), patch(
            "suite_auth.is_authenticated", return_value=False
        ):
            self.assertFalse(is_admin_user(session_state=session))
            self.assertFalse(can_switch_workspaces(session_state=session))

    def test_does_not_use_resolve_auth_daniel_default(self) -> None:
        """Empty auth identity must not inherit resolve_auth_external_id's 'daniel' fallback."""
        session = {AUTH_SESSION_KEY: True}
        with patch("suite_auth.is_auth_enabled", return_value=True), patch(
            "suite_auth.is_authenticated", return_value=True
        ), patch("suite_auth.current_auth_email", return_value=""):
            self.assertFalse(is_admin_user(session_state=session))


if __name__ == "__main__":
    unittest.main()
