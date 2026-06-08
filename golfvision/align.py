from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from golfvision.phases import SwingPhases
from golfvision.pose import PoseSequence

SELECTED_KEYPOINTS = (0, 5, 6, 9, 10, 11, 12, 13, 14, 15, 16)


@dataclass
class AlignmentResult:
    frame_pairs: list[tuple[int, int]]
    phase_pairs: dict[str, tuple[int, int]]


def _normalize_keypoints(frame_xy: np.ndarray) -> np.ndarray:
    points = frame_xy[list(SELECTED_KEYPOINTS)].astype(np.float32)
    l_hip = frame_xy[11]
    r_hip = frame_xy[12]
    l_shoulder = frame_xy[5]
    r_shoulder = frame_xy[6]
    center = np.nanmean(np.stack([l_hip, r_hip], axis=0), axis=0)
    scale = np.linalg.norm(r_shoulder - l_shoulder)
    if not np.isfinite(scale) or scale < 1.0:
        scale = 1.0
    normalized = (points - center) / scale
    normalized = np.nan_to_num(normalized, nan=0.0, posinf=0.0, neginf=0.0)
    return normalized.reshape(-1)


def _dtw_path(a: np.ndarray, b: np.ndarray) -> list[tuple[int, int]]:
    n, m = a.shape[0], b.shape[0]
    cost = np.full((n + 1, m + 1), np.inf, dtype=np.float32)
    cost[0, 0] = 0.0

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            dist = np.linalg.norm(a[i - 1] - b[j - 1])
            cost[i, j] = dist + min(cost[i - 1, j], cost[i, j - 1], cost[i - 1, j - 1])

    i, j = n, m
    path: list[tuple[int, int]] = []
    while i > 0 and j > 0:
        path.append((i - 1, j - 1))
        step = np.argmin([cost[i - 1, j], cost[i, j - 1], cost[i - 1, j - 1]])
        if step == 0:
            i -= 1
        elif step == 1:
            j -= 1
        else:
            i -= 1
            j -= 1
    path.reverse()
    return path


def _segment_bounds(phases: SwingPhases, frame_count: int) -> list[tuple[int, int]]:
    marks = phases.as_dict()
    order = ["address", "top", "impact", "follow_through", "finish"]
    indices = [int(np.clip(marks[name], 0, frame_count - 1)) for name in order]
    bounds: list[tuple[int, int]] = []
    for start, end in zip(indices[:-1], indices[1:]):
        if end <= start:
            end = min(start + 1, frame_count - 1)
        bounds.append((start, end))
    return bounds


def align_swings(
    pro_sequence: PoseSequence,
    user_sequence: PoseSequence,
    pro_phases: SwingPhases,
    user_phases: SwingPhases,
) -> AlignmentResult:
    pro_features = np.asarray([_normalize_keypoints(frame) for frame in pro_sequence.keypoints_xy], dtype=np.float32)
    user_features = np.asarray([_normalize_keypoints(frame) for frame in user_sequence.keypoints_xy], dtype=np.float32)

    pro_segments = _segment_bounds(pro_phases, pro_sequence.frame_count)
    user_segments = _segment_bounds(user_phases, user_sequence.frame_count)

    frame_pairs: list[tuple[int, int]] = []
    for (pro_start, pro_end), (user_start, user_end) in zip(pro_segments, user_segments):
        pro_slice = pro_features[pro_start : pro_end + 1]
        user_slice = user_features[user_start : user_end + 1]
        path = _dtw_path(pro_slice, user_slice)
        for pro_idx, user_idx in path:
            frame_pairs.append((pro_start + pro_idx, user_start + user_idx))

    phase_pairs = {
        "address": (pro_phases.address, user_phases.address),
        "takeaway": (pro_phases.takeaway, user_phases.takeaway),
        "top": (pro_phases.top, user_phases.top),
        "impact": (pro_phases.impact, user_phases.impact),
        "follow_through": (pro_phases.follow_through, user_phases.follow_through),
    }

    deduped = sorted(set(frame_pairs), key=lambda pair: (pair[0], pair[1]))
    return AlignmentResult(frame_pairs=deduped, phase_pairs=phase_pairs)
