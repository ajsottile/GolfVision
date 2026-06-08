from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI


DEFAULT_MODEL = "gpt-4o-mini"


def is_openai_configured() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def generate_llm_report(
    analysis_packet: dict[str, Any],
    pro_context: str,
    available_drills: list[dict[str, str]],
) -> dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    model = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
    client = OpenAI(api_key=api_key)

    system_prompt = (
        "You are an elite golf coach assistant producing a highly structured development plan.\n"
        "Critical rules:\n"
        "1) Use ONLY metric values provided in analysis_packet.\n"
        "2) Use ONLY drill IDs from available_drills.\n"
        "3) Be specific, technical, and actionable.\n"
        "4) If data is uncertain, say so briefly; do not fabricate.\n"
        "5) Output strict JSON only.\n\n"
        "Return this JSON shape exactly:\n"
        "{\n"
        '  "summary": "4-8 sentence assessment with clear strengths/weaknesses",\n'
        '  "recommendations": [\n'
        "    {\n"
        '      "title": "short focus title",\n'
        '      "focus": "what to fix in plain language",\n'
        '      "metric": "metric_name",\n'
        '      "priority": "high|medium|low",\n'
        '      "what_is_happening": "what user is doing vs pro with numbers and phase",\n'
        '      "why_it_matters": "impact on strike, consistency, or power",\n'
        '      "how_to_improve": "step-by-step correction cues",\n'
        '      "drill_ids": ["drill_id_1", "drill_id_2"]\n'
        "    }\n"
        "  ],\n"
        '  "quick_routine": {\n'
        '    "duration_min": 30,\n'
        '    "blocks": [\n'
        "      {\n"
        '        "name": "block name",\n'
        '        "minutes": 10,\n'
        '        "goal": "clear objective",\n'
        '        "instructions": "exact execution details",\n'
        '        "success_criteria": "how to know this block worked",\n'
        '        "drill_ids": ["drill_id_1"]\n'
        "      }\n"
        "    ]\n"
        "  },\n"
        '  "multiweek_plan": {\n'
        '    "weeks": [\n'
        "      {\n"
        '        "week": 1,\n'
        '        "theme": "weekly focus",\n'
        '        "sessions": [\n'
        "          {\n"
        '            "day": "Day 1",\n'
        '            "focus": "session objective",\n'
        '            "session_plan": "ordered plan and volume",\n'
        '            "target_outcome": "measurable checkpoint",\n'
        '            "drill_ids": ["drill_id_1", "drill_id_2"],\n'
        '            "notes": "constraints, pitfalls, progression"\n'
        "          }\n"
        "        ]\n"
        "      }\n"
        "    ]\n"
        "  }\n"
        "}\n\n"
        "Minimum completeness constraints:\n"
        "- recommendations: 4 to 6 entries\n"
        "- quick_routine blocks: 3 to 5 entries\n"
        "- multiweek_plan: exactly 4 weeks and exactly 3 sessions per week\n"
        "- each recommendation must cite at least one numeric value from analysis_packet.\n"
        '- do not output placeholders such as "N/A", "TBD", "not provided", or blank strings.\n\n'
        f"{pro_context}"
    )

    user_payload = {
        "analysis_packet": analysis_packet,
        "available_drills": available_drills,
    }

    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload)},
        ],
        temperature=0.4,
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("OpenAI returned an empty response.")
    return json.loads(content)
