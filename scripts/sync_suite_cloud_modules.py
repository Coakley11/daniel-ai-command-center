#!/usr/bin/env python3
"""Copy shared Supabase activity modules into sibling Streamlit app repos."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GITHUB = ROOT.parent

FILES = (
    "suite_storage_config.py",
    "suite_storage_supabase.py",
    "suite_activity_client.py",
)

TARGET_REPOS = (
    "ai-music-practice-coach",
    "baseball-stat-app",
    "nba-playoff-companion-ai",
    "investment-portfolio-analyzer",
    "Applied-mathematical-intelligence",
    "future-lens-ai-transition-simulator",
)


def main() -> None:
    for repo in TARGET_REPOS:
        dest_dir = GITHUB / repo
        if not dest_dir.is_dir():
            print(f"skip (missing): {dest_dir}")
            continue
        for name in FILES:
            src = ROOT / name
            dest = dest_dir / name
            shutil.copy2(src, dest)
            print(f"copied {name} -> {repo}/")
    print("Done. Add identical [suite_activity] secrets to each Streamlit Cloud app.")


if __name__ == "__main__":
    main()
