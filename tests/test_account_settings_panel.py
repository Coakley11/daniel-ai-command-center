"""Account Settings UX — identity, workspace namespace, and isolation diagnostics."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from suite_account_settings import (
    NAMESPACE_PREVIEW_APPS,
    build_account_settings_context,
    build_scoped_cloud_key_preview,
    detect_workspace_namespace_issues,
)
from suite_workspace import (
    SESSION_KEY,
    get_active_workspace_id,
    init_suite_workspace,
    set_active_workspace_id,
)


class FakeState(dict):
    pass


def _fake_st(*, query_params: dict | None = None, session: FakeState | None = None):
    qp = query_params or {}
    ss = session if session is not None else FakeState()
    return type("St", (), {"session_state": ss, "query_params": qp})()


class TestAccountSettingsContext(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["SUITE_USER_ID"] = "daniel-phone"
        os.environ["SUITE_USER_EMAIL"] = "daniel@example.com"
        from suite_user import reset_account_cache

        reset_account_cache()

    def tearDown(self) -> None:
        os.environ.pop("SUITE_USER_ID", None)
        os.environ.pop("SUITE_USER_EMAIL", None)
        from suite_user import reset_account_cache

        reset_account_cache()

    def test_context_includes_email_and_suite_user_id(self) -> None:
        st = _fake_st()
        set_active_workspace_id(st, "daniel")
        ctx = build_account_settings_context(st=st)
        self.assertEqual(ctx["email"], "daniel@example.com")
        self.assertEqual(ctx["suite_user_id"], "daniel-phone")
        self.assertTrue(ctx["account_user_id"])
        self.assertFalse(ctx["password_auth_available"])

    def test_daniel_and_ariel_scoped_keys_differ(self) -> None:
        daniel = build_scoped_cloud_key_preview("daniel")
        ariel = build_scoped_cloud_key_preview("ariel")
        self.assertEqual(daniel["applied_intelligence"], "applied_intelligence")
        self.assertEqual(ariel["applied_intelligence"], "applied_intelligence__ariel")
        self.assertEqual(daniel["baseball"], "baseball")
        self.assertEqual(ariel["baseball"], "baseball__ariel")
        self.assertEqual(daniel["future_lens"], "future_lens")
        self.assertEqual(ariel["future_lens"], "future_lens__ariel")
        self.assertNotEqual(daniel, ariel)

    def test_context_reflects_active_workspace(self) -> None:
        st = _fake_st()
        set_active_workspace_id(st, "ariel")
        ctx = build_account_settings_context(st=st)
        self.assertEqual(ctx["active_workspace_id"], "ariel")
        self.assertEqual(ctx["active_workspace_label"], "Ariel")
        self.assertIn("applied_intelligence__ariel", ctx["namespace_keys"])
        self.assertNotIn("applied_intelligence", ctx["namespace_keys"])
        self.assertEqual(
            ctx["scoped_cloud_keys"]["applied_intelligence"],
            "applied_intelligence__ariel",
        )

    def test_namespace_preview_covers_all_suite_apps(self) -> None:
        preview_ids = {app_id for app_id, _ in NAMESPACE_PREVIEW_APPS}
        self.assertIn("future_lens", preview_ids)
        self.assertIn("applied_intelligence", preview_ids)


class TestWorkspaceNamespaceIssues(unittest.TestCase):
    def test_query_param_mismatch_raises_error_issue(self) -> None:
        st = _fake_st(query_params={"suite_workspace": "ariel"})
        st.session_state[SESSION_KEY] = "daniel"
        with patch("suite_account_settings.load_persisted_workspace_id", return_value="daniel"):
            issues = detect_workspace_namespace_issues(st=st)
        codes = [i["code"] for i in issues]
        self.assertIn("query_workspace_mismatch", codes)
        mismatch = next(i for i in issues if i["code"] == "query_workspace_mismatch")
        self.assertEqual(mismatch["severity"], "error")

    def test_persisted_mismatch_warning(self) -> None:
        st = _fake_st()
        set_active_workspace_id(st, "daniel")
        with patch("suite_account_settings.load_persisted_workspace_id", return_value="ariel"):
            issues = detect_workspace_namespace_issues(st=st)
        codes = [i["code"] for i in issues]
        self.assertIn("persisted_workspace_mismatch", codes)

    def test_ariel_profile_includes_direct_open_info(self) -> None:
        st = _fake_st()
        set_active_workspace_id(st, "ariel")
        with patch(
            "activity_diagnostics.build_workspace_activity_namespace_diagnostics",
            return_value={"namespace_mismatch_hint": ""},
        ):
            issues = detect_workspace_namespace_issues(st=st)
        codes = [i["code"] for i in issues]
        self.assertIn("direct_app_open_risk", codes)


class TestDeepLinksPreserveWorkspace(unittest.TestCase):
    def test_get_app_url_includes_suite_workspace_daniel(self) -> None:
        from app_registry import get_app_url

        url = get_app_url("applied_intelligence", workspace_id="daniel")
        params = parse_qs(urlparse(url).query)
        self.assertEqual(params.get("suite_workspace", [""])[0], "daniel")

    def test_get_app_url_includes_suite_workspace_ariel(self) -> None:
        from app_registry import get_app_url

        url = get_app_url("future_lens", workspace_id="ariel")
        params = parse_qs(urlparse(url).query)
        self.assertEqual(params.get("suite_workspace", [""])[0], "ariel")

    def test_sample_url_in_context_matches_active_workspace(self) -> None:
        st = _fake_st()
        set_active_workspace_id(st, "ariel")
        ctx = build_account_settings_context(st=st)
        params = parse_qs(urlparse(ctx["sample_app_url"]).query)
        self.assertEqual(params.get("suite_workspace", [""])[0], "ariel")


class TestInitWorkspaceFromQuery(unittest.TestCase):
    def test_init_syncs_query_param_to_session(self) -> None:
        st = _fake_st(query_params={"suite_workspace": "guest"})
        ws = init_suite_workspace(st)
        self.assertEqual(ws, "guest")
        self.assertEqual(get_active_workspace_id(st), "guest")


class TestAccountSummaryEmail(unittest.TestCase):
    def test_account_summary_includes_email(self) -> None:
        os.environ["SUITE_USER_EMAIL"] = "ariel@example.com"
        from suite_user import reset_account_cache

        reset_account_cache()
        from suite_account import account_summary

        summary = account_summary()
        self.assertEqual(summary["email"], "ariel@example.com")
        os.environ.pop("SUITE_USER_EMAIL", None)
        reset_account_cache()


if __name__ == "__main__":
    unittest.main()
