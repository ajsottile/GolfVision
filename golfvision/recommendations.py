from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from golfvision.coaching import _severity
from golfvision.drills import DRILL_BY_ID, get_drills_for_metric, serialize_drills
from golfvision.knowledge import build_pro_context
from golfvision.llm import generate_llm_report, is_openai_configured
from golfvision.metrics import MetricComparison
from golfvision.practice_plan import build_rule_based_report


@dataclass
class CoachingReport:
    summary: str
    recommendations: list[dict[str, Any]]
    quick_routine: dict[str, Any]
    multiweek_plan: dict[str, Any]
    source: str


def _direction_for(metric: str, deviation: float) -> str:
    if metric == "tempo_ratio":
        return "too fast in transition" if deviation < 0 else "too slow in transition"
    if metric == "head_stability":
        return "more head movement than pro" if deviation > 0 else "more stable than pro"
    return "above pro baseline" if deviation > 0 else "below pro baseline"


def build_analysis_packet(
    comparisons: list[MetricComparison],
    overall_score: float,
    view_name: str,
) -> dict[str, Any]:
    ranked = sorted(comparisons, key=lambda item: item.normalized_error, reverse=True)
    faults: list[dict[str, Any]] = []
    for comparison in ranked:
        if comparison.normalized_error < 0.2:
            continue
        faults.append(
            {
                "metric": comparison.metric,
                "phase": comparison.phase,
                "pro_value": comparison.pro_value,
                "user_value": comparison.user_value,
                "deviation": comparison.deviation,
                "normalized_error": comparison.normalized_error,
                "severity": _severity(comparison.normalized_error),
                "direction": _direction_for(comparison.metric, comparison.deviation),
            }
        )

    all_comparisons = [
        {
            "metric": item.metric,
            "phase": item.phase,
            "pro_value": item.pro_value,
            "user_value": item.user_value,
            "deviation": item.deviation,
            "normalized_error": item.normalized_error,
            "severity": _severity(item.normalized_error),
            "direction": _direction_for(item.metric, item.deviation),
        }
        for item in ranked
    ]

    return {
        "overall_score": overall_score,
        "view": view_name,
        "faults": faults,
        "all_comparisons": all_comparisons,
        "top_faults": faults[:5],
        "available_drills": [{"id": drill["id"], "name": drill["name"]} for drill in serialize_drills()],
    }


def _valid_drill_ids(drill_ids: list[str]) -> list[str]:
    return [drill_id for drill_id in drill_ids if drill_id in DRILL_BY_ID]


def _is_missing_text(value: Any) -> bool:
    text = str(value or "").strip().lower()
    return text in {"", "n/a", "na", "none", "not provided", "unknown", "tbd"}


def _validate_report(raw: dict[str, Any]) -> dict[str, Any]:
    summary = str(raw.get("summary", "")).strip() or "No summary available."
    recommendations = raw.get("recommendations", [])
    if not isinstance(recommendations, list):
        recommendations = []
    cleaned_recommendations = []
    for item in recommendations:
        if not isinstance(item, dict):
            continue
        cleaned_recommendations.append(
            {
                "title": str(item.get("title", item.get("focus", "Focus area"))),
                "focus": str(item.get("focus", "Focus area")),
                "what_is_happening": str(item.get("what_is_happening", "")),
                "why_it_matters": str(item.get("why_it_matters", item.get("why", ""))),
                "how_to_improve": str(item.get("how_to_improve", "")),
                "priority_drills": list(item.get("priority_drills", [])),
                "why": str(item.get("why", item.get("why_it_matters", ""))),
                "metric": str(item.get("metric", "unknown")),
                "priority": str(item.get("priority", "medium")),
                "drill_ids": _valid_drill_ids(list(item.get("drill_ids", []))),
            }
        )

    quick_routine = raw.get("quick_routine", {})
    if not isinstance(quick_routine, dict):
        quick_routine = {}
    blocks = quick_routine.get("blocks", [])
    if not isinstance(blocks, list):
        blocks = []
    cleaned_blocks = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        cleaned_blocks.append(
            {
                "name": str(block.get("name", "Block")),
                "minutes": int(block.get("minutes", 10)),
                "drill_ids": _valid_drill_ids(list(block.get("drill_ids", []))),
                "instructions": str(block.get("instructions", "")),
                "goal": str(block.get("goal", "")),
                "success_criteria": str(block.get("success_criteria", "")),
            }
        )
    cleaned_quick = {
        "duration_min": int(quick_routine.get("duration_min", sum(block["minutes"] for block in cleaned_blocks) or 20)),
        "blocks": cleaned_blocks,
    }

    multiweek = raw.get("multiweek_plan", {})
    if not isinstance(multiweek, dict):
        multiweek = {}
    weeks = multiweek.get("weeks", [])
    if not isinstance(weeks, list):
        weeks = []
    cleaned_weeks = []
    for week in weeks:
        if not isinstance(week, dict):
            continue
        sessions = week.get("sessions", [])
        if not isinstance(sessions, list):
            sessions = []
        cleaned_sessions = []
        for session in sessions:
            if not isinstance(session, dict):
                continue
            cleaned_sessions.append(
                {
                    "day": str(session.get("day", "Day")),
                    "focus": str(session.get("focus", "")),
                    "drill_ids": _valid_drill_ids(list(session.get("drill_ids", []))),
                    "notes": str(session.get("notes", "")),
                    "session_plan": str(session.get("session_plan", "")),
                    "target_outcome": str(session.get("target_outcome", "")),
                }
            )
        cleaned_weeks.append(
            {
                "week": int(week.get("week", len(cleaned_weeks) + 1)),
                "theme": str(week.get("theme", "")),
                "sessions": cleaned_sessions,
            }
        )
    cleaned_multiweek = {"weeks": cleaned_weeks}

    return {
        "summary": summary,
        "recommendations": cleaned_recommendations,
        "quick_routine": cleaned_quick,
        "multiweek_plan": cleaned_multiweek,
    }


