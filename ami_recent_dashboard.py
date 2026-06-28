"""Recent AMI question list for Command Center."""

from __future__ import annotations

from dataclasses import dataclass

from activity_time import format_activity_display_time


@dataclass(frozen=True)
class RecentAmiQuestion:
    source_app: str
    source_label: str
    question: str
    updated_at: str
    display_time: str
    action_url: str
    item_key: str


def _app_meta() -> dict[str, dict[str, str]]:
    from app_registry import APP_DEFINITIONS

    return {app.key: {"name": app.name, "url": app.streamlit_url.strip()} for app in APP_DEFINITIONS}


def load_recent_ami_questions(limit: int = 8) -> list[RecentAmiQuestion]:
    """Return recent analytical questions across suite apps (newest first)."""
    from project_intelligence import _applied_math_continue_action_url
    from suite_analytical_question import is_practice_log_analysis_context, source_app_label
    from suite_deep_links import resume_metrics_from_item_key
    from suite_storage import load_active_resume_items

    meta = _app_meta()
    out: list[RecentAmiQuestion] = []
    seen_qids: set[str] = set()
    fetch_limit = max(limit * 3, 24)

    for item in load_active_resume_items(limit=fetch_limit):
        item_key = str(item.item_key or "")
        if item_key.startswith("ai:practice_log_analysis:"):
            continue
        if not item_key.startswith("ai:question:"):
            continue
        qid = item_key.rsplit(":", 1)[-1].strip()
        if not qid or qid in seen_qids:
            continue

        _, metrics = resume_metrics_from_item_key(
            "applied_intelligence",
            item.item_key,
            subtitle=item.subtitle,
        )
        ctx = metrics.get("context") if isinstance(metrics.get("context"), dict) else {}
        if is_practice_log_analysis_context(ctx):
            continue
        if str(metrics.get("handoff_kind") or "") == "practice_log_analysis":
            continue
        if str(metrics.get("display_category") or "") == "analysis_handoff":
            continue

        seen_qids.add(qid)
        source_app = str(metrics.get("source_app") or "").strip() or "applied_intelligence"
        question = str(metrics.get("question") or "").strip()
        if not question:
            subtitle = str(item.subtitle or "").strip()
            if subtitle.startswith("Question:"):
                question = subtitle.split("\n", 1)[0].replace("Question:", "", 1).strip()
            elif "__ctx_json__:" in subtitle:
                question = subtitle.split("\n__ctx_json__:", 1)[0].strip()
            else:
                question = subtitle.split("\n", 1)[0].strip()
        if not question:
            question = str(item.title or "Analytical question").strip()

        action_url = _applied_math_continue_action_url(
            item.item_key,
            "Solve a Problem",
            metrics,
            meta=meta,
            stored_action_url=str(item.action_url or ""),
        ) or str(item.action_url or meta.get("applied_intelligence", {}).get("url", ""))

        updated_at = str(item.updated_at or "").strip()
        out.append(
            RecentAmiQuestion(
                source_app=source_app,
                source_label=source_app_label(source_app),
                question=question,
                updated_at=updated_at,
                display_time=format_activity_display_time(updated_at) if updated_at else "",
                action_url=action_url,
                item_key=item.item_key,
            )
        )
        if len(out) >= limit:
            break
    return out
