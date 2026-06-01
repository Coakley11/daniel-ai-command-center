"""Recent Activity should surface edits above song opens."""

from __future__ import annotations

import unittest

from activity_feed import build_activity_feed


class TestActivityFeedPriority(unittest.TestCase):
    def test_verified_save_ranks_above_song_open(self) -> None:
        events = [
            {
                "app": "music",
                "event": "song_selected",
                "timestamp": "2026-06-01T15:00:00",
                "metrics": {"song": "Piano Man", "artist": "Billy Joel"},
            },
            {
                "app": "music",
                "event": "verified_chart_saved",
                "timestamp": "2026-06-01T14:00:00",
                "metrics": {
                    "song": "The Scientist",
                    "artist": "Coldplay",
                    "edited_fields": ["chords"],
                },
            },
        ]
        feed = build_activity_feed(events, limit=2)
        self.assertGreaterEqual(len(feed), 2)
        self.assertIn("Verified chart saved", feed[0].message)
        self.assertIn("Opened:", feed[1].message)


if __name__ == "__main__":
    unittest.main()