def _enrich_with_drill_details(report: dict[str, Any]) -> dict[str, Any]:
    for recommendation in report.get("recommendations", []):
        if not recommendation.get("drill_ids"):
            recommendation["drill_ids"] = [drill.id for drill in get_drills_for_metric(recommendation.get("metric", ""), 2)]
        details = []
        for drill_id in recommendation.get("drill_ids", []):
            drill = DRILL_BY_ID.get(drill_id)
            if not drill:
                continue
            details.append(
                {
                    "id": drill.id,
                    "name": drill.name,
                    "focus_cue": drill.focus_cue,
                    "reps": drill.reps,
                    "equipment": drill.equipment,
                }
            )
        recommendation["priority_drills"] = details

    return report


def _is_complete_report(report: dict[str, Any]) -> bool:
    recommendations = report.get("recommendations", [])
    if len(recommendations) < 3:
        return False
    for recommendation in recommendations:
        if _is_missing_text(recommendation.get("title")):
            return False
        if _is_missing_text(recommendation.get("what_is_happening")):
            return False
        if _is_missing_text(recommendation.get("why_it_matters")):
            return False
        if _is_missing_text(recommendation.get("how_to_improve")):
            return False
        if not recommendation.get("drill_ids"):
            return False
    weeks = report.get("multiweek_plan", {}).get("weeks", [])
    if len(weeks) < 4:
        return False
    for week in weeks[:4]:
        if _is_missing_text(week.get("theme")):
            return False
        sessions = week.get("sessions", [])
        if len(sessions) < 3:
            return False
        for session in sessions:
            if _is_missing_text(session.get("focus")):
                return False
            if _is_missing_text(session.get("session_plan")):
                return False
            if _is_missing_text(session.get("target_outcome")):
                return False
            if not session.get("drill_ids"):
                return False
    blocks = report.get("quick_routine", {}).get("blocks", [])
    if len(blocks) < 3:
        return False
    for block in blocks:
        if _is_missing_text(block.get("goal")):
            return False
        if _is_missing_text(block.get("instructions")):
            return False
        if _is_missing_text(block.get("success_criteria")):
            return False
    return True


