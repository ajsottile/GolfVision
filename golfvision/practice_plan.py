from __future__ import annotations

from typing import Any

from golfvision.drills import get_drills_for_metric


def _priority_rank(priority: str) -> int:
    if priority == "high":
        return 0
    if priority == "medium":
        return 1
    return 2


def _top_faults(analysis_packet: dict[str, Any], limit: int = 3) -> list[dict[str, Any]]:
    faults = list(analysis_packet.get("faults", []))
    faults.sort(key=lambda fault: (_priority_rank(fault.get("severity", "low")), -fault.get("normalized_error", 0.0)))
    return faults[: max(limit, 0)]


def build_rule_based_report(analysis_packet: dict[str, Any]) -> dict[str, Any]:
    faults = _top_faults(analysis_packet, limit=3)
    if not faults:
        return {
            "summary": "Metrics are close to the pro baseline. Keep a consistency-focused routine.",
            "recommendations": [],
            "quick_routine": {
                "duration_min": 20,
                "blocks": [
                    {
                        "name": "Fundamentals warmup",
                        "minutes": 8,
                        "drill_ids": [],
                        "instructions": "Hit easy swings while maintaining posture and tempo.",
                    },
                    {
                        "name": "Rhythm and strike quality",
                        "minutes": 12,
                        "drill_ids": [],
                        "instructions": "Alternate smooth tempo reps with full swings.",
                    },
                ],
            },
            "multiweek_plan": {"weeks": []},
        }

    recommendations: list[dict[str, Any]] = []
    for fault in faults:
        metric = fault["metric"]
        drills = get_drills_for_metric(metric, limit=2)
        drill_ids = [drill.id for drill in drills]
        primary_drill = drills[0] if drills else None
        recommendations.append(
            {
                "title": f"{metric.replace('_', ' ').title()} Priority",
                "focus": f"Improve {metric} during {fault['phase']}",
                "what_is_happening": (
                    f"At {fault['phase']}, your {metric} differs from pro by {fault['deviation']:.2f} "
                    f"with normalized error {fault['normalized_error']:.2f}."
                ),
                "why_it_matters": (
                    "This influences contact consistency and the sequencing needed for repeatable speed."
                ),
                "how_to_improve": (
                    f"Prioritize controlled reps with {primary_drill.name if primary_drill else 'structured drills'} "
                    "before transferring to full swings."
                ),
                "why": (
                    f"Deviation is {fault['deviation']:.2f} vs pro baseline "
                    f"(error {fault['normalized_error']:.2f})."
                ),
                "priority_drills": [
                    {
                        "id": drill.id,
                        "name": drill.name,
                        "focus_cue": drill.focus_cue,
                        "reps": drill.reps,
                        "equipment": drill.equipment,
                    }
                    for drill in drills
                ],
                "metric": metric,
                "priority": fault.get("severity", "medium"),
                "drill_ids": drill_ids,
            }
        )

    quick_blocks: list[dict[str, Any]] = [
        {
            "name": "Dynamic warmup",
            "minutes": 6,
            "drill_ids": [],
            "goal": "Prepare movement quality and sequencing before technical work.",
            "instructions": "Prepare mobility and balance with controlled rehearsal swings.",
            "success_criteria": "Body feels loose and first 5 rehearsal swings are balanced.",
        }
    ]
    for recommendation in recommendations[:2]:
        quick_blocks.append(
            {
                "name": f"Primary focus: {recommendation['metric']}",
                "minutes": 10,
                "drill_ids": recommendation["drill_ids"],
                "goal": f"Reduce deviation in {recommendation['metric']}",
                "instructions": recommendation["how_to_improve"],
                "success_criteria": "70% of reps with stable tempo and centered strike feel.",
            }
        )
    quick_blocks.append(
        {
            "name": "Transfer to full swing",
            "minutes": 8,
            "drill_ids": [],
            "goal": "Convert drill feel into full-speed swings",
            "instructions": "Hit full shots with one clear cue from the highest-priority focus.",
            "success_criteria": "Ball flight and contact remain stable for at least 6 of 10 swings.",
        }
    )

    weeks = []
    days = ["Day 1", "Day 2", "Day 3"]
    for week in range(1, 5):
        sessions = []
        for day_idx, day_name in enumerate(days):
            recommendation = recommendations[day_idx % len(recommendations)]
            sessions.append(
                {
                    "day": day_name,
                    "focus": recommendation["focus"],
                    "drill_ids": recommendation["drill_ids"],
                    "session_plan": (
                        "10 min warmup, 20 min technical drills, 15 min transfer swings, "
                        "5 min reflection and notes."
                    ),
                    "target_outcome": (
                        f"Improve {recommendation['metric']} consistency and reduce compensation patterns."
                    ),
                    "notes": (
                        f"Week {week}: track strike quality and keep tempo smooth while training "
                        f"{recommendation['metric']}."
                    ),
                }
            )
        weeks.append({"week": week, "theme": f"Build consistency in top faults (week {week})", "sessions": sessions})

    summary_metrics = ", ".join([fault["metric"] for fault in faults])
    summary = (
        "Your largest gaps vs the pro baseline are "
        f"{summary_metrics}. Prioritize one technical focus per session and reinforce it with transfer swings."
    )

    return {
        "summary": summary,
        "recommendations": recommendations,
        "quick_routine": {"duration_min": sum(block["minutes"] for block in quick_blocks), "blocks": quick_blocks},
        "multiweek_plan": {"weeks": weeks},
    }
