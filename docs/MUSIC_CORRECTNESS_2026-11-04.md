# Music → Command Center correctness slice — 2026-11-04

## Baselines and isolated worktrees

Fetched both origin/dev refs before editing. Music: ea12085dcfe99af221155ac9fa12f9769630de6a (newer than the supplied 18b7f49d reference), branch fix/cc-correctness-20261104, worktree ../cc-correctness-music. Command Center: a35dd5b0dc95d284dc6484e555fa5eabf26464eb, branch fix/music-correctness-20261104, this worktree. Candidates are local, unpushed commits; no push, merge, deployment, or cloud active-context synchronization. Music candidate: b70b4e92e572677c8b71e9fac91c8676056beebb.

## Audit before implementation

Historical Activity uses activity_feed._make_item → suite_deep_links.build_resume_action_url → encoded event metrics.resume_payload → Music's deferred suite_resume_launch finalizer → apply_music_resume_payload after full workspace/catalog hydration. It does not currently query global state at click time. The definite holes were unchecked agreement between displayed event facts and its envelope, and workflow restoration gated on progress_activity_id rather than the explicit workflow destination. Missing/invalid Mission identities silently retained the prior Mission. These are fail-closed and explicit-destination fixes; a correctly formed Mission payload already restored in the initial local browser probe, so this report does not claim every production symptom was reproduced.

Current/global contamination can enter through Music's existing creative workspace/selected Mission when a creative envelope lacks its marker, and through a newer global Fixed Practice Key setting that prevents the explicit saved resource key from committing. Music now validates Mission identity before activation, activates through the named resource's owner API, and restores authoritative saved keys using the existing standard key-mode setter. Missing Custom/Composition resources retain the existing terminal failure and library-preservation path.

Directory previously ingested Practice Logs, suite events, current-state rows, then local app-state files. The suite-event Directory summary ranked event type before timestamp (chart edits > legacy practice > backing/uploads > song selection). New practice_session_started, mission_started and song_coaching_used were not ranked. Current-state song/instrument unconditionally replaced snapshot values, then persisted app-state files could overwrite them again. Active-song disk state could be flattened/synchronized into current-state/resume metadata; it has persistence recency rather than meaningful-activity recency. Practice Logs use date-level ordering and cannot establish exact cross-workflow recency. suite_resume_items are separate workflow snapshots; main Music Continue already ranks eligible events and skips legacy Music resume rows. No transient Directory browser cache owns the summary (only connection status has a cache).

A further browser-discovered bug: _import_sibling_fallback_events re-recorded Music fallback events using import time. This fabricated recent activity and could promote an older song above newer meaningful work. Music fallback files are already read by load_all_events, so importing them again is unnecessary. The candidate skips that import and prefers an available original fallback fact over its identical artificially timestamped SQLite copy. If the original fact has been lost, its genuine historical timestamp cannot be reconstructed by this slice.

## Corrected precedence

1. Original activity timestamps win over import/delivery time for duplicate Music facts.
2. Directory chooses the newest valid timestamped meaningful Music event that jointly owns song, stable source identity, source type and instrument. Conflicting event/envelope identities are rejected; incomplete newer events do not borrow fields from another resource. Equal-time ties are deterministic by source/song/instrument.
3. Apply that complete Directory context after all legacy snapshot/log/file ingestion. Legacy metadata remains a fallback when no complete authoritative context exists. Resume rows and passive workspace saves cannot outrank a complete meaningful context.
4. Historical Resume validates and uses only its chosen event's detached envelope. It cannot substitute a newer event/global context. Continue ranks eligible event candidates; its URL is rebuilt from that candidate's envelope ahead of a conflicting stored URL.

The Directory Open action remains the generic workspace/source picker. No new workflow eligibility was added. Custom/Composition Practice and Backing keep their existing owner validation; unsafe progress workflows remain excluded. Card copy remains resource first, workflow second; Concert is used only for explicit key_kind=concert. Continue uses a small right arrow (→ Continue), centralized in the existing action renderer; Resume wording is unchanged.

## Validation

Baseline: Music's selected 58 tests pass after using an existing workspace-local pytest temp parent (initial failures were temp-directory permissions/path setup). Command Center's initial 27 tests pass. Expanded regression tests find two failures also confirmed by running inside an untouched origin/dev archive: test_app_directory_logos::test_apps_without_a_logo_keep_their_icon and test_practice_log_cc_continue::test_projects_from_events_includes_practice_log_analysis. The latter uses a June timestamp outside the current freshness window. These failures are not repaired in this slice.

