"""Manual verification script for Command Center Today's Work simplification."""

from __future__ import annotations

import inspect
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from activity_feed import build_activity_dashboard


def main() -> int:
    ok = True
    now = datetime(2026, 6, 11, 20, 0, tzinfo=timezone.utc)
    events = [
        *[
            {
                "app": "investment",
                "event": "portfolio_health_checked",
                "timestamp": f"2026-06-11T10:{i:02d}:00Z",
                "metrics": {"score": 70 + i, "review_type": "Fair"},
            }
            for i in range(10)
        ],
        *[
            {
                "app": "investment",
                "event": "scenario_run",
                "timestamp": f"2026-06-11T11:{i:02d}:00Z",
                "metrics": {"context": "Monte Carlo"},
            }
            for i in range(3)
        ],
        {
            "app": "investment",
            "event": "portfolio_created",
            "timestamp": "2026-06-11T09:00:00Z",
            "metrics": {"holdings_count": 4},
        },
        {"app": "baseball", "event": "draft_prep", "timestamp": "2026-06-11T14:00:00Z", "metrics": {}},
        {"app": "baseball", "event": "sleeper_review", "timestamp": "2026-06-11T15:00:00Z", "metrics": {}},
        {
            "app": "music",
            "event": "practice",
            "timestamp": "2026-06-11T16:00:00Z",
            "metrics": {"song": "Piano Man", "minutes": 20},
        },
        {
            "app": "music",
            "event": "backing_track_completed",
            "timestamp": "2026-06-11T17:00:00Z",
            "metrics": {"song": "Piano Man"},
        },
        {"app": "investment", "event": "page_view", "timestamp": "2026-06-11T18:00:00Z", "page": "Overview", "metrics": {}},
        {"app": "baseball", "event": "page_view", "timestamp": "2026-06-11T18:01:00Z", "page": "Home", "metrics": {}},
    ]

    dash = build_activity_dashboard(events, now=now)

    print("=== TODAY SUMMARIES ===")
    for line in dash.today_summaries:
        print(f"  {line}")

    checks = {
        "Portfolio Analysis (10 runs)": any("Portfolio Analysis (10 runs)" in s for s in dash.today_summaries),
        "Risk Assessment (3 runs)": any("Risk Assessment (3 runs)" in s for s in dash.today_summaries),
        "New portfolio created": any("New portfolio created" in s for s in dash.today_summaries),
        "Live Draft Session Started": any("Live Draft Session Started" in s for s in dash.today_summaries),
        "Sleeper Analysis": any("Sleeper Analysis" in s for s in dash.today_summaries),
        "Practiced Piano Man": any("Practiced Piano Man" in s for s in dash.today_summaries),
        "Backing Track Generated": any("Backing Track Generated" in s for s in dash.today_summaries),
    }
    print("\n=== GOOD EXAMPLES ===")
    for label, passed in checks.items():
        status = "OK" if passed else "MISSING"
        print(f"  [{status}] {label}")
        if not passed:
            ok = False

    bad_patterns = ["opened page", "viewed screen", "refreshed", "clicked button", "page_view"]
    print("\n=== NOISE CHECK ===")
    for line in dash.today_summaries:
        low = line.lower()
        for b in bad_patterns:
            if b in low:
                print(f"  FAIL bad line: {line}")
                ok = False

    print("\n=== REMOVED SECTIONS (data) ===")
    if dash.highlights:
        print(f"  FAIL highlights not empty: {len(dash.highlights)}")
        ok = False
    else:
        print("  OK highlights empty")
    # week/recent_by_app/most_active not rendered in UI even if populated
    print(f"  week_summaries (not rendered): {dash.week_summaries}")
    print(f"  recent_by_app (not rendered): {dash.recent_by_app}")
    print(f"  most_active (not rendered): {dash.most_active_workflows}")

    import ai_command_center as cc

    src = inspect.getsource(cc._render_recent_activity_feed)
    removed = [
        "Highlights",
        "Recent Activity",
        "Most active workflows",
        "This week",
        "Recent work by app",
    ]
    print("\n=== UI SOURCE CHECK ===")
    for r in removed:
        if r in src:
            print(f"  FAIL '{r}' still in _render_recent_activity_feed")
            ok = False
        else:
            print(f"  OK '{r}' removed from render")
    if "Today's Work" not in src:
        print("  FAIL Today's Work missing from render")
        ok = False
    else:
        print("  OK Today's Work present")

    print("\n=== RESULT ===")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
