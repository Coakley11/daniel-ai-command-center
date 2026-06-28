"""Command Center Continue / Recent AMI for practice log analysis handoff."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from ami_recent_dashboard import load_recent_ami_questions
from project_intelligence import (
    _practice_log_analysis_workflow,
    _projects_from_events,
    build_project_continue_cards,
)
from suite_storage import ResumeItem


class TestPracticeLogCcContinue(unittest.TestCase):
    def test_practice_log_analysis_workflow_title(self) -> None:
        ts = datetime(2026, 6, 27, 12, 0)
        wf = _practice_log_analysis_workflow(
            "music",
            {
                "question_id": "abc123",
                "resume_key": "ai:practice_log_analysis:abc123",
                "handoff_kind": "practice_log_analysis",
                "display_category": "analysis_handoff",
                "context": {
                    "user_request": "analyze_practice",
                    "display_category": "analysis_handoff",
                    "handoff_kind": "practice_log_analysis",
                    "practice_log_summary": {"session_count": 2, "total_minutes": 60},
                },
            },
            ts,
            ts.isoformat(),
        )
        self.assertIsNotNone(wf)
        assert wf is not None
        self.assertEqual(wf["title"], "Music Practice Log Analysis")
        self.assertEqual(wf["resume_key"], "ai:practice_log_analysis:abc123")

    def test_projects_from_events_includes_practice_log_analysis(self) -> None:
        from activity_store import ActivitySnapshot

        events = [
            {
                "app": "music",
                "event": "practice_log_analysis",
                "timestamp": "2026-06-27T12:00:00+00:00",
                "metrics": {
                    "question_id": "plog1",
                    "resume_key": "ai:practice_log_analysis:plog1",
                    "handoff_kind": "practice_log_analysis",
                    "display_category": "analysis_handoff",
                    "context": {
                        "user_request": "analyze_practice",
                        "practice_log_summary": {"session_count": 2, "total_minutes": 60},
                    },
                },
            }
        ]
        with patch("project_intelligence.load_all_events", return_value=events):
            rows = _projects_from_events(ActivitySnapshot())
        titles = [row[2] for row in rows]
        self.assertIn("Music Practice Log Analysis", titles)

    def test_continue_cards_include_practice_log_analysis(self) -> None:
        from activity_store import ActivitySnapshot

        import json

        snap = ActivitySnapshot()
        ctx = {
            "user_request": "analyze_practice",
            "display_category": "analysis_handoff",
            "handoff_kind": "practice_log_analysis",
            "practice_log_summary": {"session_count": 2, "total_minutes": 60},
        }
        items = [
            ResumeItem(
                app="applied_intelligence",
                item_key="ai:practice_log_analysis:plog1",
                title="Music Practice Log Analysis",
                subtitle="Analyze my practice history\n__ctx_json__:" + json.dumps(ctx),
                action_url="https://example.test/ami",
                updated_at=datetime.now().isoformat(timespec="seconds"),
            ),
        ]
        meta = {
            "applied_intelligence": {"name": "Applied Intelligence", "url": "https://example.test/ami"},
            "music": {"name": "Music", "url": "https://example.test/music"},
        }
        with patch("project_intelligence._projects_from_events", return_value=[]):
            with patch("project_intelligence.load_active_resume_items", return_value=items):
                with patch(
                    "project_intelligence._applied_math_continue_action_url",
                    return_value="https://example.test/ami?resume=plog1",
                ):
                    cards = build_project_continue_cards(snap, limit=6, meta=meta)
        self.assertTrue(any(c.title == "Music Practice Log Analysis" for c in cards), [c.title for c in cards])

    def test_recent_ami_excludes_practice_log_analysis(self) -> None:
        items = [
            ResumeItem(
                app="applied_intelligence",
                item_key="ai:practice_log_analysis:plog1",
                title="Music Practice Log Analysis",
                subtitle="Analyze my practice history",
                action_url="https://example.test/ami",
                updated_at="2026-06-27T12:00:00",
            ),
            ResumeItem(
                app="applied_intelligence",
                item_key="ai:question:coach1",
                title="Music Coach question from Music",
                subtitle="What scale fits this song?\n__ctx_json__:{\"source_app\":\"music\"}",
                action_url="https://example.test/ami",
                updated_at="2026-06-27T11:00:00",
            ),
        ]
        with patch("suite_storage.load_active_resume_items", return_value=items):
            recent = load_recent_ami_questions(limit=5)
        self.assertEqual(len(recent), 1)
        self.assertIn("scale", recent[0].question.lower())


if __name__ == "__main__":
    unittest.main()
