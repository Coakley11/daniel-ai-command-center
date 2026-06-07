"""Tests for Return Insight source_state restore flow."""

from __future__ import annotations

import unittest

from applied_math_return_insight import (
    build_return_resume_key,
    metrics_for_source_app_return,
)


class TestReturnInsightRestore(unittest.TestCase):
    def test_metrics_uses_full_player_labels_from_source_state(self) -> None:
        insight = {
            "insight_id": "abc123",
            "question_id": "q1",
            "source_app": "baseball",
            "source_page": "Comparison Tool",
            "source_state": {
                "source_page": "Comparison Tool",
                "entity_params": {
                    "player_a_label": "Juan Soto (NYY)",
                    "player_b_label": "Aaron Judge (NYY)",
                },
                "widget_params": {
                    "sig_player_a_clean": "Juan Soto (NYY)",
                    "sig_player_b_clean": "Aaron Judge (NYY)",
                },
            },
        }
        m = metrics_for_source_app_return(insight)
        self.assertEqual(m["player_a"], "Juan Soto (NYY)")
        self.assertEqual(m["player_b"], "Aaron Judge (NYY)")
        self.assertEqual(m["page"], "Comparison Tool")

    def test_build_return_resume_key_prefers_compare(self) -> None:
        insight = {
            "source_app": "baseball",
            "source_page": "Comparison Tool",
            "question_id": "q99",
            "source_state": {
                "source_page": "Comparison Tool",
                "entity_params": {
                    "player_a_label": "Juan Soto (NYY)",
                    "player_b_label": "Aaron Judge (NYY)",
                },
            },
        }
        rk = build_return_resume_key(insight)
        self.assertEqual(rk, "compare:Juan Soto (NYY):Aaron Judge (NYY)")


if __name__ == "__main__":
    unittest.main()
