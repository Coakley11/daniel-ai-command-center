"""Verify homepage app URLs resolve and are publicly reachable."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app_registry import APP_DEFINITIONS, verify_connections  # noqa: E402


def main() -> int:
    connections = verify_connections()
    failed = []
    print("App navigation verification\n")
    for conn in connections:
        status = "PASS" if conn.button_works else "FAIL"
        print(f"{status} | {conn.name} | {conn.branch} | {conn.open_url}")
        if not conn.button_works:
            failed.append(conn.name)
    print()
    if failed:
        print("Failed:", ", ".join(failed))
        return 1
    print("All Go to App links verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
