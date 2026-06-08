"""AMI return render for Fantasy cluster pages."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from applied_math_return_insight import (
    SESSION_PENDING_KEY,
    insight_page_scope_decision,
    render_suite_applied_math_insight_for_page,
    should_render_insight_on_page,
)

_STANDINGS_FILTERS = {
    "standings_scoring_format": "Points League",
    "standings_stats_source": "MLB API Auto-Fetch",
    "standings_api_season": 2025,
}

_SLEEPERS_FILTERS = {
    "fantasy_market_window": 4,
    "fantasy_market_format": "Points League",
    "fantasy_market_top_n": 20,
}

_LINEUP_FILTERS = {
    "lineup_format": "Head-to-Head Categories",
    "lineup_bench_rows": 15,
}


class TestFantasyClusterAmiReturn(unittest.TestCase):
    def _insight(self, page: str, filters: dict) -> dict:
        return {
            "insight_id": f"ami-{page[:8]}",
            "source_app": "baseball",
            "source_page": page,
            "conclusion": "Fantasy insight",
            "source_state": {
                "source_app": "baseball",
                "source_page": page,
                "filter_params": dict(filters),
            },
        }

    def test_standings_renders_only_on_standings_page(self) -> None:
        insight = self._insight("Fantasy Standings Tracker", _STANDINGS_FILTERS)
        self.assertTrue(should_render_insight_on_page("baseball", "Fantasy Standings Tracker", insight))
        self.assertFalse(should_render_insight_on_page("baseball", "Fantasy Sleepers & Busts", insight))
        scope = insight_page_scope_decision("baseball", "Fantasy Standings Tracker", insight)
        self.assertNotEqual(
            scope.get("render_skip_reason"),
            "current_page_not_eligible ('Fantasy Standings Tracker')",
        )

    def test_sleepers_renders_only_on_sleepers_page(self) -> None:
        insight = self._insight("Fantasy Sleepers & Busts", _SLEEPERS_FILTERS)
        self.assertTrue(should_render_insight_on_page("baseball", "Fantasy Sleepers & Busts", insight))
        self.assertFalse(should_render_insight_on_page("baseball", "Fantasy Standings Tracker", insight))

    def test_lineup_renders_only_on_lineup_page(self) -> None:
        insight = self._insight("Fantasy Lineup Assistant", _LINEUP_FILTERS)
        self.assertTrue(should_render_insight_on_page("baseball", "Fantasy Lineup Assistant", insight))
        self.assertFalse(should_render_insight_on_page("baseball", "Fantasy Sleepers & Busts", insight))

    def test_navigate_away_hides_card_return_page_shows_it(self) -> None:
        insight = self._insight("Fantasy Standings Tracker", _STANDINGS_FILTERS)
        st = MagicMock()
        st.session_state = {SESSION_PENDING_KEY: insight}

        with patch(
            "applied_math_return_insight.render_applied_math_insight_panel",
            return_value=True,
        ) as mock_panel:
            self.assertFalse(
                render_suite_applied_math_insight_for_page(
                    st,
                    source_app="baseball",
                    source_page="Fantasy Sleepers & Busts",
                )
            )
            self.assertTrue(
                render_suite_applied_math_insight_for_page(
                    st,
                    source_app="baseball",
                    source_page="Fantasy Standings Tracker",
                )
            )
        self.assertEqual(mock_panel.call_count, 1)


if __name__ == "__main__":
    unittest.main()
