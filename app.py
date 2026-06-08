from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import streamlit as st

from golfvision import ui

if TYPE_CHECKING:
    from golfvision.recommendations import CoachingReport

PROS_DIR = Path("data/pros")
OUTPUTS_DIR = Path("outputs")
REPORT_SCHEMA_VERSION = 3


def _list_pro_clips() -> list[Path]:
    PROS_DIR.mkdir(parents=True, exist_ok=True)
    return sorted([path for path in PROS_DIR.iterdir() if path.suffix.lower() in {".mp4", ".mov", ".m4v"}])


def _save_uploaded_video(uploaded_file: st.runtime.uploaded_file_manager.UploadedFile) -> Path:
    suffix = Path(uploaded_file.name).suffix or ".mp4"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(uploaded_file.getbuffer())
        return Path(tmp.name)


def run_pipeline(
    pro_clip_path: Path,
    user_clip_path: Path,
    view_name: str,
    sync_start_phase: str,
) -> tuple[str, float, list, list]:
    from golfvision.align import align_swings
    from golfvision.coaching import generate_coaching_tips
    from golfvision.metrics import compare_swing_metrics, compute_swing_metrics
    from golfvision.phases import detect_swing_phases
    from golfvision.pose import extract_pose_sequence
    from golfvision.render import render_side_by_side_video
    from golfvision.view import resolve_view_profile

    view_profile = resolve_view_profile(view_name)

    pro_sequence = extract_pose_sequence(str(pro_clip_path))
    user_sequence = extract_pose_sequence(str(user_clip_path))

    pro_phases = detect_swing_phases(pro_sequence)
    user_phases = detect_swing_phases(user_sequence)

    alignment = align_swings(
        pro_sequence=pro_sequence,
        user_sequence=user_sequence,
        pro_phases=pro_phases,
        user_phases=user_phases,
    )

    pro_metrics = compute_swing_metrics(pro_sequence, pro_phases, view_profile)
    user_metrics = compute_swing_metrics(user_sequence, user_phases, view_profile)
    comparisons, score = compare_swing_metrics(pro_metrics, user_metrics, view_profile)
    tips = generate_coaching_tips(comparisons)

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUTS_DIR / f"comparison_{pro_clip_path.stem}_{user_clip_path.stem}.mp4"
    render_side_by_side_video(
        pro_sequence=pro_sequence,
        user_sequence=user_sequence,
        pro_phases=pro_phases,
        user_phases=user_phases,
        alignment=alignment,
        comparisons=comparisons,
        score=score,
        tips=tips,
        output_path=str(output_path),
        sync_start_phase=sync_start_phase,
    )
    return str(output_path), score, comparisons, tips


def _render_results(result: dict) -> None:
    score = result["score"]
    comparisons = result["comparisons"]

    if not st.session_state.get("celebrated") and score >= 80:
        ui.fire_confetti()
        st.session_state["celebrated"] = True

    left, right = st.columns([1.1, 1])
    with left:
        ui.render_score_ring(score)
        ui.render_xp_bar(score)
    with right:
        ui.section_title("Pro vs You")
        ui.render_radar(comparisons)

    near_pro = sum(1 for c in comparisons if c.normalized_error < 0.35)
    biggest = max(comparisons, key=lambda c: c.normalized_error) if comparisons else None
    ui.render_stat_cards(
        [
            ("Match Score", f"{score:.0f}", ui.ACCENT_ORANGE),
            ("Metrics On Target", f"{near_pro}/{len(comparisons)}", ui.ACCENT_GREEN),
            ("Sessions Run", str(st.session_state.get("sessions_run", 1)), ui.ACCENT_PURPLE),
            (
                "Top Priority",
                biggest.metric.replace("_", " ").title() if biggest else "None",
                ui.ACCENT_AMBER,
            ),
        ]
    )

    ui.section_title("Achievements")
    ui.render_badges(comparisons)

    ui.section_title("Synchronized Side-by-Side")
    video_bytes = Path(result["output_path"]).read_bytes()
    st.video(video_bytes, format="video/mp4")
    st.download_button(
        label="Download comparison video",
        data=video_bytes,
        file_name=Path(result["output_path"]).name,
        mime="video/mp4",
    )

    ui.section_title("Metric Breakdown")
    ui.render_metric_meters(comparisons)


