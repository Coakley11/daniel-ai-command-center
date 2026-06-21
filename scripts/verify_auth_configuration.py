#!/usr/bin/env python3
"""Verify Supabase Auth backend configuration for Real Accounts (no secret values printed)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    from suite_auth import auth_backend_status, is_auth_enabled
    from suite_storage_config import cloud_storage_enabled, probe_secrets

    print("Daniel AI Suite — Supabase Auth configuration check\n")

    probe = probe_secrets()
    print("Cloud storage (PostgREST):")
    print(f"  [suite_activity] section:  {probe.suite_activity_section_found}")
    print(f"  supabase_url set:          {probe.supabase_url_found}")
    print(f"  supabase_key set:          {probe.supabase_key_found}")
    print(f"  cloud_storage_enabled:     {cloud_storage_enabled()}")
    if probe.secrets_error:
        print(f"  note:                      {probe.secrets_error}")

    status = auth_backend_status()
    print("\nReal Accounts (Supabase Auth):")
    print(f"  auth UI enabled:           {status.get('auth_ui_enabled')}")
    print(f"  supabase package:          {status.get('supabase_package_installed')}")
    print(f"  cloud config:              {status.get('cloud_config')}")
    print(f"  auth API key set:          {status.get('auth_api_key_set')}")
    print(f"  auth backend ready:        {status.get('ready')}")
    print(f"  message:                   {status.get('message')}")

    if not is_auth_enabled():
        print("\nAuth UI is OFF. Set suite_auth_enabled = true to test Real Accounts.")
        return 0

    if not status.get("ready"):
        print("\nAuth UI is ON but backend is NOT ready. Fix the message above, redeploy, and reboot.")
        return 1

    print("\nAuth backend looks correctly configured for login/signup/reset.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
