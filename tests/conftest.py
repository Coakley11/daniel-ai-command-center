"""Test isolation for process-wide state files.

``data/suite_active_workspace.json`` is the single-user install's workspace choice. Tests
that select a workspace used to write the real file, so later tests saw whatever profile
an earlier test left behind (results depended on test order). Each test now gets its own
temporary copy, starting at the default profile.
"""

from __future__ import annotations

import json

import pytest


@pytest.fixture(autouse=True)
def _isolated_workspace_file(tmp_path, monkeypatch):
    try:
        import suite_workspace
    except ImportError:
        yield
        return
    path = tmp_path / "suite_active_workspace.json"
    path.write_text(json.dumps({"workspace_id": "daniel", "label": "Daniel"}), encoding="utf-8")
    monkeypatch.setattr(suite_workspace, "_PERSISTED_FILE", path)
    yield
