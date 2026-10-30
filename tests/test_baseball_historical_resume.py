import json
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

from activity_feed import build_activity_dashboard, format_activity_message
from activity_grouping import activity_action_id
from project_intelligence import _raw_event_workflow_candidate
from project_intelligence import _projects_from_events
from activity_store import ActivitySnapshot


NOW=datetime.now(timezone.utc).replace(microsecond=0)


def event(kind,metrics,offset):
    return {'app':'baseball','event':kind,'timestamp':(NOW-timedelta(seconds=offset)).isoformat(),'metrics':metrics}


def query(item):
    return {k:v[0] for k,v in parse_qs(urlparse(item.action_url).query).items()}


def test_three_sequential_comparisons_retain_individual_resume_targets():
    players=[['Aaron Judge','Juan Soto'],['Mike Trout','Mookie Betts'],['Freddie Freeman','Corey Seager']]
    events=[event('player_comparison',{'players':p},30-i*10) for i,p in enumerate(players)]
    dash=build_activity_dashboard(events,now=NOW)
    assert any('Player Comparison (3 runs)' in line for line in dash.today_summaries)
    items=[i for i in dash.recent if i.message.startswith('Compared ')]
    assert len(items)==3
    assert {tuple(json.loads(query(i)['suite_players'])) for i in items}=={tuple(p) for p in players}
    old=next(i for i in items if 'Aaron Judge' in i.message)
    assert query(old)['suite_resume']=='compare:Aaron Judge:Juan Soto'
    assert json.loads(query(old)['suite_players'])==players[0]


def test_three_player_copy_and_continue_use_all_canonical_players():
    e=event('player_comparison',{'players':['Aaron Judge','Juan Soto','Mike Trout'],'player_a':'Aaron Judge','player_b':'Juan Soto'},1)
    assert format_activity_message(e)=='Compared Aaron Judge vs Juan Soto vs Mike Trout'
    item=build_activity_dashboard([e],now=NOW).recent[0]
    assert json.loads(query(item)['suite_players'])==e['metrics']['players']
    candidate=_raw_event_workflow_candidate(e)
    assert candidate is not None
    assert 'Mike Trout' in str(candidate)
    with patch('project_intelligence.load_all_events',return_value=[e]):
        rows=_projects_from_events(ActivitySnapshot())
    assert any(row[1]=='baseball' and 'Mike Trout' in row[2] and row[4]=='compare:Aaron Judge:Juan Soto:Mike Trout' for row in rows)


def test_saved_drafts_stay_separate_and_genuine_shared_leagues_keep_classification():
    events=[event('saved_draft_archived',{'draft_id':id,'draft_name':name,'draft_type':'simulator','saved_item_type':'saved_draft'},i+1)
            for i,(id,name) in enumerate([('draft-A','QA Mock A'),('draft-B','QA Mock B')])]
    assert all(activity_action_id(e)=='saved_draft' for e in events)
    for kind in ('shared_league_created','shared_league_invite','team_claimed'):
        assert activity_action_id(event(kind,{'league_id':'real-shared'},1))=='shared_league'
    dash=build_activity_dashboard(events,now=NOW)
    assert any('Saved Drafts (2 runs)' in line for line in dash.today_summaries)
    assert not any('Shared Leagues' in line for line in dash.today_summaries)
    assert {i.message for i in dash.recent}=={'Saved draft: QA Mock A','Saved draft: QA Mock B'}
    assert {query(i)['suite_saved_draft'] for i in dash.recent}=={'draft-A','draft-B'}
