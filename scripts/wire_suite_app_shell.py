"""Wire suite_app_shell into sibling app sidebars (Sprint B)."""

from __future__ import annotations

from pathlib import Path

GITHUB = Path(__file__).resolve().parents[2]

REPLACEMENT = """try:
    from suite_app_shell import render_suite_sidebar_account_shell

    render_suite_sidebar_account_shell(st)
except Exception:
    try:
        from suite_command_center_link import render_command_center_sidebar_link

        render_command_center_sidebar_link(st)
    except Exception:
        pass"""

MUSIC_OLD = """try:
    from suite_command_center_link import render_command_center_sidebar_link

    render_command_center_sidebar_link(st, show_divider=False)
except Exception:
    pass"""

MUSIC_NEW = """try:
    from suite_app_shell import render_suite_sidebar_account_shell

    render_suite_sidebar_account_shell(st, command_center_divider=False)
except Exception:
    try:
        from suite_command_center_link import render_command_center_sidebar_link

        render_command_center_sidebar_link(st, show_divider=False)
    except Exception:
        pass"""

FL_OLD = """    try:
        from suite_command_center_link import render_command_center_sidebar_link

        render_command_center_sidebar_link(st)
    except Exception:
        pass"""

FL_NEW = """    try:
        from suite_app_shell import render_suite_sidebar_account_shell

        render_suite_sidebar_account_shell(st)
    except Exception:
        try:
            from suite_command_center_link import render_command_center_sidebar_link

            render_command_center_sidebar_link(st)
        except Exception:
            pass"""


def _patch(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        print(f"skip (already patched): {label}")
        return
    if old not in text:
        raise SystemExit(f"OLD block not found: {label}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"patched: {label}")


def main() -> None:
    _patch(
        GITHUB / "Applied-mathematical-intelligence" / "streamlit_app.py",
        """try:
    from suite_command_center_link import render_command_center_sidebar_link

    render_command_center_sidebar_link(st)
except Exception:
    pass""",
        REPLACEMENT.replace("render_suite_sidebar_account_shell(st)", "render_suite_sidebar_account_shell(st)"),
        "AMI",
    )
    _patch(
        GITHUB / "investment-portfolio-analyzer" / "streamlit_app.py",
        """    try:
        from suite_command_center_link import render_command_center_sidebar_link

        render_command_center_sidebar_link(st)
    except Exception:
        pass""",
        """    try:
        from suite_app_shell import render_suite_sidebar_account_shell

        render_suite_sidebar_account_shell(st)
    except Exception:
        try:
            from suite_command_center_link import render_command_center_sidebar_link

            render_command_center_sidebar_link(st)
        except Exception:
            pass""",
        "Investment",
    )
    _patch(
        GITHUB / "nba-playoff-companion-ai" / "streamlit_app.py",
        """    try:
        from suite_command_center_link import render_command_center_sidebar_link

        render_command_center_sidebar_link(st)
    except Exception:
        pass""",
        """    try:
        from suite_app_shell import render_suite_sidebar_account_shell

        render_suite_sidebar_account_shell(st)
    except Exception:
        try:
            from suite_command_center_link import render_command_center_sidebar_link

            render_command_center_sidebar_link(st)
        except Exception:
            pass""",
        "NBA",
    )
    _patch(
        GITHUB / "ai-music-practice-coach" / "streamlit_music_practice_app.py",
        MUSIC_OLD,
        MUSIC_NEW,
        "Music",
    )
    _patch(
        GITHUB / "future-lens-ai-transition-simulator" / "streamlit_app.py",
        FL_OLD,
        FL_NEW,
        "FutureLens",
    )


if __name__ == "__main__":
    main()
