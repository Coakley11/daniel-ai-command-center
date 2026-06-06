"""Project-style Continue titles and weekly accomplishment lines."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from activity_store import ActivitySnapshot, WeeklySummary, get_weekly_summary
from project_intelligence import (
    _polish_resume,
    _projects_from_events,
    diagnose_continue_workflow_candidates,
    weekly_accomplishment_lines,
)
from suite_storage import ResumeItem


class TestProjectIntelligence(unittest.TestCase):
    def test_baseball_player_trend_becomes_continue_card(self) -> None:
        snap = ActivitySnapshot()
        recent = (datetime.now() - timedelta(hours=1)).isoformat(timespec="seconds")
        older = (datetime.now() - timedelta(days=2)).isoformat(timespec="seconds")
        events = [
            {
                "app": "baseball",
                "event": "player_comparison",
                "timestamp": older,
                "metrics": {"player_a": "Mike Piazza", "player_b": "Jeff Bagwell"},
            },
            {
                "app": "baseball",
                "event": "player_trend_viewed",
                "timestamp": recent,
                "metrics": {"player": "Lorenzo Cain"},
            },
        ]
        with patch("project_intelligence.load_all_events", return_value=events):
            cards = _projects_from_events(snap)
        baseball = [c for c in cards if c[1] == "baseball"]
        self.assertEqual(len(baseball), 1)
        self.assertIn("Lorenzo Cain", baseball[0][2])
        self.assertEqual(baseball[0][4], "trend:Lorenzo Cain")

    def test_baseball_trend_comparison_becomes_continue_card(self) -> None:
        snap = ActivitySnapshot()
        recent = (datetime.now() - timedelta(hours=1)).isoformat(timespec="seconds")
        events = [
            {
                "app": "baseball",
                "event": "trend_comparison_viewed",
                "timestamp": recent,
                "metrics": {"player_a": "Juan Soto", "player_b": "Anthony Volpe"},
            },
        ]
        with patch("project_intelligence.load_all_events", return_value=events):
            cards = _projects_from_events(snap)
        baseball = [c for c in cards if c[1] == "baseball"]
        self.assertEqual(len(baseball), 1)
        self.assertIn("Juan Soto vs Anthony Volpe", baseball[0][2])
        self.assertEqual(baseball[0][4], "trendcompare:Juan Soto:Anthony Volpe")
        self.assertEqual(baseball[0][0], 59)

    def test_analytical_question_becomes_applied_intelligence_continue(self) -> None:
        snap = ActivitySnapshot()
        recent = (datetime.now() - timedelta(minutes=5)).isoformat(timespec="seconds")
        events = [
            {
                "app": "baseball",
                "event": "analytical_question",
                "timestamp": recent,
                "metrics": {
                    "question": "Should I draft Juan Soto in Round 1?",
                    "source_app": "baseball",
                    "source_page": "Draft Simulation",
                    "context": {
                        "draft_format": "OBP League",
                        "draft_round": 1,
                        "player": "Juan Soto",
                    },
                },
            },
        ]
        with patch("project_intelligence.load_all_events", return_value=events):
            cards = _projects_from_events(snap)
        ami = [c for c in cards if c[1] == "applied_intelligence"]
        self.assertEqual(len(ami), 1)
        self.assertIn("Applied Math question from Baseball", ami[0][2])
        self.assertIn("Juan Soto", ami[0][3])
        self.assertTrue(str(ami[0][4]).startswith("ai:question:"))
        self.assertEqual(ami[0][0], 64)

    def test_workflow_candidate_diagnostic_marks_included_trend(self) -> None:
        snap = ActivitySnapshot()
        recent = (datetime.now() - timedelta(hours=1)).isoformat(timespec="seconds")
        events = [
            {
                "app": "baseball",
                "event": "player_trend_viewed",
                "timestamp": recent,
                "metrics": {"player": "Lorenzo Cain"},
            },
        ]
        with patch("project_intelligence.load_all_events", return_value=events):
            rows = diagnose_continue_workflow_candidates(snap)
        self.assertTrue(rows)
        self.assertEqual(rows[0]["resume_key"], "trend:Lorenzo Cain")
        self.assertIn(rows[0]["status"], {"included", "excluded"})

    def test_polish_music_chord_resume(self) -> None:
        item = ResumeItem(
            app="music",
            item_key="song:perfect",
            title="Continue: Perfect",
            subtitle="Ed Sheeran",
            action_url="",
            updated_at="2026-06-01T12:00:00",
        )
        title, _, priority = _polish_resume(item)
        self.assertIn("Perfect", title)
        self.assertGreaterEqual(priority, 40)

    def test_weekly_accomplishment_lines(self) -> None:
        snap = ActivitySnapshot(
            songs_practiced_this_week=3,
            music_verified_edits_this_week=2,
            music_uploads_this_week=1,
            portfolio_checks_this_week=2,
            investment_optimizer_runs_this_week=1,
            baseball_analyses_this_week=3,
        )
        summary = get_weekly_summary(snap)
        lines = weekly_accomplishment_lines(summary)
        labels = " ".join(label for _, label in lines)
        self.assertIn("practice session", labels)
        self.assertIn("verified chart", labels)
        self.assertIn("portfolio review", labels)
        self.assertNotIn("click", labels.lower())

    def test_weekly_summary_dataclass(self) -> None:
        summary = WeeklySummary(
            music_minutes=0,
            songs_practiced=1,
            music_practice_sessions=0,
            music_uploads=0,
            music_verified_edits=0,
            music_lyrics_edits=0,
            music_backing_sessions=0,
            baseball_analyses=0,
            portfolio_checks=0,
            investment_scenarios=0,
            investment_optimizer_runs=0,
            investment_rebalance_reviews=0,
            nba_analyses=0,
            applied_lessons_completed=0,
            future_simulations=0,
        )
        self.assertTrue(summary.has_any)


if __name__ == "__main__":
    unittest.main()
