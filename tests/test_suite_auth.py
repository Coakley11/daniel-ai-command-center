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

    def test_allowed_workspaces_for_daniel_admin(self) -> None:
        self.assertIn("ariel", allowed_workspaces_for_user("daniel"))

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

    def test_daniel_admin_keeps_ariel_workspace_when_authenticated(self) -> None:
        os.environ["SUITE_AUTH_ENABLED"] = "true"
        session = {
            AUTH_SESSION_KEY: True,
            AUTH_EXTERNAL_ID_KEY: "daniel",
            SESSION_KEY: "ariel",
        }
        with unittest.mock.patch("suite_auth.is_auth_enabled", return_value=True):
            with unittest.mock.patch("suite_auth.is_authenticated", return_value=True):
                enforce_workspace_ownership(session)
        self.assertEqual(session.get(SESSION_KEY), "ariel")

    def test_ariel_account_cannot_use_daniel_workspace(self) -> None:
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

    def test_resolve_auth_external_id_prefers_email_over_supabase_uuid(self) -> None:
        from suite_auth import AUTH_USER_EMAIL_KEY, AUTH_USER_ID_KEY, resolve_auth_external_id

        session = {
            AUTH_USER_ID_KEY: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            AUTH_USER_EMAIL_KEY: "daniel@example.com",
        }
        self.assertEqual(resolve_auth_external_id(session), "daniel")

    def test_daniel_email_includes_ariel_in_allowed_workspaces_with_uuid_user_id(self) -> None:
        from suite_auth import AUTH_USER_EMAIL_KEY, AUTH_USER_ID_KEY, allowed_workspaces_for_session

        session = {
            AUTH_SESSION_KEY: True,
            AUTH_USER_ID_KEY: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            AUTH_USER_EMAIL_KEY: "daniel@example.com",
        }
        with unittest.mock.patch("suite_auth.is_auth_enabled", return_value=True):
            with unittest.mock.patch("suite_auth.is_authenticated", return_value=True):
                allowed = allowed_workspaces_for_session(session)
        self.assertIn("ariel", allowed)

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

    def test_auth_password_reset_redirect_url_defaults_to_command_center_dev(self) -> None:
        from suite_auth import auth_password_reset_redirect_url

        url = auth_password_reset_redirect_url()
        self.assertIn("daniel-ai-command-center", url)
        self.assertIn("streamlit.app", url)
        self.assertIn("suite_auth_landing=recovery", url)

    def test_auth_password_reset_redirect_url_can_omit_landing_hint(self) -> None:
        from suite_auth import auth_password_reset_redirect_url

        url = auth_password_reset_redirect_url(with_landing_hint=False)
        self.assertNotIn("suite_auth_landing", url)

    def test_recovery_landing_failed_waits_for_client_snapshot(self) -> None:
        from suite_auth import _recovery_landing_failed

        class FakeState(dict):
            pass

        st = type(
            "St",
            (),
            {"session_state": FakeState(), "query_params": {"suite_auth_landing": "recovery"}},
        )()
        self.assertFalse(_recovery_landing_failed(st))

    def test_recovery_landing_failed_when_snapshot_has_no_tokens(self) -> None:
        from suite_auth import _recovery_landing_failed

        class FakeState(dict):
            pass

        ss = FakeState()
        ss["_suite_auth_landing_snapshot"] = "hash:0,rec:0,code:0,th:0,at:0"
        st = type(
            "St",
            (),
            {
                "session_state": ss,
                "query_params": {
                    "suite_auth_landing": "recovery",
                    "suite_auth_hash_probe": "none",
                },
            },
        )()
        self.assertTrue(_recovery_landing_failed(st))

    def test_recovery_token_hash_from_malformed_landing_query(self) -> None:
        from suite_auth import _consume_auth_recovery_token_hash, _recovery_token_hash_from_query

        class FakeState(dict):
            pass

        st = type(
            "St",
            (),
            {
                "session_state": FakeState(),
                "query_params": {
                    "suite_auth_landing": "recovery?token_hash=abc123",
                    "type": "recovery",
                },
            },
        )()
        self.assertEqual(_recovery_token_hash_from_query(st), "abc123")

    def test_consume_auth_recovery_token_hash_marks_pending(self) -> None:
        from suite_auth import AUTH_RECOVERY_PENDING_KEY, _consume_auth_recovery_token_hash

        class FakeState(dict):
            pass

        ss = FakeState()
        auth = unittest.mock.MagicMock()
        auth.verify_otp.return_value = unittest.mock.MagicMock(
            user=unittest.mock.MagicMock(id="u1", email="user@example.com"),
            session=unittest.mock.MagicMock(
                access_token="access",
                refresh_token="refresh",
                expires_at=999,
            ),
        )
        client = unittest.mock.MagicMock()
        client.auth = auth
        st = type(
            "St",
            (),
            {
                "session_state": ss,
                "query_params": {"type": "recovery", "token_hash": "abc123"},
            },
        )()
        with unittest.mock.patch("suite_auth._create_fresh_supabase_client", return_value=client):
            self.assertTrue(_consume_auth_recovery_token_hash(st))
        self.assertTrue(ss.get(AUTH_RECOVERY_PENDING_KEY))
        auth.verify_otp.assert_called_once_with({"token_hash": "abc123", "type": "recovery"})

    def test_recovery_query_promotion_needed_when_browser_has_token_only(self) -> None:
        from suite_auth import _needs_recovery_query_promotion

        class FakeState(dict):
            pass

        ss = FakeState()
        ss["_suite_auth_landing_snapshot"] = "hash:0,rec:0,code:0,th:1,at:0"
        st = type("St", (), {"session_state": ss, "query_params": {"suite_auth_landing": "recovery"}})()
        self.assertTrue(_needs_recovery_query_promotion(st))

    def test_recovery_query_promotion_skipped_when_token_hash_parsed(self) -> None:
        from suite_auth import _needs_recovery_query_promotion

        class FakeState(dict):
            pass

        st = type(
            "St",
            (),
            {
                "session_state": FakeState(),
                "query_params": {
                    "suite_auth_landing": "recovery",
                    "type": "recovery",
                    "token_hash": "abc123",
                },
            },
        )()
        self.assertFalse(_needs_recovery_query_promotion(st))

    def test_recovery_verify_failed_after_malformed_landing_consume_error(self) -> None:
        from suite_auth import (
            AUTH_RECOVERY_LAST_ERROR_KEY,
            AUTH_RECOVERY_VERIFY_ATTEMPTED_KEY,
            _consume_auth_recovery_token_hash,
            _recovery_verify_failed,
        )

        class FakeState(dict):
            pass

        ss = FakeState()
        auth = unittest.mock.MagicMock()
        auth.verify_otp.side_effect = RuntimeError("Token has expired or is invalid")
        client = unittest.mock.MagicMock()
        client.auth = auth
        st = type(
            "St",
            (),
            {
                "session_state": ss,
                "query_params": {
                    "suite_auth_landing": "recovery?token_hash=abc123",
                    "type": "recovery",
                },
            },
        )()
        with unittest.mock.patch("suite_auth._create_fresh_supabase_client", return_value=client):
            self.assertFalse(_consume_auth_recovery_token_hash(st))
        self.assertTrue(_recovery_verify_failed(st))
        self.assertEqual(ss.get(AUTH_RECOVERY_VERIFY_ATTEMPTED_KEY), "abc123")
        self.assertIn("expired", str(ss.get(AUTH_RECOVERY_LAST_ERROR_KEY)).lower())

    def test_request_password_reset_passes_redirect_to(self) -> None:
        from suite_auth import request_password_reset

        auth = unittest.mock.MagicMock()
        client = unittest.mock.MagicMock()
        client.auth = auth
        with unittest.mock.patch("suite_auth.is_auth_enabled", return_value=True):
            with unittest.mock.patch("suite_auth._create_fresh_supabase_client", return_value=client):
                with unittest.mock.patch(
                    "suite_auth.auth_password_reset_redirect_url",
                    return_value="https://example.test/cc",
                ):
                    ok, msg = request_password_reset("user@example.com")
        self.assertTrue(ok)
        auth.reset_password_email.assert_called_once_with(
            "user@example.com",
            {"redirect_to": "https://example.test/cc"},
        )
        self.assertIn("example.test", msg)

    def test_recovery_landing_detects_hash_probe(self) -> None:
        from suite_auth import _needs_recovery_hash_bridge, auth_recovery_diagnostics

        class FakeState(dict):
            pass

        st = type("St", (), {"session_state": FakeState(), "query_params": {"suite_auth_hash_probe": "recovery"}})()
        self.assertTrue(_needs_recovery_hash_bridge(st))
        diag = auth_recovery_diagnostics(st=st)
        self.assertTrue(diag["recovery_mode_detected"])
        self.assertTrue(diag["hash_bridge_waiting"])

    def test_recovery_landing_skips_bridge_after_probe_none(self) -> None:
        from suite_auth import _needs_recovery_hash_bridge

        class FakeState(dict):
            pass

        st = type("St", (), {"session_state": FakeState(), "query_params": {"suite_auth_hash_probe": "none"}})()
        self.assertFalse(_needs_recovery_hash_bridge(st))


if __name__ == "__main__":
    unittest.main()
