"""Cross-device Applied Math insight hydration tests."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from applied_math_return_insight import (
    SESSION_DISMISSED_KEY,
    SESSION_PENDING_KEY,
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
