#!/usr/bin/env python3
"""Sync Applied Intelligence suite_branding.py into Command Center (cloud deploy copy)."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GITHUB = ROOT.parent

SOURCE = GITHUB / "Applied-mathematical-intelligence" / "suite_branding.py"
DEST_DIR = ROOT / "branding"
DEST = DEST_DIR / "applied_intelligence_suite_branding.py"


def main() -> int:
    if not SOURCE.is_file():
        print(f"Missing source: {SOURCE}")
        return 1
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE, DEST)
    print(f"Synced {SOURCE.name} -> {DEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
