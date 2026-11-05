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
        self.assertEqual(hashlib.sha256(data).hexdigest(), 'd9f0256884bdf43a3469edee95ecb7cb06877938aeb790d5ddf5862662981cf5')
        with Image.open(io.BytesIO(data)) as im:
            self.assertEqual(im.size, (512, 512))

    def test_other_cards_keep_their_existing_icons(self):
        music = base64.b64decode(app_logo_data_uri('music').split(',', 1)[1])
        self.assertEqual(hashlib.sha256(music).hexdigest(), '4050c33c0ac1e6963b2b9ab79f8770f4520af78a6ec30751c7ac61a1d65fe1a7')
        for key in ('nba', 'applied_intelligence', 'future_lens'):
            self.assertEqual(app_logo_data_uri(key), '')
