"""Phase A baseball activity feed and project continue priorities."""

from __future__ import annotations

import unittest

from activity_feed import format_activity_message
from activity_store import ActivitySnapshot, _ingest_suite_events
from project_intelligence import _projects_from_events


def _projects_with_events(snapshot: ActivitySnapshot, events: list[dict]) -> list[tuple[int, str, str, str, str]]:
    import project_intelligence as pi

    original = pi.load_all_events
    pi.load_all_events = lambda _limit=500: events  # type: ignore[method-assign, assignment]
    try:
        return _projects_from_events(snapshot)
    finally:
        pi.load_all_events = original


class TestPhaseABaseballActivity(unittest.TestCase):
    def test_player_comparison_feed_line(self) -> None:
        event = {
            "app": "baseball",
            "event": "player_comparison",
            "metrics": {"player_a": "Aaron Judge", "player_b": "Juan Soto"},
        }
        self.assertEqual(
            format_activity_message(event, for_feed=False),
            "Compared Aaron Judge vs Juan Soto",
        )

    def test_draft_prep_feed_line(self) -> None:
        event = {"app": "baseball", "event": "draft_prep", "metrics": {"league": "5x5 Roto"}}
        self.assertIn("draft prep", (format_activity_message(event, for_feed=True) or "").lower())

    def test_trade_analysis_feed_line(self) -> None:
        event = {
            "app": "baseball",
            "event": "trade_analysis",
            "metrics": {"trade": "Judge for Soto"},
        }
        msg = format_activity_message(event, for_feed=True) or ""
        self.assertIn("trade", msg.lower())

    def test_projects_prioritize_draft_over_projection(self) -> None:
        snap = ActivitySnapshot()
        events = [
            {
                "app": "baseball",
                "event": "projection_report",
                "timestamp": "2026-06-01T10:00:00",
                "metrics": {"projection": "Balanced"},
            },
            {
                "app": "baseball",
                "event": "draft_prep",
                "timestamp": "2026-06-01T11:00:00",
                "metrics": {"league": "5x5 Roto"},
            },
        ]
        projects = _projects_with_events(snap, events)
        titles = [p[2] for p in projects if p[1] == "baseball"]
        self.assertTrue(titles)
        self.assertIn("draft", titles[0].lower())

    def test_ingest_counts_baseball_analyses(self) -> None:
        snapshot = ActivitySnapshot()
        events = [
            {
                "app": "baseball",
                "event": "player_comparison",
                "timestamp": "2026-06-01T12:00:00",
                "metrics": {"player_a": "A", "player_b": "B", "player": "A"},
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

        self.assertEqual(snapshot.baseball_analyses_this_week, 1)
        self.assertEqual(snapshot.last_baseball_player, "A")


if __name__ == "__main__":
    unittest.main()
