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

    def test_valuation_eligible_and_strict_scope(self) -> None:
        insight = {"source_app": "baseball", "source_page": "Valuation", "conclusion": "test"}
        scope = insight_page_scope_decision("baseball", "Valuation", insight)
        self.assertTrue(scope["should_render_insight_on_page"])
        self.assertIsNone(scope["render_skip_reason"])
        self.assertFalse(should_render_insight_on_page("baseball", "ML Predictions", insight))

    def test_ml_predictions_eligible_and_strict_scope(self) -> None:
        insight = {"source_app": "baseball", "source_page": "ML Predictions", "conclusion": "test"}
        scope = insight_page_scope_decision("baseball", "ML Predictions", insight)
        self.assertTrue(scope["should_render_insight_on_page"])
        self.assertFalse(should_render_insight_on_page("baseball", "Valuation", insight))

    def test_valuation_not_eligible_before_fix_regression(self) -> None:
        """Regression: previously skipped with current_page_not_eligible."""
        insight = {"source_app": "baseball", "source_page": "Valuation"}
        scope = insight_page_scope_decision("baseball", "Valuation", insight)
        self.assertNotEqual(scope.get("render_skip_reason"), "current_page_not_eligible ('Valuation')")
        self.assertTrue(scope["should_render_insight_on_page"])

    def test_fantasy_standings_eligible_and_strict_scope(self) -> None:
        insight = {"source_app": "baseball", "source_page": "Fantasy Standings Tracker", "conclusion": "test"}
        scope = insight_page_scope_decision("baseball", "Fantasy Standings Tracker", insight)
        self.assertTrue(scope["should_render_insight_on_page"])
        self.assertIsNone(scope["render_skip_reason"])
        self.assertFalse(should_render_insight_on_page("baseball", "Fantasy Sleepers & Busts", insight))
        self.assertNotEqual(
            scope.get("render_skip_reason"),
            "current_page_not_eligible ('Fantasy Standings Tracker')",
        )

    def test_fantasy_sleepers_eligible_and_strict_scope(self) -> None:
        insight = {"source_app": "baseball", "source_page": "Fantasy Sleepers & Busts", "conclusion": "test"}
        self.assertTrue(should_render_insight_on_page("baseball", "Fantasy Sleepers & Busts", insight))
        self.assertFalse(should_render_insight_on_page("baseball", "Fantasy Lineup Assistant", insight))

    def test_fantasy_lineup_eligible_and_strict_scope(self) -> None:
        insight = {"source_app": "baseball", "source_page": "Fantasy Lineup Assistant", "conclusion": "test"}
        self.assertTrue(should_render_insight_on_page("baseball", "Fantasy Lineup Assistant", insight))
        self.assertFalse(should_render_insight_on_page("baseball", "Leaderboards", insight))

    def test_leaderboards_eligible_and_strict_scope(self) -> None:
        insight = {"source_app": "baseball", "source_page": "Leaderboards", "conclusion": "test"}
        self.assertTrue(should_render_insight_on_page("baseball", "Leaderboards", insight))
        self.assertFalse(should_render_insight_on_page("baseball", "Fantasy Standings Tracker", insight))

    def test_emoji_fantasy_standings_source_page_normalizes(self) -> None:
        insight = {"source_app": "baseball", "source_page": "📊 Fantasy Standings Tracker", "conclusion": "test"}
        self.assertTrue(should_render_insight_on_page("baseball", "Fantasy Standings Tracker", insight))

    def test_fantasy_standings_alias_normalizes(self) -> None:
        insight = {"source_app": "baseball", "source_page": "fantasy standings tracker", "conclusion": "test"}
        scope = insight_page_scope_decision("baseball", "Fantasy Standings Tracker", insight)
        self.assertEqual(scope["source_page_normalized"], "Fantasy Standings Tracker")
        self.assertTrue(scope["should_render_insight_on_page"])

    def test_music_backing_coach_page_ids_match(self) -> None:
        insight = {"source_app": "music", "source_page": "backing", "conclusion": "test"}
        scope = insight_page_scope_decision("music", "backing", insight)
        self.assertTrue(scope["should_render_insight_on_page"])
        self.assertEqual(scope["source_page_normalized"], "backing")
        self.assertEqual(scope["current_page_normalized"], "backing")

    def test_music_backing_display_name_matches_coach_id(self) -> None:
        insight = {"source_app": "music", "source_page": "Backing Track Studio", "conclusion": "test"}
        self.assertTrue(should_render_insight_on_page("music", "backing", insight))
        self.assertFalse(should_render_insight_on_page("music", "practice", insight))

    def test_music_backing_hidden_on_picker_and_analysis(self) -> None:
        insight = {
            "source_app": "music",
            "source_page": "backing",
            "source_state": {"widget_params": {"studio_page": "backing"}},
            "conclusion": "test",
        }
        self.assertFalse(should_render_insight_on_page("music", "picker", insight))
        self.assertFalse(should_render_insight_on_page("music", "analysis", insight))
        self.assertFalse(should_render_insight_on_page("music", "custom", insight))

    def test_music_insight_labels(self) -> None:
        from applied_math_return_insight import (
            _insight_loaded_placeholder,
            _insight_panel_title,
        )

        insight = {"source_app": "music", "conclusion": "test"}
        self.assertEqual(_insight_panel_title(insight), "Music Coach Insight")
        self.assertEqual(_insight_loaded_placeholder("music"), "Music Coach insight loaded.")

    def test_music_practice_insight_not_on_picker(self) -> None:
        insight = {
            "source_app": "music",
            "source_page": "practice",
            "source_state": {"widget_params": {"studio_page": "practice"}},
            "conclusion": "test",
        }
        self.assertTrue(should_render_insight_on_page("music", "practice", insight))
        self.assertFalse(should_render_insight_on_page("music", "picker", insight))


if __name__ == "__main__":
    unittest.main()
