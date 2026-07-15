"""Command Center fantasy Continue / Activity / Directory surfaces."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from activity_feed import (
    baseball_directory_chip_line,
    baseball_directory_rank,
    format_activity_message,
)
from fantasy_workflow_activity import (
    fantasy_continue_copy,
    fantasy_resume_key,
    fantasy_resume_page,
    is_fantasy_continue_eligible,
)
from project_intelligence import _MEANINGFUL_WORKFLOW_EVENTS, _projects_from_events, _raw_event_workflow_candidate
from suite_deep_links import build_resume_action_url, resume_metrics_from_item_key


def _fantasy_event(event: str, *, hours_ago: float = 1, **metrics) -> dict:
    return {
        "app": "baseball",
        "event": event,
        "page": "Trade Center",
        "timestamp": (datetime.now() - timedelta(hours=hours_ago)).isoformat(timespec="seconds"),
        "metrics": {
            "proposal_id": "tp:abc123",
            "from_team": "Team X",
            "to_team": "Team Y",
            "trade": "José Ramírez ⇄ Francisco Lindor",
            "league_name": "Robbins League",
            "league_id": "lg-1",
            "my_team": "Team Y",
            **metrics,
        },
    }


class TestFantasyWorkflowActivity(unittest.TestCase):
    def test_trade_offer_feed_and_continue(self) -> None:
        event = _fantasy_event("trade_offer_received")
        msg = format_activity_message(event, for_feed=True)
        self.assertIn("Team X", msg or "")
        self.assertIn("trade_offer_received", _MEANINGFUL_WORKFLOW_EVENTS)
        cand = _raw_event_workflow_candidate(event)
        self.assertIsNotNone(cand)
        assert cand is not None
        self.assertEqual(cand["resume_key"], "bb:trade_center:tp:abc123")
        self.assertIn("Trade offer", cand["title"])

    def test_trade_accepted_supersedes_offer_continue(self) -> None:
        offer = _fantasy_event("trade_offer_received", hours_ago=2)
        accepted = _fantasy_event("trade_accepted", hours_ago=1)
        with patch("project_intelligence.load_all_events", return_value=[accepted, offer]):
            from activity_store import ActivitySnapshot

            projects = _projects_from_events(ActivitySnapshot())
        baseball = [p for p in projects if p[1] == "baseball"]
        self.assertTrue(baseball)
        title = baseball[0][2]
        self.assertIn("completed", title.lower())
        self.assertNotIn("offer from", title.lower())

    def test_invite_removed_after_claim(self) -> None:
        invite = {
            "app": "baseball",
            "event": "shared_league_invite",
            "page": "Saved Draft Library",
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(timespec="seconds"),
            "metrics": {
                "invite_id": "inv-1",
                "league_name": "Robbins League",
                "league_id": "lg-1",
                "as_invitee": True,
            },
        }
        claimed = {
            "app": "baseball",
            "event": "team_claimed",
            "page": "Saved Draft Library",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(timespec="seconds"),
            "metrics": {
                "invite_id": "inv-1",
                "team": "Team Y",
                "league_name": "Robbins League",
                "league_id": "lg-1",
                "draft_id": "d1",
            },
        }
        self.assertFalse(
            is_fantasy_continue_eligible(
                "shared_league_invite",
                invite["metrics"],
                resolved_invites={"inv-1"},
            )
        )
        with patch("project_intelligence.load_all_events", return_value=[claimed, invite]):
            from activity_store import ActivitySnapshot

            projects = _projects_from_events(ActivitySnapshot())
        titles = " ".join(p[2].lower() for p in projects if p[1] == "baseball")
        self.assertNotIn("invited to", titles)

    def test_waiver_completed_is_activity_not_continue(self) -> None:
        self.assertFalse(
            is_fantasy_continue_eligible(
                "waiver_transaction",
                {"league_id": "lg-1", "added": ["A"], "dropped": ["B"]},
            )
        )
        self.assertFalse(
            is_fantasy_continue_eligible(
                "waiver_recommendation",
                {"league_id": "lg-1", "player": "A"},
                completed_waivers={"lg-1"},
            )
        )
        msg = format_activity_message(
            {
                "app": "baseball",
                "event": "waiver_transaction",
                "page": "Waiver Wire / Add-Drop Center",
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "metrics": {
                    "added": ["Tyler Soderstrom"],
                    "dropped": ["Jose Abreu"],
                },
            },
            for_feed=True,
        )
        self.assertIn("Soderstrom", msg or "")

    def test_lineup_reminder_replaced_after_save(self) -> None:
        self.assertFalse(
            is_fantasy_continue_eligible(
                "lineup_reminder",
                {"league_id": "lg-1", "week": 1},
                completed_lineups={"lg-1|w1"},
            )
        )
        title, _, _ = fantasy_continue_copy("lineup_saved", {"week": 1, "league_name": "Robbins"})
        self.assertIn("saved", title.lower())

    def test_waiver_directory_chip_is_short(self) -> None:
        chip = baseball_directory_chip_line(
            "waiver_transaction",
            {"added": ["Tyler Soderstrom"], "dropped": ["Jose Abreu"]},
        )
        self.assertEqual(chip, "Waiver Wire")
        self.assertGreaterEqual(baseball_directory_rank("waiver_transaction"), 4)

    def test_trade_deep_link_targets_trade_center(self) -> None:
        url = build_resume_action_url(
            "baseball",
            resume_key="bb:trade_center:tp:abc123",
            page="Trade Center",
            metrics={"proposal_id": "tp:abc123", "my_team": "Team Y", "league_id": "lg-1"},
            base_url="https://example.test",
        )
        self.assertIn("suite_page=Trade+Center", url.replace("%20", "+"))
        self.assertIn("suite_trade_proposal=tp", url)
        self.assertIn("suite_my_team=Team", url)
        page, m = resume_metrics_from_item_key("baseball", "bb:trade_center:tp:abc123")
        self.assertEqual(page, "Trade Center")
        self.assertEqual(m.get("proposal_id"), "tp:abc123")

    def test_lineup_lock_resume(self) -> None:
        title, subtitle, pri = fantasy_continue_copy("lineup_locked", {"week": 1, "my_team": "Team X"})
        self.assertIn("locked", title.lower())
        self.assertEqual(fantasy_resume_page("lineup_locked"), "Fantasy Lineup Assistant")
        self.assertEqual(fantasy_resume_key("lineup_locked", {"week": 1, "league_id": "lg"}), "bb:lineup:lg:w1")
        self.assertGreaterEqual(pri, 60)

    def test_shared_league_invite_resume(self) -> None:
        key = fantasy_resume_key(
            "shared_league_invite",
            {"invite_id": "inv-1", "league_name": "Robbins League", "as_invitee": True},
        )
        self.assertEqual(key, "bb:invite:inv-1")
        self.assertEqual(fantasy_resume_page("shared_league_invite"), "Saved Draft Library")


if __name__ == "__main__":
    unittest.main()
