from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import supervision as sv
from ultralytics import YOLO


@dataclass
class PoseSequence:
    video_path: str
    fps: float
    frame_size: tuple[int, int]
    keypoints_xy: np.ndarray
    keypoints_conf: np.ndarray
    selected_keypoints: list[sv.KeyPoints | None]

    @property
    def frame_count(self) -> int:
        return int(self.keypoints_xy.shape[0])


def _valid_mask(xy: np.ndarray, conf: np.ndarray) -> np.ndarray:
    if conf.size == 0:
        return np.isfinite(xy[..., 0]) & np.isfinite(xy[..., 1])
    return conf > 0.05


def _select_primary_person(
    keypoints: sv.KeyPoints,
    frame_width: int,
    frame_height: int,
    previous_center: np.ndarray | None = None,
) -> int | None:
    if len(keypoints) == 0:
        return None
    if len(keypoints) == 1:
        return 0

    xy = keypoints.xy
    conf = getattr(keypoints, "confidence", np.ones(xy.shape[:2], dtype=np.float32))
    valid = _valid_mask(xy, conf)

    best_index: int | None = None
    best_score = -np.inf
    center = np.array([frame_width / 2.0, frame_height / 2.0], dtype=np.float32)
    frame_area = float(frame_width * frame_height)

    for idx in range(xy.shape[0]):
        pts = xy[idx][valid[idx]]
        if pts.size == 0:
            continue
        min_xy = np.min(pts, axis=0)
        max_xy = np.max(pts, axis=0)
        area = float(np.prod(np.maximum(max_xy - min_xy, 1.0)))
        person_center = np.mean(pts, axis=0)
        center_dist = float(np.linalg.norm(person_center - center))
        mean_conf = float(np.mean(conf[idx][valid[idx]])) if np.any(valid[idx]) else 0.0
        visible_count = int(np.sum(valid[idx]))

        # Reject tiny false-positive skeletons that often appear on the ground.
        if area < frame_area * 0.005:
            continue
        if visible_count < 8:
            continue

        if previous_center is not None:
            tracking_dist = float(np.linalg.norm(person_center - previous_center))
            score = area + (mean_conf * 1000.0) - (1.2 * tracking_dist)
        else:
            score = area + (mean_conf * 1000.0) - (0.5 * center_dist)
        if score > best_score:
            best_score = score
            best_index = idx
    return best_index


def _result_to_keypoints(result: Any) -> sv.KeyPoints:
    return sv.KeyPoints.from_ultralytics(result)


def extract_pose_sequence(
    video_path: str,
    model_name: str = "yolo11n-pose.pt",
    confidence_threshold: float = 0.25,
    iou_threshold: float = 0.7,
    device: str | None = None,
) -> PoseSequence:
    source_path = Path(video_path)
    if not source_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    video_info = sv.VideoInfo.from_video_path(video_path=video_path)
    model = YOLO(model_name)

    keypoints_xy: list[np.ndarray] = []
    keypoints_conf: list[np.ndarray] = []
    selected_keypoints: list[sv.KeyPoints | None] = []
    previous_center: np.ndarray | None = None
    previous_xy: np.ndarray | None = None
    previous_conf: np.ndarray | None = None

    for frame in sv.get_video_frames_generator(source_path=video_path):
        prediction = model.predict(
            source=frame,
            conf=confidence_threshold,
            iou=iou_threshold,
            device=device,
            verbose=False,
        )
        result = prediction[0]
        frame_keypoints = _result_to_keypoints(result)
        selected_index = _select_primary_person(
            frame_keypoints,
            frame_width=video_info.width,
            frame_height=video_info.height,
            previous_center=previous_center,
        )

        if selected_index is None:
            if previous_xy is not None and previous_conf is not None:
                # Keep temporal continuity when a frame momentarily misses detection.
                keypoints_xy.append(previous_xy.copy())
                decayed_conf = np.clip(previous_conf * 0.9, 0.0, 1.0)
                keypoints_conf.append(decayed_conf)
                selected_keypoints.append(None)
            else:
                keypoints_xy.append(np.full((17, 2), np.nan, dtype=np.float32))
                keypoints_conf.append(np.zeros((17,), dtype=np.float32))
                selected_keypoints.append(None)
            continue

        chosen = frame_keypoints[selected_index : selected_index + 1]
        selected_keypoints.append(chosen)
        chosen_xy = chosen.xy[0].astype(np.float32)
        chosen_conf = getattr(chosen, "confidence", np.ones((1, chosen.xy.shape[1]), dtype=np.float32))
        chosen_conf_arr = chosen_conf[0].astype(np.float32)
        keypoints_xy.append(chosen_xy)
        keypoints_conf.append(chosen_conf_arr)

        valid = _valid_mask(chosen_xy[np.newaxis, ...], chosen_conf_arr[np.newaxis, ...])[0]
        if np.any(valid):
            previous_center = np.mean(chosen_xy[valid], axis=0)
        previous_xy = chosen_xy
        previous_conf = chosen_conf_arr

    return PoseSequence(
        video_path=video_path,
        fps=float(video_info.fps),
        frame_size=(int(video_info.width), int(video_info.height)),
        keypoints_xy=np.asarray(keypoints_xy, dtype=np.float32),
        keypoints_conf=np.asarray(keypoints_conf, dtype=np.float32),
        selected_keypoints=selected_keypoints,
    )
