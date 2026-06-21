#!/usr/bin/env python3
"""Print Supabase Auth URL configuration checklist for Real Accounts (C4 password reset)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    from suite_auth import auth_password_reset_redirect_url, supabase_auth_redirect_url_checklist

    site_url = auth_password_reset_redirect_url()
    redirects = supabase_auth_redirect_url_checklist()

    print("Supabase Dashboard -> Authentication -> URL configuration\n")
    print("Site URL (set exactly):")
    print(f"  {site_url or '(not configured — set HOMEPAGE_DEV_URL or suite_auth_redirect_url)'}\n")
    print("Redirect URLs (add each line; wildcards optional for *.streamlit.app if your project allows):")
    for url in redirects:
        print(f"  {url}")
    print("\nOptional secrets override (all dev apps, identical [suite_activity] block):")
    print('  suite_auth_redirect_url = "https://daniel-ai-command-center-ion4vh2cvo7bgdnkuktrb3.streamlit.app"')
    print("\nRecovery email template (required for Streamlit):")
    print("  docs/SUPABASE_RECOVERY_EMAIL_TEMPLATE.md")
    print(f"  redirect_to sent by app includes landing hint: {site_url or '(not configured)'}")
    print("\nAfter dashboard changes: send a new reset email (old links keep old redirect).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
