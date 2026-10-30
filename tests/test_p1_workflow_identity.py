from datetime import datetime,timedelta
from unittest.mock import patch
from urllib.parse import parse_qs,urlparse
import pytest
from music_continue_identity import eligible_payload, candidate_copy
from music_recording_identity import latest_recording_context
from music_command_center_dashboard import payload_from_action_url
from project_intelligence import build_project_continue_cards
from activity_store import ActivitySnapshot


def payload(song="Song C",pick="catalog-c",instrument="Guitar",key="D",kind="practice"):
    return dict(version=1,workspace_id="daniel",resume_kind=kind,studio_page=kind,
                song=song,pick_key=pick,instrument=instrument,display_key=key,source_type="catalog")


def event(name,p=None,minutes=0,**extra):
    return dict(app="music",event=name,timestamp=(datetime.now()-timedelta(minutes=minutes)).isoformat(),
                metrics={"workspace_id":"daniel",**({"resume_payload":p} if p else {}),**extra})


@pytest.mark.parametrize("name",["practice_log_saved","practice","composition_saved","song_selected",
    "instrument_changed","display_key_changed","studio_page_entered","audio_uploaded"])
def test_milestones_and_passive_events_ineligible(name):
    assert not eligible_payload(name,{"resume_payload":payload()})


def test_typed_practice_and_backing_eligible():
    assert eligible_payload("practice_session_started",{"resume_payload":payload()})
    assert eligible_payload("backing_track_started",{"resume_payload":payload(kind="backing")})


def test_mission_started_only_exact_catalog():
    p=payload(kind="creative")|dict(studio_page="creative",activity_destination="missions",mission="guide_tones")
    assert eligible_payload("mission_started",{"resume_payload":p})
    assert "started mission" in candidate_copy(p)[0]
    assert not eligible_payload("mission_completed",{"resume_payload":p})
    assert not eligible_payload("mission_started",{"resume_payload":p|dict(source_type="custom")})


def test_coaching_exact_catalog():
    p=payload(kind="creative")|dict(studio_page="creative",activity_destination="coaching")
    assert eligible_payload("song_coaching_used",{"resume_payload":p})


def test_contradictory_event_payload_is_rejected():
    assert not eligible_payload("practice_session_started",{"resume_payload":payload(),"song":"QA History Entry"})


def test_continue_label_url_and_newest_workflow_agree():
    events=[event("backing_track_started",payload("Song A","a","Saxophone","Cm","backing"),20),
            event("practice_log_saved",minutes=1,song="QA History Entry",instrument="Flute"),
            event("practice_session_started",payload(),2),event("composition_saved",minutes=0,song="New save")]
    with patch("project_intelligence.load_all_events",return_value=events),patch("project_intelligence.load_active_resume_items",return_value=[]):
        cards=build_project_continue_cards(ActivitySnapshot(),meta={"music":{"name":"Music","url":"http://localhost:8580"}})
    assert len(cards)==1
    assert cards[0].title=="Continue Song C practice"
    p=payload_from_action_url(cards[0].action_url)
    assert (p["song"],p["pick_key"],p["instrument"],p["display_key"]) == ("Song C","catalog-c","Guitar","D")


def test_recording_does_not_attach_to_later_log_or_unrelated_review():
    events=[event("audio_uploaded",minutes=10,recording_id="r1",song="River Sketch",source_type="composition",source_id="river",instrument="Guitar"),
            event("practice_log_saved",song="QA History Entry",instrument="Flute"),
            event("recording_reviewed",recording_id="r2",song="Other")]
    result=latest_recording_context(events)
    assert (result["song"],result["instrument"],result["source_id"]) == ("River Sketch","Guitar","river")
    assert not result["reviewed"]
    events.append(event("recording_reviewed",recording_id="r1"))
    assert latest_recording_context(events)["reviewed"]


def test_recording_insight_ignores_global_last_song_and_instrument():
    from coach_engine import generate_coach_insights
    snap=ActivitySnapshot(last_song="QA History Entry",last_instrument="Flute",last_music_upload_days_ago=0,
        music_recording_context=dict(recording_id="r1",song="River Sketch",instrument="Guitar",reviewed=False))
    messages=[x.message for x in generate_coach_insights(snap)]
    assert any("recording of River Sketch" in x for x in messages)
    assert not any("recording of QA History Entry" in x for x in messages)


def test_log_activity_renders_owned_title_and_instrument():
    from activity_feed import format_activity_message
    row=event("practice_log_saved",song="QA History Entry",instrument="Flute")
    row["metrics"]["minutes"]=30
    text=format_activity_message(row)
    assert text == "Logged practice: QA History Entry on Flute (30 min)"


def test_same_title_different_resources_stay_separate_until_global_ranking():
    from music_continue_identity import continue_rows
    events=[event("practice_session_started",payload("Shared title","custom::one","Flute")|dict(source_type="custom"),2),
            event("practice_session_started",payload("Shared title","composition::two","Guitar")|dict(source_type="composition"),1)]
    rows=continue_rows(events)
    assert len(rows) == 2
    assert {r[6]["pick_key"] for r in rows} == {"custom::one","composition::two"}


def test_historical_payload_is_unchanged_by_newer_candidate():
    from copy import deepcopy
    from music_continue_identity import continue_rows
    old=payload("Song A","a","Saxophone","Cm","backing");before=deepcopy(old)
    rows=continue_rows([event("backing_track_started",old,20),event("practice_session_started",payload(),1)])
    assert rows[0][6]["resume_payload"] == before
    assert old == before


def test_freeform_log_is_visible_in_actual_dashboard_feed():
    from activity_feed import build_activity_dashboard
    row=event("practice_log_saved",song="QA History Entry",instrument="Flute")
    dashboard=build_activity_dashboard([row])
    assert any("QA History Entry on Flute" in x.message for x in dashboard.recent)


def test_global_snapshot_cannot_invent_a_music_continue_task():
    from project_intelligence import _projects_from_events
    snap=ActivitySnapshot(last_song="QA History Entry",last_music_edit_days_ago=0)
    with patch("project_intelligence.load_all_events",return_value=[]):
        assert not [r for r in _projects_from_events(snap) if r[1] == "music"]


def test_directory_recording_summary_cannot_borrow_new_global_instrument():
    from activity_store import get_app_directory_card
    snap=ActivitySnapshot(music_directory_primary="Uploaded recording of River Sketch",music_directory_instrument="Guitar",last_instrument="Flute")
    card=get_app_directory_card(snap,"music")
    assert "Instrument: Guitar" in card.highlights
    assert "Instrument: Flute" not in card.highlights


def test_source_metadata_must_agree_with_canonical_pick():
    assert not eligible_payload("practice_session_started",{"resume_payload":payload(pick="custom::one")})
    assert not eligible_payload("practice_session_started",{"resume_payload":payload()|dict(source_id="other")})


def test_external_practice_analysis_link_roundtrips_its_run_identity():
    from suite_deep_links import build_resume_action_url,merge_handoff_metrics_from_action_url
    url=build_resume_action_url("applied_intelligence",resume_key="ai:practice_log_analysis:log-b",page="Solve a Problem",metrics=dict(analysis_run_id="run-b",question_id="log-b",source_app="music",context={"practice_log_summary":{"top_instrument":"Flute"}}),base_url="https://analysis.example")
    qs=parse_qs(urlparse(url).query)
    assert qs["suite_practice_analysis_run_id"] == ["run-b"]
    assert "suite_resume_payload" not in qs and "suite_pick_key" not in qs
    assert merge_handoff_metrics_from_action_url({},url)["analysis_run_id"] == "run-b"
