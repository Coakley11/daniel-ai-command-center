"""
Runtime deploy marker — bump when shipping diagnostics or activity trace fixes.

Streamlit Cloud may serve a stale mount after reboot; compare this string to GitHub dev HEAD.
"""

from __future__ import annotations

# Bump on every deploy-critical release (shown in UI footer + developer banner).
SUITE_BUILD_LABEL = "2026-06-06-event-trace-v1"
GIT_COMMIT_SHORT = "c902336"
GIT_BRANCH = "dev"
WORKFLOW_DIAGNOSTICS_LIVE = True

# Commits that must be present for Lorenzo Cain trend E2E verification.
DEPLOY_COMMITS_INCLUDED = ("5e172de", "09c26cc", "c902336")
