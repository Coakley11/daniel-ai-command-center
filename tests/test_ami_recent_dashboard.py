"""Tests for Recent AMI Questions dashboard."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from ami_recent_dashboard import load_recent_ami_questions
from suite_storage import ResumeItem


class TestAmiRecentDashboard(unittest.TestCase):
    def test_load_recent_ami_questions_filters_and_parses(self) -> None:
        items = [
            ResumeItem(
                app="applied_intelligence",
                item_key="ai:question:abc123",
                title="Music Coach question from Music",
                subtitle="What songs similar to Perfect can I play?\n__ctx_json__:{\"source_app\":\"music\"}",
                action_url="https://example.test/ami?q=abc123",
                updated_at="2026-06-17T12:00:00",
            ),
            ResumeItem(
                app="music",
                item_key="song:Pop|Perfect — Ed Sheeran",
                title="Continue: Perfect",
                subtitle="Practice",
                action_url="https://example.test/music",
                updated_at="2026-06-17T11:00:00",
            ),
            ResumeItem(
                app="applied_intelligence",
                item_key="ai:question:def456",
                title="Applied Math question from Baseball",
                subtitle="Question: Would Eric Wagaman help my fantasy team?\n__ctx_json__:{\"source_app\":\"baseball\"}",
                action_url="https://example.test/ami?q=def456",
                updated_at="2026-06-16T18:00:00",
            ),
        ]
        with patch("suite_storage.load_active_resume_items", return_value=items):
            recent = load_recent_ami_questions(limit=5)
        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[0].question, "What songs similar to Perfect can I play?")
        self.assertEqual(recent[0].source_app, "music")
        self.assertIn("Music", recent[0].source_label)
        self.assertEqual(recent[1].source_app, "baseball")


if __name__ == "__main__":
    unittest.main()
