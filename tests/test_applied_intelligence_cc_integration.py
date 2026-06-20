"""CC ingest of Ariel AMI activity and page state."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from activity_feed import format_activity_message
from activity_store import ActivitySnapshot, _ingest_suite_events


class TestAppliedIntelligenceCcIntegration(unittest.TestCase):
    def test_analytical_question_counts_toward_applied_week_stats(self) -> None:
        snap = ActivitySnapshot()
        events = [
            {
                "app": "applied_intelligence",
                "event": "analytical_question",
                "page": "Explore a Math Idea",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metrics": {"question": "derivative", "workspace_id": "ariel"},
            }
        ]
        with patch("activity_store.load_all_events", return_value=events), patch(
            "activity_store.load_current_states",
            return_value={},
        ), patch("activity_store._import_sibling_fallback_events"):
            _ingest_suite_events(snap)
        self.assertGreaterEqual(snap.applied_lessons_completed_this_week, 1)

    def test_session_activity_feed_line(self) -> None:
        event = {
            "app": "applied_intelligence",
            "event": "session_activity",
            "page": "Explore a Math Idea",
            "timestamp": "2026-06-20T12:00:00",
            "metrics": {"view_mode": "Explore a Math Idea"},
        }
        line = format_activity_message(event)
        self.assertIn("Explore a Math Idea", line)

    @patch("suite_workspace.get_active_workspace_id", return_value="ariel")
    @patch("suite_storage_supabase._cloud_user_id", return_value="uid-1")
    @patch("suite_storage_supabase._request")
    def test_ariel_ami_event_matches_cc_fetch_namespace(
        self, mock_req, _uid, _ws
    ) -> None:
        mock_req.return_value = [
            {
                "app": "applied_intelligence__ariel",
                "event": "analytical_question",
                "page": "Explore a Math Idea",
                "timestamp": "2026-06-20T12:00:00",
                "metrics": {"workspace_id": "ariel", "question": "derivative"},
            }
        ]
        with patch(
            "suite_workspace.workspace_storage_app_keys",
            return_value=frozenset({"applied_intelligence__ariel"}),
        ):
            from suite_storage_supabase import load_events

            events = load_events(limit=5)
        self.assertEqual(events[0]["app"], "applied_intelligence")
        self.assertEqual(events[0]["event"], "analytical_question")


if __name__ == "__main__":
    unittest.main()
