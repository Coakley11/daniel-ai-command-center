"""Practice log analysis activity sorting — run B must beat run A on Command Center."""

from __future__ import annotations

import unittest
from datetime import datetime
from unittest.mock import patch

from project_intelligence import (
    _handoff_activity_sort_ts,
    _projects_from_events,
    build_project_continue_cards,
)
from suite_storage import ResumeItem


class TestPracticeLogActivitySort(unittest.TestCase):
    def test_handoff_sort_ts_prefers_report_generated_at(self) -> None:
        metrics = {
            "report_generated_at": "2026-06-29T01:42:00",
            "activity_sort_at": "2026-06-29T01:42:00",
        }
        sort_ts = _handoff_activity_sort_ts(metrics, "2026-06-28T12:00:00")
        self.assertEqual(sort_ts, datetime(2026, 6, 29, 1, 42, 0))

    def test_projects_from_events_picks_latest_run(self) -> None:
        from activity_store import ActivitySnapshot

        events = [
            {
                "app": "music",
                "event": "practice_log_analysis",
                "timestamp": "2026-06-28T12:00:00",
                "metrics": {
                    "question_id": "plog1",
                    "resume_key": "ai:practice_log_analysis:plog1",
                    "handoff_kind": "practice_log_analysis",
                    "analysis_run_id": "run-a",
                    "report_generated_at": "2026-06-28T12:00:00",
                    "activity_sort_at": "2026-06-28T12:00:00",
                    "context": {
                        "user_request": "analyze_practice",
                        "practice_log_summary": {"session_count": 2, "total_minutes": 60},
                    },
                },
            },
            {
                "app": "music",
                "event": "practice_log_analysis",
                "timestamp": "2026-06-28T12:05:00",
                "metrics": {
                    "question_id": "plog1",
                    "resume_key": "ai:practice_log_analysis:plog1",
                    "handoff_kind": "practice_log_analysis",
                    "analysis_run_id": "run-b",
                    "report_generated_at": "2026-06-29T01:42:00",
                    "activity_sort_at": "2026-06-29T01:42:00",
                    "context": {
                        "user_request": "analyze_practice",
                        "practice_log_summary": {"session_count": 3, "total_minutes": 90},
                    },
                },
            },
        ]
        with patch("project_intelligence.load_all_events", return_value=events):
            rows = _projects_from_events(ActivitySnapshot())
        practice_rows = [row for row in rows if row[2] == "Music Practice Log Analysis"]
        self.assertEqual(len(practice_rows), 1)
        metrics = practice_rows[0][6]
        self.assertEqual(metrics.get("analysis_run_id"), "run-b")

    def test_continue_card_prefers_newer_resume_item(self) -> None:
        from activity_store import ActivitySnapshot

        snap = ActivitySnapshot()
        older = ResumeItem(
            app="applied_intelligence",
            item_key="ai:practice_log_analysis:plog1",
            title="Music Practice Log Analysis",
            subtitle="Updated 2026-06-28 12:00 PM — Tenor Saxophone / Say",
            action_url="https://example.test/ami?suite_practice_analysis_run_id=run-a",
            updated_at="2026-06-28T12:00:00",
        )
        newer = ResumeItem(
            app="applied_intelligence",
            item_key="ai:practice_log_analysis:plog1",
            title="Music Practice Log Analysis",
            subtitle="Updated 2026-06-29 01:42 AM — Tenor Saxophone / Say",
            action_url="https://example.test/ami?suite_practice_analysis_run_id=run-b",
            updated_at="2026-06-29T01:42:00",
        )
        meta = {
            "applied_intelligence": {"name": "Applied Intelligence", "url": "https://example.test/ami"},
            "music": {"name": "Music", "url": "https://example.test/music"},
        }
        with patch("project_intelligence._projects_from_events", return_value=[]):
            with patch("project_intelligence.load_active_resume_items", return_value=[older, newer]):
                cards = build_project_continue_cards(snap, limit=6, meta=meta)
        practice_cards = [c for c in cards if c.title == "Music Practice Log Analysis"]
        self.assertEqual(len(practice_cards), 1)
        self.assertIn("run-b", practice_cards[0].action_url)
        self.assertIn("2026-06-29", practice_cards[0].subtitle)


if __name__ == "__main__":
    unittest.main()
