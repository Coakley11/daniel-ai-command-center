"""Focused App Directory tests; no server, cloud requests, or activity writes."""
import ast
import base64
import html
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from urllib.parse import urlsplit, parse_qs
import pytest
import app_registry
import app_urls
from app_branding import build_app_themes, app_logo_data_uri, uses_official_logo, app_brand_html
from robotics_directory import logo_html, description_html, launch_notice

ROOT = Path(__file__).parents[1]


@pytest.fixture(autouse=True)
def clean_configuration(monkeypatch):
    for key in ('ROBOTICS_APP_URL', 'SUITE_APP_URL_ROBOTICS', 'ROBOTICS_LOCAL_DEV', 'ROBOTICS_DEV_URL'):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr('streamlit.secrets', {})


def extracted(name, namespace):
    # Execute the actual rendering function without running unrelated dashboard startup.
    tree = ast.parse((ROOT / 'ai_command_center.py').read_text(encoding='utf-8-sig'))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    node.decorator_list = []
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(ROOT / 'ai_command_center.py'), 'exec'), namespace)
    return namespace[name]


def test_registration_preserves_existing_entries():
    apps = app_registry.APP_DEFINITIONS
    assert [a.key for a in apps[:-1]] == ['music', 'investment', 'baseball', 'nba', 'applied_intelligence', 'future_lens']
    assert all(a.streamlit_url.startswith('https://') and a.button_label == 'Go to App' and not a.logo_file for a in apps[:-1])
    robot = apps[-1]
    assert robot.name == 'Daniel AI Robotics'
    assert robot.category == 'Robotics / AI'
    assert robot.button_label == 'Open'
    assert robot.description == 'Virtual robotics laboratory for designing, simulating, and developing an intelligent physical humanoid robot.'


def test_missing_production_is_disabled():
    assert app_urls.robotics_app_url() == ''
    assert app_registry.get_app_url('robotics') == ''
    assert 'no configured deployment' in launch_notice('')


def test_local_open_preserves_workspace(monkeypatch):
    monkeypatch.setenv('ROBOTICS_LOCAL_DEV', '1')
    url = app_registry.get_app_url('robotics', workspace_id='ariel')
    assert urlsplit(url).hostname == '127.0.0.1'
    assert urlsplit(url).port == 8501
    assert parse_qs(urlsplit(url).query)['suite_workspace'] == ['ariel']
    assert 'start Robotics Lab' in launch_notice(url)


def test_production_configuration(monkeypatch):
    monkeypatch.setenv('ROBOTICS_APP_URL', 'https://robotics.example.org/')
    assert app_registry.get_app_url('robotics', workspace_id='daniel').startswith('https://robotics.example.org/')
    assert launch_notice(app_urls.robotics_app_url()) == ''


def test_existing_suite_override_convention(monkeypatch):
    monkeypatch.setenv('SUITE_APP_URL_ROBOTICS', 'https://robotics.example.org/')
    assert app_registry.get_app_url('robotics', workspace_id='daniel').startswith('https://robotics.example.org/')


@pytest.mark.parametrize('url', ['http://127.0.0.1:8501', 'javascript:alert(1)', 'https://localhost', 'https://user@example.org'])
def test_invalid_public_urls_rejected(monkeypatch, url):
    monkeypatch.setenv('ROBOTICS_APP_URL', url)
    assert app_urls.robotics_app_url() == ''


def test_actual_card_builder_contains_official_artwork():
    namespace = {'APP_DEFINITIONS': app_registry.APP_DEFINITIONS, 'APP_THEMES': build_app_themes(), 'ActivitySnapshot': object, 'app_logo_data_uri': app_logo_data_uri, 'uses_official_logo': uses_official_logo, 'app_brand_html': app_brand_html,
                 'get_app_directory_card': lambda *a: SimpleNamespace(when=None, highlights=()),
                 '_app_highlights_html': lambda *a: '', '_status_badge_html': lambda *a: '', 'html': html}
    rendered = extracted('_build_app_card_html', namespace)('robotics', object())
    assert 'alt="Daniel AI Robotics logo"' in rendered
    assert 'Robotics / AI' in rendered
    assert 'Virtual robotics laboratory' in rendered
    data = logo_html().split('base64,')[1].split('"')[0]
    assert base64.b64decode(data) == (ROOT / 'branding/logos/robotics_official.png').read_bytes()
    assert 'cc-app-logo-wrap' in rendered and 'data-app-logo="robotics"' in rendered


def test_actual_open_action_uses_configured_url(monkeypatch):
    monkeypatch.setenv('ROBOTICS_LOCAL_DEV', '1')
    fake_st = SimpleNamespace(caption=Mock())
    go = Mock()
    namespace = {'APP_DEFINITIONS': app_registry.APP_DEFINITIONS, 'ActivitySnapshot': object, 'st': fake_st,
                 'get_app_url': app_registry.get_app_url, 'get_active_workspace_id': lambda st: 'daniel',
                 '_render_unsafe_html': Mock(), '_build_app_card_html': Mock(return_value='card'), '_render_go_button': go}
    extracted('_render_app_card', namespace)('robotics', object())
    label, url, key = go.call_args.args
    assert (label, key) == ('Open', 'app_robotics')
    assert url.startswith('http://127.0.0.1:8501/')
    assert fake_st.caption.called


def test_actual_link_button_targets_local_robotics(monkeypatch):
    monkeypatch.setenv('ROBOTICS_LOCAL_DEV', '1')
    st = SimpleNamespace(link_button=Mock(), button=Mock(), caption=Mock())
    url = app_registry.get_app_url('robotics', workspace_id='daniel')
    extracted('_render_go_button', {'st': st})('Open', url, 'app_robotics')
    assert st.link_button.call_args.args == ('Open', url)
    assert urlsplit(url).hostname == '127.0.0.1' and urlsplit(url).port == 8501
    st.button.assert_not_called()


def test_seventh_card_is_not_truncated():
    class Column:
        def __enter__(self): return self
        def __exit__(self, *args): pass
    rendered = []
    namespace = {'st': SimpleNamespace(markdown=Mock(), columns=lambda *a, **k: [Column() for _ in range(3)]),
                 'ActivitySnapshot': object, 'SECTION_ICONS': {'apps': ''}, 'app_logo_data_uri': app_logo_data_uri, 'APP_DEFINITIONS': app_registry.APP_DEFINITIONS,
                 '_render_app_card': lambda key, snapshot: rendered.append(key)}
    # Avoid unrelated workstream rendering while exercising the actual directory grid.
    import sys
    monkey_module = SimpleNamespace(render_music_workstreams_section=lambda *a: None)
    from unittest.mock import patch
    with patch.dict(sys.modules, {'music_command_center_dashboard': monkey_module}):
        extracted('_render_app_directory', namespace)(object())
    assert rendered == [a.key for a in app_registry.APP_DEFINITIONS]
