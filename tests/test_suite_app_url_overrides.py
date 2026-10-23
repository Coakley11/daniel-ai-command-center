"""Staging deployments point suite links at their own apps (SUITE_APP_URL_<APP>); unset, every URL is the default."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path
from unittest import mock
from urllib.parse import urlparse

from suite_deep_links import APP_BASE_URLS, app_base_url, build_resume_action_url

ROOT = Path(__file__).resolve().parents[1]
STAGING = "https://baseball-staging.example"
CODE = textwrap.dedent("""
    import json, sys
    sys.path.insert(0, ".")
    import app_urls
    from app_registry import get_app_url
    print(json.dumps({"app_urls": app_urls.APP_URLS, "baseball_nav": get_app_url("baseball", workspace_id="qa")}))
""")


def _clean_env(**extra: str) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("SUITE_APP_URL_")}
    env.update(extra)
    return env


def _registry(**extra: str) -> dict:
    out = subprocess.run([sys.executable, "-c", CODE], cwd=ROOT, env=_clean_env(**extra), capture_output=True,
                         text=True, timeout=120)
    assert out.returncode == 0, out.stderr[-2000:]
    return json.loads(out.stdout.strip().splitlines()[-1])


class AppUrlOverrideTests(unittest.TestCase):
    def test_unset_every_base_url_is_the_default(self) -> None:
        with mock.patch.dict(os.environ, _clean_env(), clear=True):
            for app, url in APP_BASE_URLS.items():
                self.assertEqual(app_base_url(app), url)
            link = build_resume_action_url("baseball", resume_key="historical:SB:2002-2025")
        self.assertTrue(link.startswith(APP_BASE_URLS["baseball"] + "/?"), link)

    def test_override_moves_only_that_app(self) -> None:
        with mock.patch.dict(os.environ, _clean_env(SUITE_APP_URL_BASEBALL=STAGING + "/"), clear=True):
            self.assertEqual(app_base_url("baseball"), STAGING)
            link = build_resume_action_url("baseball", resume_key="historical:SB:2002-2025")
            for app in APP_BASE_URLS:
                if app != "baseball":
                    self.assertEqual(app_base_url(app), APP_BASE_URLS[app])
        self.assertEqual(urlparse(link).netloc, urlparse(STAGING).netloc)

    def test_command_center_registry_follows_the_override(self) -> None:
        default = _registry()
        staged = _registry(SUITE_APP_URL_BASEBALL=STAGING)
        self.assertEqual(default["app_urls"]["baseball"], APP_BASE_URLS["baseball"])
        self.assertEqual(staged["app_urls"]["baseball"], STAGING)
        self.assertTrue(staged["baseball_nav"].startswith(STAGING), staged["baseball_nav"])
        self.assertEqual({k: v for k, v in staged["app_urls"].items() if k != "baseball"},
                         {k: v for k, v in default["app_urls"].items() if k != "baseball"})


if __name__ == "__main__":
    unittest.main()
