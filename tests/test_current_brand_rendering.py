"""Pin the actual shipped assets and all app-brand presentation paths."""
import ast
import base64
import hashlib
import html
import json
import os
from pathlib import Path
from types import SimpleNamespace

import app_branding as brands

ROOT = Path(__file__).resolve().parents[1]


def test_shipped_assets_match_current_apps():
    manifest = json.loads((ROOT / 'branding/logos/approved_manifest.json').read_text())
    for key, record in manifest.items():
        uri = brands.app_logo_data_uri(key)
        assert hashlib.sha256(base64.b64decode(uri.split(',', 1)[1])).hexdigest() == record['sha256']
        assert record['file'] == brands._APP_LOGO_FILES[key]
        assert record['transformation'].startswith('none')


def test_missing_or_replaced_file_never_keeps_stale_brand(monkeypatch, tmp_path):
    filename = brands._APP_LOGO_FILES['music']
    current = (brands._LOGO_DIR / filename).read_bytes()
    replacement = (brands._LOGO_DIR / brands._APP_LOGO_FILES['investment']).read_bytes()
    monkeypatch.setattr(brands, '_LOGO_DIR', tmp_path)
    # A missing asset is not negatively cached or replaced by the old two-note emoji.
    assert brands.app_logo_data_uri('music') == ''
    assert 'unavailable' in brands.app_brand_html('music', 'mark', fallback_icon='🎵')
    assert '🎵' not in brands.app_brand_html('music', 'mark', fallback_icon='🎵')
    file = tmp_path / filename
    file.write_bytes(current)
    assert base64.b64decode(brands.app_logo_data_uri('music').split(',', 1)[1]) == current
    revision = file.stat().st_mtime_ns
    file.write_bytes(replacement)
    os.utime(file, ns=(revision + 1_000_000, revision + 1_000_000))
    assert base64.b64decode(brands.app_logo_data_uri('music').split(',', 1)[1]) == replacement
    file.unlink()
    assert brands.app_logo_data_uri('music') == ''


class Collector:
    def __init__(self):
        self.parts = []
    def markdown(self, text, **kwargs):
        self.parts.append(text)
    def columns(self, count, **kwargs):
        return [self] * count
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass


def render_namespace():
    st = Collector()
    ns = dict(st=st, html=html, app_brand_html=brands.app_brand_html,
              APP_THEMES=brands.build_app_themes(), SECTION_ICONS={'coach': 'Insights', 'continue': 'Continue'},
              recently_used_apps=lambda **kwargs: [], _render_go_button=lambda *args: None)
    tree = ast.parse((ROOT / 'ai_command_center.py').read_text(encoding='utf-8'))
    names = {'_render_unsafe_html', '_render_continue_section', '_render_coach_insights'}
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    functions.insert(0, ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0))
    exec(compile(ast.fix_missing_locations(ast.Module(body=functions, type_ignores=[])), '<presentation>', 'exec'), ns)
    return ns, st


def test_continue_and_both_coach_layouts_use_images_without_old_app_icons():
    ns, st = render_namespace()
    cards = [SimpleNamespace(app_key=key, app_name=key, title='Saved work', subtitle='', emoji=emoji,
                             action_url='https://example.test', button_label='Continue')
             for key, emoji in [('music', '🎵'), ('investment', '📊'), ('baseball', '⚾')]]
    ns['_render_continue_section'](SimpleNamespace(last_opened_app=''), cards)
    ns['_render_coach_insights']([SimpleNamespace(key=c.app_key, icon=c.emoji, message='Review') for c in cards])
    markup = ''.join(st.parts)
    for card in cards:
        assert markup.count(f'data-app-logo="{card.app_key}"') == 2
        assert card.emoji not in markup


def test_obsolete_assets_removed_and_command_center_bytes_unchanged():
    for obsolete in ('music_mpc_160.png', 'baseball_dcbe_160.png', 'investment_160.png'):
        assert not (ROOT / 'branding/logos' / obsolete).exists()
        assert obsolete not in (ROOT / 'app_branding.py').read_text(encoding='utf-8')
    assert hashlib.sha256((ROOT / 'branding/logos/command_160.png').read_bytes()).hexdigest() == '7b35a7dd45483254e6e6eb8ae38d49b5f8db651b4ee6984f1363f890dc55c364'
