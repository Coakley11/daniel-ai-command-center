"""Sprint B — deep-link and activity sync audits."""

from __future__ import annotations

import unittest

from suite_activity_audit import assert_activity_write_contract, audit_activity_metrics
from suite_workspace_deep_link_audit import (
    assert_deep_links_include_workspace,
    audit_command_center_link_url,
    audit_registry_open_urls,
    audit_resume_action_urls,
)


class TestSuiteDeepLinkAudit(unittest.TestCase):
    def test_registry_open_urls_include_workspace_daniel(self) -> None:
        self.assertEqual(audit_registry_open_urls(workspace_id="daniel"), [])

    def test_registry_open_urls_include_workspace_ariel(self) -> None:
        self.assertEqual(audit_registry_open_urls(workspace_id="ariel"), [])

    def test_resume_urls_include_workspace(self) -> None:
        self.assertEqual(audit_resume_action_urls(workspace_id="ariel"), [])

    def test_command_center_link_includes_workspace(self) -> None:
        self.assertEqual(audit_command_center_link_url(workspace_id="daniel"), [])

    def test_collect_audit_passes(self) -> None:
        assert_deep_links_include_workspace(workspace_id="daniel")
        assert_deep_links_include_workspace(workspace_id="ariel")


class TestSuiteActivityAudit(unittest.TestCase):
    def test_ariel_music_metrics_scoped(self) -> None:
        issues = audit_activity_metrics("music", {"workspace_id": "ariel"})
        self.assertEqual(issues, [])

    def test_missing_workspace_id_flagged(self) -> None:
        issues = audit_activity_metrics("music", {})
        self.assertIn("missing metrics.workspace_id", issues)

    def test_activity_write_contract(self) -> None:
        assert_activity_write_contract()


if __name__ == "__main__":
    unittest.main()