Browser fixtures use actual Catalog records and Music's activity-reporting/owner APIs, not hand-authored cards: Blue Bossa/Saxophone/Cm → Wave/Guitar/D → Attention/Guitar/Gm, including Practice, Backing, Song-Aware Coaching, and Improvise using only chord tones. Music is then persisted on Wave/Piano. Local wrappers disable cloud access and point both apps at an isolated QA directory and SQLite database. Chromium clicks the actual Command Center Resume/Continue links into the real Music app and waits for its first completed Streamlit load. Each controlled fixture resets only its isolated QA database. Evidence and the reproducible local harness live in the Music worktree's .qa directory.

## Final results

Music focused restoration suites: **69 passed**, plus **67 passed** preservation/default-off/Key Cycling/practice/multitrack sentinel tests, run serially. Two pre-existing invalid-escape SyntaxWarnings remain.

Command Center combined focused/regression suite: **102 passed, 2 known baseline failures**. The final Directory/history-focused follow-up also passes all 18 tests. Baseline failures were independently reproduced inside the untouched origin/dev archive, not just assumed unrelated. Both repositories pass git diff --check. The Music envelope synchronization script reports byte-for-byte equality with Command Center's vendored copy.

| Actual historical Resume click | First completed Music load |
| --- | --- |
| Blue Bossa Practice | Catalog / Saxophone / Cm / Practice |
| Attention practice with backing | Catalog / Guitar / Gm / Backing |
| Attention Mission | Catalog / Guitar / Gm / Missions / Improvise using only chord tones |
| Attention Song-Aware Coaching | Catalog / Guitar / Gm / Song-Aware Coaching |
| Older Attention Mission immediately after a real Wave Resume | Correct Attention owner and exact Mission on first load, after both servers restarted |

Actual Continue clicks passed for Blue Bossa Practice, Attention Backing, Attention Mission and Attention Song-Aware Coaching. Each URL envelope equals the fixture emitted by Music's real activity functions; resource, destination, instrument and key match the restored controls. Continue opens a new tab through Streamlit's real link button; the harness follows that tab. Historical Resume remains same-tab. No successful Music case needed a manual refresh or second click.

A real post-restore musician interaction switched Attention to Piano, then generated a Mission example. The resulting emitted mission_started event owns Attention / catalog / Piano / Gm / Improvise using only chord tones, proving the restored resource is the active owner rather than only a visual shell. The earlier Generate example interaction with Guitar also retained Attention and Gm.

Directory sequence: Blue Bossa/Saxophone → Wave/Guitar → Attention/Guitar. Each controlled prefix selected the correct newest summary. Attention remained correct after Command Center reload and both application process restarts. Explicit resource-owned instrument-change events are also supported and regression-tested; incomplete or conflicting facts cannot borrow fields from a global snapshot.

1440px and 390px: visible Continue title/metadata/arrow and Directory song/instrument were inspected with the sidebar closed. Main content scrollWidth equals clientWidth (1440 and 390 respectively); no horizontal overflow. The Music logo remains intact. Directory Open workspace retains its generic source-picker URL.

Custom and Composition restoration/missing-resource behavior was audited through existing real owner/lifecycle and cold-entry preservation tests, not expanded to unverified progress workflows. No cloud active-context synchronization was enabled.

Recommendation: **safe to integrate these paired local candidates**, with the two documented baseline failures kept separate. This is isolated local acceptance, not production/deployment acceptance. If an old imported event has no surviving original timestamped delivery, the original occurrence time cannot be recovered automatically.

## Review scope and evidence

Music: music_resume_payload.py and tests/test_historical_workflow_resume.py.

Command Center: activity_feed.py, activity_store.py, ai_command_center.py, music_command_center_dashboard.py, music_continue_identity.py, music_directory_context.py, vendored music_resume_payload.py, tests/test_music_historical_correctness.py, the corrected realistic Mission/Coaching fixture in tests/test_music_progress_activity.py, and this report.

Local QA harness/data/logs are intentionally outside the commits. Music worktree .qa contains seed.py, music_app.py, browser_acceptance.py, browser_continue.py, final_owner_interaction.py, continue-results.json and final-browser-results.json. Screenshots include history-*.png, continue-*.png, visible-continue-{1440,390}.png, visible-directory-{1440,390}.png, final-attention-mission.png and final-mission-owner-interaction.png. The Command Center QA entry wrapper is qa_correctness_app.py. QA wrappers isolate storage and disable cloud access; they do not patch rendered cards or Music's restoration functions.
