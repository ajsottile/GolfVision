"""Golf swing analysis package."""

from golfvision import ui
from golfvision.align import AlignmentResult, align_swings
from golfvision.coaching import CoachingTip, generate_coaching_tips
from golfvision.metrics import SwingMetrics, compare_swing_metrics, compute_swing_metrics
from golfvision.phases import SwingPhases, detect_swing_phases
from golfvision.pose import PoseSequence, extract_pose_sequence
from golfvision.render import render_side_by_side_video
from golfvision.view import ViewProfile, resolve_view_profile

__all__ = [
    "AlignmentResult",
    "CoachingTip",
    "PoseSequence",
    "SwingMetrics",
    "SwingPhases",
    "ViewProfile",
    "align_swings",
    "compare_swing_metrics",
    "compute_swing_metrics",
    "detect_swing_phases",
    "extract_pose_sequence",
    "generate_coaching_tips",
    "render_side_by_side_video",
    "resolve_view_profile",
    "ui",
]
