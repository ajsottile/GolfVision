from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import supervision as sv

from golfvision.align import AlignmentResult
from golfvision.coaching import CoachingTip
from golfvision.metrics import MetricComparison
from golfvision.phases import SwingPhases
from golfvision.pose import PoseSequence


def _build_video_writer(output_path: str, fps: float, size: tuple[int, int]) -> cv2.VideoWriter:
    for codec in ("avc1", "mp4v"):
        writer = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*codec), fps, size)
        if writer.isOpened():
            return writer
        writer.release()
    raise RuntimeError("Could not initialize a compatible video writer for output rendering.")


def _read_video_frames(video_path: str) -> list[np.ndarray]:
    capture = cv2.VideoCapture(video_path)
    frames: list[np.ndarray] = []
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        frames.append(frame)
    capture.release()
    return frames


def _phase_label(frame_index: int, phases: SwingPhases) -> str:
    marks = phases.as_dict()
    ordered = sorted(marks.items(), key=lambda item: item[1])
    current = "address"
    for name, idx in ordered:
        if frame_index >= idx:
            current = name
        else:
            break
    return current


def _annotate_frame(
    frame: np.ndarray,
    sequence: PoseSequence,
    frame_idx: int,
    phase_label: str,
) -> np.ndarray:
    frame_idx = int(np.clip(frame_idx, 0, len(sequence.selected_keypoints) - 1))
    result = frame.copy()
    keypoints = sequence.selected_keypoints[frame_idx]

    if keypoints is not None:
        edge_annotator = sv.EdgeAnnotator()
        vertex_annotator = sv.VertexAnnotator(radius=4)
        result = edge_annotator.annotate(scene=result, key_points=keypoints)
        result = vertex_annotator.annotate(scene=result, key_points=keypoints)

    cv2.putText(
        result,
        f"Phase: {phase_label}",
        (16, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return result


def _draw_panel_tag(frame: np.ndarray, text: str, color: tuple[int, int, int]) -> np.ndarray:
    output = frame.copy()
    cv2.rectangle(output, (12, 8), (180, 48), color, -1)
    cv2.putText(
        output,
        text,
        (24, 36),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.85,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return output


def _render_header(
    frame: np.ndarray,
    score: float,
    tips: list[CoachingTip],
    comparisons: list[MetricComparison],
) -> np.ndarray:
    output = frame.copy()
    cv2.putText(
        output,
        f"Similarity score: {score:.1f}/100",
        (16, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (18, 227, 125),
        2,
        cv2.LINE_AA,
    )

    if comparisons:
        top = max(comparisons, key=lambda c: c.normalized_error)
        cv2.putText(
            output,
            f"Biggest gap: {top.metric} ({top.phase})",
            (16, 62),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

    if tips:
        cv2.putText(
            output,
            f"Top tip: {tips[0].message[:80]}",
            (16, 92),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (237, 199, 84),
            2,
            cv2.LINE_AA,
        )

    return output


def _build_phase_locked_pairs(
    pro_phases: SwingPhases,
    user_phases: SwingPhases,
    sync_start_phase: str,
) -> list[tuple[int, int]]:
    phase_order = ["address", "takeaway", "top", "impact", "follow_through", "finish"]
    start_name = sync_start_phase.strip().lower()
    if start_name not in phase_order:
        start_name = "takeaway"
    start_idx = phase_order.index(start_name)

    pro_marks = pro_phases.as_dict()
    user_marks = user_phases.as_dict()
    pairs: list[tuple[int, int]] = []

    for idx in range(start_idx, len(phase_order) - 1):
        left = phase_order[idx]
        right = phase_order[idx + 1]
        pro_start = int(pro_marks[left])
        pro_end = int(pro_marks[right])
        user_start = int(user_marks[left])
        user_end = int(user_marks[right])

        pro_span = max(pro_end - pro_start, 1)
        user_span = max(user_end - user_start, 1)
        segment_len = max(pro_span, user_span, 1)

        for step in range(segment_len):
            t = step / float(segment_len)
            pro_idx = int(round(pro_start + t * (pro_end - pro_start)))
            user_idx = int(round(user_start + t * (user_end - user_start)))
            pairs.append((pro_idx, user_idx))

    pairs.append((int(pro_marks["finish"]), int(user_marks["finish"])))

    deduped: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    for pair in pairs:
        if pair in seen:
            continue
        deduped.append(pair)
        seen.add(pair)
    return deduped


def render_side_by_side_video(
    pro_sequence: PoseSequence,
    user_sequence: PoseSequence,
    pro_phases: SwingPhases,
    user_phases: SwingPhases,
    alignment: AlignmentResult,
    comparisons: list[MetricComparison],
    score: float,
    tips: list[CoachingTip],
    output_path: str,
    sync_start_phase: str = "takeaway",
) -> str:
    pro_frames = _read_video_frames(pro_sequence.video_path)
    user_frames = _read_video_frames(user_sequence.video_path)
    if not pro_frames or not user_frames:
        raise ValueError("Could not load source video frames for rendering.")

    frame_pairs = _build_phase_locked_pairs(
        pro_phases=pro_phases,
        user_phases=user_phases,
        sync_start_phase=sync_start_phase,
    )
    if not frame_pairs:
        pair_count = min(len(pro_frames), len(user_frames))
        frame_pairs = [(idx, idx) for idx in range(pair_count)]

    target_height = min(pro_frames[0].shape[0], user_frames[0].shape[0])
    pro_width = int(pro_frames[0].shape[1] * (target_height / pro_frames[0].shape[0]))
    user_width = int(user_frames[0].shape[1] * (target_height / user_frames[0].shape[0]))
    composite_size = (pro_width + user_width, target_height + 110)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    writer = _build_video_writer(
        output_path=output_path,
        fps=min(pro_sequence.fps, user_sequence.fps),
        size=composite_size,
    )

    for pro_idx, user_idx in frame_pairs:
        pro_idx = int(np.clip(pro_idx, 0, len(pro_frames) - 1))
        user_idx = int(np.clip(user_idx, 0, len(user_frames) - 1))
        pro_frame = pro_frames[pro_idx]
        user_frame = user_frames[user_idx]

        pro_annotated = _annotate_frame(
            pro_frame,
            pro_sequence,
            pro_idx,
            _phase_label(pro_idx, pro_phases),
        )
        user_annotated = _annotate_frame(
            user_frame,
            user_sequence,
            user_idx,
            _phase_label(user_idx, user_phases),
        )

        pro_annotated = _draw_panel_tag(pro_annotated, "PRO REFERENCE", (56, 98, 255))
        user_annotated = _draw_panel_tag(user_annotated, "YOUR SWING", (32, 184, 126))

        pro_annotated = cv2.resize(pro_annotated, (pro_width, target_height))
        user_annotated = cv2.resize(user_annotated, (user_width, target_height))

        side_by_side = np.hstack([pro_annotated, user_annotated])
        canvas = np.zeros((composite_size[1], composite_size[0], 3), dtype=np.uint8)
        canvas[: target_height, :, :] = side_by_side
        canvas = _render_header(canvas, score=score, tips=tips, comparisons=comparisons)
        writer.write(canvas)

    writer.release()
    return output_path
