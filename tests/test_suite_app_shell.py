"""Sprint B — shared account/workspace sidebar shell."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from suite_app_shell import apply_suite_auth_gate, render_suite_sidebar_account_shell


class TestSuiteAppShell(unittest.TestCase):
    def test_render_shell_calls_badge_and_account_panel(self) -> None:
        st = MagicMock()
        st.session_state = {}
        with patch("suite_app_shell.render_suite_namespace_notices") as mock_notices:
            with patch("suite_account_settings.render_global_workspace_badge") as mock_badge:
                with patch("suite_account_settings.render_account_settings_panel") as mock_panel:
                    with patch("suite_command_center_link.render_command_center_sidebar_link") as mock_cc:
                        render_suite_sidebar_account_shell(st)
        mock_notices.assert_called_once()
        mock_badge.assert_called_once()
        mock_panel.assert_called_once()
        mock_cc.assert_called_once()

    def test_render_shell_can_hide_command_center_link(self) -> None:
        st = MagicMock()
        st.session_state = {}
        with patch("suite_app_shell.render_suite_namespace_notices"):
            with patch("suite_account_settings.render_global_workspace_badge"):
                with patch("suite_account_settings.render_account_settings_panel"):
                    with patch("suite_command_center_link.render_command_center_sidebar_link") as mock_cc:
                        render_suite_sidebar_account_shell(st, show_command_center_link=False)
        mock_cc.assert_not_called()

    def test_apply_auth_gate_delegates_to_suite_auth(self) -> None:
        st = MagicMock()
        with patch("suite_auth.render_auth_gate", return_value=True) as mock_gate:
            apply_suite_auth_gate(st)
        mock_gate.assert_called_once_with(st)


if __name__ == "__main__":
    unittest.main()
