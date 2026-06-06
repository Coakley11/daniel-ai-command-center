# Cross-App Analytical Questions v1 — Audit & Plan

**Goal:** Baseball / NBA / Investment question → Command Center card → Continue in Applied Intelligence.

---

## Audit: Applied Intelligence today

| Capability | Status | Location |
|------------|--------|----------|
| Custom quantitative questions | ✅ | `components/problem_solving.py` — "Solve a Problem" (`render_problem_solving_lab`) |
| Area picker (sports, finance, etc.) | ✅ | `QUANT_AREAS` in `content/quant_areas.py` |
| Preloaded question text | ✅ | `st.session_state.ps_library_problem` + `ps_area_id` |
| Analyst flow (variables, method) | ✅ | `components/problem_analyst.py` → `render_quantitative_flow` |
| Activity logging | ✅ | `applied_intelligence_activity.log_problem_solved` |
| Deep-link resume | Partial | `suite_resume_launch` supports `suite_lesson`, `suite_ai_page` only — **not** external questions |

**Gap:** No hook to open "Solve a Problem" with a question + source context from another app.

---

## Audit: Command Center storage

| Mechanism | Fits v1? | Notes |
|-----------|----------|-------|
| `suite_activity_events` (Supabase) | ✅ | Already stores `event`, `metrics`, `summary`, `resume_key` |
| `suite_resume_items` | ✅ | Continue cards; keyed by `app` + `item_key` |
| `record_activity` / `upsert_resume_item` | ✅ | Baseball compare already uses this pattern |
| New table required? | ❌ No | Use `event=analytical_question` with structured `metrics` |

### Proposed record format (v1)

```json
{
  "app": "baseball",
  "event": "analytical_question",
  "page": "Comparison Tool",
  "metrics": {
    "question": "Is Mike Piazza better than Ken Griffey Jr. overall?",
    "source_app": "baseball",
    "source_page": "Comparison Tool",
    "context_summary": "Piazza vs Griffey Jr. comparison loaded",
    "context": {
      "player_a": "Mike Piazza",
      "player_b": "Ken Griffey Jr."
    }
  },
  "resume_key": "ai:question:<hash>",
  "resume_title": "Applied Math question from Baseball",
  "resume_subtitle": "Piazza vs Griffey Jr. — compare overall value"
}
```

Command Center card target app: `applied_intelligence` (or `math` alias).

---

## Audit: Deep-link params (Applied Intelligence)

**Today:** `suite_lesson`, `suite_ai_page` via `suite_resume_launch._apply_applied_intelligence`.

**v1 additions:**

| Param | Purpose |
|-------|---------|
| `suite_resume` | `ai:question:<id>` |
| `suite_ai_question` | User question text |
| `suite_ai_source_app` | baseball / nba / investment |
| `suite_ai_source_page` | e.g. Trend Value |
| `suite_ai_area` | Optional quant area id (sports, finance) |
| `suite_ai_context` | URL-safe JSON or pipe-delimited summary |

Applied Intelligence on launch:
- Set `view_mode` → primary action for problem solving (e.g. "Solve a Problem")
- Set `ps_library_problem`, `ps_area_id` from params
- Show source banner: "From Baseball · Comparison Tool"

---

## Smallest v1 implementation path

### Phase 1 — Shared module (Command Center + sync)

1. `suite_analytical_question.py` (new, synced to all apps)
   - `build_question_payload(source_app, page, question, context)`
   - `submit_analytical_question(st, ...)` → `record_activity` with `event=analytical_question`
   - `build_applied_math_resume_url(question_payload)`

### Phase 2 — Source apps (sidebar form)

2. **Baseball / NBA / Investment:** sidebar expander "Analyze with Applied Math"
   - Text area for question (optional default from page)
   - Auto-fill context from session (players, team, portfolio tickers)
   - Submit → `submit_analytical_question`

### Phase 3 — Command Center

3. `project_intelligence._projects_from_events` — emit card:
   - Title: `Applied Math question from {source_app}`
   - Subtitle: truncated question
   - `resume_key`: `ai:question:<hash>`
   - App: `applied_intelligence`
   - Priority: ~55 (below music/baseball workflow, above generic)

4. Homepage section (optional): "Pending analytical questions" if count > 0

### Phase 4 — Applied Intelligence

5. Extend `suite_resume_launch._apply_applied_intelligence` for new params
6. `streamlit_app.py` — after resume launch, if `_suite_ai_question` set → `view_mode = "Solve a Problem"`
7. `problem_solving.py` — read preloaded question; show source context banner

### Phase 5 — Tests

8. CC: analytical_question → Continue card URL includes `suite_ai_question`
9. Applied Intelligence: resume launch sets `ps_library_problem`

**Out of scope v1:** Auto-solving, LLM routing, perfect area detection, question dedup across apps.

---

## Estimated touch count

| Repo | Files |
|------|-------|
| Command Center | `suite_analytical_question.py`, `project_intelligence.py`, `suite_deep_links.py`, `suite_resume_launch.py` |
| Baseball / NBA / Investment | sidebar widget + 1 import each |
| Applied Intelligence | `suite_resume_launch.py`, `streamlit_app.py`, `problem_solving.py` |

~12 files, no schema migration.
