"""Canonical Baseball Continue contract (Historical, Hall of Fame, Draft Lab) and the lazy Music import.

Baseball receives these links (suite_resume_launch._apply_baseball); syncing this module into Baseball must not drop
them again, as the 2026-07-16 sync did.
"""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from suite_deep_links import build_resume_action_url, resume_metrics_from_item_key

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://baseball.example"


def _q(url: str) -> dict[str, str]:
    return {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}


class BaseballContinueContractTests(unittest.TestCase):
    def test_historical_link_carries_stat_and_years(self) -> None:
        q = _q(build_resume_action_url("baseball", resume_key="historical:SB:2002-2025", base_url=BASE))
        self.assertEqual((q["suite_page"], q["suite_historical_stat"], q["suite_historical_year_start"],
                          q["suite_historical_year_end"]), ("Historical Explorer", "SB", "2002", "2025"))

    def test_rebuilt_historical_card_has_the_page_not_the_subtitle(self) -> None:
        page, metrics = resume_metrics_from_item_key("baseball", "historical:SB:2002-2025", subtitle="Jose Reyes · SB · 2002–2025")
        self.assertEqual((page, metrics), ("Historical Explorer", {"sort_stat": "SB", "year_start": "2002", "year_end": "2025"}))

    def test_hall_of_fame_link_carries_case_and_target(self) -> None:
        q = _q(build_resume_action_url("baseball", resume_key="bb:hof_case:joey-votto",
                                       metrics={"target_player": "Joey Votto"}, base_url=BASE))
        self.assertEqual((q["suite_page"], q["suite_hof_case"], q["suite_hof_target"]), ("Career Totals", "1", "Joey Votto"))

    def test_rebuilt_hall_of_fame_card_never_uses_the_prose_subtitle_as_target(self) -> None:
        page, metrics = resume_metrics_from_item_key("baseball", "bb:hof_case:joey-votto",
                                                     subtitle="Hall of Fame statistical case for Joey Votto · cohort 17")
        q = _q(build_resume_action_url("baseball", resume_key="bb:hof_case:joey-votto", page=page, metrics=metrics, base_url=BASE))
        self.assertEqual(page, "Career Totals")
        self.assertEqual(q["suite_hof_case"], "1")
        self.assertNotIn("suite_hof_target", q)  # Baseball resolves the target from the key's slug

    def test_rebuilt_hall_of_fame_card_uses_a_subtitle_that_is_the_targets_name(self) -> None:
        page, metrics = resume_metrics_from_item_key("baseball", "bb:hof_case:albert-pujols", subtitle="Albert Pujols")
        self.assertEqual((page, metrics.get("hof_case_mode"), metrics.get("target_player")), ("Career Totals", True, "Albert Pujols"))

    def test_draft_lab_card_opens_draft_lab_team_analysis(self) -> None:
        page, metrics = resume_metrics_from_item_key("baseball", "bb:draft_lab:team:QADL01")
        q = _q(build_resume_action_url("baseball", resume_key="bb:draft_lab:team:QADL01", page=page, metrics=metrics, base_url=BASE))
        self.assertEqual((q["suite_page"], q["suite_draft_room"], q["suite_draft_section"]),
                         ("Draft Lab / Simulation", "QADL01", "team_analysis"))

    def test_applied_intelligence_hof_link_keeps_the_case(self) -> None:
        q = _q(build_resume_action_url("applied_intelligence", resume_key="ai:question:q9",
                                       metrics={"quant_area": "hall_of_fame_case", "target_player": "Joey Votto"}, base_url=BASE))
        self.assertEqual((q["suite_hof_case"], q["suite_hof_target"]), ("1", "Joey Votto"))


class MusicImportBoundaryTests(unittest.TestCase):
    def test_non_music_links_build_without_the_music_module(self) -> None:
        code = textwrap.dedent("""
            import importlib.abc, json, sys
            class Block(importlib.abc.MetaPathFinder):
                def find_spec(self, name, path, target=None):
                    if name == "music_resume_payload":
                        raise ModuleNotFoundError(name)
            sys.meta_path.insert(0, Block())
            import suite_deep_links as d
            urls = [d.build_resume_action_url(a, resume_key=k, base_url="https://x.example")
                    for a, k in (("baseball", "historical:HR:2010-2025"), ("baseball", "bb:hof_case:a-b"),
                                 ("investment", "portfolio:health"), ("nba", "nba:matchup:Knicks"), ("music", "song:p1"))]
            try:
                d.build_music_continue_url({"resume_kind": "backing", "pick_key": "p"}, base_url="https://m.example")
                typed = "built"
            except ModuleNotFoundError:
                typed = "needs module"
            print(json.dumps({"urls": urls, "typed": typed}))
        """)
        out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, timeout=120)
        self.assertEqual(out.returncode, 0, out.stderr)
        res = json.loads(out.stdout.strip().splitlines()[-1])
        self.assertTrue(all(u.startswith("https://x.example/?") for u in res["urls"]))
        self.assertEqual(res["typed"], "needs module")

    def test_music_payload_names_still_resolve_where_the_module_exists(self) -> None:
        import suite_deep_links as d

        self.assertTrue(callable(d.encode_payload_b64))
        self.assertTrue(callable(d.normalize_resume_kind))


if __name__ == "__main__":
    unittest.main()
