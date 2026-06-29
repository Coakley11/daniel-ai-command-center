"""Account & Workspace — minimal normal-mode UI."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch


class TestAccountWorkspaceMinimalUi(unittest.TestCase):
    def test_normal_mode_expander_shows_email_and_logout_only(self) -> None:
        st = MagicMock()
        st.session_state = {"_suite_auth_email": "DanielCohen11@yahoo.com"}
        ui = MagicMock()
        st.sidebar = ui
        ctx = {
            "active_workspace_label": "Daniel",
            "active_workspace_id": "daniel",
            "email_display": "DanielCohen11@yahoo.com",
        }
        with patch("suite_account_settings.init_suite_workspace"):
            with patch("suite_account_settings.build_account_settings_context", return_value=ctx):
                with patch("suite_workspace.can_show_developer_tools", return_value=False):
                    with patch("suite_auth.is_auth_enabled", return_value=True):
                        with patch("suite_auth.is_authenticated", return_value=True):
                            with patch("suite_auth.current_auth_email", return_value="DanielCohen11@yahoo.com"):
                                with patch("suite_auth.logout"):
                                    from suite_account_settings import render_account_workspace_access

                                    render_account_workspace_access(st, sidebar=True)
        ui.expander.assert_called_once()
        label = ui.expander.call_args[0][0]
        self.assertIn("Account & Workspace", label)
        self.assertIn("Daniel", label)
        ui.markdown.assert_called()
        markdown_text = " ".join(str(call.args[0]) for call in ui.markdown.call_args_list)
        self.assertIn("Signed in:", markdown_text)
        self.assertIn("DanielCohen11@yahoo.com", markdown_text)
        self.assertNotIn("Active workspace", markdown_text)
        ui.button.assert_called_once()

    def test_dev_mode_uses_full_settings_panel(self) -> None:
        st = MagicMock()
        with patch("suite_account_settings.init_suite_workspace"):
            with patch("suite_account_settings.build_account_settings_context", return_value={}):
                with patch("suite_workspace.can_show_developer_tools", return_value=True):
                    with patch("suite_auth.is_auth_enabled", return_value=False):
                        with patch("suite_account_settings.render_account_settings_panel") as panel:
                            from suite_account_settings import render_account_workspace_access

                            render_account_workspace_access(st, sidebar=True)
                            panel.assert_called_once()


if __name__ == "__main__":
    unittest.main()
