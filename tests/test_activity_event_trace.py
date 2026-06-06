"""Tests for raw baseball event trace (no Continue logic)."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from activity_event_trace import infer_resume_key, raw_baseball_events


class ActivityEventTraceTests(unittest.TestCase):
    def test_infer_resume_key_trend(self) -> None:
        rk = infer_resume_key("player_trend_viewed", {"player": "Lorenzo Cain"})
        self.assertEqual(rk, "trend:Lorenzo Cain")

    def test_infer_resume_key_comparison(self) -> None:
        rk = infer_resume_key(
            "player_comparison",
            {"player_a": "Mike Piazza", "player_b": "Jeff Bagwell"},
        )
        self.assertEqual(rk, "compare:Mike Piazza:Jeff Bagwell")

    @patch("activity_event_trace.load_all_events")
    def test_raw_baseball_events_newest_first(self, load_mock) -> None:
        load_mock.return_value = [
            {
                "app": "baseball",
                "event": "breakout_analysis",
                "timestamp": "2026-06-05T12:00:00",
                "metrics": {},
            },
            {
                "app": "baseball",
                "event": "player_trend_viewed",
                "timestamp": "2026-06-06T14:00:00",
                "metrics": {"player": "Lorenzo Cain"},
            },
            {"app": "investment", "event": "portfolio_health_checked", "timestamp": "2026-06-06T15:00:00"},
        ]
        rows = raw_baseball_events(limit=20)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["event_type"], "player_trend_viewed")
        self.assertEqual(rows[0]["player"], "Lorenzo Cain")
        self.assertEqual(rows[0]["resume_key"], "trend:Lorenzo Cain")
        self.assertEqual(rows[0]["priority"], 58)


if __name__ == "__main__":
    unittest.main()
