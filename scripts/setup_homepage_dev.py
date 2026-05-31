"""Check Homepage Dev deployment status and print setup steps."""
from __future__ import annotations

import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app_urls import HOMEPAGE_DEV_URL, HOMEPAGE_PRODUCTION_URL  # noqa: E402

HOMEPAGE_DEV_PATH = "coakley11/daniel-ai-command-center/dev/ai_command_center.py"


def resolve_dev_url() -> str | None:
    response = requests.get(
        "https://share.streamlit.io/api/v2/apps/disambiguate",
        params={"path": HOMEPAGE_DEV_PATH},
        timeout=15,
    )
    if response.status_code != 200:
        return None
    return "https://" + response.json()["host"]


def main() -> int:
    print("Homepage deployment status\n")
    print(f"Production: {HOMEPAGE_PRODUCTION_URL}")
    print("  Branch: main")
    print()

    configured = HOMEPAGE_DEV_URL.strip()
    resolved = resolve_dev_url()

    if resolved:
        print(f"Dev (Streamlit Cloud): {resolved}")
        print("  Branch: dev")
        if configured and configured != resolved:
            print(f"\nNote: app_urls.py has {configured!r} but API resolves {resolved!r}")
            print("Update HOMEPAGE_DEV_URL in app_urls.py to match.")
        elif not configured:
            print("\nDev deployment exists but HOMEPAGE_DEV_URL is empty in app_urls.py.")
            print(f"Set HOMEPAGE_DEV_URL = {resolved!r}")
        return 0

    print("Dev: NOT DEPLOYED")
    print("  Branch: dev (configured, no Streamlit app yet)")
    print()
    print("Create Homepage Dev on Streamlit Cloud:")
    print("  1. Open https://share.streamlit.io")
    print("  2. Create app -> Coakley11/daniel-ai-command-center")
    print("  3. Branch: dev")
    print("  4. Main file: ai_command_center.py")
    print("  5. Deploy, then run this script again to get the URL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
