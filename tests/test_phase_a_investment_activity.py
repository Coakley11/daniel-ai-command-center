"""Phase A investment activity feed and directory priority."""

from __future__ import annotations

import unittest

from activity_feed import format_activity_message, investment_directory_rank
from activity_store import ActivitySnapshot, _ingest_suite_events


class TestPhaseAInvestmentActivity(unittest.TestCase):
    def test_goal_feed_line(self) -> None:
        event = {
            "app": "investment",
            "event": "investment_goal_selected",
            "metrics": {"goal_title": "Retirement"},
        }
        self.assertEqual(format_activity_message(event), "Selected investment goal: Retirement")

    def test_portfolio_created_feed_line(self) -> None:
        event = {
            "app": "investment",
            "event": "portfolio_created",
            "metrics": {"holdings_count": 6},
        }
        self.assertIn("6 holdings", format_activity_message(event) or "")

    def test_directory_rank_prefers_health_over_goal(self) -> None:
        self.assertGreater(
            investment_directory_rank("portfolio_health_checked"),
            investment_directory_rank("investment_goal_selected"),
        )

    def test_ingest_sets_directory_primary(self) -> None:
        snapshot = ActivitySnapshot()
        events = [
            {
                "app": "investment",
                "event": "investment_goal_selected",
                "timestamp": "2026-06-01T10:00:00",
                "metrics": {"goal_title": "Retirement"},
            },
            {
                "app": "investment",
                "event": "portfolio_health_checked",
                "timestamp": "2026-06-01T11:00:00",
                "metrics": {"review_type": "Good", "score": 72},
            },
        ]

        def fake_load(_limit: int = 500):
            return events

        import activity_store as store

        original = store.load_all_events
        store.load_all_events = fake_load  # type: ignore[method-assign]
        try:
            _ingest_suite_events(snapshot)
        finally:
            store.load_all_events = original

        self.assertIn("portfolio health check", snapshot.investment_directory_primary.lower())
        self.assertEqual(snapshot.last_investment_goal, "Retirement")


if __name__ == "__main__":
    unittest.main()
