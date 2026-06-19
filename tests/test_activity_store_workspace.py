"""Activity store disk reads must prefer workspace-scoped user state paths."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class TestActivityStoreWorkspacePaths(unittest.TestCase):
    def test_user_state_paths_put_workspace_segment_first(self) -> None:
        with patch("suite_workspace.get_active_workspace_id", return_value="ariel"):
            from activity_store import _user_state_paths

            paths = _user_state_paths("nba")
        self.assertGreaterEqual(len(paths), 2)
        self.assertIn("workspaces", str(paths[0]))
        self.assertIn("ariel", str(paths[0]))
        self.assertEqual(paths[0].name, "nba_user_state.json")

    def test_load_app_user_state_prefers_workspace_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            nba_data = Path(tmp) / "data"
            ws_file = nba_data / "workspaces" / "ariel" / "nba_user_state.json"
            legacy = nba_data / "nba_user_state.json"
            ws_file.parent.mkdir(parents=True)
            ws_file.write_text(
                json.dumps({"state": {"favorite_team": "Boston Celtics"}}),
                encoding="utf-8",
            )
            legacy.write_text(
                json.dumps({"state": {"favorite_team": "New York Knicks"}}),
                encoding="utf-8",
            )

            def fake_paths(app_key: str) -> tuple[Path, ...]:
                if app_key == "nba":
                    return (ws_file, legacy)
                return ()

            with patch("activity_store._user_state_paths", side_effect=fake_paths):
                from activity_store import load_app_user_state_block

                block = load_app_user_state_block("nba")

            self.assertEqual(block.get("favorite_team"), "Boston Celtics")


if __name__ == "__main__":
    unittest.main()
