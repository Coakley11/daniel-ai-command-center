"""Cloud session blob helpers."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from suite_cloud_state import (
    FULL_SESSION_KEY,
    has_resume_query_params,
    pick_newer_session,
    session_page_summary,
)


class TestSuiteCloudState(unittest.TestCase):
    def test_has_resume_query_params_suite_page(self) -> None:
        st = MagicMock()
        st.session_state = {}
        st.query_params = {"suite_page": "Comparison Tool"}
        self.assertTrue(has_resume_query_params(st, "baseball"))

    def test_has_resume_query_params_launch_flag(self) -> None:
        st = MagicMock()
        st.session_state = {"_suite_resume_launch_baseball": True}
        st.query_params = {}
        self.assertTrue(has_resume_query_params(st, "baseball"))

    def test_pick_newer_prefers_cloud(self) -> None:
        cloud = {"active_page": "Trending"}
        disk = {"active_page": "Historical Explorer"}
        picked = pick_newer_session(cloud, "2026-06-01T12:00:00", disk, "2026-05-01T12:00:00")
        self.assertEqual(picked["active_page"], "Trending")

    def test_session_page_summary_baseball(self) -> None:
        page, summary = session_page_summary("baseball", {"active_page": "Comparison Tool"})
        self.assertEqual(page, "Comparison Tool")
        self.assertEqual(summary, "Comparison Tool")

    def test_full_session_key_constant(self) -> None:
        self.assertEqual(FULL_SESSION_KEY, "full_session")


if __name__ == "__main__":
    unittest.main()