def _upgrade_recommendation_fields(report: dict[str, Any], analysis_packet: dict[str, Any]) -> dict[str, Any]:
    fault_by_metric = {fault["metric"]: fault for fault in analysis_packet.get("all_comparisons", [])}
    for recommendation in report.get("recommendations", []):
        metric = recommendation.get("metric", "")
        fault = fault_by_metric.get(metric, {})
        if _is_missing_text(recommendation.get("what_is_happening")):
            recommendation["what_is_happening"] = (
                f"At {fault.get('phase', 'key phases')}, your {metric} differs from pro by "
                f"{fault.get('deviation', 0.0):.2f} ({fault.get('direction', 'different pattern')})."
            )
        if _is_missing_text(recommendation.get("why_it_matters")):
            recommendation["why_it_matters"] = (
                "This affects contact quality, sequencing, and repeatability across the swing."
            )
        if _is_missing_text(recommendation.get("how_to_improve")):
            recommendation["how_to_improve"] = (
                "Use the listed drills with slow rehearsal first, then transfer to full-speed swings."
            )
        if _is_missing_text(recommendation.get("title")):
            recommendation["title"] = recommendation.get("focus", "Priority Focus")
        if not recommendation.get("drill_ids"):
            recommendation["drill_ids"] = [drill.id for drill in get_drills_for_metric(metric, 2)]
        if _is_missing_text(recommendation.get("focus")):
            recommendation["focus"] = f"Improve {metric} in {fault.get('phase', 'key swing phases')}"

    covered_metrics = {item.get("metric") for item in report.get("recommendations", [])}
    high_faults = [fault for fault in analysis_packet.get("faults", []) if fault.get("severity") == "high"]
    for fault in high_faults:
        metric = fault["metric"]
        if metric in covered_metrics:
            continue
        report["recommendations"].append(
            {
                "title": f"{metric.replace('_', ' ').title()} Priority",
                "focus": f"Improve {metric} during {fault['phase']}",
                "what_is_happening": (
                    f"At {fault['phase']}, your {metric} differs from pro by {fault['deviation']:.2f} "
                    f"(normalized error {fault['normalized_error']:.2f}, {fault['direction']})."
                ),
                "why_it_matters": "This error is materially affecting consistency and strike quality.",
                "how_to_improve": "Prioritize drill work, then transfer to full swings with one clear cue.",
                "priority_drills": [],
                "why": "High-severity deviation from pro reference.",
                "metric": metric,
                "priority": "high",
                "drill_ids": [drill.id for drill in get_drills_for_metric(metric, 2)],
            }
        )
        covered_metrics.add(metric)

    quick = report.get("quick_routine", {})
    blocks = quick.get("blocks", [])
    for idx, block in enumerate(blocks):
        if _is_missing_text(block.get("goal")):
            block["goal"] = "Execute controlled reps that reduce the target fault."
        if _is_missing_text(block.get("instructions")):
            block["instructions"] = "Perform slow rehearsals first, then blend into full swings."
        if _is_missing_text(block.get("success_criteria")):
            block["success_criteria"] = "At least 7/10 reps with stable contact and balanced finish."
        if not block.get("drill_ids") and report.get("recommendations"):
            metric = report["recommendations"][idx % len(report["recommendations"])].get("metric", "")
            block["drill_ids"] = [drill.id for drill in get_drills_for_metric(metric, 2)]

    weeks = report.get("multiweek_plan", {}).get("weeks", [])
    for week_idx, week in enumerate(weeks, start=1):
        if _is_missing_text(week.get("theme")):
            week["theme"] = f"Week {week_idx} focus: build consistency in priority faults"
        sessions = week.get("sessions", [])
        for sess_idx, session in enumerate(sessions, start=1):
            metric = ""
            if report.get("recommendations"):
                metric = report["recommendations"][(sess_idx - 1) % len(report["recommendations"])].get("metric", "")
            if _is_missing_text(session.get("focus")):
                session["focus"] = f"Technical session for {metric or 'core swing stability'}"
            if _is_missing_text(session.get("session_plan")):
                session["session_plan"] = "10 min warmup, 20 min drills, 15 min transfer swings, 5 min review."
            if _is_missing_text(session.get("target_outcome")):
                session["target_outcome"] = "Reduce compensations and improve centered strike pattern."
            if not session.get("drill_ids"):
                session["drill_ids"] = [drill.id for drill in get_drills_for_metric(metric, 2)]
    return report


