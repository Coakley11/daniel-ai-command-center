import base64
import hashlib
import io
import unittest
from pathlib import Path

from PIL import Image
from app_branding import app_logo_data_uri


class BaseballLogoTests(unittest.TestCase):
    def test_approved_asset_is_used_without_reencoding(self):
        data = base64.b64decode(app_logo_data_uri('baseball').split(',', 1)[1])
        self.assertEqual(hashlib.sha256(data).hexdigest(), '835b406170661fb6151e53ff1d6e0c179120122bfac2418e2343a951fb37f47a')
        with Image.open(io.BytesIO(data)) as im:
            self.assertEqual(im.size, (160, 160))

    def test_other_cards_keep_their_existing_icons(self):
        music = base64.b64decode(app_logo_data_uri('music').split(',', 1)[1])
        self.assertEqual(music, (Path(__file__).resolve().parents[1] / 'branding/logos/music_mpc_160.png').read_bytes())
        for key in ('investment', 'nba', 'applied_intelligence', 'future_lens'):
            self.assertEqual(app_logo_data_uri(key), '')
