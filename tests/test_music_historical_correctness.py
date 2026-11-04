import ast
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest
from activity_feed import build_activity_dashboard
from music_directory_context import latest_music_context, apply_music_directory_context
from music_resume_payload import decode_payload_b64


def event(song='Attention', instrument='Guitar', hour=15, kind='mission_started'):
    pick = 'Pop\x1f' + song
    destination = 'missions' if kind == 'mission_started' else 'coaching'
    p = dict(version=1, workspace_id='daniel', song=song, pick_key=pick,
             source_type='catalog', source_id=pick, instrument=instrument, display_key='Gm',
             resume_kind='creative', studio_page='creative', activity_destination=destination,
             mission='Improvise using only chord tones', progress_activity_id=song + kind)
    m = dict(song=song, source_id=pick, source_type='catalog', instrument=instrument,
             practice_key='Gm', mission=p['mission'], progress_activity_id=p['progress_activity_id'],
             workspace_id='daniel', resume_payload=p)
    return dict(app='music', event=kind, timestamp=f'2026-11-04T{hour}:00:00Z', metrics=m)


@pytest.mark.parametrize('kind', ['mission_started', 'song_coaching_used', 'practice_session_started', 'backing_track_completed'])
def test_history_owns_all_url_fields_after_newer_unrelated_context(kind):
    old = event(kind=kind)
    if kind in {'practice_session_started', 'backing_track_completed'}:
        p = old['metrics']['resume_payload']
        p['resume_kind'] = p['studio_page'] = 'backing' if kind.startswith('backing') else 'practice'
        p.pop('activity_destination')
    if kind == 'backing_track_completed':
        old['event'] = 'practice_session_started'
        old['metrics']['backing_active'] = True
    newer = event('Wave', 'Flute', 16)
    dashboard = build_activity_dashboard([newer, old], now=datetime(2026, 11, 4, 18, tzinfo=timezone.utc))
    card = next(i for i in dashboard.recent if 'Attention' in i.message)
    query = parse_qs(urlparse(card.action_url).query)
    assert decode_payload_b64(query['suite_resume_payload'][0]) == old['metrics']['resume_payload']
    assert 'Wave' not in card.action_url


@pytest.mark.parametrize('field,value', [('song','Other'), ('instrument','Flute'), ('practice_key','F#'),
                                        ('source_id','other'), ('mission','Other mission')])
def test_inconsistent_history_never_offers_a_substitute(field,value):
    row = event(); row['metrics'][field] = value
    d = build_activity_dashboard([row], now=datetime(2026,11,4,18,tzinfo=timezone.utc))
    assert d.recent and not d.recent[0].action_url


def test_directory_timestamp_beats_old_type_rank_and_global_fallbacks():
    rows = [event('Blue Bossa','Saxophone',13, 'verified_chart_saved'),
            event('Wave','Guitar',14), event()]
    for order in [rows, list(reversed(rows))]:
        assert latest_music_context(order)['song'] == 'Attention'
        snapshot = SimpleNamespace(last_song='Blue Bossa', last_instrument='Flute')
        apply_music_directory_context(snapshot, order)
        assert snapshot.last_song == 'Attention' and snapshot.last_instrument == 'Guitar'
        assert snapshot.music_directory_primary == 'Last song: Attention · Catalog'


def test_missing_metadata_does_not_borrow_from_another_event():
    old, new = event(), event('Wave','Flute',16)
    del new['metrics']['instrument']; del new['metrics']['resume_payload']['instrument']
    assert latest_music_context([old,new])['song'] == 'Attention'
    assert latest_music_context([new]) == {}


def test_fallback_original_timestamp_wins_over_import_time_copy():
    import activity_store
    original = event('Blue Bossa','Saxophone',13)
    imported = deepcopy(original); imported['timestamp'] = '2026-11-04T19:00:00Z'
    newer = event()
    with patch.object(activity_store,'_load_db_events',return_value=[imported]), \
         patch.object(activity_store,'_load_fallback_events',return_value=[original,newer]):
        rows = activity_store.load_all_events()
    assert imported not in rows
    assert latest_music_context(rows)['song'] == 'Attention'


def test_music_fallback_import_cannot_re_record_old_work_as_new():
    import activity_store
    with patch.object(activity_store,'_load_db_events',return_value=[]), \
         patch.object(activity_store,'_load_fallback_events',return_value=[event()]), \
         patch.object(activity_store,'log_event') as record:
        activity_store._import_sibling_fallback_events()
    record.assert_not_called()


def test_continue_url_uses_candidate_envelope_instead_of_stale_stored_url():
    from suite_deep_links import build_music_continue_url
    from music_command_center_dashboard import resolve_music_continue_action_url
    chosen = event()['metrics']
    stale = build_music_continue_url(event('Wave','Flute',16)['metrics']['resume_payload'])
    url = resolve_music_continue_action_url(chosen,base_url='http://localhost:8611',stored_action_url=stale)
    assert decode_payload_b64(parse_qs(urlparse(url).query)['suite_resume_payload'][0]) == chosen['resume_payload']


def test_continue_action_has_consistent_forward_icon_only_for_continue():
    tree = ast.parse((Path(__file__).parents[1] / 'ai_command_center.py').read_text(encoding='utf-8'))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_render_go_button')
    calls = []
    ns = {'st': SimpleNamespace(link_button=lambda *a, **kw: calls.append(a))}
    exec(compile(ast.Module(body=[node],type_ignores=[]),'buttons','exec'),ns)
    for label in ['Continue','Resume','Open workspace']:
        ns['_render_go_button'](label,'http://localhost','test')
    assert [c[0] for c in calls] == ['→ Continue','Resume','Open workspace']


@pytest.mark.parametrize('source_id', ['custom::other', 'composition::other'])
def test_directory_rejects_declared_catalog_context_with_another_owner(source_id):
    row = event()
    row['metrics']['source_id'] = source_id
    row['metrics']['resume_payload']['pick_key'] = source_id
    row['metrics']['resume_payload']['source_id'] = source_id
    assert latest_music_context([row]) == {}


def test_directory_follows_explicit_resource_owned_instrument_change():
    previous = event()
    switched = event('Attention', 'Piano', 16, kind='instrument_changed')
    assert latest_music_context([previous, switched])['instrument'] == 'Piano'
