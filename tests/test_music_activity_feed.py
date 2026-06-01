"""Music verified-save → Command Center feed wiring."""

from __future__ import annotations

import unittest

from activity_feed import format_activity_message
from activity_store import get_app_directory_card, load_activity_snapshot
from suite_activity_client import record_activity


class TestMusicActivityFeed(unittest.TestCase):
    def test_verified_chart_feed_line(self) -> None:
        event = {
            "app": "music",
            "event": "verified_chart_saved",
            "page": "Song Picker",
            "timestamp": "2026-06-01T12:00:00",
            "metrics": {
                "song": "The Scientist",
                "artist": "Coldplay",
                "edited_fields": ["chords"],
                "last_edited_song": "The Scientist",
            },
            "summary": "Saved verified chords for The Scientist",
        }
        msg = format_activity_message(event)
        self.assertIsNotNone(msg)
        assert msg is not None
        self.assertIn("The Scientist", msg)
        self.assertIn("Coldplay", msg)
        self.assertIn("Verified chart saved", msg)

    def test_lyrics_feed_line(self) -> None:
        event = {
            "app": "music",
            "event": "lyrics_saved",
            "metrics": {
                "song": "Autumn Leaves",
                "artist": "Eric Clapton",
                "edited_fields": ["lyrics"],
            },
        }
        msg = format_activity_message(event)
        self.assertEqual(msg, "Lyrics updated: Autumn Leaves — Eric Clapton")

    def test_record_and_snapshot(self) -> None:
        from activity_feed import format_activity_message
        from activity_store import load_all_events

        record_activity(
            "music",
            "verified_chart_saved",
            page="test",
            metrics={
                "song": "Hotel California",
                "artist": "Eagles",
                "edited_fields": ["chords"],
                "last_edited_song": "Hotel California",
            },
            summary="Saved verified chords for Hotel California",
            resume_key="song:test-hotel-california",
            resume_title="Continue: Hotel California",
            resume_subtitle="Eagles",
        )
        latest = next(
            e
            for e in reversed(load_all_events(30))
            if e.get("event") == "verified_chart_saved"
            and (e.get("metrics") or {}).get("song") == "Hotel California"
        )
        self.assertIsNotNone(latest)
        msg = format_activity_message(latest)
        self.assertIn("Hotel California", msg or "")
        self.assertIn("Eagles", msg or "")


if __name__ == "__main__":
    unittest.main()
