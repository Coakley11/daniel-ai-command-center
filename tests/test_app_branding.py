"""Applied Intelligence branding matches the AMI app source of truth."""

from __future__ import annotations

import unittest

from app_branding import (
    app_icon,
    app_theme,
    applied_intelligence_branding_source,
    build_app_themes,
)
from app_registry import APP_DEFINITIONS


class TestAppliedIntelligenceBranding(unittest.TestCase):
    def test_icon_is_triangular_ruler_not_brain(self) -> None:
        self.assertEqual(app_icon("applied_intelligence"), "📐")
        self.assertNotEqual(app_icon("applied_intelligence"), "🧠")

    def test_registry_uses_same_icon(self) -> None:
        ami = next(a for a in APP_DEFINITIONS if a.key == "applied_intelligence")
        self.assertEqual(ami.icon, "📐")

    def test_theme_colors_match_ami_palette(self) -> None:
        theme = app_theme("applied_intelligence")
        self.assertEqual(theme["emoji"], "📐")
        self.assertEqual(theme["accent"], "#0ea5e9")
        self.assertEqual(theme["bg"], "#f0f9ff")
        self.assertEqual(theme["border"], "#7dd3fc")

    def test_app_directory_theme_in_build_app_themes(self) -> None:
        themes = build_app_themes()
        self.assertEqual(themes["applied_intelligence"]["emoji"], "📐")

    def test_branding_loaded_from_sibling_or_synced(self) -> None:
        self.assertIn(
            applied_intelligence_branding_source(),
            ("sibling", "synced", "fallback"),
        )
        self.assertNotEqual(applied_intelligence_branding_source(), "fallback")


if __name__ == "__main__":
    unittest.main()
