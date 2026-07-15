# Command Center Philosophy + Fantasy Workflow Integration

**Date:** 2026-07-14  
**Status:** Implemented (first slice) — Continue / Activity / Directory + Baseball emitters  
**Repos:** `daniel-ai-command-center` (`dev`) + emitters in `baseball-stat-app` (`dev`)

---

## Three surfaces (keep separated)

### 1. Continue — recent, actionable resume

Very recent events that still make sense to continue. Each card restores the user into the exact workflow, focused on the relevant item.

| Event | Continue copy (examples) | Resume target |
|-------|--------------------------|---------------|
| Trade offer received | Trade offer from Team X | Trade Center · that offer selected |
| Trade accepted | Trade completed · A ⇄ B | Trade Center · completed trade |
| Trade declined / expired / canceled | Offer declined / expired | Trade Center · history |
| Waiver add/drop | Dropped A · Added B | Waiver Wire · that transaction |
| Shared league invite | Invited to Robbins League | Saved Draft Library · that invite |
| Shared league created | Robbins League created | Saved Draft Library · that league |
| Lineup locked / saved | Week 1 lineup locked | Fantasy Lineup · that week |
| Live Draft completed | Completed Live Draft: … | Live Draft summary |
| Active Draft changed | Active League set to … | Saved Draft Library · Active card |
| Team claimed | Claimed Team Y | Library / Active League |

**Lifecycle:** When a trade offer is accepted, remove the pending-offer Continue card and emit a Trade Accepted card.

Continue is **not** a full history. Age out or supersede when no longer actionable.

### 2. App Directory — identity card (not navigation)

Short reminders of meaningful work this app has been used for recently.

- Not a notification feed
- Not exact resume
- Clicking Baseball still opens the app’s normal entry
- Examples: Robbins League Live Draft · Fantasy Trade Management · Fantasy Lineup · Waiver Wire · Hall of Fame Case Studies

### 3. Activity — detailed work history

Describes what the user did (compare players, lock lineup, create shared league, accept trade, waiver moves, complete Live Draft, …).

---

## Fantasy event emission (source apps → Command Center)

Baseball (and eventually other apps) should emit suite activity rows / continue payloads for:

- Shared league created / invited / claimed
- Trade offered / accepted / declined / expired / canceled
- Waiver add / drop
- Weekly lineup saved / locked
- Live Draft start / complete / draft saved
- Active Draft / Active League changed

**Deep links** should use existing `suite_resume_launch` + `suite_deep_links` patterns (`?suite_workspace=`, page, proposal id, invite id, league id, week).

---

## Implementation slices

1. **CC taxonomy** — Map fantasy event types → Continue vs Activity vs Directory chips; supersede rules (offer → accepted).
2. **Emitters in Baseball** — Ensure trade/waiver/lineup/library/live-draft paths write activity + continue-eligible flags.
3. **Continue dashboard** — Card builders + deep links for each fantasy resume target.
4. **App Directory** — High-level chips derived from recent significant fantasy work (deduped titles).
5. **Activity feed** — Grouping/noise filters so fantasy history is readable without drowning Continue.
6. **Tests** — Classification, supersede, deep-link, feed isolation (Daniel vs coakley).

---

## Philosophy (one line each)

- **Continue** resumes work that is still current.  
- **Activity** explains what the user accomplished.  
- **App Directory** identifies the app through a few meaningful recent uses.
