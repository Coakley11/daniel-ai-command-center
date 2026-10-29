"""App Directory tiles show the approved Music logo; other apps retain their icons."""

from __future__ import annotations

import base64
import unittest
from pathlib import Path

from app_branding import app_logo_data_uri

ROOT = Path(__file__).resolve().parents[1]


class AppDirectoryLogoTests(unittest.TestCase):
    def test_music_has_png_logo(self) -> None:
        for key in ("music",):
            uri = app_logo_data_uri(key)
            self.assertTrue(uri.startswith("data:image/png;base64,"), key)
            raw = base64.b64decode(uri.split(",", 1)[1])
            self.assertEqual(raw[:8], b"\x89PNG\r\n\x1a\n", key)

    def test_logo_files_are_square_and_crisp_at_2x(self) -> None:
        from PIL import Image

        for name in ("music_mpc_160.png",):
            with Image.open(ROOT / "branding" / "logos" / name) as im:
                self.assertEqual(im.size[0], im.size[1], name)
                self.assertGreaterEqual(im.size[0], 136, name)  # 4.25rem tile at 2x

    def test_apps_without_a_logo_keep_their_icon(self) -> None:
        for key in ("baseball", "investment", "nba", "applied_intelligence", "future_lens", "unknown"):
            self.assertEqual(app_logo_data_uri(key), "", key)

    def test_card_html_uses_logo_and_keeps_name(self) -> None:
        src = (ROOT / "ai_command_center.py").read_text(encoding="utf-8")
        block = src[src.index("def _build_app_card_html"):src.index("def _render_app_card")]
        self.assertIn("app_logo_data_uri(app.key)", block)
        self.assertIn('class="cc-app-logo"', block)
        self.assertIn('alt="{html.escape(app.name)} logo"', block)
        self.assertIn("theme['emoji']", block)  # fallback for apps without a logo

    def test_product_name_unchanged(self) -> None:
        from app_registry import APP_DEFINITIONS

        names = {a.key: a.name for a in APP_DEFINITIONS}
        self.assertEqual(names["music"], "Music Practice Coach")


if __name__ == "__main__":
    unittest.main()
