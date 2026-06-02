"""Project-style Continue titles and weekly accomplishment lines."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from activity_store import ActivitySnapshot, WeeklySummary, get_weekly_summary
from project_intelligence import _polish_resume, weekly_accomplishment_lines
from suite_storage import ResumeItem


class TestProjectIntelligence(unittest.TestCase):
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
