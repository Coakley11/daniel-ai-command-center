"""Command Center — normal mode hides admin diagnostics."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch


class TestSuiteAppShellAccountPanel(unittest.TestCase):
    def test_normal_mode_uses_collapsed_account_workspace(self) -> None:
        st = MagicMock()
        with patch("suite_workspace.can_show_developer_tools", return_value=False):
            with patch("suite_account_settings.render_account_workspace_access") as workspace_access:
                from suite_app_shell import render_suite_sidebar_account_shell

                render_suite_sidebar_account_shell(st, show_command_center_link=False)
                workspace_access.assert_called_once()
                self.assertTrue(workspace_access.call_args.kwargs.get("sidebar"))

    def test_dev_mode_shows_full_account_panel_via_workspace_access(self) -> None:
        st = MagicMock()
        with patch("suite_workspace.can_show_developer_tools", return_value=True):
            with patch("suite_account_settings.render_account_workspace_access") as workspace_access:
                from suite_app_shell import render_suite_sidebar_account_shell

                render_suite_sidebar_account_shell(st, show_command_center_link=False)
                workspace_access.assert_called_once()


if __name__ == "__main__":
    unittest.main()
