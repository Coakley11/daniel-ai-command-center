#!/usr/bin/env python3
"""Print Streamlit secrets checklist for all suite apps."""

from __future__ import annotations

from suite_storage_config import EXPECTED_SECRETS_TOML

APPS = (
    ("Command Center", "daniel-ai-command-center", "ai_command_center.py"),
    ("Music Practice Coach", "ai-music-practice-coach", "streamlit_music_practice_app.py"),
    ("Baseball Analytics", "baseball-stat-app", "streamlit_app.py"),
    ("Basketball Companion", "nba-playoff-companion-ai", "streamlit_app.py"),
    ("Investment Analytics", "investment-portfolio-analyzer", "streamlit_app.py"),
    ("Applied Intelligence", "Applied-mathematical-intelligence", "streamlit_app.py"),
    ("AI Future Simulator", "future-lens-ai-transition-simulator", "streamlit_app.py"),
)


def main() -> None:
    print("Daniel AI Suite — Streamlit Cloud secrets checklist\n")
    print("Use branch: dev | Reboot after saving secrets\n")
    for label, repo, main_file in APPS:
        print(f"## {label}")
        print(f"   Repo: Coakley11/{repo}")
        print(f"   Main: {main_file}")
        print("   Secrets: Settings -> Secrets -> paste block below -> Reboot app")
        print()
    print("--- TOML block (identical on every app) ---\n")
    print(EXPECTED_SECRETS_TOML)


if __name__ == "__main__":
    main()
