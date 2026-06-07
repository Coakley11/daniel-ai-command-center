# Future Lens persistence audit + implementation plan — Priority E (2026-06-08)

**Repo:** `future-lens-ai-transition-simulator`

**Status:** Audit complete; implementation ordered below (after Music C verify + Applied Math D roadmap review)

---

## 1. What persists today

| Key / area | Persisted? | Mechanism |
|------------|------------|-----------|
| `broad_domain` | ✓ | Disk + cloud via `build_future_lens_disk_state` |
| `area` | ✓ | Same |
| `specific_skill` | ✓ | Same |
| `sim_year` | ✓ | Default 2030 if missing |
| `timeline_year` | ✓ | When set on Evolution tab |
| `wizard_complete` | ✓ key / ✗ value | Key in `_SESSION_KEYS` but **never assigned `True`** in app |
| `_suite_fl_view` | ✓ | Active tab (timeline/drivers/advice/simulation) |
| `_suite_fl_sim` | ✓ | Simulation identity string |
| `future_project` | ✓ | Derived `"{domain} / {area}"` on save |
| Active tab label | ✓ indirect | `apply_future_lens_view_from_restore` maps view ↔ tab |
| Simulation outputs / charts | ✗ | Recomputed on load |
| Career scenario library | ✗ | No saved scenarios |
| Skill forecast selections | ✗ | Only activity event, not session restore |
| Timeline topic focus | Partial | `timeline_year` only — not topic label |
| Resume identity (CC) | Partial | `simulation_completed` events with `resume_key=sim:{name}` |

**Persist key count:** 9 scalar keys + 3 extras — thinnest suite persistence vs Music (~30+ keys) or NBA (dynamic keys).

---

## 2. What does NOT persist

| Area | Gap | User impact |
|------|-----|-------------|
| **Career analysis logging** | `log_career_analysis()` defined in `future_lens_activity.py` but **never called** from `streamlit_app.py` | No Continue card for career scenario comparisons |
| **Resume URL depth** | CC deep link only sets `suite_sim` (120 chars) — no `domain`, `area`, `timeline_year`, `sim_year` | Second device / Continue opens wrong wizard context |
| **Domain on resume** | `_apply_suite_fl_sim` only backfills `specific_skill` + parses `future_project` if missing | Resume with sim name only loses area/domain |
| **Scenario library** | No disk structure for named saved scenarios | Cannot resume arbitrary career branches |
| **Simulation run state** | Slider inputs, branch choices, comparison table | User re-enters scenario after refresh |
| **Career analysis results** | No logging hook wired | Command Center has no career workflow card |
| **Skill persistence** | `log_skill_forecast_review` fires but skill profile fields not in `_SESSION_KEYS` beyond `specific_skill` | Skill tab context thin on restore |
| **Timeline topic** | `log_technology_timeline_review(topic=year)` logs year as topic | Topic conflated with year; timeline narrative not restored |

---

## 3. Root causes

### RC-1 — Dead activity hook

`future_lens_activity.log_career_analysis` exists (lines 59–68) but grep shows **zero imports** in `streamlit_app.py` for career flows. Simulation completion calls `log_simulation_completed` only.

### RC-2 — Resume URL under-specified

```218:223:c:\Users\danie\Documents\GitHub\daniel-ai-command-center\suite_deep_links.py
    elif app_key == "future_lens":
        sim = str(m.get("simulation") or m.get("project") or "").strip()
        ...
        if sim:
            params["suite_sim"] = sim[:120]
```

No params for `broad_domain`, `area`, `timeline_year`, `sim_year`, `_suite_fl_view`.

### RC-3 — Restore order vs resume launch

`streamlit_app.py` calls `restore_future_lens_state_once` early, then `finalize_suite_resume_launch` / `_apply_suite_fl_sim`. Resume sim hint can overwrite partial state if disk empty on new device.

### RC-4 — No scenario entity model

Persistence is flat session keys — no `{scenario_id, domain, area, skill, year, tab, notes}` records.

### RC-5 — `wizard_complete` never set

