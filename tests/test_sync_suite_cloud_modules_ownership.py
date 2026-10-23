"""The suite sync never overwrites a repo's app-owned files, and still syncs the canonical shared ones."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sync_suite_cloud_modules", ROOT / "scripts" / "sync_suite_cloud_modules.py")
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class SyncOwnershipTests(unittest.TestCase):
    def test_baseball_owned_files_are_kept_and_canonical_files_are_synced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            github = Path(tmp)
            repo = github / "baseball-stat-app"
            (repo / ".streamlit").mkdir(parents=True)
            for name in sync.MODULE_FILES:
                (repo / name).write_text(f"# baseball copy of {name}\n", encoding="utf-8")
            (repo / ".streamlit" / "secrets.toml.example").write_text("# baseball secrets example\n", encoding="utf-8")
            with mock.patch.object(sync, "GITHUB", github), mock.patch("builtins.print"):
                sync.main()
            owned = sync.APP_OWNED_FILES["baseball-stat-app"]
            for name in owned:
                self.assertTrue((repo / name).read_text(encoding="utf-8").startswith("# baseball "), name)
            for name in ("suite_deep_links.py", "suite_resume_launch.py", "suite_activity_client.py"):
                self.assertNotIn(name, owned)
                self.assertEqual((repo / name).read_bytes(), (ROOT / name).read_bytes(), name)

    def test_other_repos_are_unaffected_by_baseball_ownership(self) -> None:
        dest = Path("does-not-matter.py")
        self.assertEqual(sync._should_skip_overwrite("ai-music-practice-coach", "suite_workspace.py", dest), "")
        self.assertEqual(sync._should_skip_overwrite("baseball-stat-app", "suite_workspace.py", dest),
                         "baseball-stat-app-owned suite_workspace.py")


if __name__ == "__main__":
    unittest.main()
