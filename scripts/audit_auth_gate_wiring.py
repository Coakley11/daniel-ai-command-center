#!/usr/bin/env python3
"""Audit auth-gate wiring in suite app entry files."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

GITHUB = Path(__file__).resolve().parents[2]

ENTRY_FILES = (
    GITHUB / "daniel-ai-command-center" / "ai_command_center.py",
    GITHUB / "ai-music-practice-coach" / "streamlit_music_practice_app.py",
    GITHUB / "Applied-mathematical-intelligence" / "streamlit_app.py",
    GITHUB / "investment-portfolio-analyzer" / "streamlit_app.py",
    GITHUB / "nba-playoff-companion-ai" / "streamlit_app.py",
    GITHUB / "future-lens-ai-transition-simulator" / "streamlit_app.py",
    GITHUB / "future-lens-ai-transition-simulator" / "future_lens_boot.py",
)


def _top_level_returns(path: Path, tree: ast.AST) -> list[int]:
    lines: list[int] = []
    for node in tree.body:
        if isinstance(node, ast.Return):
            lines.append(node.lineno)
    return lines


def audit_file(path: Path) -> list[str]:
    issues: list[str] = []
    if not path.is_file():
        return [f"missing file: {path.name}"]
    text = path.read_text(encoding="utf-8")
    try:
        compile(text, str(path), "exec")
    except SyntaxError as exc:
        issues.append(f"SyntaxError line {exc.lineno}: {exc.msg}")
        return issues
    tree = ast.parse(text)
    bad_returns = _top_level_returns(path, tree)
    if bad_returns:
        issues.append(f"top-level return at lines {bad_returns}")
    if "apply_suite_auth_gate" in text:
        for i, line in enumerate(text.splitlines(), start=1):
            if "apply_suite_auth_gate" not in line:
                continue
            if line.startswith("try:") or (line.strip().startswith("try:") and not line.startswith("    ")):
                # module-level try before auth import is OK if next lines are imports at col 4
                prev = text.splitlines()[i - 2] if i > 1 else ""
                if prev.strip() == "pass" and not prev.startswith("    "):
                    issues.append(f"suspicious auth gate insertion near line {i}")
    if path.name == "future_lens_boot.py" and "apply_suite_auth_gate" in text:
        issues.append("auth gate must not live in future_lens_boot.py")
    return issues


def main() -> int:
    failed = 0
    for path in ENTRY_FILES:
        label = path.parent.name + "/" + path.name
        issues = audit_file(path)
        if issues:
            failed += 1
            print(f"FAIL {label}")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"PASS {label}")
    return failed


if __name__ == "__main__":
    raise SystemExit(main())