Key persists as `False` default forever; downstream code cannot distinguish "fresh wizard" vs "returning user with partial fields".

---

## 4. Proposed fixes

| ID | Fix | Files |
|----|-----|-------|
| **FL-P0a** | Wire `log_career_analysis(scenario=…)` when user completes career comparison flow | `streamlit_app.py`, locate career sim completion UI |
| **FL-P0b** | Enrich CC resume URL: `suite_fl_domain`, `suite_fl_area`, `suite_fl_year`, `suite_fl_view` (mirror NBA/music pattern) | CC `suite_deep_links.py`, FL `suite_resume_launch.py` |
| **FL-P0c** | `_apply_suite_fl_sim`: apply domain/area/year from resume params before defaults | `future_lens_persistent_state.py` |
| **FL-P1a** | Set `wizard_complete=True` after first successful wizard submit | `streamlit_app.py` |
| **FL-P1b** | Persist skill forecast profile id/name in `_PERSIST_EXTRA_KEYS` | `future_lens_persistent_state.py` |
| **FL-P1c** | Persist timeline topic string separate from `timeline_year` | `_SESSION_KEYS` + Evolution tab |
| **FL-P2a** | Scenario library: `saved_scenarios: list[dict]` in disk state (max 20, user-named) | New helpers + UI "Save scenario" |
| **FL-P2b** | Simulation slider snapshot under `_suite_fl_sim_state` | Persist on sim tab autosave |
| **FL-P2c** | Integration test matrix: wizard → tab switch → refresh → cloud pick | `tests/test_future_lens_persistence.py` |

---

## 5. Implementation order

Aligned with user-approved suite order:

| Step | Work | Depends on |
|------|------|------------|
| **E1** | FL-P0a — wire `log_career_analysis` | None | **Done** |
| **E2** | FL-P0b + FL-P0c — resume URL + restore enrichment | CC sync script push to FL repo | **Done** |
| **E3** | FL-P1a–c — wizard flag, skill profile, timeline topic | E2 |
| **E4** | Tests: restore + resume launch + CC metrics rebuild | E2 |
| **E5** | FL-P2a — scenario library (minimal: save/load one scenario) | E3 |
| **E6** | FL-P2b — simulation slider snapshot | E5 optional |

**Command Center coordination (Priority A follow-up):**

- Continue cards for `career_analysis` event (may already classify via generic FL events — verify `project_intelligence.py`)
- App Directory: show `domain / area / sim_year` from disk ingest (partially done in Priority A)

---

## Restore path diagram

```
App open
  ├─ restore_future_lens_state_once()
  │    ├─ disk music_user_state.json equivalent: future_lens_user_state.json
  │    ├─ cloud pick_restore_session (if Supabase + not resume URL)
  │    └─ apply_future_lens_disk_state → _SESSION_KEYS + extras
  ├─ apply_future_lens_view_from_restore()  → tab label
  ├─ finalize_suite_resume_launch("future_lens")
  │    └─ query params: suite_sim only (today)
  └─ _apply_suite_fl_sim()  → backfill specific_skill from sim string
```

**Failure modes:**

| Symptom | Cause |
|---------|-------|
| Wrong tab after Continue | `_suite_fl_view` not in resume URL; cloud stale |
| Wrong domain on phone | Cloud empty; only `suite_sim` in link |
| No career Continue card | `log_career_analysis` never fired |
| Wizard resets | `wizard_complete` false + defaults overwrite |

---

## Manual verification checklist (post E2)

- [ ] Set domain + area + skill + sim year → refresh → same
- [ ] Hard refresh / reboot → same (Supabase cloud)
- [ ] Phone ↔ Dell → cloud banner + matching wizard
- [ ] Command Center Continue → correct tab + domain
- [ ] App Directory → domain / area / simulation identity
- [ ] Career comparison → Continue card appears
- [ ] Reset → factory defaults only

---

## Related docs

- Suite usability audit §4 — [suite-usability-audit-2026-06-08.md](./suite-usability-audit-2026-06-08.md)
- Command Center tasks — [app_tasks.md](../app_tasks.md) P4

**Last updated:** 2026-06-08
