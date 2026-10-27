from __future__ import annotations

import unittest
from datetime import datetime, timezone

from activity_feed import build_activity_dashboard, format_activity_message
from activity_grouping import activity_action_id, milestone_today_line


def _event(**metrics):
    base = {
        "activity_schema_version": 1,
        "activity_type": "practice_session_started",
        "song": "Shape of You",
        "artist": "Ed Sheeran",
        "source_type": "catalog",
        "source_id": "Pop|Shape of You — Ed Sheeran",
        "pick_key": "Pop|Shape of You — Ed Sheeran",
        "instrument": "Alto Sax",
        "practice_key": "C minor",
        "key_cycling_active": False,
        "backing_active": False,
        "resume_payload": {
            "version": 1,
            "resume_kind": "practice",
            "workspace_id": "daniel",
            "studio_page": "practice",
            "song": "Shape of You",
            "artist": "Ed Sheeran",
            "pick_key": "Pop|Shape of You — Ed Sheeran",
            "instrument": "Alto Sax",
            "display_key": "C minor",
            "practice_focus_section": "Full Song",
            "bpm": 96,
        },
    }
    base.update(metrics)
    return {
        "app": "music",
        "event": "practice_session_started",
        "page": "Practice",
        "timestamp": "2026-10-26T15:30:00Z",
        "metrics": base,
    }


class MusicPracticeActivityTests(unittest.TestCase):
    def test_catalog_session_has_human_readable_summary(self) -> None:
        self.assertEqual(
            format_activity_message(_event()),
            "Practiced Shape of You on Alto Sax in C minor · Catalog",
        )

    def test_compact_minor_key_is_rendered_naturally(self) -> None:
        self.assertEqual(
            format_activity_message(_event(practice_key="Cm")),
            "Practiced Shape of You on Alto Sax in C minor · Catalog",
        )

    def test_key_cycling_uses_start_key_without_overwriting_practice_key(self) -> None:
        event = _event(
            practice_key="B minor",
            key_cycling_active=True,
            key_cycling_start_key="B minor",
            key_cycling_sounding_key="D minor",
        )
        self.assertEqual(
            format_activity_message(event),
            "Practiced Shape of You on Alto Sax with Key Cycling, starting in B minor · Catalog",
        )
        self.assertNotIn("D minor", format_activity_message(event) or "")

    def test_optional_fields_are_not_fabricated(self) -> None:
        event = _event(
            instrument="",
            practice_key="",
            source_type="composition",
        )
        self.assertEqual(
            format_activity_message(event),
            "Practiced Shape of You · Composition",
        )

    def test_started_session_is_grouped_as_practice_and_promoted_with_detail(self) -> None:
        event = _event(source_type="custom")
        self.assertEqual(activity_action_id(event), "practice_session")
        line = milestone_today_line(event)
        self.assertIsNotNone(line)
        self.assertIn("Custom progression", line or "")
        self.assertIn("Shape of You", line or "")

    def test_dashboard_exposes_recent_music_card_with_timestamp(self) -> None:
        event = _event()
        dashboard = build_activity_dashboard(
            [event],
            now=datetime(2026, 10, 26, 16, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(len(dashboard.recent), 1)
        card = dashboard.recent[0]
        self.assertEqual(card.app, "music")
        self.assertEqual(card.app_label, "Music")
        self.assertEqual(card.timestamp, "2026-10-26T15:30:00Z")
        self.assertIn("Shape of You", card.message)
        self.assertIn("Catalog", card.message)
        self.assertIn("suite_resume_payload=", card.action_url)

    def test_repeated_starts_roll_up_without_duplicate_cards(self) -> None:
        first = _event()
        second = _event()
        second["timestamp"] = "2026-10-26T15:40:00Z"
        dashboard = build_activity_dashboard(
            [first, second],
            now=datetime(2026, 10, 26, 16, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(len(dashboard.recent), 1)
        self.assertTrue(dashboard.recent[0].is_rollup)
        self.assertEqual(
            dashboard.recent[0].message,
            "Practiced Shape of You on Alto Sax in C minor · Catalog",
        )
        self.assertEqual(dashboard.recent[0].timestamp, "2026-10-26T15:40:00Z")


if __name__ == "__main__":
    unittest.main()
