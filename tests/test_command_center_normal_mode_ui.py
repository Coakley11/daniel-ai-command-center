"""Command Center — normal mode hides admin diagnostics."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch


class TestSuiteAppShellAccountPanel(unittest.TestCase):
    def test_normal_mode_uses_user_account_access(self) -> None:
        st = MagicMock()
        with patch("suite_workspace.can_show_developer_tools", return_value=False):
            with patch("suite_account_settings.render_user_account_access") as user_access:
                with patch("suite_account_settings.render_account_settings_panel") as full_panel:
                    with patch("suite_account_settings.render_global_workspace_badge"):
                        from suite_app_shell import render_suite_sidebar_account_shell

                        render_suite_sidebar_account_shell(st, show_command_center_link=False)
                        user_access.assert_called_once()
                        full_panel.assert_not_called()

    def test_dev_mode_shows_full_account_panel(self) -> None:
        st = MagicMock()
        with patch("suite_workspace.can_show_developer_tools", return_value=True):
            with patch("suite_account_settings.render_user_account_access") as user_access:
                with patch("suite_account_settings.render_account_settings_panel") as full_panel:
                    with patch("suite_account_settings.render_global_workspace_badge"):
                        from suite_app_shell import render_suite_sidebar_account_shell

                        render_suite_sidebar_account_shell(st, show_command_center_link=False)
                        full_panel.assert_called_once()
                        user_access.assert_not_called()


if __name__ == "__main__":
    unittest.main()
