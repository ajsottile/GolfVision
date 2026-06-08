from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ViewProfile:
    name: str
    key_metrics: tuple[str, ...]
    notes: str


DTL_PROFILE = ViewProfile(
    name="dtl",
    key_metrics=(
        "shoulder_turn",
        "hip_turn",
        "x_factor",
        "spine_tilt",
        "lead_arm_extension",
        "head_stability",
        "tempo_ratio",
    ),
    notes="Down-the-line profile tuned for rotational and posture metrics.",
)

FACE_ON_PROFILE = ViewProfile(
    name="face_on",
    key_metrics=(
        "spine_tilt",
        "lead_knee_flex",
        "head_stability",
        "tempo_ratio",
    ),
    notes="Face-on profile is a stub and can be expanded with frontal-plane metrics.",
)


def resolve_view_profile(view_name: str) -> ViewProfile:
    normalized = view_name.strip().lower()
    if normalized in {"dtl", "down_the_line", "down-the-line"}:
        return DTL_PROFILE
    if normalized in {"face_on", "face-on", "fo"}:
        return FACE_ON_PROFILE
    raise ValueError(f"Unsupported view '{view_name}'. Use 'dtl' or 'face_on'.")
