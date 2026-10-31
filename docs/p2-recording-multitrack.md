# Resource-aware Music activity

Recording-upload deliveries collapse by workspace, action and recording ID, independent of filenames and delivery timestamps. Existing review semantics remain unchanged. Saved Multitrack exports collapse by canonical export ID. Distinct IDs remain distinct even with the same song, filename and second. Legacy events without resource identity are not fuzzily merged.

Resource collapse runs before ingestion counters and dashboard grouping, including SQLite-only reads. Fallback import uses the same identity instead of song-title matching, preserving distinct same-song resources and avoiding repeated imports of untitled exports. The legacy ingestion key no longer erases different identified recordings in the same second. Existing P1 recording insights continue using the upload's own context.

Saved export wording is `Saved multitrack mix QA River Mix for River Sketch · Composition`. It is a factual export milestone, not Composition-save activity or a layer edit. It has no Resume and is not added to inferred Continue. Counts/durations may be retained as safe facts but are not invented in the headline.

Tests cover mirrored delivery times, same-second distinct IDs, same filename, workspace isolation, review separation, legacy uncertainty, export collapse/rendering and no Resume, alongside existing activity/grouping/noise/P1 checks.
