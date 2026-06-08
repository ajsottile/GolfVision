from __future__ import annotations


BASE_BIOMECHANICS_CONTEXT = """\
Reference principles for high-level golf swings:
- Maintain posture and balance through the full motion.
- Build pressure and sequence from ground up in transition.
- Keep head movement controlled through impact.
- Match shoulder and hip turn to produce efficient separation.
- Preserve lead-arm structure and swing radius at the top.
- Prioritize strike quality and repeatability over max speed.
"""


def build_pro_context(pro_name: str | None = None) -> str:
    if pro_name and pro_name.strip():
        pro_reference = (
            f"Professional reference context: compare against {pro_name.strip()} as the target motion "
            "for sequencing, turn, and impact stability."
        )
    else:
        pro_reference = (
            "Professional reference context: compare against the selected pro clip as the target motion "
            "for sequencing, turn, and impact stability."
        )
    return f"{pro_reference}\n\n{BASE_BIOMECHANICS_CONTEXT}"
