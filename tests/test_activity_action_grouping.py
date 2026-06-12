"""Tests for activity action grouping."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from activity_feed import build_activity_dashboard


class TestActivityActionGrouping(unittest.TestCase):
    def test_ten_portfolio_analyses_collapse_to_one_line(self) -> None:
        now = datetime(2026, 6, 12, 18, 0, tzinfo=timezone.utc)
        events = [
            {
                "app": "investment",
                "event": "portfolio_health_checked",
                "timestamp": f"2026-06-12T{17 - i // 2:02d}:{(i * 5) % 60:02d}:00Z",
                "metrics": {"score": 70 + i, "review_type": "Fair"},
            }
            for i in range(10)
        ]
        dash = build_activity_dashboard(events, now=now)
        portfolio_lines = [m for m in dash.today_summaries if "Portfolio Analysis" in m]
        self.assertTrue(any("(10 runs)" in m for m in portfolio_lines))
        self.assertLessEqual(
            sum(1 for m in dash.today_summaries if m.startswith("Portfolio Analysis") and "(10 runs)" not in m),
            1,
        )
        self.assertIsNotNone(dash.feed_trace)
        assert dash.feed_trace is not None
        self.assertGreaterEqual(dash.feed_trace.get("duplicate_events_collapsed", 0), 8)


if __name__ == "__main__":
    unittest.main()