def _merge_with_fallback(report: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    merged = dict(report)
    if _is_missing_text(merged.get("summary")):
        merged["summary"] = fallback.get("summary", "")

    recs = merged.get("recommendations", [])
    fallback_recs = fallback.get("recommendations", [])
    rec_by_metric = {item.get("metric"): item for item in recs if isinstance(item, dict)}
    for fallback_rec in fallback_recs:
        metric = fallback_rec.get("metric")
        if metric in rec_by_metric:
            rec = rec_by_metric[metric]
            for key in ("title", "focus", "what_is_happening", "why_it_matters", "how_to_improve", "why", "priority"):
                if _is_missing_text(rec.get(key)):
                    rec[key] = fallback_rec.get(key, "")
            if not rec.get("drill_ids"):
                rec["drill_ids"] = fallback_rec.get("drill_ids", [])
            if not rec.get("priority_drills"):
                rec["priority_drills"] = fallback_rec.get("priority_drills", [])
        else:
            recs.append(fallback_rec)
    merged["recommendations"] = recs

    quick = merged.get("quick_routine", {})
    fallback_quick = fallback.get("quick_routine", {})
    blocks = quick.get("blocks", [])
    fallback_blocks = fallback_quick.get("blocks", [])
    if len(blocks) < len(fallback_blocks):
        blocks = blocks + fallback_blocks[len(blocks) :]
    for idx, block in enumerate(blocks):
        fallback_block = fallback_blocks[idx] if idx < len(fallback_blocks) else {}
        for key in ("name", "goal", "instructions", "success_criteria"):
            if _is_missing_text(block.get(key)):
                block[key] = fallback_block.get(key, "")
        if not block.get("drill_ids"):
            block["drill_ids"] = fallback_block.get("drill_ids", [])
        block["minutes"] = int(block.get("minutes", fallback_block.get("minutes", 10)))
    quick["blocks"] = blocks
    if int(quick.get("duration_min", 0)) <= 0:
        quick["duration_min"] = fallback_quick.get("duration_min", 30)
    merged["quick_routine"] = quick

    multi = merged.get("multiweek_plan", {})
    fallback_multi = fallback.get("multiweek_plan", {})
    weeks = multi.get("weeks", [])
    fallback_weeks = fallback_multi.get("weeks", [])
    if len(weeks) < len(fallback_weeks):
        weeks = weeks + fallback_weeks[len(weeks) :]
    for widx, week in enumerate(weeks):
        fallback_week = fallback_weeks[widx] if widx < len(fallback_weeks) else {}
        if _is_missing_text(week.get("theme")):
            week["theme"] = fallback_week.get("theme", f"Week {widx+1} development")
        sessions = week.get("sessions", [])
        fallback_sessions = fallback_week.get("sessions", [])
        if len(sessions) < len(fallback_sessions):
            sessions = sessions + fallback_sessions[len(sessions) :]
        for sidx, session in enumerate(sessions):
            fallback_session = fallback_sessions[sidx] if sidx < len(fallback_sessions) else {}
            for key in ("day", "focus", "session_plan", "target_outcome", "notes"):
                if _is_missing_text(session.get(key)):
                    session[key] = fallback_session.get(key, "")
            if not session.get("drill_ids"):
                session["drill_ids"] = fallback_session.get("drill_ids", [])
        week["sessions"] = sessions
    multi["weeks"] = weeks
    merged["multiweek_plan"] = multi
    return merged


def generate_coaching_report(
    comparisons: list[MetricComparison],
    overall_score: float,
    view_name: str,
    pro_name: str | None = None,
) -> CoachingReport:
    packet = build_analysis_packet(comparisons=comparisons, overall_score=overall_score, view_name=view_name)
    pro_context = build_pro_context(pro_name=pro_name)

    source = "rule_based"
    fallback_report = build_rule_based_report(packet)
    fallback_validated = _enrich_with_drill_details(
        _upgrade_recommendation_fields(_validate_report(fallback_report), packet)
    )
    if is_openai_configured():
        try:
            raw_report = generate_llm_report(
                analysis_packet=packet,
                pro_context=pro_context,
                available_drills=serialize_drills(),
            )
            validated = _validate_report(raw_report)
            validated = _upgrade_recommendation_fields(validated, packet)
            validated = _enrich_with_drill_details(validated)
            validated = _merge_with_fallback(validated, fallback_validated)
            if _is_complete_report(validated):
                source = "llm"
            else:
                raw_report = fallback_report
                source = "rule_based"
                validated = fallback_validated
        except Exception:
            raw_report = fallback_report
            source = "rule_based"
            validated = fallback_validated
    else:
        raw_report = fallback_report
        validated = fallback_validated

    return CoachingReport(
        summary=validated["summary"],
        recommendations=validated["recommendations"],
        quick_routine=validated["quick_routine"],
        multiweek_plan=validated["multiweek_plan"],
        source=source,
    )


def format_report_markdown(report: CoachingReport) -> str:
    lines = [
        "# AI Coaching Report",
        "",
        f"Source: {report.source}",
        "",
        "## Summary",
        report.summary,
        "",
        "## Recommendations",
    ]
    for recommendation in report.recommendations:
        lines.append(
            "- "
            f"{recommendation['title']} ({recommendation['priority']}): {recommendation['what_is_happening']} "
            f"Why: {recommendation['why_it_matters']} "
            f"How: {recommendation['how_to_improve']} "
            f"[drills: {', '.join(recommendation['drill_ids']) or 'none'}]"
        )

    lines.extend(["", "## Quick Routine"])
    lines.append(f"Total duration: {report.quick_routine.get('duration_min', 0)} minutes")
    for block in report.quick_routine.get("blocks", []):
        lines.append(
            "- "
            f"{block['name']} ({block['minutes']} min): {block['instructions']} "
            f"[drills: {', '.join(block['drill_ids']) or 'none'}]"
        )

    lines.extend(["", "## Multi-Week Plan"])
    for week in report.multiweek_plan.get("weeks", []):
        lines.append(f"### Week {week['week']}: {week['theme']}")
        for session in week.get("sessions", []):
            lines.append(
                "- "
                f"{session['day']}: {session['focus']} "
                f"[drills: {', '.join(session['drill_ids']) or 'none'}] "
                f"- {session['notes']}"
            )
    lines.append("")
    return "\n".join(lines)
