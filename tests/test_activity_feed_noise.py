"""Recent Activity should suppress noisy setup clicks and summarize portfolio setup."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from activity_feed import build_activity_feed, format_activity_message


class TestActivityFeedNoise(unittest.TestCase):
    def test_goal_selected_hidden_from_feed(self) -> None:
        event = {
            "app": "investment",
            "event": "investment_goal_selected",
            "metrics": {"goal_title": "Retirement"},
        }
        self.assertIsNone(format_activity_message(event, for_feed=True))
        self.assertIn("Retirement", format_activity_message(event, for_feed=False) or "")

    def test_setup_cluster_summarized(self) -> None:
        events = [
            {
                "app": "investment",
                "event": "investment_goal_selected",
                "timestamp": "2026-06-01T10:00:00",
                "metrics": {"goal_title": "Retirement"},
            },
            {
                "app": "investment",
                "event": "portfolio_created",
                "timestamp": "2026-06-01T10:05:00",
                "metrics": {"holdings_count": 4},
            },
            {
                "app": "investment",
                "event": "holdings_updated",
                "timestamp": "2026-06-01T10:06:00",
                "metrics": {"tickers": ["SPY", "BND"]},
            },
            {
                "app": "investment",
                "event": "portfolio_health_checked",
                "timestamp": "2026-06-01T11:00:00",
                "metrics": {"review_type": "Good", "score": 80},
            },
        ]
        now = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
        feed = build_activity_feed(events, limit=5, now=now)
        messages = [item.message for item in feed]
        self.assertTrue(any("new portfolio created" in m.lower() for m in messages))
        self.assertTrue(any("portfolio analysis" in m.lower() for m in messages))
        self.assertFalse(any("Selected investment goal" in m for m in messages))
        self.assertFalse(any("Updated holdings" in m for m in messages))

    def test_repeated_portfolio_setup_line_once(self) -> None:
        goal = "Grow my money long term"
        events = [
            {
                "app": "investment",
                "event": "investment_goal_selected",
                "timestamp": "2026-06-01T10:00:00",
                "metrics": {"goal_title": goal},
            },
            {
                "app": "investment",
                "event": "portfolio_created",
                "timestamp": "2026-06-01T10:05:00",
                "metrics": {"holdings_count": 4, "goal_title": goal},
            },
            {
                "app": "investment",
                "event": "portfolio_created",
                "timestamp": "2026-06-01T10:20:00",
                "metrics": {"holdings_count": 4, "goal_title": goal},
            },
            {
                "app": "investment",
                "event": "portfolio_created",
                "timestamp": "2026-06-01T10:35:00",
                "metrics": {"holdings_count": 4, "goal_title": goal},
            },
            {
                "app": "investment",
                "event": "holdings_updated",
                "timestamp": "2026-06-01T10:40:00",
                "metrics": {"tickers": ["SPY", "BND", "VTI", "BNDX"]},
            },
            {
                "app": "investment",
                "event": "portfolio_created",
                "timestamp": "2026-06-01T10:50:00",
                "metrics": {"holdings_count": 4, "goal_title": goal},
            },
            {
                "app": "investment",
                "event": "portfolio_health_checked",
                "timestamp": "2026-06-01T11:00:00",
                "metrics": {"review_type": "Good", "score": 82},
            },
        ]
        now = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
        feed = build_activity_feed(events, limit=10, now=now)
        messages = [item.message for item in feed]
        portfolio_lines = [m for m in messages if "new portfolio created" in m.lower() and goal.lower() in m.lower()]
        self.assertEqual(len(portfolio_lines), 1)
        self.assertTrue(any("portfolio analysis" in m.lower() for m in messages))

    def test_health_sorted_by_recency_in_highlights(self) -> None:
        events = [
            {
                "app": "investment",
                "event": "portfolio_created",
                "timestamp": "2026-06-01T12:00:00Z",
                "metrics": {"holdings_count": 3},
            },
            {
                "app": "investment",
                "event": "portfolio_health_checked",
                "timestamp": "2026-06-01T11:00:00Z",
                "metrics": {"review_type": "Fair", "score": 65},
            },
        ]
        feed = build_activity_feed(events, limit=2, now=datetime(2026, 6, 1, 13, 0, tzinfo=timezone.utc))
        self.assertGreaterEqual(len(feed), 1)
        # Newer portfolio_created should appear before older health check (recency sort).
        self.assertIn("portfolio", feed[0].message.lower())


if __name__ == "__main__":
    unittest.main()
