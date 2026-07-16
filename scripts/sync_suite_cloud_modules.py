#!/usr/bin/env python3
"""Copy shared Supabase activity modules into sibling Streamlit app repos."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GITHUB = ROOT.parent

# Explicitly shared modules only. App-owned SAQ implementations are never synced
# (Music / Baseball / AMI / Investment keep local suite_analytical_question.py).
MODULE_FILES = (
    "activity_time.py",
    "suite_storage_config.py",
    "suite_storage_supabase.py",
    "suite_activity_client.py",
    "suite_user.py",
    "suite_account.py",
    "suite_account_settings.py",
    "suite_app_shell.py",
    "suite_activity_audit.py",
    "suite_workspace_deep_link_audit.py",
    "suite_auth.py",
    "suite_auth_browser.py",
    "suite_command_center_link.py",
    "suite_deep_links.py",
    "suite_resume_launch.py",
    "suite_cloud_state.py",
    "suite_egress_trace.py",
    "suite_user_persistence.py",
    "suite_workspace.py",
    "suite_workspace_registry.py",
    "applied_math_return_insight.py",
)

# Never overwrite these filenames in any sibling repo.
NEVER_OVERWRITE = frozenset(
    {
        "suite_analytical_question.py",
    }
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

# App-owned suite_auth markers (forms / flat sidebar) — do not clobber.
_APP_OWNED_AUTH_MARKERS = (
    "flat_sidebar",
    "AUTH_PENDING_LOGIN_KEY",
    "suite_auth_login_form",
)


def _should_skip_overwrite(repo: str, name: str, dest: Path) -> str:
    """Avoid wiping app-owned modules that diverge from Command Center."""
    if name in NEVER_OVERWRITE:
        return f"never-overwrite {name}"
    if name == "suite_analytical_question.py":
        return "app-owned suite_analytical_question.py"
    if name == "suite_auth.py" and dest.is_file():
        try:
            text = dest.read_text(encoding="utf-8")
        except OSError:
            return ""
        if any(marker in text for marker in _APP_OWNED_AUTH_MARKERS):
            return f"{repo}-owned suite_auth.py"
    return ""


def main() -> None:
    for repo in TARGET_REPOS:
        dest_dir = GITHUB / repo
        if not dest_dir.is_dir():
            print(f"skip (missing): {dest_dir}")
            continue
        for name in MODULE_FILES:
            src = ROOT / name
            dest = dest_dir / name
            skip_reason = _should_skip_overwrite(repo, name, dest)
            if skip_reason:
                print(f"skip ({skip_reason}): {repo}/{name}")
                continue
            if not src.is_file():
                print(f"skip (missing source): {name}")
                continue
            shutil.copy2(src, dest)
            print(f"copied {name} -> {repo}/")
        if SECRETS_EXAMPLE.is_file():
            secrets_dest = dest_dir / ".streamlit"
            secrets_dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SECRETS_EXAMPLE, secrets_dest / "secrets.toml.example")
            print(f"copied secrets.toml.example -> {repo}/.streamlit/")
    print()
    print("Done. App-owned suite_analytical_question.py is never overwritten.")
    print("Paste identical [suite_activity] secrets into every Streamlit Cloud app,")
    print("then reboot each deployment (Settings -> Reboot app).")


if __name__ == "__main__":
    main()
