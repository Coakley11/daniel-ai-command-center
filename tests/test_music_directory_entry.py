"""Execute the actual Directory action without importing the Streamlit app."""
import ast
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import parse_qs,urlparse
from suite_deep_links import build_music_continue_url


def directory_action():
    tree=ast.parse((Path(__file__).resolve().parents[1]/'ai_command_center.py').read_text(encoding='utf-8'))
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_render_app_card')
    calls=[]
    ns=dict(ActivitySnapshot=object,APP_DEFINITIONS=[SimpleNamespace(key='music')],st=SimpleNamespace(),
            _render_unsafe_html=lambda html:None,_build_app_card_html=lambda *a:'card',
            _render_go_button=lambda label,url,key:calls.append((label,url,key)),
            get_app_url=lambda *a,**kw:'wrong-fallback',get_active_workspace_id=lambda st:'ariel')
    exec(compile(ast.Module(body=[node],type_ignores=[]),'directory-action','exec'),ns)
    with patch('music_command_center_dashboard.active_workspace_id',return_value='ariel'):
        ns['_render_app_card']('music',None)
    return calls[0]


def test_directory_opens_generic_songs_for_active_workspace():
    label,url,key=directory_action();q=parse_qs(urlparse(url).query)
    assert label=='Open workspace';assert key=='app_music'
    assert q['suite_entry_mode']==['workstream'];assert q['suite_page']==['picker']
    assert q['suite_workspace']==['ariel']
    assert not any(k.startswith('suite_resume') for k in q)
    assert 'suite_pick_key' not in q


def test_building_old_activity_does_not_change_directory_or_continue_semantics():
    before=directory_action()
    payload=dict(practice_context_id='old-context',resume_kind='practice',workspace_id='ariel',
                 pick_key='composition::old-document',song='Old saved composition',studio_page='practice',display_key='Eb')
    activity=build_music_continue_url(payload);q=parse_qs(urlparse(activity).query)
    assert q['suite_entry_mode']==['continue'];assert 'suite_resume_payload' in q
    assert directory_action()==before
