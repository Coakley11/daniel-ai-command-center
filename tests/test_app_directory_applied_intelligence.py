"""App Directory should not surface Applied Math question text."""

from __future__ import annotations

import unittest

from activity_store import ActivitySnapshot, get_app_directory_card


class TestAppDirectoryAppliedIntelligence(unittest.TestCase):
    def test_analytical_question_not_in_app_directory(self) -> None:
        snap = ActivitySnapshot()
        snap.last_applied_intelligence_analysis = (
            "Do you think Brunson will pass Allan Houston in playoff rebounds in 2026?"
        )
        snap.last_applied_intelligence_lesson = (
            "Do you think Brunson will pass Allan Houston in playoff rebounds in 2026?"
        )
        snap.last_applied_intelligence_page = "Solve a Problem"
        card = get_app_directory_card(snap, "applied_intelligence")
        joined = " ".join(card.highlights)
        self.assertNotIn("Brunson", joined)
        self.assertTrue(
            any("Explore" in line or "Solve" in line or "quantitative" in line for line in card.highlights)
            or card.highlights == ("Ready to start.",)
        )

    def test_short_lesson_still_shows(self) -> None:
        snap = ActivitySnapshot()
        snap.last_applied_intelligence_lesson = "Bayes theorem intro"
        card = get_app_directory_card(snap, "applied_intelligence")
        self.assertTrue(any("Bayes" in line for line in card.highlights))


if __name__ == "__main__":
    unittest.main()
