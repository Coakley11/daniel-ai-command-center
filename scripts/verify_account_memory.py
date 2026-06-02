#!/usr/bin/env python3
"""Verify unified account memory configuration (no secret values printed)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    from suite_storage_config import cloud_storage_enabled, probe_secrets
    from suite_user import (
        account_mode,
        get_account_user_id,
        get_display_name,
        get_external_user_id,
        get_user_email,
    )

    print("Daniel AI Suite — account memory check\n")
    print(f"  suite_user_id (resolved):  {get_external_user_id()!r}")
    print(f"  suite_user_email:          {get_user_email()!r}")
    print(f"  display_name:              {get_display_name()!r}")
    print(f"  account_mode:              {account_mode()}")
    print(f"  account_user_id (storage): {get_account_user_id()!r}")

    probe = probe_secrets()
    print("\nSecrets probe:")
    print(f"  [suite_activity] section:  {probe.suite_activity_section_found}")
    print(f"  supabase_url set:          {probe.supabase_url_found}")
    print(f"  supabase_key set:          {probe.supabase_key_found}")
    print(f"  resolved via:              {probe.resolved_source}")
    if probe.secrets_error:
        print(f"  note:                      {probe.secrets_error}")

    if not probe.supabase_url_found or not probe.supabase_key_found:
        print(
            "\nMissing supabase_url and/or supabase_key under [suite_activity]. "
            "Cross-device sync requires both plus suite_user_id on every Streamlit app."
        )
        return 1

    if get_external_user_id() != "daniel":
        print(f"\nWarning: suite_user_id is {get_external_user_id()!r}, expected 'daniel' for your account.")

    if cloud_storage_enabled():
        try:
            from suite_storage_supabase import ping

            ok = ping()
            print(f"\nSupabase ping:               {'OK' if ok else 'FAILED'}")
        except Exception as exc:
            print(f"\nSupabase ping error:         {exc}")
            return 1
        if account_mode() != "cloud":
            print("Cloud secrets OK but account_mode is local — check ensure_user_row / migration 002.")
            return 1
    else:
        print("\nCloud storage not enabled — add Supabase URL + service_role key to secrets.")
        return 1

    print("\nAccount memory looks correctly configured for cross-device sync.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
