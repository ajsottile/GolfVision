from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from golfvision.phases import SwingPhases
from golfvision.pose import PoseSequence
from golfvision.view import ViewProfile

NOSE = 0
LEFT_SHOULDER = 5
RIGHT_SHOULDER = 6
LEFT_ELBOW = 7
LEFT_WRIST = 9
LEFT_HIP = 11
RIGHT_HIP = 12
LEFT_KNEE = 13
LEFT_ANKLE = 15


@dataclass
class SwingMetrics:
    phase_metrics: dict[str, dict[str, float]]
    tempo_ratio: float
    head_stability: float
    overall_score: float | None = None


@dataclass
class MetricComparison:
    metric: str
    phase: str
    pro_value: float
    user_value: float
    deviation: float
    normalized_error: float


def _angle_degrees(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    ba = a - b
    bc = c - b
    denom = np.linalg.norm(ba) * np.linalg.norm(bc)
    if denom <= 1e-6:
        return float("nan")
    value = np.clip(np.dot(ba, bc) / denom, -1.0, 1.0)
    return float(np.degrees(np.arccos(value)))


def _line_angle(p1: np.ndarray, p2: np.ndarray) -> float:
    delta = p2 - p1
    return float(np.degrees(np.arctan2(delta[1], delta[0])))


def _safe_mean(points: np.ndarray) -> np.ndarray:
    return np.nanmean(points, axis=0)


def _frame_metrics(keypoints: np.ndarray) -> dict[str, float]:
    l_shoulder = keypoints[LEFT_SHOULDER]
    r_shoulder = keypoints[RIGHT_SHOULDER]
    l_hip = keypoints[LEFT_HIP]
    r_hip = keypoints[RIGHT_HIP]
    l_elbow = keypoints[LEFT_ELBOW]
    l_wrist = keypoints[LEFT_WRIST]
    nose = keypoints[NOSE]
    l_knee = keypoints[LEFT_KNEE]
    l_ankle = keypoints[LEFT_ANKLE]

    shoulder_turn = _line_angle(l_shoulder, r_shoulder)
    hip_turn = _line_angle(l_hip, r_hip)
    x_factor = shoulder_turn - hip_turn

    mid_shoulder = _safe_mean(np.stack([l_shoulder, r_shoulder], axis=0))
    mid_hip = _safe_mean(np.stack([l_hip, r_hip], axis=0))
    spine_vector = mid_shoulder - mid_hip
    spine_tilt = float(np.degrees(np.arctan2(spine_vector[0], -spine_vector[1])))

    lead_arm_extension = _angle_degrees(l_shoulder, l_elbow, l_wrist)
    lead_knee_flex = _angle_degrees(l_hip, l_knee, l_ankle)

    return {
        "shoulder_turn": shoulder_turn,
        "hip_turn": hip_turn,
        "x_factor": x_factor,
        "spine_tilt": spine_tilt,
        "lead_arm_extension": lead_arm_extension,
        "lead_knee_flex": lead_knee_flex,
        "nose_x": float(nose[0]),
        "nose_y": float(nose[1]),
        "shoulder_width": float(np.linalg.norm(r_shoulder - l_shoulder)),
    }


def _phase_snapshot(frame_metrics: list[dict[str, float]], frame_idx: int) -> dict[str, float]:
    if not frame_metrics:
        return {}
    frame_idx = int(np.clip(frame_idx, 0, len(frame_metrics) - 1))
    return frame_metrics[frame_idx]


def compute_swing_metrics(
    sequence: PoseSequence,
    phases: SwingPhases,
    view_profile: ViewProfile,
) -> SwingMetrics:
    all_frame_metrics = [_frame_metrics(frame) for frame in sequence.keypoints_xy]

    phase_frames = phases.as_dict()
    phase_metrics: dict[str, dict[str, float]] = {}
    for phase_name, frame_idx in phase_frames.items():
        snapshot = _phase_snapshot(all_frame_metrics, frame_idx)
        phase_metrics[phase_name] = {
            metric_name: float(snapshot.get(metric_name, np.nan))
            for metric_name in view_profile.key_metrics
            if metric_name != "tempo_ratio"
        }

    backswing_frames = max(phases.top - phases.address, 1)
    downswing_frames = max(phases.impact - phases.top, 1)
    tempo_ratio = float(backswing_frames / downswing_frames)

    nose_x = np.array([m["nose_x"] for m in all_frame_metrics], dtype=np.float32)
    nose_y = np.array([m["nose_y"] for m in all_frame_metrics], dtype=np.float32)
    shoulder_width = np.array([m["shoulder_width"] for m in all_frame_metrics], dtype=np.float32)
    shoulder_width = np.where(shoulder_width < 1.0, np.nanmedian(shoulder_width), shoulder_width)
    baseline_x = nose_x[phases.address]
    baseline_y = nose_y[phases.address]
    drift = np.sqrt((nose_x - baseline_x) ** 2 + (nose_y - baseline_y) ** 2)
    head_stability = float(np.nanmax(drift / np.maximum(shoulder_width, 1.0)))

    phase_metrics["tempo"] = {"tempo_ratio": tempo_ratio}
    phase_metrics["stability"] = {"head_stability": head_stability}

    return SwingMetrics(
        phase_metrics=phase_metrics,
        tempo_ratio=tempo_ratio,
        head_stability=head_stability,
    )


def _metric_scale(metric_name: str) -> float:
    if metric_name == "tempo_ratio":
        return 0.7
    if metric_name == "head_stability":
        return 0.2
    return 15.0


def compare_swing_metrics(
    pro_metrics: SwingMetrics,
    user_metrics: SwingMetrics,
    view_profile: ViewProfile,
) -> tuple[list[MetricComparison], float]:
    comparisons: list[MetricComparison] = []

    for phase_name, pro_phase_values in pro_metrics.phase_metrics.items():
        user_phase_values = user_metrics.phase_metrics.get(phase_name, {})
        for metric_name, pro_value in pro_phase_values.items():
            if metric_name not in view_profile.key_metrics:
                continue
            user_value = float(user_phase_values.get(metric_name, np.nan))
            if np.isnan(pro_value) or np.isnan(user_value):
                continue
            deviation = user_value - pro_value
            scale = _metric_scale(metric_name)
            normalized_error = min(abs(deviation) / max(scale, 1e-6), 1.0)
            comparisons.append(
                MetricComparison(
                    metric=metric_name,
                    phase=phase_name,
                    pro_value=float(pro_value),
                    user_value=float(user_value),
                    deviation=float(deviation),
                    normalized_error=float(normalized_error),
                )
            )

    tempo_deviation = user_metrics.tempo_ratio - pro_metrics.tempo_ratio
    comparisons.append(
        MetricComparison(
            metric="tempo_ratio",
            phase="tempo",
            pro_value=pro_metrics.tempo_ratio,
            user_value=user_metrics.tempo_ratio,
            deviation=tempo_deviation,
            normalized_error=min(abs(tempo_deviation) / _metric_scale("tempo_ratio"), 1.0),
        )
    )

    stability_deviation = user_metrics.head_stability - pro_metrics.head_stability
    comparisons.append(
        MetricComparison(
            metric="head_stability",
            phase="stability",
            pro_value=pro_metrics.head_stability,
            user_value=user_metrics.head_stability,
            deviation=stability_deviation,
            normalized_error=min(abs(stability_deviation) / _metric_scale("head_stability"), 1.0),
        )
    )

    mean_error = float(np.mean([c.normalized_error for c in comparisons])) if comparisons else 1.0
    overall_score = float(np.clip(100.0 * (1.0 - mean_error), 0.0, 100.0))
    return comparisons, overall_score
