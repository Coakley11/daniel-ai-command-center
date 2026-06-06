"""Resume launch query-param application (Command Center shared module)."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
class _FakeQueryParams(dict):
    def get(self, key, default=None):
        return super().get(key, default)


class TestSuiteResumeLaunch(unittest.TestCase):
    def _st(self, params: dict[str, str]) -> SimpleNamespace:
        return SimpleNamespace(
            session_state={},
            query_params=_FakeQueryParams(params),
        )

    def test_music_restore_pick_key_display_key_section(self) -> None:
        st = self._st(
            {
                "suite_resume": "song:Pop|Perfect",
                "suite_page": "practice",
                "suite_pick_key": "Pop|Perfect",
                "suite_display_key": "D Major",
                "suite_section_focus": "Chorus",
            }
        )
        from suite_resume_launch import apply_suite_resume_launch

        self.assertTrue(apply_suite_resume_launch(st, "music"))
        self.assertEqual(st.session_state["active_catalog_pick_key"], "Pop|Perfect")
        self.assertEqual(st.session_state["practice_focus_section"], "Chorus")
        self.assertIn(st.session_state.get("studio_page"), ("practice", None))

    def test_baseball_compare_players_and_page(self) -> None:
        st = self._st(
            {
                "suite_resume": "compare:Juan Soto:Mike Piazza",
                "suite_page": "Comparison Tool",
                "suite_player_a": "Juan Soto",
                "suite_player_b": "Mike Piazza",
            }
        )
        from suite_resume_launch import apply_suite_resume_launch

        self.assertTrue(apply_suite_resume_launch(st, "baseball"))
        self.assertEqual(st.session_state["pending_sig_player_a"], "Juan Soto")
        self.assertEqual(st.session_state["pending_sig_player_b"], "Mike Piazza")
        self.assertEqual(st.session_state["pending_compare_players"], ["Juan Soto", "Mike Piazza"])
        self.assertEqual(st.session_state["_navigate_to_page"], "Comparison Tool")

    def test_investment_tab_and_holdings_fp(self) -> None:
        st = self._st(
            {
                "suite_resume": "portfolio:health",
                "suite_page": "Portfolio Health",
                "suite_holdings_fp": "SPY:60.0:Equity|BND:40.0:Bonds",
            }
        )
        from suite_resume_launch import apply_suite_resume_launch

        self.assertTrue(apply_suite_resume_launch(st, "investment"))
        self.assertEqual(st.session_state["_suite_investment_page"], "Portfolio Health")
        self.assertEqual(st.session_state["_suite_holdings_fp"], "SPY:60.0:Equity|BND:40.0:Bonds")

    def test_nba_knicks_live_game_center(self) -> None:
        st = self._st(
            {
                "suite_resume": "nba:game:New York Knicks",
                "suite_page": "🔴 Live Game Center",
                "suite_team": "New York Knicks",
            }
        )
        from suite_resume_launch import apply_suite_resume_launch

        self.assertTrue(apply_suite_resume_launch(st, "nba"))
        self.assertEqual(st.session_state["_nba_restore_team"], "New York Knicks")
        self.assertEqual(st.session_state["page_override"], "🔴 Live Game Center")


if __name__ == "__main__":
    unittest.main()
