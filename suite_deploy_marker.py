"""
Runtime deploy marker — bump when shipping diagnostics or Continue pipeline fixes.

Streamlit Cloud may serve a stale mount after reboot; compare this string to GitHub dev HEAD.
"""

from __future__ import annotations

# Bump on every deploy-critical release (shown in UI footer + developer banner).
SUITE_BUILD_LABEL = "2026-06-06-trend-diagnostics-v2"
GIT_COMMIT_SHORT = "5e172de+deploy-v2"
GIT_BRANCH = "dev"
WORKFLOW_DIAGNOSTICS_LIVE = True
