"""Continue vs App Directory classification — passive events and music dedupe."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from activity_store import ActivitySnapshot, get_app_directory_card
from project_intelligence import (
    _consolidate_music_continue_rows,
    _continue_merge_key,
    _projects_from_events,
    build_project_continue_cards,
)


class TestContinueClassification(unittest.TestCase):
    def test_song_selected_does_not_emit_continue(self) -> None:
        snap = ActivitySnapshot()
        recent = (datetime.now() - timedelta(hours=1)).isoformat(timespec="seconds")
        events = [
            {
                "app": "music",
                "event": "song_selected",
                "timestamp": recent,
                "metrics": {"song": "Turn the Lights Back On", "pick_key": "turn_lights"},
            },
        ]
        with patch("project_intelligence.load_all_events", return_value=events):
            cards = _projects_from_events(snap)
        self.assertEqual([c for c in cards if c[1] == "music"], [])

    def test_holdings_updated_does_not_emit_continue(self) -> None:
        snap = ActivitySnapshot()
        recent = (datetime.now() - timedelta(hours=1)).isoformat(timespec="seconds")
        events = [
            {
                "app": "investment",
                "event": "holdings_updated",
                "timestamp": recent,
                "metrics": {"holdings": 5},
            },
        ]
        with patch("project_intelligence.load_all_events", return_value=events):
            cards = _projects_from_events(snap)
        self.assertEqual([c for c in cards if c[1] == "investment"], [])

    def test_backing_track_emits_continue(self) -> None:
        snap = ActivitySnapshot()
        recent = (datetime.now() - timedelta(hours=1)).isoformat(timespec="seconds")
        events = [
            {
                "app": "music",
                "event": "backing_track_started",
                "timestamp": recent,
                "metrics": {
                    "song": "Turn the Lights Back On",
                    "pick_key": "turn_lights",
                    "studio_page": "backing",
                },
            },
        ]
        with patch("project_intelligence.load_all_events", return_value=events):
            cards = _projects_from_events(snap)
        music = [c for c in cards if c[1] == "music"]
        self.assertEqual(len(music), 1)
        self.assertIn("Turn the Lights Back On", music[0][2])

    def test_music_dedupe_one_card_per_song(self) -> None:
        snap = ActivitySnapshot()
        recent = (datetime.now() - timedelta(hours=1)).isoformat(timespec="seconds")
        events = [
            {
                "app": "music",
                "event": "practice",
                "timestamp": recent,
                "metrics": {"song": "Perfect", "pick_key": "perfect"},
            },
            {
                "app": "music",
                "event": "backing_track_started",
                "timestamp": recent,
                "metrics": {"song": "Perfect", "pick_key": "perfect", "studio_page": "backing"},
            },
        ]
        with patch("project_intelligence.load_all_events", return_value=events):
            cards = _projects_from_events(snap)
        music = [c for c in cards if c[1] == "music"]
        self.assertEqual(len(music), 1)
        self.assertEqual(_continue_merge_key("music", music[0][4], music[0][6]), "music:song:perfect")

    def test_consolidate_music_rows_keeps_highest_priority(self) -> None:
        rows = [
            (42, "music", "Practice", "", "music:practice:x", "practice", {"pick_key": "x"}),
            (61, "music", "Backing", "", "backing:x", "backing", {"pick_key": "x"}),
        ]
        merged = _consolidate_music_continue_rows(rows)
        music = [r for r in merged if r[1] == "music"]
        self.assertEqual(len(music), 1)
        self.assertEqual(music[0][0], 61)

    def test_nba_player_comparison_continue(self) -> None:
        snap = ActivitySnapshot()
        recent = (datetime.now() - timedelta(hours=1)).isoformat(timespec="seconds")
        events = [
            {
                "app": "nba",
                "event": "player_comparison",
                "timestamp": recent,
                "metrics": {
                    "team": "New York Knicks",
                    "player_a": "Jalen Brunson",
                    "player_b": "Tyrese Maxey",
                },
            },
        ]
        with patch("project_intelligence.load_all_events", return_value=events):
            cards = _projects_from_events(snap)
        nba = [c for c in cards if c[1] == "nba"]
        self.assertEqual(len(nba), 1)
        self.assertIn("Jalen Brunson vs Tyrese Maxey", nba[0][2])

    def test_music_resume_card_prefers_newer_song(self) -> None:
        snap = ActivitySnapshot()
        old = (datetime.now() - timedelta(days=3)).isoformat(timespec="seconds")
        recent = (datetime.now() - timedelta(hours=1)).isoformat(timespec="seconds")
        events = [
            {
                "app": "music",
                "event": "practice",
                "timestamp": old,
                "metrics": {"song": "Perfect", "pick_key": "perfect", "instrument": "Voice"},
            },
            {
                "app": "music",
                "event": "backing_track_started",
                "timestamp": recent,
                "metrics": {
                    "song": "Piano Man",
                    "pick_key": "piano_man",
                    "instrument": "Tenor Sax",
                    "studio_page": "backing",
                },
            },
        ]
        with patch("project_intelligence.load_all_events", return_value=events), patch(
            "project_intelligence.load_active_resume_items", return_value=[]
        ):
            cards = build_project_continue_cards(snap, limit=6)
        music = [c for c in cards if c.app_key == "music"]
        self.assertEqual(len(music), 1)
        self.assertIn("Piano Man", music[0].title)
        self.assertIn("Tenor Sax", music[0].subtitle)

    def test_stale_resume_item_does_not_override_recent_event(self) -> None:
        from suite_storage import ResumeItem

        snap = ActivitySnapshot()
        recent = (datetime.now() - timedelta(hours=1)).isoformat(timespec="seconds")
        events = [
            {
                "app": "music",
                "event": "practice",
                "timestamp": recent,
                "metrics": {"song": "Piano Man", "pick_key": "piano_man", "instrument": "Tenor Sax"},
            },
        ]
        stale_item = ResumeItem(
            app="music",
            item_key="song:perfect",
            title="Continue: Perfect",
            subtitle="Voice",
            action_url="https://example.com",
            updated_at=(datetime.now() - timedelta(days=20)).isoformat(timespec="seconds"),
        )
        with patch("project_intelligence.load_all_events", return_value=events), patch(
            "project_intelligence.load_active_resume_items", return_value=[stale_item]
        ):
            cards = build_project_continue_cards(snap, limit=6)
        music = [c for c in cards if c.app_key == "music"]
        self.assertEqual(len(music), 1)
        self.assertIn("Piano Man", music[0].title)

    def test_directory_shows_portfolio_preset_from_snapshot(self) -> None:
        snap = ActivitySnapshot(
            investment_portfolio_preset="Long-term retirement portfolio",
            last_investment_holdings_count=8,
        )
        card = get_app_directory_card(snap, "investment")
        self.assertIn("retirement", card.highlights[0].lower())


if __name__ == "__main__":
    unittest.main()
