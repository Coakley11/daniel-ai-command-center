"""
Shared activity feed types (no imports from activity_time or activity_store).

Kept in a separate module so Streamlit Cloud never sees a partially-initialized
activity_feed when timestamp helpers fail to import.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ActivityFeedItem:
    app: str
    app_label: str
    timestamp: str
    message: str
    sort_key: datetime
    is_highlight: bool = False
    is_rollup: bool = False


@dataclass(frozen=True)
class ActivityDashboard:
    """Executive activity view: today's summary, highlights, and recent rollups."""

    today_summaries: tuple[str, ...]
    highlights: tuple[ActivityFeedItem, ...]
    recent: tuple[ActivityFeedItem, ...]


__all__ = ("ActivityFeedItem", "ActivityDashboard")
