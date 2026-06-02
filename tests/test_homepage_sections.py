"""Homepage sections must exist and underlying logic must not raise."""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from activity_store import ActivitySnapshot
from homepage_sections import (
    HOMEPAGE_RENDERERS,
    activity_feed_items,
    cross_app_insights_for_snapshot,
    load_homepage_context,
    weekly_lines_for_snapshot,
)

COMMAND_CENTER = Path(__file__).resolve().parent.parent / "ai_command_center.py"


def _defined_functions(source_path: Path) -> set[str]:
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}


class TestHomepageSections(unittest.TestCase):
    def test_renderer_functions_defined_in_command_center(self) -> None:
        defined = _defined_functions(COMMAND_CENTER)
        for name in HOMEPAGE_RENDERERS:
            self.assertIn(name, defined, f"{name} missing from ai_command_center.py")

    def test_cross_app_call_in_main_flow(self) -> None:
        tree = ast.parse(COMMAND_CENTER.read_text(encoding="utf-8"))
        calls = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in HOMEPAGE_RENDERERS
        }
        self.assertIn("_render_cross_app_section", calls)

    @patch("homepage_sections.load_activity_snapshot")
    @patch("homepage_sections.continue_cards_for_snapshot", return_value=[])
    @patch("homepage_sections.generate_coach_insights", return_value=[])
    def test_load_homepage_context(self, _coach, _cards, mock_load) -> None:
        mock_load.return_value = ActivitySnapshot()
        snapshot, insights, cards = load_homepage_context()
        self.assertIsInstance(snapshot, ActivitySnapshot)
        self.assertIsInstance(insights, list)
        self.assertIsInstance(cards, list)

    def test_cross_app_and_weekly_logic(self) -> None:
        snap = ActivitySnapshot(
            week_activity_by_app={"music": 4, "investment": 2},
            top_project_label="Perfect",
            pending_review_count=2,
        )
        cross = cross_app_insights_for_snapshot(snap)
        self.assertIsInstance(cross, list)
        lines = weekly_lines_for_snapshot(snap)
        self.assertIsInstance(lines, list)
        feed = activity_feed_items(limit=5)
        self.assertIsInstance(feed, list)

    def test_command_center_startup_reaches_all_sections(self) -> None:
        """Import app module (runs homepage body) with Streamlit and I/O stubbed."""
        mock_st = MagicMock()
        mock_st.cache_data = lambda **kwargs: (lambda fn: fn)
        mock_st.columns = lambda n, **kwargs: [MagicMock() for _ in range(n)]
        mock_st.expander = MagicMock(
            return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock())
        )
        empty_snap = ActivitySnapshot()

        saved = dict(sys.modules)
        try:
            sys.modules.pop("ai_command_center", None)
            with patch.dict(sys.modules, {"streamlit": mock_st}):
                with patch(
                    "activity_store.load_activity_snapshot", return_value=empty_snap
                ):
                    with patch("activity_store._sync_disk_user_states_to_storage"):
                        with patch("activity_store._import_sibling_fallback_events"):
                            with patch("activity_store._ingest_music_logs"):
                                with patch(
                                    "continue_dashboard.continue_cards_for_snapshot",
                                    return_value=[],
                                ):
                                    with patch(
                                        "coach_engine.generate_coach_insights",
                                        return_value=[],
                                    ):
                                        with patch(
                                            "app_registry.verify_connections",
                                            return_value=[],
                                        ):
                                            import ai_command_center as cc  # noqa: WPS433

                for name in HOMEPAGE_RENDERERS:
                    fn = getattr(cc, name, None)
                    self.assertTrue(callable(fn), f"{name} not callable on import")

                cc._render_cross_app_section(empty_snap)
                cc._render_weekly_summary(empty_snap)
                cc._render_coach_insights([])
                cc._render_recent_activity_feed()
        finally:
            sys.modules.clear()
            sys.modules.update(saved)
            if isinstance(sys.modules.get("streamlit"), MagicMock):
                del sys.modules["streamlit"]


if __name__ == "__main__":
    unittest.main()
