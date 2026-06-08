"""Strict Applied Math insight page scope decision tests."""

from __future__ import annotations

import unittest

from applied_math_return_insight import insight_page_scope_decision, should_render_insight_on_page


class TestInsightPageScopeDecision(unittest.TestCase):
    def test_trend_insight_strict_on_trend_only(self) -> None:
        insight = {"source_app": "baseball", "source_page": "Trend Value"}
        scope = insight_page_scope_decision("baseball", "Trend Value", insight)
        self.assertTrue(scope["should_render_insight_on_page"])
        self.assertEqual(scope["source_page_normalized"], "Trend Value")
        self.assertEqual(scope["current_page_normalized"], "Trend Value")
        self.assertIsNone(scope["render_skip_reason"])

        scope_cmp = insight_page_scope_decision("baseball", "Comparison Tool", insight)
        self.assertFalse(scope_cmp["should_render_insight_on_page"])
        self.assertIn("normalized_page_mismatch", scope_cmp["render_skip_reason"] or "")
        self.assertFalse(should_render_insight_on_page("baseball", "Comparison Tool", insight))

    def test_missing_source_page_never_renders(self) -> None:
        insight = {"source_app": "baseball"}
        scope = insight_page_scope_decision("baseball", "Trend Value", insight)
        self.assertFalse(scope["should_render_insight_on_page"])
        self.assertEqual(scope["render_skip_reason"], "missing_normalized_source_page")

    def test_chart_snapshot_resolves_source_page(self) -> None:
        insight = {
            "source_app": "baseball",
            "source_state": {"chart_params": {"chart_snapshot": {"page": "Trend Value"}}},
        }
        scope = insight_page_scope_decision("baseball", "Trend Value", insight)
        self.assertTrue(scope["should_render_insight_on_page"])
        self.assertEqual(scope["source_page_normalized"], "Trend Value")


if __name__ == "__main__":
    unittest.main()
