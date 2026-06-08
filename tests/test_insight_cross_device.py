"""Cross-device Applied Math insight hydration tests."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from applied_math_return_insight import (
    SESSION_DISMISSED_KEY,
    SESSION_PENDING_KEY,
    apply_ami_insight_from_query,
    dismiss_applied_math_insight,
    hydrate_applied_math_insight_for_session,
)


class TestInsightCrossDeviceHydrate(unittest.TestCase):
    def test_hydrate_from_cloud_saved_items(self) -> None:
        st = MagicMock()
        st.session_state = {}
        st.query_params = {}
        cloud_insight = {
            "insight_id": "ins123",
            "question_id": "q1",
            "source_app": "baseball",
            "source_page": "Comparison Tool",
            "conclusion": "Cabrera leads in HR profile.",
            "source_state": {
                "source_page": "Comparison Tool",
                "widget_params": {"compare_stat": "HR", "compare_x_axis_mode": "Age"},
            },
        }

        with patch(
            "applied_math_return_insight.load_latest_applied_math_insight_for_app",
            return_value=cloud_insight,
        ), patch(
            "applied_math_return_insight.apply_return_source_state",
        ) as mock_apply:
            ok = hydrate_applied_math_insight_for_session(st, "baseball")

        self.assertTrue(ok)
        self.assertEqual(st.session_state[SESSION_PENDING_KEY]["insight_id"], "ins123")
        self.assertTrue(st.session_state.get("_ami_insight_loaded_from_cloud"))
        mock_apply.assert_called_once()

    def test_hydrate_skips_dismissed_insight_in_session(self) -> None:
        st = MagicMock()
        st.session_state = {
            SESSION_PENDING_KEY: {
                "insight_id": "gone1",
                "conclusion": "Old insight",
            },
            SESSION_DISMISSED_KEY: ["gone1"],
        }
        st.query_params = {}

        with patch(
            "applied_math_return_insight.load_latest_applied_math_insight_for_app",
            return_value={},
        ):
            ok = hydrate_applied_math_insight_for_session(st, "baseball")

        self.assertFalse(ok)
        self.assertNotIn(SESSION_PENDING_KEY, st.session_state)

    def test_url_hydrate_reloads_after_workspace_overwrite(self) -> None:
        """Regression: cloud workspace restore must not block URL insight re-hydrate."""
        st = MagicMock()
        st.session_state = {
            "_ami_hydrated_insight_id": "cmp123",
            SESSION_PENDING_KEY: {
                "insight_id": "trend999",
                "source_app": "baseball",
                "source_page": "Trend Value",
                "conclusion": "Old trend insight",
            },
        }
        st.query_params = {"suite_ami_insight": "cmp123", "suite_page": "Comparison Tool"}
        comparison_insight = {
            "insight_id": "cmp123",
            "source_app": "baseball",
            "source_page": "Comparison Tool",
            "conclusion": "Comparison insight conclusion",
            "source_state": {
                "source_page": "Comparison Tool",
                "entity_params": {"player_a_label": "A", "player_b_label": "B"},
                "widget_params": {},
            },
        }

        with patch(
            "applied_math_return_insight.load_applied_math_insight",
            return_value=comparison_insight,
        ), patch("applied_math_return_insight.apply_return_source_state"):
            ok = apply_ami_insight_from_query(st, "baseball", force=True)

        self.assertTrue(ok)
        self.assertEqual(st.session_state[SESSION_PENDING_KEY]["insight_id"], "cmp123")
        self.assertEqual(st.session_state[SESSION_PENDING_KEY]["source_page"], "Comparison Tool")
        self.assertTrue(st.session_state.get("_ami_insight_return_preserve"))

    def test_dismiss_marks_insight_id(self) -> None:
        st = MagicMock()
        st.session_state = {
            SESSION_PENDING_KEY: {
                "insight_id": "abc",
                "conclusion": "Test",
            }
        }
        dismiss_applied_math_insight(st)
        self.assertNotIn(SESSION_PENDING_KEY, st.session_state)
        self.assertEqual(st.session_state[SESSION_DISMISSED_KEY], ["abc"])
        self.assertTrue(st.session_state.get("_suite_persist_insight_dirty"))


if __name__ == "__main__":
    unittest.main()
