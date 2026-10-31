from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from activity_store import ActivitySnapshot, _ingest_suite_events, load_all_events, _import_sibling_fallback_events
from activity_feed import build_activity_dashboard, format_activity_message
from music_recording_identity import collapse_resource_deliveries


def upload(rid='r1', seconds=0, workspace='daniel', **extra):
    return dict(app='music', event='audio_uploaded', page='Recording Analysis',
        timestamp=(datetime.now(timezone.utc)+timedelta(seconds=seconds)).isoformat(),
        metrics=dict(recording_id=rid, workspace_id=workspace, filename='same.wav',
                     song='River Sketch', source_type='composition', source_id='river', **extra))


def test_mirrors_with_different_timestamps_count_one_before_rollup():
    events=[upload(),upload(seconds=3)]
    with patch('activity_store.load_all_events',return_value=events):
        snap=ActivitySnapshot();_ingest_suite_events(snap)
    assert snap.music_uploads_this_week == 1


def test_distinct_ids_same_filename_owner_second_count_two():
    first=upload();second=dict(first, metrics=dict(first['metrics'],recording_id='r2'))
    with patch('activity_store.load_all_events',return_value=[first,second]):
        snap=ActivitySnapshot();_ingest_suite_events(snap)
    assert snap.music_uploads_this_week == 2


def test_load_all_does_not_erase_distinct_ids_in_same_second():
    first=upload();second=dict(first,metrics=dict(first['metrics'],recording_id='r2'))
    mirror=dict(first,timestamp=upload(seconds=3)['timestamp'])
    with patch('activity_store._load_db_events',return_value=[first,second]),patch('activity_store._load_fallback_events',return_value=[mirror]):
        assert len(load_all_events()) == 2
    with patch('activity_store._load_db_events',return_value=[first,mirror]),patch('activity_store._load_fallback_events',return_value=[]):
        assert len(load_all_events()) == 1


def test_workspace_and_review_actions_are_separate():
    first=upload();review=dict(first,event='recording_reviewed')
    assert len(collapse_resource_deliveries([first,upload(workspace='ariel'),review])) == 3
    # A second review is an action, not evidence of another resource delivery.
    assert len(collapse_resource_deliveries([review,dict(review,timestamp=upload(seconds=3)['timestamp'])])) == 2


def test_unknown_legacy_resources_are_not_fuzzily_collapsed():
    first=upload('');second=dict(first)
    assert len(collapse_resource_deliveries([first,second])) == 2


def test_export_mirrors_collapse_and_have_no_resume():
    e=upload();e.update(event='multitrack_export_saved',page='Multitrack')
    e['metrics'].update(export_id='e1',export_name='QA River Mix',track_count=2,duration_seconds=5)
    mirror=dict(e,timestamp=upload(seconds=3)['timestamp'])
    dashboard=build_activity_dashboard([e,mirror])
    expected='Saved multitrack mix QA River Mix for River Sketch · Composition'
    assert format_activity_message(e) == expected
    assert [i.message for i in dashboard.recent] == [expected]
    assert not dashboard.recent[0].action_url
    from music_continue_identity import eligible_payload
    assert eligible_payload('multitrack_export_saved', e['metrics']) == {}
    distinct=dict(e,metrics=dict(e['metrics'],export_id='e2'))
    assert len(build_activity_dashboard([e,distinct]).recent) == 2


def test_fallback_import_preserves_distinct_same_song_recordings():
    first=upload();second=dict(first,metrics=dict(first['metrics'],recording_id='r2'))
    with patch('activity_store._load_db_events',return_value=[first]),patch('activity_store._load_fallback_events',return_value=[first,second,dict(second,timestamp=upload(seconds=3)['timestamp'])]),patch('activity_store.log_event') as log:
        _import_sibling_fallback_events()
    assert log.call_count==1 and log.call_args.kwargs['metrics']['recording_id']=='r2'


def test_fallback_import_does_not_repeat_an_untitled_export():
    first=upload();first.update(event='multitrack_export_saved')
    first['metrics'].update(export_id='e1',song='')
    copy=dict(first,timestamp=upload(seconds=3)['timestamp'])
    with patch('activity_store._load_db_events',return_value=[first]),patch('activity_store._load_fallback_events',return_value=[copy]),patch('activity_store.log_event') as log:
        _import_sibling_fallback_events()
    log.assert_not_called()
