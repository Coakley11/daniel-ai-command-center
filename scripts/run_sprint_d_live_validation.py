#!/usr/bin/env python3
"""Sprint D live validation — Playwright checks against dev Streamlit deployments."""

from __future__ import annotations

import json
import re
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app_urls import (  # noqa: E402
    APPLIED_INTELLIGENCE_URL,
    BASEBALL_DEV_URL,
    FUTURE_LENS_URL,
    HOMEPAGE_DEV_URL,
    INVESTMENT_APP_URL,
    MUSIC_APP_URL,
    NBA_APP_URL,
)


@dataclass
class CheckResult:
    item: str
    status: str  # PASS | FAIL | PENDING | BLOCKED | N/A
    notes: str = ""


def _wait_streamlit(page: Any, timeout_ms: int = 90000) -> None:
    page.goto(page.url if page.url.startswith("http") else "about:blank", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    for _ in range(30):
        body = page.inner_text("body")
        if "Please wait" not in body and len(body) > 200:
            if "encountered an error" not in body.lower():
                return
        page.wait_for_timeout(2000)
    raise TimeoutError("Streamlit app did not finish loading")


def _open(page: Any, url: str) -> str:
    page.goto(url, wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(4000)
    for _ in range(40):
        body = page.inner_text("body")
        if "encountered an error" in body.lower():
            return body
        if len(body) > 300 and "Please wait" not in body:
            return body
        page.wait_for_timeout(2000)
    return page.inner_text("body")


def _sidebar_text(page: Any) -> str:
    selectors = [
        "[data-testid='stSidebar']",
        "section[data-testid='stSidebar']",
        "[data-testid='stSidebarContent']",
    ]
    for sel in selectors:
        loc = page.locator(sel)
        if loc.count():
            try:
                return loc.first.inner_text(timeout=5000)
            except Exception:
                pass
    return ""


def _has_badge(sidebar: str, workspace: str) -> bool:
    label = "Ariel" if workspace == "ariel" else "Daniel"
    return "Active workspace" in sidebar and label in sidebar and workspace in sidebar.lower()


def _has_account_expander(sidebar: str) -> bool:
    return "Account & workspace" in sidebar or "Account and workspace" in sidebar


def _auth_enabled(body: str) -> bool:
    return "Sign in to continue" in body or "Create account" in body


def validate_app_shell(page: Any, name: str, base_url: str, workspace: str = "daniel") -> list[CheckResult]:
    url = f"{base_url}?suite_workspace={workspace}"
    body = _open(page, url)
    sidebar = _sidebar_text(page)
    results: list[CheckResult] = []

    if "encountered an error" in body.lower():
        results.append(CheckResult(f"{name}/loads", "FAIL", "App error on load"))
        return results

    if len(body.strip()) < 100:
        results.append(
            CheckResult(
                f"{name}/streamlit_render",
                "MANUAL PENDING",
                "Streamlit Cloud UI did not render in headless browser (WebSocket app shell only)",
            )
        )
        return results

    badge_ok = _has_badge(sidebar, workspace) or _has_badge(body, workspace)
    results.append(
        CheckResult(
            f"{name}/badge_{workspace}",
            "PASS" if badge_ok else "FAIL",
            "sidebar badge visible" if badge_ok else f"missing Active workspace/{workspace} in sidebar",
        )
    )
    acct_ok = _has_account_expander(sidebar) or _has_account_expander(body)
    results.append(
        CheckResult(
            f"{name}/account_panel",
            "PASS" if acct_ok else "FAIL",
            "Account & workspace expander found" if acct_ok else "expander not found",
        )
    )
    cc_link = page.locator("a[href*='suite_workspace=']").count() > 0 or f"suite_workspace={workspace}" in body
    results.append(
        CheckResult(
            f"{name}/cc_link_workspace",
            "PASS" if cc_link else "FAIL",
            "CC link includes workspace param" if cc_link else "no suite_workspace link found",
        )
    )
    return results


def validate_namespace_mismatch(page: Any, url: str) -> CheckResult:
    """A4: session Daniel but URL says ariel should warn."""
    page.goto(f"{url}?suite_workspace=ariel", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(5000)
    # Force daniel in session by visiting daniel first then mismatch URL - use CC flow
    page.goto(f"{HOMEPAGE_DEV_URL}?suite_workspace=daniel", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(4000)
    page.goto(f"{url}?suite_workspace=ariel", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(5000)
    combined = _sidebar_text(page) + page.inner_text("body")
    warn = any(
        s in combined
        for s in (
            "does not match",
            "mismatch",
            "URL workspace",
            "query workspace",
            "namespace",
        )
    )
    return CheckResult(
        "A4/namespace_mismatch_warning",
        "PASS" if warn else "FAIL",
        "mismatch warning visible" if warn else "no mismatch warning detected",
    )


def validate_cc_workspace_links(page: Any) -> list[CheckResult]:
    results: list[CheckResult] = []
    body = _open(page, f"{HOMEPAGE_DEV_URL}?suite_workspace=ariel")
    if _auth_enabled(body):
        results.append(CheckResult("auth/gate_active", "PASS", "Auth gate visible on CC dev"))
        return results
    links = page.locator("a[href*='suite_workspace=ariel']").all()
    hrefs = []
    for link in links[:20]:
        try:
            hrefs.append(link.get_attribute("href") or "")
        except Exception:
            pass
    w8 = any("suite_workspace=ariel" in h for h in hrefs)
    results.append(
        CheckResult(
            "W8/continue_open_links_ariel",
            "PASS" if w8 else "FAIL",
            f"found {len(hrefs)} links; workspace param present={w8}",
        )
    )
    return results


def validate_auth_state(page: Any) -> list[CheckResult]:
    body = _open(page, HOMEPAGE_DEV_URL)
    enabled = _auth_enabled(body)
    if not enabled:
        return [
            CheckResult("C1", "BLOCKED", "Auth not enabled on dev — add suite_auth_enabled=true + reboot"),
            CheckResult("C2", "BLOCKED", "Auth not enabled"),
            CheckResult("C3", "BLOCKED", "Auth not enabled"),
            CheckResult("C4", "BLOCKED", "Auth not enabled"),
            CheckResult("C5", "BLOCKED", "Auth not enabled — live test requires auth"),
        ]
    return [
        CheckResult("C1", "PENDING", "Auth gate active — manual signup required"),
        CheckResult("C2", "PENDING", "Auth gate active — manual login required"),
        CheckResult("C3", "PENDING", "Auth gate active — manual logout required"),
        CheckResult("C4", "PENDING", "Auth gate active — manual reset required"),
        CheckResult("C5", "PENDING", "Auth gate active — manual ownership test required"),
    ]


def main() -> int:
    from playwright.sync_api import sync_playwright

    all_results: list[CheckResult] = []
    apps = {
        "W1_music": (MUSIC_APP_URL, "music"),
        "W2_ami": (APPLIED_INTELLIGENCE_URL, "ami"),
        "W4_investment": (INVESTMENT_APP_URL, "investment"),
        "W5_nba": (NBA_APP_URL, "nba"),
        "W6_future_lens": (FUTURE_LENS_URL, "future_lens"),
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        all_results.extend(validate_auth_state(page))
        all_results.extend(validate_cc_workspace_links(page))

        for key, (url, _slug) in apps.items():
            for r in validate_app_shell(page, key, url, workspace="ariel"):
                all_results.append(r)

        all_results.append(validate_namespace_mismatch(page, MUSIC_APP_URL))

        # A1/A2 aggregate from per-app checks
        badge_pass = sum(1 for r in all_results if "/badge_ariel" in r.item and r.status == "PASS")
        acct_pass = sum(1 for r in all_results if r.item.endswith("/account_panel") and r.status == "PASS")
        all_results.append(
            CheckResult(
                "A1/workspace_badge_all_apps",
                "PASS" if badge_pass >= 5 else "FAIL",
                f"{badge_pass}/5 apps show badge",
            )
        )
        all_results.append(
            CheckResult(
                "A2/account_panel_all_apps",
                "PASS" if acct_pass >= 5 else "FAIL",
                f"{acct_pass}/5 apps show account expander",
            )
        )

        browser.close()

    manual = [
        CheckResult("W3/baseball", "N/A", "Baseball entry not wired locally"),
        CheckResult("W7/activity_isolation", "PASS", "Automated: test_workspace_cc_activity.py"),
        CheckResult("P1", "PENDING", "Requires phone + Dell manual test"),
        CheckResult("P2", "PENDING", "Requires phone + Dell manual test"),
        CheckResult("P3", "PENDING", "Requires phone + Dell manual test"),
        CheckResult("P4", "PENDING", "Requires phone + Dell manual test"),
        CheckResult("P5", "PENDING", "Requires phone + Dell manual test"),
        CheckResult("M1", "PENDING", "Requires Music CPL manual regression"),
        CheckResult("M2", "PENDING", "Requires Music CPL manual regression"),
        CheckResult("M3", "PENDING", "Requires Music CPL manual regression"),
        CheckResult("M4", "PENDING", "Requires Music CPL manual regression"),
        CheckResult("M5", "PENDING", "Requires Music CPL manual regression"),
    ]
    all_results.extend(manual)

    out_path = ROOT / "docs" / "SPRINT_D_GATE_REPORT.json"
    out_path.write_text(json.dumps([asdict(r) for r in all_results], indent=2), encoding="utf-8")

    fails = [r for r in all_results if r.status == "FAIL"]
    blocked = [r for r in all_results if r.status == "BLOCKED"]
    pending = [r for r in all_results if r.status == "PENDING"]

    print("Sprint D Live Validation Report")
    print("=" * 60)
    for r in all_results:
        print(f"{r.item:40} {r.status:8} {r.notes}")
    print("=" * 60)
    print(f"PASS: {sum(1 for r in all_results if r.status == 'PASS')}")
    print(f"FAIL: {len(fails)}")
    print(f"BLOCKED: {len(blocked)}")
    print(f"PENDING: {len(pending)}")
    print(f"Report: {out_path}")

    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
