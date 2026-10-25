"""Regression tests for the roster-resume-to-page fix.

The hosted staging blocker: a ``roster:Team A`` resume item in Supabase was
rebuilt by Command Center with ``suite_page=Team+A`` (the subtitle) instead of
``suite_page=Draft+Lab+/+Simulation``, because ``resume_metrics_from_item_key``
had no branch for the ``roster:`` prefix.

These tests pin the CC-side URL generation so the same bug shape can't recur,
and confirm that every other Baseball resume-key family is unaffected.
"""

from __future__ import annotations

import unittest
from urllib.parse import parse_qs, urlparse

from suite_deep_links import (
    _BASEBALL_PAGE_BY_RESUME,
    _resolve_page,
    build_resume_action_url,
    resume_metrics_from_item_key,
)


class RosterResumeTests(unittest.TestCase):
    """The exact failing case: ``roster:Team A``."""

    def test_page_hint_is_draft_lab(self) -> None:
        page, metrics = resume_metrics_from_item_key("baseball", "roster:Team A", subtitle="Team A")
        self.assertEqual(page, "Draft Lab / Simulation")

    def test_my_team_is_extracted(self) -> None:
        page, metrics = resume_metrics_from_item_key("baseball", "roster:Team A", subtitle="Team A")
        self.assertEqual(metrics["my_team"], "Team A")

    def test_bare_baseball_roster_key(self) -> None:
        """The no-team variant ``baseball:roster``."""
        page, metrics = resume_metrics_from_item_key("baseball", "baseball:roster", subtitle="Draft room")
        self.assertEqual(page, "Draft Lab / Simulation")
        self.assertNotIn("my_team", metrics)

    def test_build_url_contains_correct_params(self) -> None:
        page, metrics = resume_metrics_from_item_key("baseball", "roster:Team A", subtitle="Team A")
        url = build_resume_action_url(
            "baseball",
            resume_key="roster:Team A",
            page=page,
            metrics=metrics,
            base_url="https://example.streamlit.app",
        )
        qs = parse_qs(urlparse(url).query)
        self.assertEqual(qs["suite_resume"], ["roster:Team A"])
        self.assertEqual(qs["suite_page"], ["Draft Lab / Simulation"])
        self.assertEqual(qs["suite_my_team"], ["Team A"])

    def test_rebuild_from_exact_qa_record(self) -> None:
        """The exact Supabase record shape that caused the hosted failure."""
        item_key = "roster:Team A"
        subtitle = "Team A"
        stored_action_url = (
            "https://baseball-stat-app-d4jlymjc4iptaadc3kquwx.streamlit.app/"
            "?suite_resume=roster%3ATeam+A&suite_page=Draft+Room"
            "&suite_my_team=Team+A&suite_workspace=daniel"
        )
        page_hint, metrics = resume_metrics_from_item_key("baseball", item_key, subtitle=subtitle)
        # The rebuild must produce Draft Lab, not the stored legacy "Draft Room"
        self.assertEqual(page_hint, "Draft Lab / Simulation")
        url = build_resume_action_url(
            "baseball",
            resume_key=item_key,
            page=page_hint,
            metrics=metrics,
            base_url="https://stage2.streamlit.app",
        )
        qs = parse_qs(urlparse(url).query)
        self.assertEqual(qs["suite_page"], ["Draft Lab / Simulation"])
        # The old stored URL had "Draft Room" — we must NOT emit that
        self.assertNotIn("Draft Room", url)

    def test_resolve_page_roster_prefix(self) -> None:
        """_resolve_page falls back to _BASEBALL_PAGE_BY_RESUME when page is empty."""
        self.assertEqual(
            _resolve_page("baseball", "roster:Team A", "", {}),
            "Draft Lab / Simulation",
        )

    def test_resolve_page_baseball_roster_prefix(self) -> None:
        self.assertEqual(
            _resolve_page("baseball", "baseball:roster", "", {}),
            "Draft Lab / Simulation",
        )


