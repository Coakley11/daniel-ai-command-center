#!/usr/bin/env python3
"""Copy shared Supabase activity modules into sibling Streamlit app repos."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GITHUB = ROOT.parent

MODULE_FILES = (
    "activity_time.py",
    "suite_storage_config.py",
    "suite_storage_supabase.py",
    "suite_activity_client.py",
    "suite_user.py",
    "suite_account.py",
    "suite_deep_links.py",
    "suite_resume_launch.py",
    "suite_cloud_state.py",
    "suite_user_persistence.py",
)

TARGET_REPOS = (
    "ai-music-practice-coach",
    "baseball-stat-app",
    "nba-playoff-companion-ai",
    "investment-portfolio-analyzer",
    "Applied-mathematical-intelligence",
    "future-lens-ai-transition-simulator",
)

SECRETS_EXAMPLE = ROOT / ".streamlit" / "secrets.toml.example"


def main() -> None:
    for repo in TARGET_REPOS:
        dest_dir = GITHUB / repo
        if not dest_dir.is_dir():
            print(f"skip (missing): {dest_dir}")
            continue
        for name in MODULE_FILES:
            src = ROOT / name
            dest = dest_dir / name
            shutil.copy2(src, dest)
            print(f"copied {name} -> {repo}/")
        if SECRETS_EXAMPLE.is_file():
            secrets_dest = dest_dir / ".streamlit"
            secrets_dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SECRETS_EXAMPLE, secrets_dest / "secrets.toml.example")
            print(f"copied secrets.toml.example -> {repo}/.streamlit/")
    print()
    print("Done. Paste identical [suite_activity] secrets into every Streamlit Cloud app,")
    print("then reboot each deployment (Settings -> Reboot app).")


if __name__ == "__main__":
    main()
