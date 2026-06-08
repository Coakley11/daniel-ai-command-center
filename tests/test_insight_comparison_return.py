"""Comparison Tool Applied Math insight return path tests."""

from __future__ import annotations

import unittest

from applied_math_return_insight import (
    build_return_resume_key,
    insight_page_scope_decision,
    should_render_insight_on_page,
)


class TestComparisonInsightReturn(unittest.TestCase):
    def test_comparison_resume_key_from_entity_player_labels(self) -> None:
        insight = {
            "source_app": "baseball",
            "source_page": "Comparison Tool",
            "source_state": {
                "source_page": "Comparison Tool",
                "entity_params": {
                    "player_a": "Judge",
                    "player_b": "Soto",
                },
            },
        }
        rk = build_return_resume_key(insight)
        self.assertEqual(rk, "compare:Judge:Soto")

    def test_comparison_insight_renders_only_on_comparison_page(self) -> None:
        insight = {
            "source_app": "baseball",
            "source_page": "Comparison Tool",
            "conclusion": "Test",
            "source_state": {
                "source_page": "Comparison Tool",
                "entity_params": {"player_a_label": "A", "player_b_label": "B"},
            },
        }
        self.assertTrue(should_render_insight_on_page("baseball", "Comparison Tool", insight))
        self.assertFalse(should_render_insight_on_page("baseball", "Trend Value", insight))
        scope = insight_page_scope_decision("baseball", "Comparison Tool", insight)
        self.assertEqual(scope["source_page_normalized"], "Comparison Tool")
        self.assertTrue(scope["should_render_insight_on_page"])


if __name__ == "__main__":
    unittest.main()
