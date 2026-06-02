# Music App vs Command Center — product split

**Music App** = personal music teacher (learning, coaching, recommendations).  
**Command Center** = personal activity dashboard (what you did, continue, reminders, cross-app awareness).

Do not duplicate coaching depth on the Command Center. Do not reduce the Music App to a launch-only shell.

---

## Music App (practice coach)

### Practice logs (in-app depth)

| Capability | Purpose |
|------------|---------|
| Minutes practiced | Session tracking |
| Songs practiced | Repertoire focus |
| Instrument used | Context for advice |
| What improved / needs work | Qualitative coaching |
| Streaks & consistency | Habit building |

**Today:** `practice_history.json`, Practice Log UI, progress trends in `streamlit_music_practice_app.py`.  
**Gap:** Structured “what improved / needs work” coaching copy; richer streak UX tied to recommendations.

### Uploads & videos (in-app depth)

| Capability | Purpose |
|------------|---------|
| Videos / audio uploaded | Performance archive |
| Compare to prior uploads | Progress over time |
| Improvement vs weak areas | Teacher-style feedback |

**Today:** Practice learning video panels exist in app.  
**Gap:** No `video_uploaded` / `audio_uploaded` activity events; no Command Center feed lines yet.

### Song recommendations (Music only)

Examples (generated inside Music App, not CC):

- “You’ve practiced Piano Man several times — focus on dynamics.”
- “Chord transitions improving — work on fills next.”
- “Try Shallow — similar patterns.”
- “Continue Hotel California — rhythm consistency.”

**Today:** Partial (practice trends, song library).  
**Gap:** Dedicated recommendation engine using skill level + history + weak areas.

### Progress tracking (Music only)

Technique, chord vocabulary, scales, rhythm, repertoire — charts and narratives stay in Music.

---

## Command Center (activity dashboard)

### Music activity — what to track

| Activity | Suggested event | Feed example |
|----------|-----------------|--------------|
| Last song opened | `song_selected` | Opened: Piano Man — Billy Joel |
| Last song practiced | `practice` | Practiced Piano Man (25 min) |
| Last song uploaded | `video_uploaded` / `audio_uploaded` | Uploaded video of Shallow |
| Last song edited | `chart_edit` (optional) | Edited chart for … |
| Verified chart save | `verified_chart_saved` | Saved verified chords for Hotel California |
| Verified lyrics save | `lyrics_saved` | Updated lyrics for The Scientist |
| Display key change | `display_key_changed` | Changed display key for Perfect |
| Instrument used | in `practice` / `app_state` metrics | Practiced guitar for 25 minutes |
| Backing track | `backing_track` | Used Backing Track Studio on Isn't She Lovely |
| Practice session | `practice` | (minutes + song) |
| Audio upload | `audio_uploaded` | Uploaded audio of … |
| Video upload | `video_uploaded` | Uploaded video of … |

### Continue where you left off

Resume items from `record_activity(..., resume_key=, resume_title=)`:

- Continue Piano Man  
- Continue Hotel California chart edits  
- Continue Shallow practice session  
- Continue Backing Track Studio project  

**Today:** Continue cards from resume items + `Continue: {title}` on song pick / practice / verified save.  
**Gap:** Distinct resume subtitles for chart edits vs practice vs backing track studio.

### Coach insights (Command Center)

Actionable reminders from **activity facts**, not full Music coaching:

- “You edited Hotel California yesterday but haven’t practiced it yet.”
- “You uploaded a performance of Piano Man — review and compare older recordings.” (after upload events exist)
- “You haven’t practiced guitar in 5 days.”
- “You recently saved verified chords for The Scientist.”

**Today:** Generic music insights in `coach_engine.py` (practice recency, block 30 min).  
**Gap:** Edit-without-practice, upload review, verified-save reminders.

### Weekly summary (Command Center)

| Metric | Source |
|--------|--------|
| Songs practiced | `practice` events + `practice_history.json` |
| Uploads | `video_uploaded` + `audio_uploaded` (not wired) |
| Verified chart edits | `verified_chart_saved` |
| Practice minutes | `practice.metrics.minutes` |
| Backing track sessions | `backing_track` |

**Today:** Minutes + songs practiced from history/events; verified edits partially via events.  
**Gap:** Upload counts, backing track week counts, lyrics_saved week count in `WeeklySummary`.

---

## Implementation status (2026-06)

### Wired to shared activity store

| Event | Music hook | CC feed | CC card / weekly |
|-------|------------|---------|------------------|
| `song_selected` | `songs/state.py` | Yes | Last song |
| `practice` | Practice log save | Yes | Minutes / streak (history) |
| `verified_chart_saved` | `verified_user_save.py` | Yes | Edit label |
| `lyrics_saved` | `verified_user_save.py` | Yes | Edit label |
| `backing_track` | Partial / varies | Yes (if emitted) | Partial |

### Not wired yet

- `video_uploaded`, `audio_uploaded`
- `display_key_changed`
- Upload-aware coach insights
- Music App recommendation engine (stays in Music repo)
- Weekly: uploads, verified lyrics count, backing track count

### Infrastructure

- **Supabase** shared store: all apps write; CC reads (`docs/SUITE_CLOUD_ACTIVITY.md`).
- **Feed priority:** Edits & practice rank above `song_selected` (`activity_feed.py`).

---

## Phased work

### Phase A — Command Center activity completeness ✅ (2026-06)

1. Music hooks: `music_activity.py` + `streamlit_music_practice_app.py` / `songs/key_state.py`
2. Events: `video_uploaded`, `audio_uploaded`, `display_key_changed`, `backing_track_started`,
   `backing_track_completed`, `recording_reviewed` (+ existing `practice`, verified/lyrics)
3. Command Center: `activity_feed.py`, `activity_store.py`, `coach_engine.py`, weekly summary UI
4. App Directory uses `music_directory_primary` (edits > practice > uploads > opens)

### Phase B — Music App coaching (no CC duplication)

1. Recommendation module (history + skill + similar songs).
2. Upload comparison UX (in Music only).
3. “What improved / needs work” fields on practice log.

### Phase C — Polish

1. Deprioritize `song_selected` on App Directory when edit/practice exists.
2. Cross-app insights remain separate per app key in `coach_engine.py`.

---

## Rule of thumb for new features

| Question | Music App | Command Center |
|----------|-----------|----------------|
| “What should I work on next?” | Yes | Only short reminder |
| “What did I do?” | Optional mirror | Yes |
| “How am I improving?” | Yes (depth) | No |
| “Continue where I left off?” | Deep link target | Yes (card) |

When adding Music functionality, ask: **does this teach?** → Music. **does this record or remind?** → emit `record_activity` + Command Center display.
