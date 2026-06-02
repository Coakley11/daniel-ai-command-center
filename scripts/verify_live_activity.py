#!/usr/bin/env python3
"""CLI check: Supabase rows vs Command Center load path (requires secrets or env)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from activity_diagnostics import run_live_activity_diagnostics  # noqa: E402


def main() -> int:
    d = run_live_activity_diagnostics()
    print("=== Live activity verification ===\n")
    print(f"Supabase configured: {d.cloud_storage_configured}")
    print(f"Supabase reachable:  {d.cloud_storage_reachable}")
    if d.supabase_error:
        print(f"Supabase error:      {d.supabase_error}")
    print(f"Supabase events:     {d.supabase_event_count}")
    print(f"CC merged events:    {d.command_center_event_count}")
    print(f"Status:              {d.failure_step}\n")

    print("Event count by app (Supabase):")
    for app in sorted(d.counts_by_app_supabase):
        print(f"  {app}: {d.counts_by_app_supabase[app]}")
    print("\nEvent count by app (Command Center):")
    for app in sorted(d.counts_by_app_command_center):
        print(f"  {app}: {d.counts_by_app_command_center[app]}")

    print("\nMost recent by app (Command Center):")
    for app in sorted(d.last_event_by_app_command_center):
        print(f"  {app}: {d.last_event_by_app_command_center[app]}")

    print("\nPhase A — Music events:")
    print(f"{'Event':<28} {'Supabase':<10} {'CC read':<10} Feed preview")
    print("-" * 90)
    for row in d.phase_a_music:
        print(
            f"{row.event_type:<28} {str(row.in_supabase):<10} {str(row.in_command_center):<10} "
            f"{row.feed_preview[:48]}"
        )

    print(f"\n{d.recommendation}")
    return 0 if d.failure_step.startswith("none") else 1


if __name__ == "__main__":
    raise SystemExit(main())
