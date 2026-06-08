from __future__ import annotations

from dataclasses import dataclass

from golfvision.metrics import MetricComparison


@dataclass
class CoachingTip:
    metric: str
    phase: str
    severity: str
    message: str
    deviation: float
    pro_value: float
    user_value: float


def _severity(normalized_error: float) -> str:
    if normalized_error >= 0.75:
        return "high"
    if normalized_error >= 0.45:
        return "medium"
    return "low"


def _message_for(metric: str, deviation: float) -> str:
    if metric == "lead_arm_extension":
        if deviation < -10:
            return "Lead arm is bending too much at the top. Keep it wider for a bigger arc."
        return "Lead arm is very rigid. Keep structure, but stay relaxed through transition."
    if metric == "tempo_ratio":
        if deviation < -0.2:
            return "Downswing is rushing. Try a smoother 3-to-1 backswing-to-downswing tempo."
        return "Tempo is a little slow in transition. Add intent from the top to impact."
    if metric == "head_stability":
        if deviation > 0:
            return "Head movement is higher than the reference. Keep your head quieter through impact."
        return "Head is stable. Keep this centered pattern through the strike."
    if metric == "x_factor":
        if deviation < -5:
            return "Create a little more shoulder-hip separation at the top for potential power."
        return "Separation is high. Maintain sequence so hips unwind before shoulders."
    if metric == "spine_tilt":
        if deviation > 5:
            return "Posture is standing up through the swing. Maintain spine tilt longer."
        return "Spine tilt is lower than reference. Avoid over-bending and stay athletic."
    if metric == "shoulder_turn":
        if deviation < -8:
            return "Complete shoulder turn more fully at the top."
        return "Shoulder turn is larger than reference. Keep balance and timing centered."
    if metric == "hip_turn":
        if deviation < -8:
            return "Allow slightly more hip turn to support rotation."
        return "Hip turn is high. Ensure lower-body stability at address."
    if metric == "lead_knee_flex":
        if deviation < -8:
            return "Lead knee is getting too straight. Keep athletic flex through impact."
        return "Lead knee is very flexed. Stay dynamic, but avoid sitting too much."
    return "Small deviation detected. Keep rehearsing with phase-matched feedback."


def generate_coaching_tips(
    comparisons: list[MetricComparison],
    max_tips: int = 6,
) -> list[CoachingTip]:
    ranked = sorted(comparisons, key=lambda item: item.normalized_error, reverse=True)
    tips: list[CoachingTip] = []

    for comparison in ranked:
        if comparison.normalized_error < 0.2:
            continue
        tips.append(
            CoachingTip(
                metric=comparison.metric,
                phase=comparison.phase,
                severity=_severity(comparison.normalized_error),
                message=_message_for(comparison.metric, comparison.deviation),
                deviation=comparison.deviation,
                pro_value=comparison.pro_value,
                user_value=comparison.user_value,
            )
        )
        if len(tips) >= max_tips:
            break

    return tips
