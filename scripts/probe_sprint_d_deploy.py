"""Probe dev Streamlit deployments for Sprint B account shell markers."""

from __future__ import annotations

import re
import sys
from typing import Any

import requests

from app_urls import (
    APPLIED_INTELLIGENCE_URL,
    FUTURE_LENS_URL,
    HOMEPAGE_DEV_URL,
    INVESTMENT_APP_URL,
    MUSIC_APP_URL,
    NBA_APP_URL,
)

APPS: dict[str, str] = {
    "command_center": HOMEPAGE_DEV_URL,
    "music": MUSIC_APP_URL,
    "investment": INVESTMENT_APP_URL,
    "nba": NBA_APP_URL,
    "ami": APPLIED_INTELLIGENCE_URL,
    "future_lens": FUTURE_LENS_URL,
}

MARKERS = (
    ("loads", lambda t: "streamlit" in t.lower() or "stApp" in t),
    ("no_fatal_error", lambda t: "encountered an error" not in t.lower() and "AttributeError" not in t),
    ("auth_gate_off", lambda t: "Sign in to continue" not in t),
    ("workspace_badge_hint", lambda t: "Profile:" in t or "workspace" in t.lower() or "Ariel" in t or "Daniel" in t),
    ("account_panel_hint", lambda t: "Account" in t and "workspace" in t.lower()),
    ("cc_link_workspace_param", lambda t: "suite_workspace=" in t),
)


def probe(name: str, url: str) -> dict[str, Any]:
    row: dict[str, Any] = {"url": url, "ok": False}
    try:
        resp = requests.get(url, timeout=60, headers={"User-Agent": "SprintDProbe/1.0"})
        text = resp.text
        row["status"] = resp.status_code
        row["ok"] = resp.status_code == 200
    except Exception as exc:
        row["error"] = str(exc)
        return row
    for key, fn in MARKERS:
        row[key] = bool(fn(text))
    commits = re.findall(r"[0-9a-f]{7}", text)
    row["commit_hints"] = sorted(set(commits))[:8]
    return row


def main() -> int:
    failed = 0
    for name, url in APPS.items():
        row = probe(name, url)
        print(f"=== {name} ===")
        for k, v in row.items():
            print(f"  {k}: {v}")
        if not row.get("ok") or not row.get("no_fatal_error"):
            failed += 1
        print()
    return failed


if __name__ == "__main__":
    sys.exit(main())
