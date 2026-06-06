"""Deep-link URL building for Command Center Continue buttons."""

from __future__ import annotations

import unittest
from urllib.parse import parse_qs, urlparse

from suite_deep_links import build_resume_action_url, resume_metrics_from_item_key


def _params(url: str) -> dict[str, str]:
    parsed = urlparse(url)
    raw = parse_qs(parsed.query)
    return {k: v[0] for k, v in raw.items()}


class TestSuiteDeepLinks(unittest.TestCase):
    def test_music_perfect_practice(self) -> None:
        url = build_resume_action_url(
            "music",
            resume_key="song:Pop|Perfect",
            page="Practice Log",
            metrics={
                "song": "Perfect",
                "artist": "Ed Sheeran",
                "pick_key": "Pop|Perfect",
                "display_key": "D Major",
                "practice_focus_section": "Verse",
            },
        )
        p = _params(url)
        self.assertEqual(p["suite_resume"], "song:Pop|Perfect")
        self.assertEqual(p["suite_page"], "practice")
        self.assertEqual(p["suite_pick_key"], "Pop|Perfect")
        self.assertEqual(p["suite_song"], "Perfect")
        self.assertEqual(p["suite_display_key"], "D Major")
        self.assertEqual(p["suite_section_focus"], "Verse")

    def test_investment_portfolio_health(self) -> None:
        url = build_resume_action_url(
            "investment",
            resume_key="portfolio:health",
            page="Portfolio Health",
            metrics={
                "holdings_fingerprint": "SPY:60.0:Equity|BND:40.0:Bonds",
                "review_type": "Moderate",
            },
        )
        p = _params(url)
        self.assertEqual(p["suite_resume"], "portfolio:health")
        self.assertEqual(p["suite_page"], "Portfolio Health")
        self.assertIn("SPY", p["suite_holdings_fp"])

    def test_baseball_player_comparison(self) -> None:
        url = build_resume_action_url(
            "baseball",
            resume_key="compare:Juan Soto:Mike Piazza",
            page="Comparison Tool",
            metrics={"player_a": "Juan Soto", "player_b": "Mike Piazza"},
        )
        p = _params(url)
        self.assertEqual(p["suite_resume"], "compare:Juan Soto:Mike Piazza")
        self.assertEqual(p["suite_page"], "Comparison Tool")
        self.assertEqual(p["suite_player_a"], "Juan Soto")
        self.assertEqual(p["suite_player_b"], "Mike Piazza")

    def test_nba_knicks_live_game_center(self) -> None:
        url = build_resume_action_url(
            "nba",
            resume_key="nba:game:New York Knicks",
            page="🔴 Live Game Center",
            metrics={"team": "New York Knicks"},
        )
        p = _params(url)
        self.assertEqual(p["suite_resume"], "nba:game:New York Knicks")
        self.assertEqual(p["suite_page"], "🔴 Live Game Center")
        self.assertEqual(p["suite_team"], "New York Knicks")

    def test_resume_metrics_from_compare_key(self) -> None:
        page, metrics = resume_metrics_from_item_key(
            "baseball",
            "compare:Aaron Judge:Juan Soto",
            subtitle="Aaron Judge vs Juan Soto",
        )
        self.assertEqual(page, "Comparison Tool")
        self.assertEqual(metrics["player_a"], "Aaron Judge")
        self.assertEqual(metrics["player_b"], "Juan Soto")

    def test_baseball_draft_resume_key_aliases(self) -> None:
        for key in ("baseball:draft", "baseball:draft_prep", "bb:draft"):
            url = build_resume_action_url("baseball", resume_key=key, page="")
            p = _params(url)
            self.assertEqual(p["suite_page"], "Draft Simulation", msg=key)


if __name__ == "__main__":
    unittest.main()
