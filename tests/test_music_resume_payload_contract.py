"""Command Center's vendored music_resume_payload.py must equal Music's contract.

Music owns this module. There is no automatic Music -> Command Center sync, so
these tests pin the behaviors both apps must agree on; update the vendored copy
by copying Music's file verbatim, never by editing it here.
"""
from urllib.parse import parse_qs, urlparse

from music_command_center import build_continue_card
from music_continue_identity import candidate_copy, eligible_payload
from music_resume_payload import (continue_card_subtitle, continue_card_title, decode_payload_b64,
                                  resume_key_for_payload)


def _payload(**extra):
    base = dict(version=1, workspace_id="daniel", resume_kind="backing", studio_page="backing",
                song="Blue Bossa", pick_key="bb", instrument="Tenor Sax", display_key="Cm",
                key_kind="concert", backing_track_bpm=120, style="Auto", mood="Mellow")
    return base | extra


def test_vendored_titles_and_key_kind_match_command_center_copy():
    p = _payload()
    assert continue_card_title(p) == candidate_copy(p)[0] == "Continue Blue Bossa — Backing"
    assert continue_card_subtitle(p) == candidate_copy(p)[1] == "Catalog · Tenor Sax · Concert Cm · 120 BPM"


def test_vendored_mission_and_coaching_items_are_distinct_and_restorable():
    mission = _payload(resume_kind="creative", studio_page="creative", activity_destination="missions",
                       mission="guide_tones", progress_activity_id="a")
    coaching = _payload(resume_kind="creative", studio_page="creative", activity_destination="coaching",
                        progress_activity_id="b")
    km, kc = resume_key_for_payload(mission), resume_key_for_payload(coaching)
    assert km != kc and "creative_" not in (km, kc)
    for p, dest in ((mission, "missions"), (coaching, "coaching")):
        card = build_continue_card(p)
        q = parse_qs(urlparse(card["action_url"]).query)
        assert decode_payload_b64(q["suite_resume_payload"][0])["activity_destination"] == dest


def test_vendored_upload_does_not_claim_catalog():
    p = dict(version=1, workspace_id="daniel", resume_kind="upload", studio_page="analysis",
             upload_label="Gig.wav", upload_id="rec1", source_type="upload", source_id="rec1")
    assert continue_card_title(p) == "Continue Gig.wav — Upload"
    assert continue_card_subtitle(p) == "Upload"
    assert not eligible_payload("practice_session_started", {"resume_payload": p})
