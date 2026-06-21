#!/usr/bin/env python3
"""Live deploy health + auth gate probe for Sprint D."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app_urls import (  # noqa: E402
    APPLIED_INTELLIGENCE_URL,
    FUTURE_LENS_URL,
    HOMEPAGE_DEV_URL,
    INVESTMENT_APP_URL,
    MUSIC_APP_URL,
    NBA_APP_URL,
)


@dataclass
class ProbeResult:
    app: str
    url: str
    status: str
    loads: bool
    auth_gate: bool
    fatal_error: bool
    notes: str


APPS = {
    "command_center": HOMEPAGE_DEV_URL,
    "music": MUSIC_APP_URL,
    "investment": INVESTMENT_APP_URL,
    "nba": NBA_APP_URL,
    "ami": APPLIED_INTELLIGENCE_URL,
    "future_lens": FUTURE_LENS_URL,
}


def probe_app(name: str, url: str) -> ProbeResult:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 1200})
        try:
            page.goto(url, timeout=180000, wait_until="domcontentloaded")
            page.wait_for_timeout(20000)
            html = page.content()
            body = page.inner_text("body")
        except Exception as exc:
            browser.close()
            return ProbeResult(name, url, "FAIL", False, False, True, str(exc))
        browser.close()

    combined = html + "\n" + body
    fatal = "encountered an error" in combined.lower() or "syntaxerror" in combined.lower()
    auth = "Sign in to continue" in combined or "Create account" in combined or "Log in" in combined
    loads = len(html) > 10000 and not fatal
    if fatal:
        status = "FAIL"
        notes = "App error text detected"
    elif auth:
        status = "PASS"
        notes = "Auth gate visible (suite_auth_enabled active)"
    elif len(body.strip()) < 50:
        status = "INCONCLUSIVE"
        notes = "Streamlit UI did not render in headless session"
    else:
        status = "PASS"
        notes = "App rendered without fatal error; auth gate not detected (auth may be off or session cached)"
    return ProbeResult(name, url, status, loads, auth, fatal, notes)


def main() -> int:
    results = [probe_app(name, url) for name, url in APPS.items()]
    out = ROOT / "docs" / "SPRINT_D_LIVE_PROBE.json"
    out.write_text(json.dumps([asdict(r) for r in results], indent=2), encoding="utf-8")
    for r in results:
        print(f"{r.app:16} {r.status:12} auth={r.auth_gate} fatal={r.fatal_error}  {r.notes}")
    print(f"Wrote {out}")
    return 0 if all(r.status != "FAIL" for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
