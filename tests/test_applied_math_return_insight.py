"""Tests for Return Insight source_state restore flow."""

from __future__ import annotations

import unittest

from applied_math_return_insight import (
    AMI_INSIGHT_STORE_VERSION,
    _source_state_has_restore_payload,
    build_return_resume_key,
    metrics_for_source_app_return,
    prepare_ami_insight_store_context,
    resolve_ami_return_source_state_for_store,
    store_applied_math_insight,
)


class TestReturnInsightRestore(unittest.TestCase):
    def test_metrics_uses_full_player_labels_from_source_state(self) -> None:
        insight = {
            "insight_id": "abc123",
            "question_id": "q1",
            "source_app": "baseball",
            "source_page": "Comparison Tool",
            "source_state": {
                "source_page": "Comparison Tool",
                "entity_params": {
                    "player_a_label": "Juan Soto (NYY)",
                    "player_b_label": "Aaron Judge (NYY)",
                },
                "widget_params": {
                    "sig_player_a_clean": "Juan Soto (NYY)",
                    "sig_player_b_clean": "Aaron Judge (NYY)",
                },
            },
        }
        m = metrics_for_source_app_return(insight)
        self.assertEqual(m["player_a"], "Juan Soto (NYY)")
        self.assertEqual(m["player_b"], "Aaron Judge (NYY)")
        self.assertEqual(m["page"], "Comparison Tool")

    def test_build_return_resume_key_prefers_compare(self) -> None:
        insight = {
            "source_app": "baseball",
            "source_page": "Comparison Tool",
            "question_id": "q99",
            "source_state": {
                "source_page": "Comparison Tool",
                "entity_params": {
                    "player_a_label": "Juan Soto (NYY)",
                    "player_b_label": "Aaron Judge (NYY)",
                },
            },
        }
        rk = build_return_resume_key(insight)
        self.assertEqual(rk, "compare:Juan Soto (NYY):Aaron Judge (NYY)")

    def test_music_return_metrics_include_pick_key(self) -> None:
        insight = {
            "insight_id": "mc1",
            "question_id": "qmc",
            "source_app": "music",
            "source_page": "backing",
            "source_state": {
                "source_page": "backing",
                "entity_params": {"pick_key": "pop:test_song", "song_title": "Test Song"},
                "widget_params": {
                    "studio_page": "backing",
                    "instrument": "Piano",
                    "display_key": "C",
                },
            },
        }
        m = metrics_for_source_app_return(insight)
        self.assertEqual(m["pick_key"], "pop:test_song")
        self.assertEqual(m["studio_page"], "backing")
        self.assertEqual(m["source_app"], "music")
        rk = build_return_resume_key(insight)
        self.assertEqual(rk, "backing:pop:test_song")

    def test_resolve_ami_return_source_state_for_store_loads_question_blob(self) -> None:
        from unittest.mock import patch

        class _FakeSessionState(dict):
            def __getattr__(self, name):
                return self[name]

            def __setattr__(self, name, value):
                self[name] = value

        class _FakeSt:
            def __init__(self) -> None:
                self.session_state = _FakeSessionState()

        question_ss = {
            "source_app": "investment",
            "source_page": "Portfolio Health",
            "entity_params": {
                "holdings_fingerprint": "BND:50.0:Bonds|VYM:50.0:Dividend ETF",
                "holdings_df": [{"Ticker": "BND", "Weight (%)": 50.0}],
            },
            "widget_params": {},
            "page_params": {"page": "Portfolio Health", "tab": "Portfolio Health"},
        }
        st = _FakeSt()
        insight = {
            "question_id": "q-cc-1",
            "source_app": "investment",
            "source_page": "Portfolio Health",
        }
        with patch(
            "suite_analytical_question.load_analytical_question_source_state",
            return_value=question_ss,
        ):
            resolved = resolve_ami_return_source_state_for_store(
                st,
                insight,
                source_state={"source_app": "investment"},
            )
        self.assertTrue(_source_state_has_restore_payload(resolved))
        self.assertEqual(
            resolved["entity_params"]["holdings_fingerprint"],
            "BND:50.0:Bonds|VYM:50.0:Dividend ETF",
        )

    def test_store_applied_math_insight_embeds_store_trace_in_blob(self) -> None:
        from unittest.mock import patch

        question_ss = {
            "source_app": "investment",
            "source_page": "Portfolio Health",
            "entity_params": {
                "holdings_fingerprint": "BND:50.0:Bonds|VYM:50.0:Dividend ETF",
                "holdings_df": [{"Ticker": "BND", "Weight (%)": 50.0}],
            },
            "page_params": {"page": "Portfolio Health"},
        }
        insight = {
            "insight_id": "f0ac14c07b16500c",
            "question_id": "q-store-trace",
            "source_app": "investment",
            "source_page": "Portfolio Health",
            "conclusion": "Test",
        }
        captured: list[dict] = []

        def _remember_saved_item(_app, _item_type, _item_key, *, title="", payload=None, **_kwargs):
            captured.append(dict(payload or {}))
            return True

        with patch(
            "suite_analytical_question.load_analytical_question_source_state",
            return_value=question_ss,
        ), patch("suite_account.remember_saved_item", side_effect=_remember_saved_item), patch(
            "suite_activity_client.record_activity",
            return_value=None,
        ):
            store_applied_math_insight(insight, source_state=question_ss)

        self.assertTrue(captured)
        stored = captured[-1]
        trace = stored.get("_ami_store_trace") or {}
        self.assertTrue(trace.get("store_source_state_exists"))
        self.assertTrue(trace.get("store_blob_written_success"))
        self.assertEqual(trace.get("store_insight_id"), "f0ac14c07b16500c")
        self.assertEqual(trace.get("store_question_id"), "q-store-trace")
        self.assertTrue(stored.get("store_blob_written_success"))
        self.assertEqual(stored.get("store_version"), AMI_INSIGHT_STORE_VERSION)
        self.assertTrue(_source_state_has_restore_payload(stored.get("source_state")))

    def test_store_applied_math_insight_resolves_source_state_when_st_provided(self) -> None:
        from unittest.mock import patch

        class _FakeSessionState(dict):
            def __getattr__(self, name):
                return self[name]

            def __setattr__(self, name, value):
                self[name] = value

        class _FakeSt:
            def __init__(self) -> None:
                self.session_state = _FakeSessionState()

        question_ss = {
            "source_app": "investment",
            "source_page": "Portfolio Health",
            "entity_params": {"holdings_fingerprint": "BND:50.0:Bonds|VYM:50.0:Dividend ETF"},
            "widget_params": {},
            "page_params": {"page": "Portfolio Health"},
        }
        st = _FakeSt()
        insight = {
            "insight_id": "ins-cc",
            "question_id": "q-cc-2",
            "source_app": "investment",
            "source_page": "Portfolio Health",
            "conclusion": "Test",
        }
        captured: list[dict] = []

        def _remember_saved_item(_app, _item_type, _item_key, *, title="", payload=None, **_kwargs):
            captured.append(dict(payload or {}))
            return True

        with patch(
            "suite_analytical_question.load_analytical_question_source_state",
            return_value=question_ss,
        ), patch("suite_account.remember_saved_item", side_effect=_remember_saved_item), patch(
            "suite_activity_client.record_activity",
            return_value=None,
        ):
            store_applied_math_insight(insight, st=st)

        self.assertTrue(captured)
        self.assertTrue(_source_state_has_restore_payload(captured[-1].get("source_state")))

    def test_store_applied_math_insight_write_trace_sets_duplicate_handled(self) -> None:
        from unittest.mock import patch

        class _FakeSessionState(dict):
            def __getattr__(self, name):
                return self[name]

            def __setattr__(self, name, value):
                self[name] = value

        class _FakeSt:
            def __init__(self) -> None:
                self.session_state = _FakeSessionState()

        st = _FakeSt()
        insight = {
            "insight_id": "dup-test",
            "question_id": "q-dup",
            "source_app": "investment",
            "source_page": "Portfolio Health",
            "conclusion": "Test",
        }
        call_n = {"n": 0}

        def _remember_saved_item(_app, _item_type, _item_key, *, title="", payload=None, **_kwargs):
            call_n["n"] += 1
            if call_n["n"] <= 3:
                return {"write_mode": "upsert", "duplicate_handled": False}
            return {"write_mode": "update", "duplicate_handled": True}

        with patch("suite_account.remember_saved_item", side_effect=_remember_saved_item), patch(
            "suite_activity_client.record_activity",
            return_value=None,
        ):
            store_applied_math_insight(insight, st=st)

        trace = st.session_state.get("_ami_insight_store_trace") or {}
        self.assertTrue(trace.get("store_blob_written_success"))
        self.assertEqual(trace.get("store_write_mode"), "update")
        self.assertTrue(trace.get("store_duplicate_handled"))
        self.assertIsNone(trace.get("store_exception"))

    def test_prepare_ami_insight_store_context_prefers_session_question_id(self) -> None:
        from unittest.mock import patch

        class _FakeSessionState(dict):
            def __getattr__(self, name):
                return self[name]

            def __setattr__(self, name, value):
                self[name] = value

        class _FakeSt:
            def __init__(self) -> None:
                self.session_state = _FakeSessionState(
                    {
                        "_suite_ai_question_id": "q-investment-send",
                    }
                )
                self.query_params = {}

        question_ss = {
            "source_app": "investment",
            "source_page": "Portfolio Health",
            "entity_params": {
                "holdings_fingerprint": "BND:50.0:Bonds|VYM:50.0:Dividend ETF",
            },
            "page_params": {"page": "Portfolio Health"},
        }
        st = _FakeSt()
        with patch(
            "suite_analytical_question.load_analytical_question_source_state",
            return_value=question_ss,
        ), patch(
            "suite_analytical_question.build_question_payload",
            return_value={"question_id": "q-regenerated-wrong", "source_app": "investment"},
        ), patch(
            "suite_analytical_question.persist_question_context_blob",
            return_value=None,
        ) as persist_mock:
            payload, ss, qid = prepare_ami_insight_store_context(
                st,
                source_app="investment",
                source_page="Portfolio Health",
                question="How balanced is my portfolio?",
                context={},
            )
        self.assertEqual(qid, "q-investment-send")
        self.assertEqual(payload.get("question_id"), "q-investment-send")
        self.assertTrue(_source_state_has_restore_payload(ss))
        persist_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
