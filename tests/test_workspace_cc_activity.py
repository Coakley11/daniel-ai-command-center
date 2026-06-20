"""Command Center aggregation must respect active workspace profile."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from suite_workspace import SESSION_KEY, set_active_workspace_id


class TestWorkspaceCloudReads(unittest.TestCase):
    @patch("suite_storage_supabase._cloud_user_id", return_value="uid-1")
    @patch("suite_storage_supabase._request")
    def test_load_events_filters_by_ariel_workspace(self, mock_req: MagicMock, _uid: MagicMock) -> None:
        mock_req.return_value = [
            {
                "app": "baseball",
                "event": "daniel_compare",
                "page": "Comparison",
                "timestamp": "2026-06-18T10:00:00",
                "metrics": {},
            },
            {
                "app": "baseball__ariel",
                "event": "ariel_compare",
                "page": "Comparison",
                "timestamp": "2026-06-18T11:00:00",
                "metrics": {},
            },
        ]
        with patch(
            "suite_workspace.workspace_storage_app_keys",
            return_value=frozenset({"baseball__ariel", "investment__ariel"}),
        ):
            from suite_storage_supabase import load_events

            events = load_events(limit=10)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event"], "ariel_compare")
        self.assertEqual(events[0]["app"], "baseball")
        params = mock_req.call_args.kwargs.get("params") or mock_req.call_args[1].get("params")
        self.assertIn("baseball__ariel", params["app"])

    @patch("suite_storage_supabase._scoped_user_id", return_value="uid-1")
    @patch("suite_storage_supabase._request")
    def test_load_active_resume_items_scoped_to_workspace(
        self, mock_req: MagicMock, _uid: MagicMock
    ) -> None:
        mock_req.return_value = [
            {
                "app": "applied_intelligence__ariel",
                "item_key": "ami:q1",
                "title": "Ariel AMI",
                "subtitle": "",
                "action_url": "",
                "updated_at": "2026-06-18T12:00:00",
            }
        ]
        with patch(
            "suite_workspace.workspace_storage_app_keys",
            return_value=frozenset({"applied_intelligence__ariel"}),
        ):
            from suite_storage_supabase import load_active_resume_items

            rows = load_active_resume_items(limit=5)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["app"], "applied_intelligence")
        self.assertEqual(rows[0]["title"], "Ariel AMI")

    @patch("suite_storage_supabase._scoped_user_id", return_value="uid-1")
    @patch("suite_storage_supabase._request")
    def test_load_saved_items_excludes_other_profile_rows(
        self, mock_req: MagicMock, _uid: MagicMock
    ) -> None:
        mock_req.return_value = [
            {
                "app": "baseball",
                "item_type": "comparison",
                "item_key": "daniel",
                "title": "Daniel",
                "payload": {},
                "updated_at": "2026-06-18T09:00:00",
            },
            {
                "app": "baseball__ariel",
                "item_type": "comparison",
                "item_key": "ariel",
                "title": "Ariel",
                "payload": {},
                "updated_at": "2026-06-18T10:00:00",
            },
        ]
        with patch(
            "suite_workspace.workspace_storage_app_keys",
            return_value=frozenset({"baseball__ariel"}),
        ):
            from suite_storage_supabase import load_saved_items

            rows = load_saved_items(limit=10)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["item_key"], "ariel")

    @patch("suite_storage_supabase._cloud_user_id", return_value="uid-1")
    @patch("suite_storage_supabase._request")
    def test_load_events_filters_nba_ariel_workspace(self, mock_req: MagicMock, _uid: MagicMock) -> None:
        mock_req.return_value = [
            {
                "app": "nba",
                "event": "daniel_game",
                "page": "Live Game Center",
                "timestamp": "2026-06-18T10:00:00",
                "metrics": {},
            },
            {
                "app": "nba__ariel",
                "event": "ariel_game",
                "page": "Playoff Bracket",
                "timestamp": "2026-06-18T11:00:00",
                "metrics": {},
            },
        ]
        with patch(
            "suite_workspace.workspace_storage_app_keys",
            return_value=frozenset({"nba__ariel", "investment__ariel"}),
        ):
            from suite_storage_supabase import load_events

            events = load_events(limit=10)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event"], "ariel_game")
        self.assertEqual(events[0]["app"], "nba")

    @patch("suite_storage_supabase._cloud_user_id", return_value="uid-1")
    @patch("suite_storage_supabase._request")
    def test_load_events_filters_future_lens_ariel_workspace(self, mock_req: MagicMock, _uid: MagicMock) -> None:
        mock_req.return_value = [
            {
                "app": "future_lens",
                "event": "daniel_sim",
                "page": "Simulation",
                "timestamp": "2026-06-18T10:00:00",
                "metrics": {},
            },
            {
                "app": "future_lens__ariel",
                "event": "ariel_sim",
                "page": "Simulation",
                "timestamp": "2026-06-18T11:00:00",
                "metrics": {},
            },
        ]
        with patch(
            "suite_workspace.workspace_storage_app_keys",
            return_value=frozenset({"future_lens__ariel", "investment__ariel"}),
        ):
            from suite_storage_supabase import load_events

            events = load_events(limit=10)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event"], "ariel_sim")
        self.assertEqual(events[0]["app"], "future_lens")


class TestWorkspaceAmiActivity(unittest.TestCase):
    @patch("suite_storage_supabase._cloud_user_id", return_value="uid-1")
    @patch("suite_storage_supabase._request")
    def test_load_events_filters_applied_intelligence_ariel_workspace(
        self, mock_req: MagicMock, _uid: MagicMock
    ) -> None:
        mock_req.return_value = [
            {
                "app": "applied_intelligence",
                "event": "daniel_ami",
                "page": "Solve a Problem",
                "timestamp": "2026-06-18T10:00:00",
                "metrics": {"workspace_id": "daniel"},
            },
            {
                "app": "applied_intelligence__ariel",
                "event": "ariel_ami",
                "page": "Solve a Problem",
                "timestamp": "2026-06-18T11:00:00",
                "metrics": {"workspace_id": "ariel"},
            },
        ]
        with patch(
            "suite_workspace.workspace_storage_app_keys",
            return_value=frozenset({"applied_intelligence__ariel"}),
        ):
            from suite_storage_supabase import load_events

            events = load_events(limit=10)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event"], "ariel_ami")
        self.assertEqual(events[0]["app"], "applied_intelligence")


class TestArielAmiWriteCcRead(unittest.TestCase):
    @patch("suite_storage_supabase._cloud_user_id", return_value="uid-1")
    @patch("suite_storage_supabase._request")
    def test_ariel_session_activity_visible_in_cc_reads(self, mock_req: MagicMock, _uid: MagicMock) -> None:
        mock_req.return_value = [
            {
                "app": "applied_intelligence__ariel",
                "event": "session_activity",
                "page": "Explore a Math Idea",
                "timestamp": "2026-06-20T12:00:00",
                "metrics": {"workspace_id": "ariel", "view_mode": "Explore a Math Idea"},
            }
        ]
        with patch(
            "suite_workspace.workspace_storage_app_keys",
            return_value=frozenset({"applied_intelligence__ariel"}),
        ):
            from suite_storage_supabase import load_events

            events = load_events(limit=10)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event"], "session_activity")
        self.assertEqual(events[0]["app"], "applied_intelligence")
        self.assertEqual(events[0]["page"], "Explore a Math Idea")

    @patch("suite_storage_supabase._cloud_user_id", return_value="uid-1")
    @patch("suite_storage_supabase._request")
    def test_ariel_current_state_page_from_full_session(self, mock_req: MagicMock, _uid: MagicMock) -> None:
        mock_req.return_value = [
            {
                "app": "applied_intelligence__ariel",
                "page": "",
                "summary": "Explore a Math Idea",
                "metrics": {
                    "full_session": {
                        "view_mode": "Explore a Math Idea",
                        "_ami_ui_state": {"mie_example": "Derivative"},
                    }
                },
                "updated_at": "2026-06-20T12:00:00",
            }
        ]
        with patch(
            "suite_workspace.workspace_storage_app_keys",
            return_value=frozenset({"applied_intelligence__ariel"}),
        ):
            from suite_storage_supabase import load_current_states

            states = load_current_states()
        self.assertEqual(states["applied_intelligence"]["page"], "Explore a Math Idea")


class TestWorkspaceSqliteReads(unittest.TestCase):
    def test_sqlite_load_events_respects_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            db_path = data / "suite_activity.db"
            with patch("suite_storage.DATA_DIR", data), patch("suite_storage.DB_PATH", db_path):
                from suite_storage import _sqlite_append_event, _sqlite_load_events

                with patch("suite_storage._scoped_storage_app", side_effect=["baseball", "baseball__ariel"]):
                    _sqlite_append_event("baseball", "daniel_event")
                    _sqlite_append_event("baseball", "ariel_event")
                with patch(
                    "suite_storage._workspace_storage_keys",
                    return_value=frozenset({"baseball__ariel"}),
                ):
                    events = _sqlite_load_events(limit=10)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event"], "ariel_event")
        self.assertEqual(events[0]["app"], "baseball")


class TestWorkspaceFutureLensIsolation(unittest.TestCase):
    @patch("suite_storage_supabase._cloud_user_id", return_value="uid-1")
    @patch("suite_storage_supabase._request")
    def test_daniel_profile_excludes_ariel_future_lens_events(
        self, mock_req: MagicMock, _uid: MagicMock
    ) -> None:
        mock_req.return_value = [
            {
                "app": "future_lens",
                "event": "daniel_sim",
                "page": "Simulation",
                "timestamp": "2026-06-18T10:00:00",
                "metrics": {"workspace_id": "daniel"},
            },
            {
                "app": "future_lens__ariel",
                "event": "ariel_sim",
                "page": "Career",
                "timestamp": "2026-06-18T11:00:00",
                "metrics": {"workspace_id": "ariel"},
            },
        ]
        with patch(
            "suite_workspace.workspace_storage_app_keys",
            return_value=frozenset({"future_lens", "baseball", "investment"}),
        ):
            from suite_storage_supabase import load_events

            events = load_events(limit=10)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event"], "daniel_sim")
        self.assertEqual(events[0]["app"], "future_lens")
        params = mock_req.call_args.kwargs.get("params") or mock_req.call_args[1].get("params")
        self.assertIn("future_lens", params["app"])
        self.assertNotIn("future_lens__ariel", params["app"])


class TestWorkspaceSwitchCacheClear(unittest.TestCase):
    def test_profile_switch_clears_cc_session_keys(self) -> None:
        cleared: list[str] = []

        class FakeState(dict):
            pass

        st = type("St", (), {"session_state": FakeState({SESSION_KEY: "daniel"})})()
        st.session_state["_cc_snapshot"] = {}
        st.session_state["_ami_recent"] = []
        st.session_state["activity_feed_cache"] = True
        with patch("streamlit.cache_data") as mock_cache:
            mock_cache.clear.side_effect = lambda: cleared.append("cache")
            set_active_workspace_id(st, "ariel")
        self.assertEqual(st.session_state[SESSION_KEY], "ariel")
        self.assertNotIn("_cc_snapshot", st.session_state)
        self.assertNotIn("_ami_recent", st.session_state)
        self.assertNotIn("activity_feed_cache", st.session_state)
        self.assertEqual(cleared, ["cache"])


if __name__ == "__main__":
    unittest.main()
