"""Activity (today), Weekly Summary (this week), App Directory and Continue for meaningful work."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from meaningful_activity import (
    investment_directory_lines,
    local_week_start,
    today_sections,
    week_sections,
)

# Thursday 2026-11-19 14:00 New York (19:00 UTC).
NOW = datetime(2026, 11, 19, 19, 0, tzinfo=timezone.utc)


def ev(app: str, event: str, ts: str, **metrics) -> dict:
    return {"app": app, "event": event, "page": "", "timestamp": ts, "metrics": metrics}


def lines(sections) -> dict[str, list[str]]:
    return {s.title: s.lines for s in sections}


INVESTMENT_DAY = [
    ev("investment", "real_cash_deposited", "2026-11-19T15:00:00Z", portfolio_kind="real",
       event_key="txn:a", amount=1.0, real_transaction_count=1, real_cash_balance=1.0, real_tickers=[]),
    ev("investment", "real_investment_purchased", "2026-11-19T15:05:00Z", portfolio_kind="real",
       event_key="txn:b", ticker="VTI", shares=0.002, price=361.29, amount=0.72,
       first_purchase_of_ticker=True, first_real_purchase=True,
       real_transaction_count=2, real_cash_balance=0.28, real_tickers=["VTI"]),
    ev("investment", "investment_goal_selected", "2026-11-19T15:10:00Z", portfolio_kind="planning",
       event_key="goal:x", goal_title="Long-Term Growth"),
    ev("investment", "holdings_updated", "2026-11-19T15:20:00Z", portfolio_kind="planning",
       event_key="planning:fp1", allocation_label="100% VTI", removed=["BND", "VNQ", "VXUS"]),
    ev("investment", "portfolio_health_checked", "2026-11-19T15:30:00Z", portfolio_kind="planning",
       event_key="health:1", review_type="Good", score=72.0),
]


class TestInvestmentActivity(unittest.TestCase):
    def test_today_reads_like_the_work_done(self) -> None:
        got = lines(today_sections(INVESTMENT_DAY, now=NOW))["Investment Portfolio Analyzer"]
        self.assertEqual(
            got,
            [
                "Recorded first real VTI purchase — 0.002 shares at $361.29",
                "Added $1.00 to your real portfolio",
                "Set investment goal: Long-Term Growth",
                "Updated planning portfolio — 100% VTI (removed BND, VNQ, VXUS)",
                "Completed a portfolio health evaluation — Good (72)",
            ],
        )

    def test_planning_change_is_never_shown_as_a_purchase(self) -> None:
        planning_only = [e for e in INVESTMENT_DAY if e["metrics"]["portfolio_kind"] == "planning"]
        text = " ".join(lines(today_sections(planning_only, now=NOW))["Investment Portfolio Analyzer"])
        self.assertNotIn("purchase", text.lower())
        self.assertNotIn("real", text.lower())

    def test_duplicates_by_event_key_count_once(self) -> None:
        dup = INVESTMENT_DAY + [dict(INVESTMENT_DAY[1], timestamp="2026-11-19T16:00:00Z")]
        got = lines(today_sections(dup, now=NOW))["Investment Portfolio Analyzer"]
        self.assertEqual(sum("VTI purchase" in l for l in got), 1)

    def test_repeated_actions_are_combined(self) -> None:
        deposits = [
            ev("investment", "real_cash_deposited", f"2026-11-19T15:0{i}:00Z", portfolio_kind="real",
               event_key=f"txn:{i}", amount=10.0)
            for i in range(3)
        ]
        got = lines(today_sections(deposits, now=NOW))["Investment Portfolio Analyzer"]
        self.assertEqual(got, ["Added $30.00 to your real portfolio (3 deposits)"])

    def test_legacy_per_edit_holdings_events_collapse_to_one_per_day(self) -> None:
        legacy = [ev("investment", "holdings_updated", f"2026-11-19T15:{m:02d}:00Z", tickers=["VTI"]) for m in range(10)]
        got = lines(today_sections(legacy, now=NOW))["Investment Portfolio Analyzer"]
        self.assertEqual(got, ["Updated the planning portfolio"])

    def test_page_views_and_selections_are_not_accomplishments(self) -> None:
        noise = [
            ev("investment", "ticker_analyzed", "2026-11-19T15:00:00Z", ticker="VTI"),
            ev("nba", "matchup_analysis", "2026-11-19T15:00:00Z", team="BOS"),
            ev("nba", "team_session", "2026-11-19T15:00:00Z"),
            ev("music", "practice_session_started", "2026-11-19T15:00:00Z"),
            ev("music", "mission_started", "2026-11-19T15:00:00Z"),
            ev("music", "song_selected", "2026-11-19T15:00:00Z"),
            ev("music", "studio_page_entered", "2026-11-19T15:00:00Z"),
            ev("baseball", "trend_filter_changed", "2026-11-19T15:00:00Z"),
            ev("baseball", "player_trend_viewed", "2026-11-19T15:00:00Z"),
            ev("baseball", "draft_assistant_session", "2026-11-19T15:00:00Z"),
            ev("applied_intelligence", "session_activity", "2026-11-19T15:00:00Z"),
            ev("applied_intelligence", "lesson_completed", "2026-11-19T15:00:00Z"),
        ]
        self.assertEqual(today_sections(noise, now=NOW), [])

    def test_directory_keeps_real_and_planning_apart(self) -> None:
        self.assertEqual(
            investment_directory_lines(INVESTMENT_DAY),
            [
                "Real portfolio: VTI · $0.28 cash · 2 transactions",
                "Planning portfolio: 100% VTI",
                "Goal: Long-Term Growth",
            ],
        )


class TestOtherApps(unittest.TestCase):
    def test_baseball_draft_is_grouped(self) -> None:
        events = [ev("baseball", "shared_league_created", "2026-11-18T01:00:00Z", league_name="Dynasty")]
        events += [ev("baseball", "live_draft_created", "2026-11-18T02:00:00Z", draft_room_id="r1")]
        events += [
            ev("baseball", "live_draft_pick", f"2026-11-18T02:{i:02d}:00Z", pick_number=i, draft_room_id="r1")
            for i in range(15)
        ]
        events += [ev("baseball", "completed_live_draft", "2026-11-18T03:00:00Z", draft_room_id="r1")]
        events += [ev("baseball", "trade_accepted", "2026-11-18T04:00:00Z", proposal_id="p1")]
        got = lines(week_sections(events, now=NOW))["Baseball Explorer"]
        self.assertEqual(
            got,
            [
                "Created shared league — Dynasty",
                "Started a live fantasy draft",
                "Completed a live draft",
                "Made 15 live draft selections",
                "Completed a trade",
            ],
        )

    def test_music_practice_and_saved_work(self) -> None:
        events = [
            ev("music", "practice_log_saved", f"2026-11-1{d}T15:00:00Z", practice_log_id=f"p{d}", minutes=20, song="Blues")
            for d in (6, 7, 8, 9)
        ]
        events += [
            ev("music", "multitrack_export_saved", "2026-11-17T15:00:00Z", export_id="x1", export_name="Take 1"),
            ev("music", "composition_saved", "2026-11-18T15:00:00Z", song="Night Song", composition_milestone="saved"),
            ev("music", "recording_reviewed", "2026-11-18T16:00:00Z", recording_id="r1", song="Blues"),
            ev("music", "recording_reviewed", "2026-11-18T16:01:00Z", recording_id="r1", song="Blues"),
        ]
        got = lines(week_sections(events, now=NOW))["Music Practice Coach"]
        self.assertEqual(
            got,
            [
                "Saved original composition — Night Song",
                "Saved a multitrack recording — Take 1",
                "Completed 4 practice sessions (80 min)",
                "Completed an AI coaching review — Blues",
            ],
        )

    def test_apps_are_grouped_in_suite_order(self) -> None:
        events = INVESTMENT_DAY + [
            ev("music", "practice_log_saved", "2026-11-19T16:00:00Z", practice_log_id="p", minutes=10),
            ev("baseball", "lineup_saved", "2026-11-19T16:00:00Z"),
        ]
        titles = [s.title for s in today_sections(events, now=NOW)]
        self.assertEqual(titles, ["Investment Portfolio Analyzer", "Baseball Explorer", "Music Practice Coach"])


class TestDates(unittest.TestCase):
    def test_today_uses_new_york_not_utc(self) -> None:
        # 2026-11-19 03:00 UTC is 22:00 on Nov 18 in New York: yesterday, not today.
        late = [ev("investment", "optimizer_run", "2026-11-19T03:00:00Z", event_key="o1", portfolio_kind="planning")]
        self.assertEqual(today_sections(late, now=NOW), [])
        self.assertEqual(len(week_sections(late, now=NOW)), 1)

    def test_week_starts_monday_in_new_york(self) -> None:
        self.assertEqual(local_week_start(NOW).isoformat(), "2026-11-16")
        # Sunday 23:30 New York (Monday 04:30 UTC) belongs to last week.
        sunday = [ev("investment", "optimizer_run", "2026-11-16T04:30:00Z", event_key="o2", portfolio_kind="planning")]
        monday = [ev("investment", "optimizer_run", "2026-11-16T05:30:00Z", event_key="o3", portfolio_kind="planning")]
        self.assertEqual(week_sections(sunday, now=NOW), [])
        self.assertEqual(len(week_sections(monday, now=NOW)), 1)

    def test_first_occurrence_keeps_its_real_date(self) -> None:
        a = ev("investment", "real_cash_deposited", "2026-11-17T15:00:00Z", event_key="txn:z", amount=5.0, portfolio_kind="real")
        b = dict(a, timestamp="2026-11-19T15:00:00Z")
        self.assertEqual(today_sections([a, b], now=NOW), [])  # done on Tuesday, not today
        self.assertEqual(len(week_sections([a, b], now=NOW)), 1)


class TestUserFacingCopy(unittest.TestCase):
    def test_no_developer_language_in_empty_states(self) -> None:
        import ai_command_center as cc

        for text in (cc.EMPTY_ACTIVITY_TEXT, cc.EMPTY_WEEK_TEXT, cc.LOAD_FAILED_TEXT):
            low = text.lower()
            for word in ("sibling", "repo", "backend", "streamlit", "supabase", "cloud", "sync"):
                self.assertNotIn(word, low)
        source = Path(cc.__file__).read_text(encoding="utf-8").lower()
        self.assertNotIn("sibling repos", source)
        self.assertNotIn("cloud activity backend", source)
        self.assertEqual(
            cc.EMPTY_ACTIVITY_TEXT,
            "No meaningful activity recorded yet. Your completed work across Daniel AI Suite will appear here.",
        )


class TestLoadStatus(unittest.TestCase):
    def test_cloud_failure_is_reported_not_shown_as_empty(self) -> None:
        import suite_storage

        with patch.object(suite_storage, "_use_cloud", return_value=True), patch(
            "suite_storage_supabase.load_events", side_effect=RuntimeError("Supabase GET failed (503)")
        ), patch.object(suite_storage, "_sqlite_load_events", return_value=[]):
            self.assertEqual(suite_storage.load_events(), [])
        self.assertFalse(suite_storage.LAST_EVENT_LOAD["ok"])
        self.assertIn("503", suite_storage.LAST_EVENT_LOAD["error"])
        with patch.object(suite_storage, "_use_cloud", return_value=True), patch(
            "suite_storage_supabase.load_events", return_value=[{"app": "investment"}]
        ):
            suite_storage.load_events()
        self.assertTrue(suite_storage.LAST_EVENT_LOAD["ok"])

    def test_read_cache_expires(self) -> None:
        import suite_storage_supabase as sb

        calls = []

        class Resp:
            status_code = 200
            content = b"[]"
            text = "[]"

            def json(self):
                return []

        cfg = type("C", (), {"url": "https://x", "key": "k"})()
        bucket: dict = {}
        with patch("requests.request", side_effect=lambda *a, **k: calls.append(1) or Resp()), patch.object(
            sb, "_read_cache_bucket", return_value=bucket
        ):
            sb._request("GET", "suite_activity_events", cfg=cfg, params={"a": "1"})
            sb._request("GET", "suite_activity_events", cfg=cfg, params={"a": "1"})
            self.assertEqual(len(calls), 1)  # cached
            for k, v in list(bucket.items()):
                bucket[k] = (v[0], v[1], v[2] - sb.READ_CACHE_TTL_SECONDS - 1)
            sb._request("GET", "suite_activity_events", cfg=cfg, params={"a": "1"})
            self.assertEqual(len(calls), 2)  # expired → refetched


class TestContinue(unittest.TestCase):
    def test_investment_resume_position_card(self) -> None:
        from project_intelligence import ResumeItem, _polish_resume

        item = ResumeItem(
            app="investment",
            item_key="portfolio:resume",
            title="My Portfolio → Transactions",
            subtitle="Real portfolio: 2 transactions · VTI · $0.28 cash",
            action_url="https://investment-portfolio-analyzer-ty2sbzumvxsqwbqhkvf6rz.streamlit.app?suite_page=My+Portfolio&suite_subtab=Transactions",
            updated_at="2026-11-19T15:00:00Z",
        )
        title, subtitle, priority = _polish_resume(item)
        self.assertEqual(title, "My Portfolio → Transactions")
        self.assertIn("Real portfolio", subtitle)
        self.assertGreaterEqual(priority, 60)


if __name__ == "__main__":
    unittest.main()