class ExistingCasesUnchangedTests(unittest.TestCase):
    """Pin that the fix doesn't alter any other resume-key family."""

    CASES: list[tuple[str, str, str, str, dict]] = [
        # (item_key, subtitle, expected_page, description, extra_metric_checks)
        ("bb:draft_lab:abc123", "Draft Lab", "Draft Lab / Simulation", "draft lab with room", {"draft_room_id": "abc123"}),
        ("bb:draft_lab:team:xyz", "Team analysis", "Draft Lab / Simulation", "draft lab team", {"draft_room_id": "xyz", "draft_section": "team_analysis"}),
        ("bb:draft_lab", "Draft Lab", "Draft Simulation", "bare draft lab (catch-all)", {}),
        ("bb:live_draft:room1", "Live Draft", "Live Draft Room", "live draft", {"draft_room_id": "room1"}),
        ("historical:HR:2010-2025", "Aaron Judge · HR", "Historical Explorer", "historical", {"sort_stat": "HR", "year_start": "2010", "year_end": "2025"}),
        ("bb:saved_draft:d1", "My draft", "Saved Draft Library", "saved draft", {"draft_id": "d1"}),
        ("bb:simulator_draft", "5x5 Roto", "Draft Simulation", "mock draft (catch-all: 'draft' in key)", {}),
        ("bb:trade_center:p1", "Trade", "Trade Center", "trade with proposal", {"proposal_id": "p1"}),
        ("bb:waiver:w1", "Waiver", "Waiver Wire / Add-Drop Center", "waiver", {"waiver_tx_id": "w1"}),
        ("bb:lineup:league1:w5", "Lineup", "Fantasy Lineup Assistant", "lineup", {}),
        ("bb:hof_case:babe-ruth", "Babe Ruth", "Career Totals", "Hall of Fame", {"hof_case_mode": True, "hof_case_target_slug": "babe-ruth", "target_player": "Babe Ruth"}),
        ("compare:Judge:Soto", "Comparison", "Comparison Tool", "comparison", {}),
        ("trend:Aaron Judge", "Trends", "Trend Value", "trend", {"player": "Aaron Judge"}),
    ]

    def test_page_resolution(self) -> None:
        for item_key, subtitle, expected_page, desc, _ in self.CASES:
            with self.subTest(desc):
                page, _metrics = resume_metrics_from_item_key("baseball", item_key, subtitle=subtitle)
                self.assertEqual(page, expected_page, f"page for {desc}")

    def test_metric_extraction(self) -> None:
        for item_key, subtitle, _, desc, expected_metrics in self.CASES:
            if not expected_metrics:
                continue
            with self.subTest(desc):
                _page, metrics = resume_metrics_from_item_key("baseball", item_key, subtitle=subtitle)
                for k, v in expected_metrics.items():
                    self.assertEqual(metrics.get(k), v, f"{k} for {desc}")


class MappingTableTests(unittest.TestCase):
    """Pin that _BASEBALL_PAGE_BY_RESUME has the updated entries."""

    def test_roster_prefix_in_mapping(self) -> None:
        mapping = dict(_BASEBALL_PAGE_BY_RESUME)
        self.assertEqual(mapping["roster:"], "Draft Lab / Simulation")
        self.assertEqual(mapping["baseball:roster"], "Draft Lab / Simulation")

    def test_no_draft_room_target_in_mapping(self) -> None:
        """The legacy 'Draft Room' page name must not appear as a target."""
        for _prefix, target in _BASEBALL_PAGE_BY_RESUME:
            self.assertNotEqual(target, "Draft Room", f"prefix {_prefix!r} still points to 'Draft Room'")

    def test_existing_prefixes_unchanged(self) -> None:
        mapping = dict(_BASEBALL_PAGE_BY_RESUME)
        self.assertEqual(mapping["bb:draft_lab:"], "Draft Lab / Simulation")
        self.assertEqual(mapping["bb:draft_lab"], "Draft Lab / Simulation")
        self.assertEqual(mapping["bb:live_draft:"], "Live Draft Room")
        self.assertEqual(mapping["historical:"], "Historical Explorer")
        self.assertEqual(mapping["bb:saved_draft:"], "Saved Draft Library")
        self.assertEqual(mapping["bb:simulator_draft"], "Draft Room Simulator")
        self.assertEqual(mapping["bb:standings:"], "Fantasy Standings Tracker")
        self.assertEqual(mapping["bb:draft_assistant"], "Draft Assistant Simulator")
        self.assertEqual(mapping["baseball:sleepers"], "Fantasy Market")


if __name__ == "__main__":
    unittest.main()
