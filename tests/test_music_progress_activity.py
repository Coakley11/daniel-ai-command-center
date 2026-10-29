from copy import deepcopy
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit
import pytest
from activity_feed import build_activity_dashboard, format_activity_message, collapse_music_progress


def event(kind,**changes):
    m=dict(progress_activity_id='milestone-1',workspace_id='qa',source_type='catalog',
           source_id='Pop\x1fShape of You',song='Shape of You',practice_key='Cm',
           mission='Target only guide tones (3rds & 7ths)',coaching_focus='Chord tones',
           resume_payload=dict(version=1,resume_kind='creative',studio_page='creative',
               activity_destination='coaching',progress_activity_id='milestone-1',workspace_id='qa',
               pick_key='Pop\x1fShape of You',song='Shape of You',display_key='Cm',instrument='Saxophone'))
    m.update(changes)
    return dict(app='music',event=kind,timestamp='2026-10-28T15:00:00Z',metrics=m)


@pytest.mark.parametrize('kind,expected',[
    ('mission_started','Started mission: Target only guide tones (3rds & 7ths) on Shape of You · Catalog'),
    ('song_coaching_used','Used Song-Aware Coaching for Shape of You · Catalog'),
    ('composition_saved','Saved composition Shape of You · Catalog')])
def test_exact_summary_duplicate_cloud_fallback_and_resume(kind,expected):
    e=event(kind)
    assert format_activity_message(e)==expected
    dashboard=build_activity_dashboard([e,deepcopy(e)],now=datetime(2026,10,28,16,tzinfo=timezone.utc))
    assert len(dashboard.recent)==1
    assert any(expected in line for line in dashboard.today_summaries)
    assert not any('Practiced 1 song' in line for line in dashboard.today_summaries)
    assert dashboard.recent[0].message==expected
    assert 'runs' not in dashboard.recent[0].message
    if kind=='composition_saved':
        assert not dashboard.recent[0].action_url
        return
    params=parse_qs(urlsplit(dashboard.recent[0].action_url).query)
    assert params['suite_display_key']==['Cm']
    assert 'suite_resume_payload' in params


@pytest.mark.parametrize('source,label',[('catalog','Catalog'),('custom','Custom progression'),('composition','Composition')])
def test_source_labels(source,label):
    assert format_activity_message(event('song_coaching_used',source_type=source)).endswith(' · '+label)


def test_composition_updated_and_missing_optional_fields():
    assert format_activity_message(event('composition_saved',song='River Sketch',source_type='composition',composition_milestone='updated'))=='Updated composition River Sketch · Composition'
    for kind in ['composition_saved','song_coaching_used','mission_started']:
        e=event(kind);e['metrics']={}
        assert format_activity_message(e)


@pytest.mark.parametrize('change',[{'workspace_id':'other'},{'source_id':'other'},{'source_type':'custom'},{'progress_activity_id':'another'}])
def test_distinct_milestones_are_preserved(change):
    assert len(collapse_music_progress([event('composition_saved'),event('composition_saved',**change)]))==2


def test_old_practice_context_richer_revision_still_wins_with_progress():
    from tests.test_music_practice_context import event as practice
    old=practice(practice_context_revision=1)
    new=practice(practice_context_revision=2,backing_active=True,key_cycling_active=True)
    progress=event('song_coaching_used')
    dashboard=build_activity_dashboard([old,new,progress,deepcopy(progress)],now=datetime(2026,10,28,16,tzinfo=timezone.utc))
    assert len(dashboard.recent)==2
    assert any('with backing and Key Cycling' in item.message for item in dashboard.recent)


def test_retry_cannot_downgrade_updated_composition_summary():
    updated=event('composition_saved',composition_milestone='updated')
    saved=event('composition_saved',composition_milestone='saved')
    for events in [[updated,saved],[saved,updated]]:
        assert collapse_music_progress(events)==[updated]


@pytest.mark.parametrize('source',['custom','composition'])
def test_unverified_cold_source_resume_is_not_offered(source):
    e=event('song_coaching_used',source_type=source)
    dashboard=build_activity_dashboard([e],now=datetime(2026,10,28,16,tzinfo=timezone.utc))
    assert not dashboard.recent[0].action_url
