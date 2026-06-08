from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from golfvision.pose import PoseSequence

LEFT_WRIST = 9
RIGHT_WRIST = 10


@dataclass
class SwingPhases:
    address: int
    takeaway: int
    top: int
    downswing: int
    impact: int
    follow_through: int
    finish: int

    def as_dict(self) -> dict[str, int]:
        return {
            "address": self.address,
            "takeaway": self.takeaway,
            "top": self.top,
            "downswing": self.downswing,
            "impact": self.impact,
            "follow_through": self.follow_through,
            "finish": self.finish,
        }


def _moving_average(signal: np.ndarray, window: int = 7) -> np.ndarray:
    if signal.size == 0:
        return signal
    window = max(1, min(window, signal.size))
    if window == 1:
        return signal.astype(np.float32)
    kernel = np.ones(window, dtype=np.float32) / float(window)
    left = window // 2
    right = window - 1 - left
    padded = np.pad(signal, (left, right), mode="edge")
    return np.convolve(padded, kernel, mode="valid")


def _fill_nan_forward(values: np.ndarray) -> np.ndarray:
    out = values.astype(np.float32).copy()
    if np.all(np.isnan(out)):
        return np.zeros_like(out)
    valid = np.where(np.isfinite(out))[0]
    first = int(valid[0])
    out[:first] = out[first]
    for idx in range(first + 1, out.size):
        if not np.isfinite(out[idx]):
            out[idx] = out[idx - 1]
    return out


def detect_swing_phases(sequence: PoseSequence) -> SwingPhases:
    xy = sequence.keypoints_xy
    if xy.ndim != 3 or xy.shape[0] < 12:
        raise ValueError("Not enough frames to detect swing phases.")

    hand_y = np.nanmean(xy[:, [LEFT_WRIST, RIGHT_WRIST], 1], axis=1)
    hand_y = _moving_average(_fill_nan_forward(hand_y), window=9)

    frame_count = hand_y.shape[0]
    address_window = max(3, int(frame_count * 0.05))
    address = int(np.argmin(np.abs(hand_y[: max(address_window, 1)] - np.median(hand_y[: max(address_window, 1)]))))

    search_end = max(int(frame_count * 0.85), address + 2)
    top = int(np.argmin(hand_y[address:search_end]) + address)
    downswing = min(top + 1, frame_count - 2)

    velocity = np.gradient(hand_y)
    impact_range_start = min(top + 1, frame_count - 2)
    impact_range_end = max(int(frame_count * 0.95), impact_range_start + 1)
    impact = int(np.argmax(velocity[impact_range_start:impact_range_end]) + impact_range_start)

    baseline = float(np.median(hand_y[: max(5, int(frame_count * 0.08))]))
    takeaway_candidates = np.where(np.abs(hand_y[:top] - baseline) > 4.0)[0]
    takeaway = int(takeaway_candidates[0]) if takeaway_candidates.size else max(address + 1, int(top * 0.3))

    follow_start = min(impact + 1, frame_count - 1)
    follow_end = frame_count
    if follow_start >= follow_end:
        follow_through = frame_count - 1
    else:
        follow_through = int(np.argmin(hand_y[follow_start:follow_end]) + follow_start)

    finish = frame_count - 1

    ordered = sorted([address, takeaway, top, downswing, impact, follow_through, finish])
    return SwingPhases(
        address=ordered[0],
        takeaway=ordered[1],
        top=ordered[2],
        downswing=ordered[3],
        impact=ordered[4],
        follow_through=ordered[5],
        finish=ordered[6],
    )
