#!/usr/bin/env python3
"""Inject a test verified-chart event and print the feed line (local dev check)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from activity_feed import build_activity_feed, format_activity_message
from activity_store import get_app_directory_card, load_activity_snapshot, load_all_events
from suite_activity_client import record_activity


def main() -> int:
    record_activity(
        "music",
        "verified_chart_saved",
        page="Song Picker",
        metrics={
            "song": "The Scientist",
            "artist": "Coldplay",
            "edited_fields": ["chords"],
            "last_edited_song": "The Scientist",
        },
        summary="Saved verified chords for The Scientist",
        resume_key="song:test-scientist",
        resume_title="Continue: The Scientist",
        resume_subtitle="Coldplay",
    )
    snap = load_activity_snapshot()
    print("App Directory:", get_app_directory_card(snap, "music").highlights)
    feed = build_activity_feed(load_all_events(15), limit=5)
    for item in feed:
        print("Feed:", item.message)
    latest = next(
        (e for e in reversed(load_all_events(30)) if e.get("event") == "verified_chart_saved"),
        None,
    )
    if latest:
        print("Latest verified:", format_activity_message(latest))
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
