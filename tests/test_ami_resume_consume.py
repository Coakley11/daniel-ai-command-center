"""AMI return resume consume — manual navigation must win after first return."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from applied_math_return_insight import (
    SESSION_PENDING_KEY,
    SESSION_RETURN_PAGE_KEY,
    _should_apply_ami_return_navigation,
    ami_resume_consumed,
    apply_ami_insight_from_query,
    consume_ami_return_resume,
    hydrate_applied_math_insight_for_session,
    render_suite_applied_math_insight_for_page,
)


class TestAmiResumeConsume(unittest.TestCase):
    def test_consume_clears_query_params_and_preserve(self) -> None:
        st = MagicMock()
        st.session_state = {
            "_ami_insight_return_preserve": True,
            "_suite_resume_insight_hydration_only": True,
        }
        st.query_params = {
            "suite_ami_insight": "ins1",
            "suite_page": "Trend Value",
            "suite_resume": "1",
        }

        ok = consume_ami_return_resume(st, "baseball")

        self.assertTrue(ok)
        self.assertTrue(ami_resume_consumed(st, "baseball"))
        self.assertNotIn("_ami_insight_return_preserve", st.session_state)
        self.assertNotIn("suite_ami_insight", st.query_params)

    def test_user_nav_blocks_ami_return_navigation(self) -> None:
        st = MagicMock()
        st.session_state = {
            "active_page": "Comparison Tool",
            "_suite_last_persisted_page": "Comparison Tool",
            SESSION_RETURN_PAGE_KEY: "Trend Value",
        }
        self.assertFalse(_should_apply_ami_return_navigation(st, "baseball", "Trend Value"))

    def test_apply_insight_does_not_schedule_nav_after_user_nav(self) -> None:
        st = MagicMock()
        st.session_state = {
            "active_page": "Comparison Tool",
            "_suite_last_persisted_page": "Comparison Tool",
        }
        st.query_params = {"suite_ami_insight": "trend1", "suite_page": "Trend Value"}
        trend_insight = {
            "insight_id": "trend1",
            "source_app": "baseball",
            "source_page": "Trend Value",
            "conclusion": "Trend insight",
            "source_state": {
                "source_page": "Trend Value",
                "widget_params": {},
                "entity_params": {"player_label": "Judge"},
            },
        }

        with patch(
            "applied_math_return_insight.load_applied_math_insight",
            return_value=trend_insight,
        ):
            ok = apply_ami_insight_from_query(st, "baseball", force=True)

        self.assertTrue(ok)
        self.assertNotIn("_navigate_to_page", st.session_state)
        self.assertTrue(st.session_state.get("_ami_insight_return_preserve"))

    def test_hydrate_after_consume_uses_session_not_url(self) -> None:
        st = MagicMock()
        st.session_state = {
            "_ami_resume_consumed_baseball": True,
            SESSION_PENDING_KEY: {
                "insight_id": "trend1",
                "source_page": "Trend Value",
                "conclusion": "Still here",
            },
        }
        st.query_params = {"suite_ami_insight": "trend1", "suite_page": "Trend Value"}

        with patch("applied_math_return_insight.apply_ami_insight_from_query") as mock_apply:
            ok = hydrate_applied_math_insight_for_session(st, "baseball")

        self.assertTrue(ok)
        mock_apply.assert_not_called()

    def test_render_consumes_resume_after_first_card(self) -> None:
        st = MagicMock()
        st.session_state = {
            SESSION_PENDING_KEY: {
                "insight_id": "trend1",
                "source_app": "baseball",
                "source_page": "Trend Value",
                "conclusion": "Trend insight",
            },
            SESSION_RETURN_PAGE_KEY: "Trend Value",
            "_ami_insight_return_preserve": True,
        }
        st.query_params = {"suite_ami_insight": "trend1", "suite_page": "Trend Value"}

        with patch(
            "applied_math_return_insight.render_applied_math_insight_panel",
            return_value=True,
        ):
            ok = render_suite_applied_math_insight_for_page(
                st,
                source_app="baseball",
                source_page="Trend Value",
            )

        self.assertTrue(ok)
        self.assertTrue(ami_resume_consumed(st, "baseball"))
        self.assertNotIn("suite_ami_insight", st.query_params)


if __name__ == "__main__":
    unittest.main()
