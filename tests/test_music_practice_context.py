from copy import deepcopy
from datetime import datetime, timezone
import pytest
from activity_feed import build_activity_dashboard, format_activity_message, collapse_music_practice_contexts


def event(**metrics):
    m = dict(practice_context_id='visit-1', activity_schema_version=2, song='Shape of You',
        source_type='catalog', source_id='Pop|Shape of You', instrument='Saxophone',
        practice_key='Cm', workspace_id='qa', backing_active=False, key_cycling_active=False)
    m.update(metrics)
    return dict(app='music', event='practice_session_started', timestamp='2026-10-28T15:00:00Z', metrics=m)


@pytest.mark.parametrize('source,label', [('catalog','Catalog'),('custom','Custom progression'),('composition','Composition')])
@pytest.mark.parametrize('backing,cycling,words', [(True,False,'with backing on Saxophone in C minor'),
    (False,True,'with Key Cycling on Saxophone, starting in D minor'),
    (True,True,'with backing and Key Cycling on Saxophone, starting in D minor')])
def test_exact_summaries(source,label,backing,cycling,words):
    e = event(source_type=source, backing_active=backing, key_cycling_active=cycling,
        key_cycling_start_key='Dm', key_cycling_sounding_key='F#m')
    assert format_activity_message(e) == f'Practiced Shape of You {words} · {label}'


def test_snapshots_collapse_to_one_combined_card_without_runs():
    events = [event(),event(backing_active=True),event(backing_active=True,key_cycling_active=True,key_cycling_start_key='Cm')]
    for i,e in enumerate(events): e['timestamp'] = f'2026-10-28T15:0{i}:00Z'
    # Duplicated cloud/fallback deliveries, arbitrary load order.
    events = events + deepcopy(events)
    dashboard = build_activity_dashboard(list(reversed(events)), now=datetime(2026,10,28,16,tzinfo=timezone.utc))
    assert len(dashboard.recent) == 1
    assert 'with backing and Key Cycling' in dashboard.recent[0].message
    assert len(dashboard.today_summaries) == 1
    assert 'runs' not in dashboard.today_summaries[0]


@pytest.mark.parametrize('change', [dict(source_type='custom'),dict(source_id='other'),dict(practice_key='Gm'),
    dict(instrument='Piano'),dict(workspace_id='other'),dict(practice_context_id='visit-2')])
def test_isolation(change):
    assert len(collapse_music_practice_contexts([event(),event(**change)])) == 2


def test_missing_optional_and_legacy():
    assert format_activity_message(event(instrument='',practice_key='',source_type='')) == 'Practiced Shape of You'
    old = event(); old['metrics'].pop('practice_context_id')
    assert len(collapse_music_practice_contexts([old,old])) == 2

def test_equal_second_timestamps_cannot_downgrade_cumulative_activity():
    old = event(practice_context_revision=1)
    new = event(practice_context_revision=2,backing_active=True,key_cycling_active=True)
    assert collapse_music_practice_contexts([new,old,new,old]) == [new]
