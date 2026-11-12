# Daniel AI Robotics App Directory entry

The existing registry, workspace-aware URL builder, three-column card grid, and
Open link button now include `robotics`. Its official logo is copied unchanged
from `C:/Users/danie/Downloads/daniel_ai_robotics_logo.png` to
`branding/logos/robotics_official.png`. It uses the existing approved-logo renderer and the same 4.25rem card icon container with
`object-fit: contain`. No existing app registrations or user data are changed.

There is no known deployed Robotics URL. With no configuration, the card remains
visible and Open is disabled with a configuration notice.

For local development, set these in the Command Center process:

```powershell
$env:ROBOTICS_LOCAL_DEV = "1"
# Optional override; defaults to http://127.0.0.1:8501/
$env:ROBOTICS_DEV_URL = "http://127.0.0.1:8501/"
```

Start Robotics Lab separately on that computer before selecting Open. A remote
browser's loopback address refers to its own computer; do not enable this mode in
a public deployment. A card notice identifies local development explicitly.

For a future deployed application, set `SUITE_APP_URL_ROBOTICS` (the existing Suite
override convention) or `ROBOTICS_APP_URL` to its verified HTTPS
address, or add `[suite_apps] robotics_url = "https://YOUR_VERIFIED_HOST/"` to
Streamlit secrets. Public configuration rejects loopback and non-HTTPS URLs.
No production URL is invented. Workspace context is appended using the existing
Suite helper; it is not a login credential and does not bypass Robotics Auth.

Validation: run `python -m pytest -q tests/test_robotics_directory.py
tests/test_app_directory_workspace_links.py tests/test_app_directory_applied_intelligence.py`.
These tests cover registration, actual card HTML, artwork bytes, all seven grid
entries, missing/public/local URL configuration, workspace propagation, and the
Open action's target. Browser clicking was not verified because computer use
was not approved for Chrome. No Command Center server is started by these tests.
