"""Tests for cross-app analytical question payload and deep links."""

from __future__ import annotations

import unittest
import unittest.mock

from suite_analytical_question import (
    build_applied_math_resume_url,
    build_question_payload,
    default_area_for_source,
    question_id,
    submit_analytical_question,
)


class TestSuiteAnalyticalQuestion(unittest.TestCase):
    def test_build_question_payload_baseball(self) -> None:
        payload = build_question_payload(
            source_app="baseball",
            source_page="Trend Value",
            question="Is Lorenzo Cain's trend meaningful?",
            context={"player": "Lorenzo Cain"},
        )
        self.assertEqual(payload["source_app"], "baseball")
        self.assertEqual(payload["quant_area"], "sports")
        self.assertTrue(payload["resume_key"].startswith("ai:question:"))
        self.assertIn("Lorenzo Cain", payload["context_summary"])

    def test_default_area_investment(self) -> None:
        self.assertEqual(default_area_for_source("investment"), "forecasting")

    def test_question_id_stable(self) -> None:
        a = question_id("Same Q", source_app="baseball")
        b = question_id("Same Q", source_app="baseball")
        self.assertEqual(a, b)

    def test_applied_math_resume_url_includes_question(self) -> None:
        payload = build_question_payload(
            source_app="nba",
            source_page="Live Game Center",
            question="Is 95% win probability reasonable?",
            context={"team": "New York Knicks"},
        )
        url = build_applied_math_resume_url(payload, base_url="https://ami.example.com")
        self.assertIn("suite_ai_question=", url)
        self.assertIn("suite_ai_source_app=nba", url)
        self.assertIn("suite_ai_area=sports", url)

    def test_submit_analytical_question_records(self) -> None:
        with unittest.mock.patch("suite_activity_client.record_activity") as rec:
            with unittest.mock.patch("suite_storage.upsert_resume_item"):
                result = submit_analytical_question(
                    source_app="baseball",
                    source_page="Comparison Tool",
                    question="Is Piazza better than Bagwell?",
                    context={"player_a": "Mike Piazza", "player_b": "Jeff Bagwell"},
                )
        self.assertIn("action_url", result)
        rec.assert_called_once()
        args, kwargs = rec.call_args
        self.assertEqual(args[0], "baseball")
        self.assertEqual(args[1], "analytical_question")
        self.assertIn("suite_ai_question", kwargs.get("action_url") or result["action_url"])


if __name__ == "__main__":
    unittest.main()
