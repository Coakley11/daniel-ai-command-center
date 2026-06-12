"""Tests for cross-app analytical question payload and deep links."""

from __future__ import annotations

import json
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
    load_analytical_question_context,
    merge_analytical_context,
    metrics_for_applied_math_resume,
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
        self.assertEqual(title, "Applied Math question from Baseball")
        self.assertEqual(subtitle, "Should I draft Juan Soto in Round 1?")
        self.assertNotIn("Context:", subtitle)
        self.assertNotIn("Juan Soto", title)
        self.assertEqual(btn, ANALYTICAL_QUESTION_BUTTON_LABEL)

    def test_music_continue_copy_title(self) -> None:
        payload = build_question_payload(
            source_app="music",
            source_page="practice",
            question="How should I practice this song?",
            context={"workflow": "Music practice coach"},
        )
        title, subtitle, btn = analytical_question_continue_copy(payload)
        self.assertEqual(title, "Music Coach question from Music")
        self.assertEqual(subtitle, "How should I practice this song?")
        self.assertEqual(btn, "Continue with Music Coach →")

    def test_music_continue_copy_from_context_label(self) -> None:
        title, _, btn = analytical_question_continue_copy(
            {
                "source_app": "",
                "question": "How do I use backing tracks?",
                "context": {"source_app": "Music Practice Coach", "page": "Backing Track Studio"},
            }
        )
        self.assertEqual(title, "Music Coach question from Music")
        self.assertEqual(btn, "Continue with Music Coach →")

    def test_normalize_source_app_id_aliases(self) -> None:
        from suite_analytical_question import normalize_source_app_id

        self.assertEqual(normalize_source_app_id("Music Practice Coach"), "music")
        self.assertEqual(
            normalize_source_app_id("", {"source_app": "Music Practice Coach"}),
            "music",
        )
        self.assertEqual(normalize_source_app_id("baseball"), "baseball")

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


