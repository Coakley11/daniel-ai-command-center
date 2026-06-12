"""Activity dashboard: highlights, rollups, recency sort."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from activity_feed import build_activity_dashboard


class TestActivityDashboard(unittest.TestCase):
    def test_comparison_rollup_in_today_work(self) -> None:
        now = datetime(2026, 6, 3, 18, 0, tzinfo=timezone.utc)
        events = [
            {
                "app": "baseball",
                "event": "player_comparison",
                "timestamp": "2026-06-03T17:50:00Z",
                "metrics": {"player_a": "A", "player_b": "B"},
            },
            {
                "app": "baseball",
                "event": "player_comparison",
                "timestamp": "2026-06-03T17:55:00Z",
                "metrics": {"player_a": "C", "player_b": "D"},
            },
            {
                "app": "baseball",
                "event": "player_comparison",
                "timestamp": "2026-06-03T17:58:00Z",
                "metrics": {"player_a": "E", "player_b": "F"},
            },
        ]
        dash = build_activity_dashboard(events, now=now)
        self.assertTrue(any("Player Comparison (3 runs)" in m for m in dash.today_summaries))
        self.assertFalse(dash.highlights)

    def test_milestone_portfolio_created_in_today_work(self) -> None:
        now = datetime(2026, 6, 3, 18, 0, tzinfo=timezone.utc)
        events = [
            {
                "app": "investment",
                "event": "portfolio_created",
                "timestamp": "2026-06-03T12:00:00Z",
                "metrics": {"holdings_count": 3},
            },
            {
                "app": "investment",
                "event": "portfolio_health_checked",
                "timestamp": "2026-06-03T11:00:00Z",
                "metrics": {"review_type": "Fair", "score": 65},
            },
        ]
        dash = build_activity_dashboard(events, now=now)
        self.assertTrue(any("New portfolio created" in m for m in dash.today_summaries))
        self.assertTrue(any("Portfolio Analysis" in m for m in dash.today_summaries))

    def test_today_summary_practice_songs(self) -> None:
        now = datetime(2026, 6, 3, 18, 0, tzinfo=timezone.utc)
        events = [
            {
                "app": "music",
                "event": "practice",
                "timestamp": "2026-06-03T17:30:00Z",
                "metrics": {"song": "Piano Man", "minutes": 10},
            },
        ]
        dash = build_activity_dashboard(events, now=now)
        self.assertTrue(any("Piano Man" in s for s in dash.today_summaries))


if __name__ == "__main__":
    unittest.main()
