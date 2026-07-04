"""Music Command Center UI — workspace isolation and deep-link contracts."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from activity_store import ActivitySnapshot
from continue_dashboard import ContinueCard
from music_command_center_dashboard import (
    event_matches_active_workspace,
    merge_music_continue_cards,
    music_workstream_cards,
    payload_from_action_url,
    resolve_music_continue_action_url,
)
from music_resume_payload import build_music_resume_payload, encode_payload_b64
from suite_deep_links import build_music_continue_url, build_music_workstream_url


def _practice_payload(*, workspace_id: str = "daniel") -> dict:
    return build_music_resume_payload(
        {
            "_suite_active_workspace_id": workspace_id,
            "studio_page": "practice",
            "active_catalog_pick_key": "Pop|Shape of You — Ed Sheeran",
            "song": "Shape of You",
            "instrument": "Tenor Sax",
            "display_key": "B minor",
            "bpm": 90,
        },
        workspace_id=workspace_id,
    )


class TestMusicCommandCenterDashboard(unittest.TestCase):
    def test_continue_url_has_payload_and_entry_mode(self) -> None:
        payload = _practice_payload(workspace_id="coakley11")
        url = build_music_continue_url(payload)
        self.assertIn("suite_entry_mode=continue", url)
        self.assertIn("suite_resume_payload=", url)
        self.assertIn("suite_workspace=coakley11", url)

    def test_workstream_url_soft_entry(self) -> None:
        url = build_music_workstream_url("backing", workspace_id="coakley11")
        self.assertIn("suite_entry_mode=workstream", url)
        self.assertIn("suite_page=backing", url)
        self.assertIn("suite_workspace=coakley11", url)
        self.assertNotIn("suite_pick_key", url)
        self.assertNotIn("suite_resume_payload", url)

    def test_payload_round_trip_from_action_url(self) -> None:
        payload = _practice_payload(workspace_id="daniel")
        url = build_music_continue_url(payload)
        decoded = payload_from_action_url(url)
        self.assertEqual(decoded.get("workspace_id"), "daniel")
        self.assertEqual(decoded.get("song"), "Shape of You")

    def test_event_workspace_isolation(self) -> None:
        with patch("music_command_center_dashboard.active_workspace_id", return_value="coakley11"):
            daniel_event = {
                "app": "music",
                "metrics": {"workspace_id": "daniel", "song": "Shape of You"},
            }
            coakley_event = {
                "app": "music",
                "metrics": {"workspace_id": "coakley11", "song": "Autumn Leaves"},
            }
            self.assertFalse(event_matches_active_workspace(daniel_event))
            self.assertTrue(event_matches_active_workspace(coakley_event))

    def test_resolve_music_continue_rejects_foreign_payload(self) -> None:
        payload = _practice_payload(workspace_id="daniel")
        with patch("music_command_center_dashboard.active_workspace_id", return_value="coakley11"):
            url = resolve_music_continue_action_url(
                {"resume_payload": payload},
                base_url="https://music.example.app",
            )
            self.assertEqual(url, "")

    def test_resolve_music_continue_accepts_matching_workspace(self) -> None:
        payload = _practice_payload(workspace_id="coakley11")
        with patch("music_command_center_dashboard.active_workspace_id", return_value="coakley11"):
            url = resolve_music_continue_action_url(
                {"resume_payload": payload},
                base_url="https://music.example.app",
            )
            self.assertIn("suite_resume_payload=", url)
            self.assertIn("suite_entry_mode=continue", url)

    def test_merge_music_continue_cards_prioritizes_music(self) -> None:
        music_card = ContinueCard(
            app_key="music",
            app_name="Music Practice Coach",
            title="Continue Shape of You — Tenor Sax — Key: B minor — 90 BPM",
            subtitle="practice",
            action_url="https://music.example/?suite_entry_mode=continue&suite_resume_payload=abc",
            emoji="🎵",
        )
        other = ContinueCard(
            app_key="investment",
            app_name="Investment",
            title="Review portfolio",
            subtitle="",
            action_url="https://inv.example/",
            emoji="📈",
        )
        with patch(
            "music_command_center_dashboard.music_continue_cards_from_resume_items",
            return_value=[music_card],
        ):
            merged = merge_music_continue_cards([other], limit=6)
        self.assertEqual(merged[0].app_key, "music")
        self.assertEqual(len(merged), 2)

    def test_workstream_cards_use_soft_urls(self) -> None:
        snap = ActivitySnapshot(last_song="Shape of You")
        with patch("music_command_center_dashboard.active_workspace_id", return_value="daniel"):
            with patch(
                "music_command_center_dashboard._payloads_from_snapshot",
                return_value=[_practice_payload(workspace_id="daniel")],
            ):
                cards = music_workstream_cards(snap)
        self.assertGreaterEqual(len(cards), 6)
        for card in cards:
            url = str(card.get("action_url") or "")
            self.assertIn("suite_entry_mode=workstream", url)
            self.assertNotIn("suite_resume_payload", url)
            self.assertNotIn("suite_pick_key", url)

    def test_resume_item_card_filters_wrong_workspace(self) -> None:
        from music_command_center_dashboard import _resume_item_to_continue_card

        payload = _practice_payload(workspace_id="daniel")
        url = build_music_continue_url(payload)
        item = MagicMock(
            title="Continue Shape of You",
            subtitle="practice",
            action_url=url,
        )
        with patch("music_command_center_dashboard.active_workspace_id", return_value="coakley11"):
            card = _resume_item_to_continue_card(
                item,
                music_url="https://music.example.app",
                themes={"music": "🎵"},
            )
        self.assertIsNone(card)


if __name__ == "__main__":
    unittest.main()
