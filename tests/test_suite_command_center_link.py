"""Tests for suite Command Center return link."""

from __future__ import annotations

from suite_command_center_link import command_center_url, render_command_center_sidebar_link


def test_command_center_url_uses_dev_fallback():
    url = command_center_url()
    assert url.startswith("https://")
    assert "daniel-ai-command-center" in url


def test_render_command_center_sidebar_link_calls_sidebar(monkeypatch):
    calls: list[tuple[str, str]] = []

    class _Sidebar:
        def link_button(self, label, url, **kwargs):
            calls.append((label, url))

        def divider(self):
            calls.append(("divider", ""))

    class _St:
        sidebar = _Sidebar()

    render_command_center_sidebar_link(_St())
    assert calls[0][0] == "← Command Center"
    assert calls[0][1] == command_center_url()
    assert calls[1][0] == "divider"
