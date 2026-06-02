"""Phase A music activity feed and directory priority."""

from __future__ import annotations

import unittest

from activity_feed import format_activity_message, music_directory_rank
from activity_store import ActivitySnapshot, _ingest_suite_events


class TestPhaseAMusicActivity(unittest.TestCase):
    def test_upload_feed_lines(self) -> None:
        video = {
            "app": "music",
            "event": "video_uploaded",
            "metrics": {"song": "Piano Man", "artist": "Billy Joel", "upload_kind": "performance video"},
        }
        self.assertIn("Piano Man", format_activity_message(video) or "")
        audio = {
            "app": "music",
            "event": "audio_uploaded",
            "metrics": {"song": "Shallow", "artist": "Lady Gaga", "upload_kind": "audio recording"},
        }
        self.assertIn("Shallow", format_activity_message(audio) or "")

    def test_directory_rank_prefers_edit_over_open(self) -> None:
        self.assertGreater(music_directory_rank("verified_chart_saved"), music_directory_rank("song_selected"))
        self.assertGreater(music_directory_rank("practice"), music_directory_rank("song_selected"))

    def test_ingest_sets_directory_primary(self) -> None:
        snapshot = ActivitySnapshot()
        events = [
            {
                "app": "music",
                "event": "song_selected",
                "timestamp": "2026-06-01T10:00:00",
                "metrics": {"song": "Piano Man", "artist": "Billy Joel"},
            },
            {
                "app": "music",
                "event": "verified_chart_saved",
                "timestamp": "2026-06-01T11:00:00",
                "metrics": {"song": "Hotel California", "artist": "Eagles", "edited_fields": ["chords"]},
            },
        ]

        def fake_load(_limit: int = 500):
            return events

        import activity_store as store

        original = store.load_all_events
        store.load_all_events = fake_load  # type: ignore[method-assign]
        try:
            _ingest_suite_events(snapshot)
        finally:
            store.load_all_events = original

        self.assertIn("Hotel California", snapshot.music_directory_primary)
        self.assertIn("Verified chart saved", snapshot.music_directory_primary)


if __name__ == "__main__":
    unittest.main()
