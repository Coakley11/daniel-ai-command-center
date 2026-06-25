"""Command Center surfaces Live Draft / Draft Lab baseball activity."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from activity_feed import _feed_priority, format_activity_message, baseball_directory_rank
from activity_store import (
    ActivitySnapshot,
    _ingest_suite_events,
    _normalize_loaded_event,
    get_app_directory_card,
)
from project_intelligence import _MEANINGFUL_WORKFLOW_EVENTS, _projects_from_events, _raw_event_workflow_candidate


def _production_draft_analysis_event(*, app: str = "baseball-stat-app") -> dict:
    """Payload shape Baseball emits after Analyze Completed Draft."""
    return {
        "app": app,
        "event": "draft_analysis_created",
        "page": "Draft Simulation Test Mode",
        "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(timespec="seconds"),
        "metrics": {
            "teams": ["Daniel", "Ariel"],
            "team_matchup": "Daniel vs Ariel",
            "draft_room_id": "ROOM-ABC123",
            "room_code": "",
            "picks_per_team": 15,
            "feature": "Draft Simulation Test Mode",
            "activity_type": "draft_analysis_created",
            "page": "Draft Simulation Test Mode",
            "workspace_id": "daniel",
            "suite_external_id": "daniel@example.com",
            "draft_section": "team_analysis",
        },
    }


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

    def test_normalize_baseball_stat_app_name(self) -> None:
        raw = _production_draft_analysis_event(app="baseball-stat-app")
        normalized = _normalize_loaded_event(raw)
        self.assertEqual(normalized["app"], "baseball")

    def test_draft_analysis_created_not_unknown_event(self) -> None:
        self.assertIn("draft_analysis_created", _MEANINGFUL_WORKFLOW_EVENTS)
        self.assertIn("draft_analysis_attempted", _MEANINGFUL_WORKFLOW_EVENTS)

    def test_production_payload_workflow_candidate(self) -> None:
        event = _normalize_loaded_event(_production_draft_analysis_event())
        candidate = _raw_event_workflow_candidate(event)
        self.assertIsNotNone(candidate)
        assert candidate is not None
        self.assertEqual(candidate["title"], "Continue Draft Analysis")
        self.assertEqual(candidate["resume_key"], "bb:draft_lab:team:ROOM-ABC123")

    def test_production_payload_continue_and_directory(self) -> None:
        snap = ActivitySnapshot()
        event = _normalize_loaded_event(_production_draft_analysis_event(app="Baseball Analytics"))

        with patch("project_intelligence.load_all_events", return_value=[event]):
            cards = _projects_from_events(snap)
        baseball = [c for c in cards if c[1] == "baseball"]
        self.assertEqual(len(baseball), 1)
        self.assertIn("Draft Analysis", baseball[0][2])
        self.assertIn("Daniel vs Ariel", baseball[0][3] or "")

        with patch("activity_store.load_all_events", return_value=[event]):
            _ingest_suite_events(snap)
        card = get_app_directory_card(snap, "baseball")
        joined = " ".join(card.highlights)
        self.assertIn("Daniel vs Ariel", joined)

    def test_command_center_continue_generates_draft_lab_url(self) -> None:
        from project_intelligence import build_project_continue_cards

        snap = ActivitySnapshot()
        event = _normalize_loaded_event(_production_draft_analysis_event())
        with patch("project_intelligence.load_all_events", return_value=[event]):
            with patch("project_intelligence.load_active_resume_items", return_value=[]):
                cards = build_project_continue_cards(snap, limit=6, meta={
                    "baseball": {"name": "Baseball Analytics", "url": "https://example.test"},
                })
        baseball = [c for c in cards if c.app_key == "baseball"]
        self.assertTrue(baseball)
        url = baseball[0].action_url
        self.assertIn("suite_page=Draft+Simulation+Test+Mode", url)
        self.assertIn("suite_draft_room=ROOM-ABC123", url)
        self.assertIn("bb%3Adraft_lab%3Ateam%3AROOM-ABC123", url)

        for app_name in ("baseball-stat-app", "Baseball Analytics", "baseball"):
            event = _normalize_loaded_event(_production_draft_analysis_event(app=app_name))
            msg = format_activity_message(event, for_feed=True)
            self.assertIn("Daniel vs Ariel", msg or "", msg=f"filtered for app={app_name!r}")


if __name__ == "__main__":
    unittest.main()