def _render_report(report: CoachingReport) -> None:
    ui.section_title("Coach Summary")
    st.markdown(f'<div class="gv-card">{report.summary}</div>', unsafe_allow_html=True)

    ui.section_title("Priority Quests")
    for idx, recommendation in enumerate(report.recommendations, start=1):
        ui.render_quest_card(idx, recommendation)

    ui.section_title(f"Quick Routine - {report.quick_routine.get('duration_min', 0)} min")
    ui.render_routine_timeline(report.quick_routine)

    ui.section_title("4-Week Progression")
    ui.render_week_cards(report.multiweek_plan)

    from golfvision.recommendations import format_report_markdown

    markdown = format_report_markdown(report)
    st.download_button(
        label="Download coaching plan (Markdown)",
        data=markdown,
        file_name="coaching_plan.md",
        mime="text/markdown",
    )


def main() -> None:
    st.set_page_config(page_title="GolfVision by cloudHack", page_icon="⛳", layout="wide")
    ui.inject_global_styles()
    ui.render_hero(
        "GolfVision",
        "Upload your swing, match it against a pro, and unlock an AI-built improvement plan — powered by cloudHack.",
    )

    if sys.version_info >= (3, 13):
        st.warning(
            "This app is deployed on Python "
            f"{sys.version_info.major}.{sys.version_info.minor}. "
            "For OpenCV/YOLO compatibility, set **Python 3.12** (or 3.11) in "
            "Streamlit Cloud → Manage app → Settings → Python version, then reboot."
        )

    if st.session_state.get("report_schema_version") != REPORT_SCHEMA_VERSION:
        st.session_state["coaching_report"] = None
        st.session_state["report_schema_version"] = REPORT_SCHEMA_VERSION
    st.session_state.setdefault("comparison_result", None)
    st.session_state.setdefault("coaching_report", None)
    st.session_state.setdefault("sessions_run", 0)

    pro_clips = _list_pro_clips()
    if not pro_clips:
        st.warning("Add at least one professional clip to data/pros/ before running comparison.")
        st.stop()

    ui.section_title("Setup")
    with st.container():
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            selected_pro = st.selectbox("Pro reference clip", pro_clips, format_func=lambda p: p.name)
        with col_b:
            view_name = st.selectbox("Camera view", ["dtl", "face_on"], index=0)
        with col_c:
            sync_start_phase = st.selectbox(
                "Sync start phase",
                ["address", "takeaway", "top", "impact"],
                index=1,
                help="Both videos start playback at this phase.",
            )
        user_upload = st.file_uploader("Upload your swing video", type=["mp4", "mov", "m4v"])

    if st.button("Analyze My Swing", type="primary", disabled=user_upload is None):
        if user_upload is None:
            st.error("Please upload your swing video.")
            st.stop()
        with st.spinner("Tracking pose, detecting phases, and aligning swings..."):
            user_tmp = _save_uploaded_video(user_upload)
            output_path, score, comparisons, tips = run_pipeline(
                selected_pro, user_tmp, view_name, sync_start_phase
            )
            st.session_state["comparison_result"] = {
                "output_path": output_path,
                "score": score,
                "comparisons": comparisons,
                "tips": tips,
                "view_name": view_name,
                "pro_name": selected_pro.stem,
            }
            st.session_state["coaching_report"] = None
            st.session_state["celebrated"] = False
            st.session_state["sessions_run"] = int(st.session_state.get("sessions_run", 0)) + 1

    result = st.session_state.get("comparison_result")
    if result is not None:
        _render_results(result)

        ui.section_title("AI Coaching Plan")
        pro_name = st.text_input(
            "Pro reference name (optional)",
            value=result.get("pro_name", ""),
            help="Frames the AI plan against your chosen pro's swing style.",
        )
        if not os.getenv("OPENAI_API_KEY"):
            st.info("OPENAI_API_KEY not found. Generating with the built-in rule-based coach.")

        if st.button("Generate AI Plan", type="secondary"):
            from golfvision.recommendations import generate_coaching_report

            with st.spinner("Your AI coach is building a personalized plan..."):
                report = generate_coaching_report(
                    comparisons=result["comparisons"],
                    overall_score=result["score"],
                    view_name=result["view_name"],
                    pro_name=pro_name,
                )
            st.session_state["coaching_report"] = report

        report = st.session_state.get("coaching_report")
        if report is not None:
            _render_report(report)

    ui.render_footer()


if __name__ == "__main__":
    main()
