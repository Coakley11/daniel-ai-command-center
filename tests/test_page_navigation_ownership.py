"""Page navigation ownership — startup lock and post-AMI return."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from applied_math_return_insight import (
    SESSION_PENDING_KEY,
    SESSION_RETURN_PAGE_KEY,
    ami_return_navigation_active,
    hydrate_applied_math_insight_for_session,
    maybe_consume_ami_return_on_page_match,
    reconcile_stale_page_navigation,
)
from suite_user_persistence import (
    SESSION_USER_OWNED_PAGE_KEY,
    _user_page_blocks_cloud_overwrite,
    claim_user_page_ownership,
    sync_cloud_workspace_before_sidebar,
)


class TestPageNavigationOwnership(unittest.TestCase):
    def test_cloud_hydrate_does_not_force_navigation(self) -> None:
        st = MagicMock()
        st.session_state = {}
        st.query_params = {}
        cloud_insight = {
            "insight_id": "trend1",
            "source_app": "baseball",
            "source_page": "Trend Value",
            "conclusion": "Trend insight",
            "source_state": {"source_page": "Trend Value", "widget_params": {}},
        }

        with patch(
            "applied_math_return_insight.load_latest_applied_math_insight_for_app",
            return_value=cloud_insight,
        ), patch(
            "applied_math_return_insight.sync_dismissed_insights_from_cloud",
        ), patch(
            "applied_math_return_insight.apply_return_source_state",
        ) as mock_apply:
            ok = hydrate_applied_math_insight_for_session(st, "baseball")

        self.assertTrue(ok)
        self.assertNotIn("_navigate_to_page", st.session_state)
        mock_apply.assert_not_called()

    def test_reconcile_clears_stale_navigate_to_page(self) -> None:
        st = MagicMock()
        st.session_state = {
            "_navigate_to_page": "Trend Value",
            "_skip_page_restore_for": "Trend Value",
            "_suite_cloud_target_page": "Trend Value",
        }
        st.query_params = {}

        reconcile_stale_page_navigation(st, "baseball")

        self.assertNotIn("_navigate_to_page", st.session_state)
        self.assertNotIn("_skip_page_restore_for", st.session_state)
        self.assertNotIn("_suite_cloud_target_page", st.session_state)

    def test_reconcile_keeps_nav_during_active_ami_return(self) -> None:
        st = MagicMock()
        st.session_state = {
            "_navigate_to_page": "Trend Value",
            "_ami_insight_return_preserve": True,
        }
        st.query_params = {"suite_ami_insight": "ins1"}

        reconcile_stale_page_navigation(st, "baseball")

        self.assertEqual(st.session_state.get("_navigate_to_page"), "Trend Value")

    def test_consume_on_page_match_without_render(self) -> None:
        st = MagicMock()
        st.session_state = {
            SESSION_RETURN_PAGE_KEY: "Trend Value",
            SESSION_PENDING_KEY: {
                "insight_id": "t1",
                "source_page": "Trend Value",
                "conclusion": "ok",
            },
            "_ami_insight_return_preserve": True,
            "_ami_insight_hydrate_source": "url",
        }
        st.query_params = {"suite_ami_insight": "t1"}

        ok = maybe_consume_ami_return_on_page_match(st, "baseball", current_page="Trend Value")

        self.assertTrue(ok)
        self.assertTrue(st.session_state.get("_ami_resume_consumed_baseball"))

    def test_user_owned_page_blocks_cloud_overwrite(self) -> None:
        st = MagicMock()
        st.session_state = {
            SESSION_USER_OWNED_PAGE_KEY: "Comparison Tool",
            "active_page": "Comparison Tool",
            "main_sidebar_page": "Comparison Tool",
        }
        self.assertTrue(_user_page_blocks_cloud_overwrite(st, "Trend Value"))
        self.assertFalse(_user_page_blocks_cloud_overwrite(st, "Comparison Tool"))

    def test_claim_user_page_clears_stale_navigate(self) -> None:
        st = MagicMock()
        st.session_state = {"_navigate_to_page": "Trend Value"}
        st.query_params = {}

        claim_user_page_ownership(st, "baseball", "Comparison Tool")

        self.assertEqual(st.session_state.get(SESSION_USER_OWNED_PAGE_KEY), "Comparison Tool")
        self.assertNotIn("_navigate_to_page", st.session_state)

    def test_page_sync_skips_when_user_owns_different_page(self) -> None:
        st = MagicMock()
        st.session_state = {
            SESSION_USER_OWNED_PAGE_KEY: "Comparison Tool",
            "active_page": "Comparison Tool",
            "main_sidebar_page": "Comparison Tool",
        }
        cloud_state = {"active_page": "Trend Value", "page_filter_state": {}}
        applied: list[dict] = []

        with patch("suite_cloud_state.has_resume_query_params", return_value=False), patch(
            "suite_cloud_state.load_cloud_full_session",
            return_value=(cloud_state, "2026-06-08T16:00:00+00:00"),
        ), patch(
            "suite_user_persistence._load_raw",
            return_value=({"active_page": "Comparison Tool"}, None, "2026-06-08T12:00:00+00:00"),
        ):
            ok = sync_cloud_workspace_before_sidebar(
                st,
                "baseball",
                apply_state=lambda _s, state: applied.append(state),
            )

        self.assertFalse(ok)
        self.assertEqual(applied, [])


if __name__ == "__main__":
    unittest.main()
