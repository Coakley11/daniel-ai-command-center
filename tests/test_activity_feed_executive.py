"""Executive Recent Activity — meaningful work only."""

from __future__ import annotations

import unittest

from activity_feed import build_activity_feed, format_activity_message


class TestActivityFeedExecutive(unittest.TestCase):
    def test_passive_page_views_hidden(self) -> None:
        event = {
            "app": "nba",
            "event": "page_view",
            "metrics": {"team": "Knicks", "page": "Team Home"},
        }
        self.assertIsNone(format_activity_message(event, for_feed=True))

    def test_injury_page_view_is_meaningful(self) -> None:
        event = {
            "app": "nba",
            "event": "page_view",
            "metrics": {"team": "Knicks", "page": "Injury Report"},
        }
        msg = format_activity_message(event, for_feed=True)
        self.assertIsNotNone(msg)
        self.assertIn("injury", msg.lower())

    def test_music_executive_copy(self) -> None:
        practice = format_activity_message(
            {
                "app": "music",
                "event": "practice",
                "metrics": {"song": "Piano Man", "minutes": 25},
            },
            for_feed=True,
        )
        self.assertIn("Piano Man", practice or "")
        self.assertIn("25", practice or "")

        chords = format_activity_message(
            {
                "app": "music",
                "event": "verified_chart_saved",
                "metrics": {"song": "Hotel California", "edited_fields": ["chords"]},
            },
            for_feed=True,
        )
        self.assertIn("Saved verified chords", chords or "")
        self.assertIn("Hotel California", chords or "")

    def test_macro_shown_in_feed(self) -> None:
        event = {
            "app": "investment",
            "event": "macro_environment_applied",
            "metrics": {},
        }
        msg = format_activity_message(event, for_feed=True)
        self.assertIsNotNone(msg)
        self.assertIn("macro", msg.lower())

    def test_monte_carlo_label(self) -> None:
        event = {
            "app": "investment",
            "event": "scenario_run",
            "metrics": {"scenario_type": "monte_carlo"},
        }
        msg = format_activity_message(event, for_feed=True)
        self.assertIn("Monte Carlo", msg or "")

    def test_opened_topic_suppressed(self) -> None:
        event = {
            "app": "applied_intelligence",
            "event": "page_view",
            "metrics": {"lesson": "Probability"},
            "summary": "Opened topic: Probability",
        }
        self.assertIsNone(format_activity_message(event, for_feed=True))

    def test_lesson_completed_in_feed(self) -> None:
        events = [
            {
                "app": "applied_intelligence",
                "event": "lesson_completed",
                "timestamp": "2026-06-01T12:00:00",
                "metrics": {"lesson": "Bayesian reasoning"},
            },
            {
                "app": "music",
                "event": "song_selected",
                "timestamp": "2026-06-01T13:00:00",
                "metrics": {"song": "Shallow"},
            },
        ]
        feed = build_activity_feed(events, limit=5)
        messages = [item.message for item in feed]
        self.assertTrue(any("lesson" in m.lower() for m in messages))
        self.assertFalse(any("Opened" in m for m in messages))


if __name__ == "__main__":
    unittest.main()
