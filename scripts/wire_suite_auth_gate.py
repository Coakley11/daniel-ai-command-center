"""Wire apply_suite_auth_gate into sibling app entry files (Sprint C)."""

from __future__ import annotations

from pathlib import Path

GITHUB = Path(__file__).resolve().parents[2]

AUTH_GATE = """
try:
    from suite_app_shell import apply_suite_auth_gate

    apply_suite_auth_gate(st)
except Exception:
    pass"""


def _insert_after(path: Path, anchor: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if "apply_suite_auth_gate" in text:
        print(f"skip (already patched): {label}")
        return
    if anchor not in text:
        raise SystemExit(f"anchor not found: {label}")
    path.write_text(text.replace(anchor, anchor + AUTH_GATE, 1), encoding="utf-8")
    print(f"patched: {label}")


def main() -> None:
    _insert_after(
        GITHUB / "Applied-mathematical-intelligence" / "streamlit_app.py",
        "    init_suite_workspace(st)\nexcept Exception:\n    pass\n",
        "AMI",
    )
    _insert_after(
        GITHUB / "investment-portfolio-analyzer" / "streamlit_app.py",
        "    init_suite_workspace(st)\nexcept Exception:\n    pass\n",
        "Investment",
    )
    _insert_after(
        GITHUB / "nba-playoff-companion-ai" / "streamlit_app.py",
        "        init_suite_workspace(st)\n    except Exception:\n        pass\n",
        "NBA",
    )
    _insert_after(
        GITHUB / "ai-music-practice-coach" / "streamlit_music_practice_app.py",
        "    apply_suite_resume_launch(st, \"music\")\nexcept Exception:\n    pass\n",
        "Music",
    )
    boot = GITHUB / "future-lens-ai-transition-simulator" / "streamlit_app.py"
    _insert_after(
        boot,
        "    initial_sidebar_state=\"expanded\",\n)\n",
        "FutureLens",
    )


if __name__ == "__main__":
    main()
