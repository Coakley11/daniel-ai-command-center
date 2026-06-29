"""Practice Log card subtitle and Eastern Time display tests."""

from __future__ import annotations

import unittest

from activity_time import format_eastern_time_label, parse_activity_timestamp
from suite_analytical_question import practice_log_analysis_card_subtitle


class TestPracticeLogCardDisplay(unittest.TestCase):
    def test_utc_converts_to_eastern_june(self) -> None:
        dt = parse_activity_timestamp("2026-06-29T13:28:00+00:00")
        assert dt is not None
        self.assertIn("9:28 AM ET", format_eastern_time_label(dt))

    def test_mixed_instruments_not_guitar_slash_say(self) -> None:
        subtitle = practice_log_analysis_card_subtitle(
            {
                "report_generated_at": "2026-06-29T13:28:00+00:00",
                "context": {
                    "practice_log_summary": {
                        "practice_time_by_instrument": {"Tenor Saxophone": 30, "Guitar": 30},
                        "practice_time_by_song": {"Say": 45},
                    }
                },
            }
        )
        self.assertIn("Top song: Say", subtitle)
        self.assertIn("Multiple instruments", subtitle)
        self.assertNotIn("Guitar / Say", subtitle)
        self.assertNotIn("+00:00", subtitle)


if __name__ == "__main__":
    unittest.main()
