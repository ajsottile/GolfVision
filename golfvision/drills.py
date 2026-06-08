from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Drill:
    id: str
    name: str
    focus_cue: str
    reps: str
    equipment: str
    difficulty: str


DRILLS_BY_METRIC: dict[str, list[Drill]] = {
    "lead_arm_extension": [
        Drill(
            id="drill_towel_connection",
            name="Towel Connection Drill",
            focus_cue="Keep lead arm structured while rotating through top and transition.",
            reps="3 sets x 8 slow swings",
            equipment="Small towel",
            difficulty="beginner",
        ),
        Drill(
            id="drill_split_grip_arc",
            name="Split-Grip Arc Builder",
            focus_cue="Maintain width in the backswing to improve radius and consistency.",
            reps="2 sets x 10 reps",
            equipment="Club",
            difficulty="intermediate",
        ),
    ],
    "tempo_ratio": [
        Drill(
            id="drill_metronome_tempo",
            name="Metronome 3:1 Tempo",
            focus_cue="Count backswing-three and downswing-one with smooth transition.",
            reps="15 swings with metronome",
            equipment="Metronome app",
            difficulty="beginner",
        ),
        Drill(
            id="drill_pause_transition",
            name="Pause at the Top",
            focus_cue="Create sequencing by feeling a brief pause before firing through impact.",
            reps="3 sets x 6 swings",
            equipment="Club",
            difficulty="beginner",
        ),
    ],
    "head_stability": [
        Drill(
            id="drill_head_wall_reference",
            name="Head Wall Reference",
            focus_cue="Keep head centered relative to a fixed reference through impact.",
            reps="2 sets x 10 swings",
            equipment="Alignment stick or wall edge",
            difficulty="beginner",
        ),
        Drill(
            id="drill_centered_turn",
            name="Centered Pivot Drill",
            focus_cue="Rotate around spine tilt without lateral sway.",
            reps="3 sets x 8 reps",
            equipment="Club",
            difficulty="intermediate",
        ),
    ],
    "x_factor": [
        Drill(
            id="drill_separation_pump",
            name="Separation Pump Drill",
            focus_cue="Load shoulders against a stable lower body at the top.",
            reps="3 sets x 6 pump reps + strike",
            equipment="Club",
            difficulty="intermediate",
        ),
        Drill(
            id="drill_step_through_sequence",
            name="Step-Through Sequence Drill",
            focus_cue="Initiate downswing from ground up to improve kinematic sequence.",
            reps="2 sets x 8 reps",
            equipment="Club",
            difficulty="intermediate",
        ),
    ],
    "spine_tilt": [
        Drill(
            id="drill_posture_hold",
            name="Posture Hold Drill",
            focus_cue="Retain forward bend while rotating to prevent early extension.",
            reps="3 sets x 8 reps",
            equipment="Club and mirror",
            difficulty="beginner",
        ),
        Drill(
            id="drill_chair_depth",
            name="Chair Depth Feedback",
            focus_cue="Keep glutes in depth through transition to maintain tilt.",
            reps="2 sets x 10 reps",
            equipment="Chair",
            difficulty="intermediate",
        ),
    ],
    "shoulder_turn": [
        Drill(
            id="drill_shoulder_to_chin",
            name="Shoulder-to-Chin Turn",
            focus_cue="Complete backswing turn with balance and pressure control.",
            reps="3 sets x 8 reps",
            equipment="Club",
            difficulty="beginner",
        ),
        Drill(
            id="drill_cross_arms_turn",
            name="Cross-Arms Rotation Drill",
            focus_cue="Train full thoracic turn independent of arm lift.",
            reps="2 sets x 10 reps",
            equipment="No equipment",
            difficulty="beginner",
        ),
    ],
    "hip_turn": [
        Drill(
            id="drill_hip_depth_wall",
            name="Hip Depth Wall Drill",
            focus_cue="Rotate pelvis without thrusting toward the ball.",
            reps="3 sets x 8 reps",
            equipment="Wall",
            difficulty="intermediate",
        ),
        Drill(
            id="drill_feet_together_balance",
            name="Feet-Together Balance Swings",
            focus_cue="Improve lower body control and centered turn.",
            reps="2 sets x 10 swings",
            equipment="Club",
            difficulty="beginner",
        ),
    ],
    "lead_knee_flex": [
        Drill(
            id="drill_lead_knee_athletic",
            name="Lead Knee Athletic Flex",
            focus_cue="Maintain dynamic flex into impact without collapsing.",
            reps="3 sets x 8 reps",
            equipment="Club",
            difficulty="beginner",
        ),
        Drill(
            id="drill_squat_to_rotate",
            name="Squat-to-Rotate Sequence",
            focus_cue="Blend ground force with rotational control.",
            reps="2 sets x 6 reps",
            equipment="Club",
            difficulty="intermediate",
        ),
    ],
}


DRILL_BY_ID: dict[str, Drill] = {
    drill.id: drill
    for metric_drills in DRILLS_BY_METRIC.values()
    for drill in metric_drills
}


def get_drills_for_metric(metric: str, limit: int = 2) -> list[Drill]:
    return DRILLS_BY_METRIC.get(metric, [])[: max(limit, 0)]


def serialize_drills() -> list[dict[str, str]]:
    return [asdict(drill) for drill in DRILL_BY_ID.values()]
