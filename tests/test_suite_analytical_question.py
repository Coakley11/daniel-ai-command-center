"""Tests for cross-app analytical question payload and deep links."""

from __future__ import annotations

import unittest
import unittest.mock

from suite_analytical_question import (
    ANALYTICAL_QUESTION_BUTTON_LABEL,
    analytical_question_continue_copy,
    build_applied_math_resume_url,
    build_context_from_session,
    build_question_payload,
    default_area_for_source,
    format_context_lines,
    question_dedupe_fingerprint,
    question_id,
    submit_analytical_question,
)


class TestSuiteAnalyticalQuestion(unittest.TestCase):
    def test_build_question_payload_baseball(self) -> None:
        payload = build_question_payload(
            source_app="baseball",
            source_page="Trend Value",
            question="Is Lorenzo Cain's trend meaningful?",
            context={"player": "Lorenzo Cain", "workflow": "Player trend analysis"},
        )
        self.assertEqual(payload["source_app"], "baseball")
        self.assertEqual(payload["context"]["page"], "Trends")
        self.assertEqual(payload["quant_area"], "sports")
        self.assertTrue(payload["resume_key"].startswith("ai:question:"))
        self.assertIn("Lorenzo Cain", payload["context"]["player"])

    def test_format_context_lines_whitelist_only(self) -> None:
        lines = format_context_lines(
            {
                "source_app": "Baseball",
                "page": "Trends",
                "workflow": "Player trend analysis",
                "player": "Lorenzo Cain",
                "metrics": ["AB", "HR"],
                "trend_ab_min": 100,
            }
        )
        joined = "\n".join(lines)
        self.assertIn("Lorenzo Cain", joined)
        self.assertIn("AB", joined)
        self.assertNotIn("trend_ab_min", joined)

    def test_build_context_from_session_baseball_trends(self) -> None:
        session = {
            "single_trend_dashboard_player": "Lorenzo Cain (KC)",
            "single_trend_dashboard_stats": ["AB", "HR"],
            "trend_plot_stat": "BA",
        }
        ctx, _ = build_context_from_session("baseball", "Trend Value", session)
        self.assertEqual(ctx["workflow"], "Player trend analysis")
        self.assertEqual(ctx["player"], "Lorenzo Cain")
        self.assertIn("AB", ctx["metrics"])

    def test_question_id_includes_context(self) -> None:
        a = question_id(
            "Same Q",
            source_app="baseball",
            source_page="Trend Value",
            context={"player": "Lorenzo Cain"},
        )
        b = question_id(
            "Same Q",
            source_app="baseball",
            source_page="Trend Value",
            context={"player": "Mike Trout"},
        )
        self.assertNotEqual(a, b)
        self.assertEqual(
            a,
            question_dedupe_fingerprint(
                "Same Q",
                source_app="baseball",
                source_page="Trend Value",
                context={"player": "Lorenzo Cain"},
            ),
        )

    def test_default_area_investment(self) -> None:
        self.assertEqual(default_area_for_source("investment"), "forecasting")

    def test_question_id_stable(self) -> None:
        a = question_id("Same Q", source_app="baseball", source_page="Trends")
        b = question_id("Same Q", source_app="baseball", source_page="Trends")
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

    def test_analytical_question_continue_copy(self) -> None:
        payload = build_question_payload(
            source_app="baseball",
            source_page="Draft Simulation",
            question="Should I draft Juan Soto in Round 1?",
            context={"draft_format": "OBP League", "draft_round": 1, "player": "Juan Soto"},
        )
        title, subtitle, btn = analytical_question_continue_copy(payload)
        self.assertIn("Baseball", title)
        self.assertEqual(subtitle, "Should I draft Juan Soto in Round 1?")
        self.assertNotIn("Context:", subtitle)
        self.assertNotIn("Juan Soto", title)
        self.assertEqual(btn, ANALYTICAL_QUESTION_BUTTON_LABEL)

    def test_submit_analytical_question_records(self) -> None:
        with unittest.mock.patch("suite_activity_client.record_activity") as rec:
            with unittest.mock.patch("suite_analytical_question._upsert_applied_intelligence_resume"):
                result = submit_analytical_question(
                    source_app="baseball",
                    source_page="Comparison Tool",
                    question="Is Piazza better than Bagwell?",
                    context={"player_a": "Mike Piazza", "player_b": "Jeff Bagwell"},
                )
        self.assertIn("action_url", result)
        self.assertIn("suite_ai_question", result["action_url"])
        rec.assert_called_once()
        args, kwargs = rec.call_args
        self.assertEqual(args[0], "baseball")
        self.assertEqual(args[1], "analytical_question")
        self.assertNotIn("resume_key", kwargs)

    def test_submit_skips_duplicate_event_within_cooldown(self) -> None:
        session: dict = {}
        with unittest.mock.patch("suite_activity_client.record_activity") as rec:
            with unittest.mock.patch("suite_analytical_question._upsert_applied_intelligence_resume"):
                first = submit_analytical_question(
                    source_app="baseball",
                    source_page="Trend Value",
                    question="Trend?",
                    context={"player": "Lorenzo Cain"},
                    session_state=session,
                )
                second = submit_analytical_question(
                    source_app="baseball",
                    source_page="Trend Value",
                    question="Trend?",
                    context={"player": "Lorenzo Cain"},
                    session_state=session,
                )
        self.assertFalse(first.get("duplicate"))
        self.assertTrue(second.get("duplicate"))
        rec.assert_called_once()


if __name__ == "__main__":
    unittest.main()
