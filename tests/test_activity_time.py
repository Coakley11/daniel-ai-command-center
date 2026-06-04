"""UTC activity timestamps and relative display."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from activity_time import (
    format_relative_time,
    normalize_timestamp_iso,
    parse_activity_timestamp,
    utc_now_iso,
)


class TestActivityTime(unittest.TestCase):
    def test_utc_now_iso_has_z_suffix(self) -> None:
        self.assertTrue(utc_now_iso().endswith("Z"))

    def test_parse_z_and_offset_equivalent(self) -> None:
        a = parse_activity_timestamp("2026-06-03T18:30:00Z")
        b = parse_activity_timestamp("2026-06-03T18:30:00+00:00")
        self.assertIsNotNone(a)
        self.assertIsNotNone(b)
        assert a is not None and b is not None
        self.assertEqual(a, b)

    def test_normalize_preserves_instant(self) -> None:
        raw = "2026-06-03T14:15:00+00:00"
        norm = normalize_timestamp_iso(raw)
        self.assertTrue(norm.endswith("Z"))
        self.assertEqual(parse_activity_timestamp(norm), parse_activity_timestamp(raw))

    def test_relative_just_now(self) -> None:
        now = datetime(2026, 6, 3, 18, 0, tzinfo=timezone.utc)
        dt = now - timedelta(seconds=30)
        self.assertEqual(format_relative_time(dt, now=now), "Just now")

    def test_relative_minutes_and_hours(self) -> None:
        now = datetime(2026, 6, 3, 18, 0, tzinfo=timezone.utc)
        self.assertEqual(format_relative_time(now - timedelta(minutes=5), now=now), "5 min ago")
        self.assertEqual(format_relative_time(now - timedelta(hours=2), now=now), "2 hours ago")


if __name__ == "__main__":
    unittest.main()
