"""Cross-repo: app-owned suite_analytical_question exports must survive suite sync."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

GITHUB = Path(__file__).resolve().parents[2]

REQUIRED_EXPORTS: dict[str, frozenset[str]] = {
    "ai-music-practice-coach": frozenset(
        {
            "submit_practice_log_analysis_handoff",
            "build_submit_context",
            "submit_analytical_question",
        }
    ),
    "baseball-stat-app": frozenset(
        {
            "BASEBALL_INSIGHT_BUTTON_LABEL",
            "BASEBALL_INSIGHT_SECTION_TITLE",
            "build_submit_context",
            "submit_analytical_question",
        }
    ),
    "Applied-mathematical-intelligence": frozenset(
        {
            "render_applied_intelligence_solve_problem_content",
            "should_render_hof_full_memo_content",
            "should_render_practice_log_full_report",
        }
    ),
    "investment-portfolio-analyzer": frozenset(
        {
            "peek_investment_portfolio_entity_params",
            "sync_analytical_question_instant_insight",
            "ensure_investment_source_state_portfolio_payload",
        }
    ),
}


def _exported_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


class TestAppOwnedSaqExports(unittest.TestCase):
    def test_required_app_saq_exports_present(self) -> None:
        missing_repos: list[str] = []
        for repo, required in REQUIRED_EXPORTS.items():
            path = GITHUB / repo / "suite_analytical_question.py"
            if not path.is_file():
                missing_repos.append(f"{repo}: file missing")
                continue
            present = _exported_names(path)
            missing = sorted(required - present)
            if missing:
                missing_repos.append(f"{repo}: {missing}")
        self.assertEqual(missing_repos, [], msg="; ".join(missing_repos))

    def test_sync_script_never_overwrites_saq(self) -> None:
        sync_path = (
            Path(__file__).resolve().parents[1] / "scripts" / "sync_suite_cloud_modules.py"
        )
        text = sync_path.read_text(encoding="utf-8")
        self.assertIn("NEVER_OVERWRITE", text)
        self.assertIn("suite_analytical_question.py", text)
        # Must not list SAQ in MODULE_FILES copy set.
        self.assertNotIn(
            '"suite_analytical_question.py"',
            text.split("MODULE_FILES")[1].split(")")[0],
        )


class TestAdminGatesIntact(unittest.TestCase):
    def test_admin_email_local_parts_only(self) -> None:
        from suite_workspace_registry import ADMIN_EMAIL_LOCAL_PARTS, is_admin_user

        self.assertIn("coakley11", ADMIN_EMAIL_LOCAL_PARTS)
        self.assertIn("daniel.cohen11", ADMIN_EMAIL_LOCAL_PARTS)
        self.assertNotIn("daniel", ADMIN_EMAIL_LOCAL_PARTS)
        self.assertFalse(is_admin_user(external_id="daniel"))
        self.assertTrue(is_admin_user(email="daniel.cohen11@example.com"))
        self.assertTrue(is_admin_user(email="coakley11@aol.com"))


if __name__ == "__main__":
    unittest.main()
