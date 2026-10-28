from __future__ import annotations
import ast, html
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Any
import streamlit as st
from activity_models import ActivityFeedItem
from activity_feed import build_activity_dashboard
from activity_time import format_activity_display_time
st.set_page_config(page_title='Command Center Slice 2 QA',layout='wide',initial_sidebar_state='collapsed')
source=Path(__file__).with_name('ai_command_center.py').read_text(encoding='utf-8')
for node in ast.parse(source).body:
    if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call):
        call=node.value
        if call.args and isinstance(call.args[0],ast.Constant) and '<style>' in str(call.args[0].value):
            st.markdown(call.args[0].value,unsafe_allow_html=True)
    if isinstance(node,ast.FunctionDef) and node.name in {'_render_unsafe_html','_render_feed_items','_render_recent_activity_feed'}:
        exec(compile(ast.Module(body=[node],type_ignores=[]),__file__,'exec'),globals())
SECTION_ICONS={'feed':'🕐'}
def can_show_developer_tools(**kw): return False

def load_all_events():
    events=[]
    for i,(source,title,backing,cycling) in enumerate([
        ('catalog','Shape of You',False,True),('catalog','Shape of You',True,False),
        ('catalog','Shape of You',True,True),('custom','Evening progression',True,True),
        ('composition','River sketch',True,False)]):
        m=dict(activity_schema_version=2,practice_context_id=f'qa-{i}',source_type=source,
            source_id=f'{source}::qa-{i}',song=title,instrument='Saxophone',practice_key='Cm',
            backing_active=backing,key_cycling_active=cycling,key_cycling_start_key='Cm',workspace_id='qa')
        m['resume_payload']=dict(version=1,resume_kind='backing' if backing else 'practice',
            studio_page='backing' if backing else 'practice',workspace_id='qa',pick_key=m['source_id'],
            song=title,instrument='Saxophone',display_key='Cm',practice_context_id=f'qa-{i}')
        events.append(dict(app='music',event='practice_session_started',
            timestamp=(datetime.now(timezone.utc)-timedelta(minutes=i)).isoformat(),metrics=m))
    return events
st.title('Command Center')
_render_recent_activity_feed()