class TestRichContextPayloads(unittest.TestCase):
    def test_trend_context_includes_slope_delta_r2(self) -> None:
        ctx = merge_analytical_context(
            {"workflow": "Player trend analysis", "player": "Lorenzo Cain", "metrics": ["HR"]},
            {
                "trend_summary": {
                    "stat": "HR",
                    "latest": 15,
                    "delta": 6,
                    "slope": 1.2,
                    "r2": 0.64,
                    "summary": "upward but noisy trend",
                }
            },
        )
        lines = format_context_lines(ctx)
        joined = "\n".join(lines)
        self.assertIn("slope=1.2", joined)
        self.assertIn("R²=0.64", joined)
        self.assertIn("change=6", joined)
        self.assertIn("noisy trend", joined)

    def test_comparison_context_includes_both_players(self) -> None:
        ctx = {
            "player_a": "Mike Piazza",
            "player_b": "Jeff Bagwell",
            "players": ["Mike Piazza", "Jeff Bagwell"],
            "comparison_stats": ["OPS", "HR"],
            "comparison_differences": [
                {"player": "Mike Piazza", "Slope": 0.02},
                {"player": "Jeff Bagwell", "Slope": 0.01},
            ],
        }
        lines = format_context_lines(ctx)
        joined = "\n".join(lines)
        self.assertIn("Mike Piazza", joined)
        self.assertIn("Jeff Bagwell", joined)
        self.assertIn("OPS", joined)

    def test_command_center_card_hides_full_context(self) -> None:
        payload = build_question_payload(
            source_app="baseball",
            source_page="Trend Value",
            question="Is Lorenzo Cain's HR trend meaningful?",
            context={
                "player": "Lorenzo Cain",
                "trend_summary": {"slope": 1.2, "r2": 0.64, "delta": 6},
            },
        )
        title, subtitle, btn = analytical_question_continue_copy(payload)
        self.assertIn("Baseball", title)
        self.assertEqual(subtitle, "Is Lorenzo Cain's HR trend meaningful?")
        self.assertNotIn("slope", subtitle)
        self.assertNotIn("R²", subtitle)
        self.assertNotIn("Context:", subtitle)

    def test_nba_probability_context(self) -> None:
        ctx = {
            "team": "New York Knicks",
            "opponent": "Boston Celtics",
            "win_probability": "62%",
            "series_probability": "71%",
            "page": "Live Game Center",
        }
        lines = format_context_lines(ctx)
        joined = "\n".join(lines)
        self.assertIn("Knicks", joined)
        self.assertIn("Celtics", joined)
        self.assertIn("62%", joined)

    def test_nba_player_stat_gap_context(self) -> None:
        ctx = {
            "player": "Jalen Brunson",
            "stat_gap": {
                "player": "Jalen Brunson",
                "comparison": "Allan Houston",
                "stat": "playoff rebounds",
                "gap": 12,
                "games_remaining": 4,
                "rate_needed": "3.0 RPG",
            },
            "games_remaining": 4,
            "rate_needed": "3.0 RPG",
        }
        lines = format_context_lines(ctx)
        joined = "\n".join(lines)
        self.assertIn("Jalen Brunson", joined)
        self.assertIn("4", joined)

    def test_investment_context_holdings_health_macro_labels(self) -> None:
        ctx = {
            "holdings": ["VTI", "BND"],
            "current_weights": {"VTI": "60.0%", "BND": "40.0%"},
            "health_score": 78.5,
            "expected_return": "8.2%",
            "volatility": "12.1%",
            "sharpe_ratio": "0.68",
            "max_drawdown": "-18.3%",
            "risk_level": "Moderate",
            "macro_outlook": "Recession prob 25%; rates stable",
            "context_note_historical": "return/volatility are historical",
            "context_note_forward": "macro affects forward projections only",
        }
        lines = format_context_lines(ctx)
        joined = "\n".join(lines)
        self.assertIn("VTI", joined)
        self.assertIn("78.5", joined)
        self.assertIn("Sharpe", joined)
        self.assertIn("Recession", joined)

    def test_metrics_include_question_id_for_hydration(self) -> None:
        payload = build_question_payload(
            source_app="investment",
            source_page="Portfolio Health",
            question="Should I rebalance?",
            context={"health_score": 70},
        )
        metrics = metrics_for_applied_math_resume(payload)
        self.assertEqual(metrics["question_id"], payload["question_id"])
        self.assertIn("health_score", metrics["context_json"])

    def test_resume_url_includes_question_id(self) -> None:
        payload = build_question_payload(
            source_app="baseball",
            source_page="Trend Value",
            question="Trend?",
            context={"trend_summary": {"slope": 1.0, "r2": 0.5}},
        )
        url = build_applied_math_resume_url(payload, base_url="https://ami.example.com")
        self.assertIn("suite_ai_question_id=", url)

    def test_store_and_load_context_by_question_id(self) -> None:
        payload = build_question_payload(
            source_app="nba",
            source_page="Matchup",
            question="Who wins?",
            context={"team": "Knicks", "win_probability": "55%"},
        )
        qid = payload["question_id"]
        saved: dict = {}

        def _fake_remember(app: str, item_type: str, item_key: str, **kwargs: object) -> None:
            saved[(app, item_type, item_key)] = kwargs.get("payload")

        def _fake_load(app: str, item_type: str, limit: int = 50) -> list:
            rows = []
            for (a, t, k), payload_blob in saved.items():
                if a == app and t == item_type:
                    rows.append({"item_key": k, "payload": payload_blob})
            return rows

        with unittest.mock.patch("suite_account.remember_saved_item", side_effect=_fake_remember):
            with unittest.mock.patch("suite_account.load_saved_items", side_effect=_fake_load):
                with unittest.mock.patch("suite_activity_client.record_activity"):
                    with unittest.mock.patch("suite_analytical_question._upsert_applied_intelligence_resume"):
                        submit_analytical_question(
                            source_app="nba",
                            source_page="Matchup",
                            question="Who wins?",
                            context={"team": "Knicks", "win_probability": "55%"},
                        )
                loaded = load_analytical_question_context(qid)
        self.assertEqual(loaded.get("team"), "Knicks")
        self.assertEqual(loaded.get("win_probability"), "55%")

    def test_hydrate_prefers_question_id_blob_over_url(self) -> None:
        qid = "ami-blob-first-test"
        full_ctx = {
            "player": "Corbin Carroll",
            "draft_snapshot": {
                "current_pick": 18,
                "user_roster": ["Aaron Judge", "Juan Soto"],
                "recommended_players": [{"player": "Elly De La Cruz"}],
            },
        }

        class _QP:
            def get(self, name: str) -> str:
                if name == "suite_ai_question_id":
                    return qid
                if name == "suite_ai_question":
                    return "Who should I draft next?"
                if name == "suite_ai_context":
                    return '{"player":"URL-only"}'
                return ""

        class _ST:
            session_state: dict = {}
            query_params = _QP()

        st = _ST()
        with unittest.mock.patch(
            "suite_analytical_question.load_analytical_question_payload",
            return_value={"context": full_ctx, "source_state": {"page": "Draft"}},
        ):
            from suite_analytical_question import hydrate_applied_intelligence_session

            hydrate_applied_intelligence_session(st, metrics={"question_id": qid})

        loaded = json.loads(st.session_state["_suite_ai_context"])
        self.assertEqual(loaded.get("player"), "Corbin Carroll")
        self.assertIn("draft_snapshot", loaded)
        self.assertEqual(st.session_state.get("_suite_ai_hydrate_source"), "question_id_blob")

    def test_build_context_from_session_investment_health(self) -> None:
        session = {
            "_ami_investment_context": {"rebalance_drift": {"VTI": "+5pp"}},
            "sidebar_portfolio_value": 100000,
        }

        class _HR:
            score = 82.0
            expected_return = 7.5
            volatility = 11.0
            sharpe = 0.55
            max_drawdown = -15.0
            risk_level = "Moderate"

        session["health_result"] = _HR()
        ctx, _ = build_context_from_session("investment", "Portfolio Health", session)
        self.assertEqual(ctx["health_score"], 82.0)
        self.assertIn("sharpe_ratio", ctx)


if __name__ == "__main__":
    unittest.main()
