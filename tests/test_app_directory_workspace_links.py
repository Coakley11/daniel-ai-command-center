"""App Directory must propagate the active workspace into open URLs (W1)."""

from __future__ import annotations

import unittest
import unittest.mock
from urllib.parse import parse_qs, urlparse

from suite_auth import AUTH_EXTERNAL_ID_KEY, AUTH_SESSION_KEY, enforce_workspace_ownership
from suite_workspace import SESSION_KEY, get_active_workspace_id, set_active_workspace_id


class _FakeState(dict):
    pass


def _fake_st(*, session: _FakeState | None = None) -> object:
    return type("St", (), {"session_state": session or _FakeState(), "query_params": {}})()


class TestAppDirectoryWorkspaceLinks(unittest.TestCase):
    def test_daniel_admin_ariel_active_yields_ariel_music_url(self) -> None:
        from app_registry import get_app_url

        st = _fake_st()
        st.session_state[AUTH_SESSION_KEY] = True
        st.session_state[AUTH_EXTERNAL_ID_KEY] = "daniel"
        set_active_workspace_id(st, "ariel")
        with unittest.mock.patch("suite_auth.is_auth_enabled", return_value=True):
            with unittest.mock.patch("suite_auth.is_authenticated", return_value=True):
                enforce_workspace_ownership(st.session_state)
        self.assertEqual(get_active_workspace_id(st), "ariel")
        url = get_app_url("music", workspace_id=get_active_workspace_id(st))
        params = parse_qs(urlparse(url).query)
        self.assertEqual(params.get("suite_workspace", [""])[0], "ariel")


if __name__ == "__main__":
    unittest.main()
