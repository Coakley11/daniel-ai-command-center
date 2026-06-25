"""Command Center surfaces Live Draft / Draft Lab baseball activity."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from activity_feed import _feed_priority, format_activity_message, baseball_directory_rank
from activity_store import ActivitySnapshot, _ingest_suite_events, get_app_directory_card
from project_intelligence import _projects_from_events


def _draft_event(event: str, *, ts: str, matchup: str = "Daniel vs Ariel") -> dict:
    return {
        "app": "baseball",
        "event": event,
        "page": "Live Draft Room" if "analysis" not in event else "Draft Simulation Test Mode",
        "timestamp": ts,
        "metrics": {
            "team_matchup": matchup,
            "teams": ["Daniel", "Ariel"],
            "draft_room_id": "ROOM-ABC123",
            "feature": "Live Draft Room",
        },
    }


class TestBaseballDraftActivityFeed(unittest.TestCase):
    def test_recent_feed_includes_completed_draft(self) -> None:
        event = _draft_event("completed_live_draft", ts="2026-06-22T18:00:00Z")
        msg = format_activity_message(event, for_feed=True)
        self.assertIsNotNone(msg)
        assert msg is not None
        self.assertIn("Daniel vs Ariel", msg)

    def test_draft_analysis_feed_line(self) -> None:
        event = _draft_event("draft_analysis_created", ts="2026-06-22T19:00:00Z")
        msg = format_activity_message(event, for_feed=True)
        self.assertIn("Draft analysis ready", msg or "")
        self.assertIn("Daniel vs Ariel", msg or "")

    def test_draft_activity_outranks_page_view(self) -> None:
        draft = _draft_event("draft_analysis_created", ts="2026-06-21T10:00:00Z")
        page = {
            "app": "baseball",
            "event": "page_view",
            "page": "Trend Value",
            "timestamp": "2026-06-22T12:00:00Z",
            "metrics": {},
        }
        self.assertGreater(_feed_priority(draft), _feed_priority(page))

    def test_continue_card_from_completed_draft(self) -> None:
        snap = ActivitySnapshot()
        recent = (datetime.now() - timedelta(hours=2)).isoformat(timespec="seconds")
        events = [_draft_event("completed_live_draft", ts=recent)]
        with patch("project_intelligence.load_all_events", return_value=events):
            cards = _projects_from_events(snap)
        baseball = [c for c in cards if c[1] == "baseball"]
        self.assertEqual(len(baseball), 1)
        self.assertIn("Review completed draft", baseball[0][2])
        self.assertEqual(baseball[0][4], "bb:live_draft:ROOM-ABC123")

    def test_draft_analysis_continue_outranks_draft_prep(self) -> None:
        snap = ActivitySnapshot()
        recent = (datetime.now() - timedelta(hours=1)).isoformat(timespec="seconds")
        older = (datetime.now() - timedelta(hours=3)).isoformat(timespec="seconds")
        events = [
            {
                "app": "baseball",
                "event": "draft_prep",
                "timestamp": older,
                "metrics": {"league": "5x5 Roto"},
            },
            _draft_event("draft_analysis_created", ts=recent),
        ]
        with patch("project_intelligence.load_all_events", return_value=events):
            cards = _projects_from_events(snap)
        baseball = [c for c in cards if c[1] == "baseball"]
        self.assertTrue(baseball)
        self.assertGreaterEqual(baseball[0][0], 63)
        self.assertIn("Draft Analysis", baseball[0][2])

    def test_app_directory_shows_draft_analysis(self) -> None:
        snap = ActivitySnapshot()

        def fake_load(_limit: int = 500):
            return [_draft_event("draft_analysis_created", ts="2026-06-22T19:00:00Z")]

        with patch("activity_store.load_all_events", fake_load):
            _ingest_suite_events(snap)
        card = get_app_directory_card(snap, "baseball")
        joined = " ".join(card.highlights)
        self.assertIn("Daniel vs Ariel", joined)

    def test_baseball_directory_rank_prefers_analysis(self) -> None:
        self.assertGreater(
            baseball_directory_rank("draft_analysis_created"),
            baseball_directory_rank("draft_prep"),
        )


if __name__ == "__main__":
    unittest.main()
