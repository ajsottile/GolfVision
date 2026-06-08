from __future__ import annotations

import html
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

ACCENT_ORANGE = "#ff6a1a"
ACCENT_PURPLE = "#a855f7"
ACCENT_GREEN = "#34d399"
ACCENT_AMBER = "#fbbf24"
ACCENT_RED = "#fb7185"

# Backwards-compatible aliases (older code referenced cyan/violet names).
ACCENT_CYAN = ACCENT_ORANGE
ACCENT_VIOLET = ACCENT_PURPLE


GLOBAL_STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

:root {
  --gv-bg: #0b0710;
  --gv-card: rgba(255,255,255,0.04);
  --gv-card-border: rgba(255,255,255,0.10);
  --gv-cyan: #ff6a1a;
  --gv-violet: #a855f7;
  --gv-green: #34d399;
  --gv-amber: #fbbf24;
  --gv-red: #fb7185;
  --gv-text: #f1ecf6;
  --gv-muted: #9a8fb0;
}

.stApp {
  background:
    radial-gradient(1200px 600px at 12% -10%, rgba(255,106,26,0.12), transparent 60%),
    radial-gradient(1000px 500px at 100% 0%, rgba(168,85,247,0.14), transparent 55%),
    var(--gv-bg);
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
h1, h2, h3, h4 { font-family: 'Space Grotesk', sans-serif !important; letter-spacing: -0.01em; }

#MainMenu, footer { visibility: hidden; }
[data-testid="stHeader"] { background: transparent; }

/* Hero */
.gv-hero {
  position: relative;
  border-radius: 22px;
  padding: 34px 36px;
  margin-bottom: 22px;
  background: linear-gradient(135deg, rgba(255,106,26,0.10), rgba(168,85,247,0.10));
  border: 1px solid var(--gv-card-border);
  overflow: hidden;
  animation: gv-fade-up 0.7s ease both;
}
.gv-hero::after {
  content: "";
  position: absolute; inset: 0;
  background: linear-gradient(115deg, transparent 30%, rgba(255,255,255,0.06) 50%, transparent 70%);
  transform: translateX(-120%);
  animation: gv-shine 5.5s ease-in-out infinite;
}
.gv-hero h1 {
  font-size: 2.5rem; margin: 0;
  background: linear-gradient(90deg, var(--gv-cyan), var(--gv-violet));
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
}
.gv-hero p { color: var(--gv-muted); margin: 8px 0 0; font-size: 1.02rem; }
.gv-badge-pill {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 5px 13px; border-radius: 999px; font-size: 0.76rem; font-weight: 600;
  background: rgba(52,211,153,0.14); color: var(--gv-green);
  border: 1px solid rgba(52,211,153,0.3); margin-bottom: 14px;
}
.gv-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--gv-green); animation: gv-pulse 1.6s infinite; }

/* CloudHack brand */
.gv-brandrow { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
.gv-brand { display: inline-flex; align-items: center; gap: 10px; }
.gv-brand-logo {
  width: 30px; height: 30px; border-radius: 9px;
  background: linear-gradient(135deg, var(--gv-cyan), var(--gv-violet));
  box-shadow: 0 0 18px rgba(255,106,26,0.45);
  display: inline-flex; align-items: center; justify-content: center;
  font-family: 'Space Grotesk', sans-serif; font-weight: 800; color: #0b0710; font-size: 0.95rem;
}
.gv-brand-name {
  font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 1.02rem; letter-spacing: 0.01em;
}
.gv-brand-name .gv-brand-hack {
  background: linear-gradient(90deg, var(--gv-cyan), var(--gv-violet));
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
}
.gv-brand-tag {
  font-size: 0.72rem; color: var(--gv-muted); border: 1px solid var(--gv-card-border);
  padding: 4px 10px; border-radius: 999px; white-space: nowrap;
}
.gv-footer {
  margin-top: 30px; padding: 18px 6px; text-align: center;
  border-top: 1px solid var(--gv-card-border); color: var(--gv-muted); font-size: 0.82rem;
}
.gv-footer .gv-brand-hack {
  background: linear-gradient(90deg, var(--gv-cyan), var(--gv-violet));
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; font-weight: 700;
}

/* Glass cards */
.gv-card {
  background: var(--gv-card);
  border: 1px solid var(--gv-card-border);
  border-radius: 18px; padding: 20px 22px; margin-bottom: 16px;
  backdrop-filter: blur(8px);
  animation: gv-fade-up 0.6s ease both;
}
.gv-section-title {
  font-family: 'Space Grotesk', sans-serif; font-size: 1.28rem; font-weight: 600;
  margin: 6px 0 14px; color: var(--gv-text); display: flex; align-items: center; gap: 10px;
}
.gv-section-title .gv-accent-bar {
  width: 4px; height: 20px; border-radius: 4px;
  background: linear-gradient(180deg, var(--gv-cyan), var(--gv-violet));
}

/* Stat cards */
.gv-stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 14px; }
.gv-stat {
  background: var(--gv-card); border: 1px solid var(--gv-card-border);
  border-radius: 16px; padding: 16px 18px; animation: gv-fade-up 0.6s ease both;
  transition: transform 0.2s ease, border-color 0.2s ease;
}
.gv-stat:hover { transform: translateY(-3px); border-color: rgba(255,106,26,0.4); }
.gv-stat .gv-stat-label { color: var(--gv-muted); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; }
.gv-stat .gv-stat-value { font-family: 'Space Grotesk', sans-serif; font-size: 1.7rem; font-weight: 700; margin-top: 4px; }

/* XP bar */
.gv-xp-wrap { margin-top: 6px; }
.gv-xp-head { display: flex; justify-content: space-between; font-size: 0.82rem; color: var(--gv-muted); margin-bottom: 6px; }
.gv-xp-track { height: 12px; border-radius: 999px; background: rgba(255,255,255,0.07); overflow: hidden; }
.gv-xp-fill {
  height: 100%; border-radius: 999px;
  background: linear-gradient(90deg, var(--gv-cyan), var(--gv-violet));
  box-shadow: 0 0 16px rgba(255,106,26,0.6);
  animation: gv-grow-x 1.1s cubic-bezier(0.16,1,0.3,1) both;
}

/* badges */
.gv-badges { display: flex; flex-wrap: wrap; gap: 10px; }
.gv-badge {
  display: flex; align-items: center; gap: 9px;
  padding: 9px 14px; border-radius: 13px; font-size: 0.86rem; font-weight: 600;
  border: 1px solid var(--gv-card-border); background: var(--gv-card);
  animation: gv-pop 0.5s cubic-bezier(0.16,1.4,0.4,1) both;
}
.gv-badge .gv-badge-icon { font-size: 1.1rem; }
.gv-badge.earned { border-color: rgba(52,211,153,0.45); background: rgba(52,211,153,0.10); }
.gv-badge.locked { opacity: 0.45; }

/* progress meter for metrics */
.gv-meter-row { margin-bottom: 14px; }
.gv-meter-top { display: flex; justify-content: space-between; font-size: 0.86rem; margin-bottom: 6px; }
.gv-meter-metric { font-weight: 600; color: var(--gv-text); }
.gv-meter-val { color: var(--gv-muted); font-variant-numeric: tabular-nums; }
.gv-meter-track { height: 9px; border-radius: 999px; background: rgba(255,255,255,0.07); overflow: hidden; }
.gv-meter-fill { height: 100%; border-radius: 999px; animation: gv-grow-x 1s cubic-bezier(0.16,1,0.3,1) both; }

/* quest / recommendation cards */
.gv-quest {
  border-radius: 16px; padding: 18px 20px; margin-bottom: 14px;
  background: var(--gv-card); border: 1px solid var(--gv-card-border);
  border-left: 4px solid var(--gv-cyan);
  animation: gv-fade-up 0.55s ease both;
}
.gv-quest .gv-quest-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 10px; }
.gv-quest .gv-quest-title { font-family: 'Space Grotesk', sans-serif; font-size: 1.08rem; font-weight: 600; }
.gv-prio { font-size: 0.7rem; font-weight: 700; padding: 4px 10px; border-radius: 999px; text-transform: uppercase; letter-spacing: 0.05em; }
.gv-prio.high { background: rgba(251,113,133,0.16); color: var(--gv-red); }
.gv-prio.medium { background: rgba(251,191,36,0.16); color: var(--gv-amber); }
.gv-prio.low { background: rgba(52,211,153,0.16); color: var(--gv-green); }
.gv-field { margin: 8px 0; font-size: 0.92rem; line-height: 1.5; }
.gv-field b { color: var(--gv-cyan); font-weight: 600; }
.gv-drill {
  background: rgba(255,255,255,0.03); border: 1px solid var(--gv-card-border);
  border-radius: 11px; padding: 10px 13px; margin-top: 8px; font-size: 0.88rem;
}
.gv-drill .gv-drill-name { font-weight: 600; color: var(--gv-text); }
.gv-drill .gv-drill-meta { color: var(--gv-muted); font-size: 0.8rem; margin-top: 3px; }

/* timeline for routine */
.gv-timeline { position: relative; padding-left: 26px; }
.gv-timeline::before { content: ""; position: absolute; left: 7px; top: 4px; bottom: 4px; width: 2px;
  background: linear-gradient(180deg, var(--gv-cyan), var(--gv-violet)); }
.gv-tl-node { position: relative; margin-bottom: 16px; animation: gv-fade-up 0.5s ease both; }
.gv-tl-node::before { content: ""; position: absolute; left: -23px; top: 4px; width: 12px; height: 12px;
  border-radius: 50%; background: var(--gv-cyan); box-shadow: 0 0 12px rgba(255,106,26,0.8); }
.gv-tl-title { font-weight: 600; color: var(--gv-text); }
.gv-tl-min { color: var(--gv-cyan); font-size: 0.8rem; font-weight: 600; }
.gv-tl-body { color: var(--gv-muted); font-size: 0.86rem; margin-top: 4px; line-height: 1.45; }

/* week cards */
.gv-week-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 14px; }
.gv-week {
  background: var(--gv-card); border: 1px solid var(--gv-card-border);
  border-radius: 16px; padding: 16px 18px; animation: gv-fade-up 0.6s ease both;
  transition: transform 0.2s ease, border-color 0.2s ease;
}
.gv-week:hover { transform: translateY(-3px); border-color: rgba(168,85,247,0.45); }
.gv-week .gv-week-tag {
  display: inline-block; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.05em;
  color: var(--gv-violet); background: rgba(168,85,247,0.14); padding: 3px 10px; border-radius: 999px;
}
.gv-week .gv-week-theme { font-weight: 600; margin: 8px 0 10px; color: var(--gv-text); font-size: 0.96rem; }
.gv-sess { font-size: 0.82rem; color: var(--gv-muted); margin-bottom: 7px; padding-left: 14px; position: relative; }
.gv-sess::before { content: ""; position: absolute; left: 0; top: 7px; width: 6px; height: 6px; border-radius: 50%; background: var(--gv-violet); }
.gv-sess b { color: var(--gv-text); font-weight: 600; }

/* buttons */
.stButton > button {
  border-radius: 12px !important; font-weight: 600 !important;
  border: 1px solid rgba(255,106,26,0.4) !important;
  transition: transform 0.15s ease, box-shadow 0.2s ease !important;
}
.stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 24px rgba(255,106,26,0.25) !important; }

@keyframes gv-fade-up { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: translateY(0); } }
@keyframes gv-pop { from { opacity: 0; transform: scale(0.8); } to { opacity: 1; transform: scale(1); } }
@keyframes gv-grow-x { from { width: 0; } }
@keyframes gv-shine { 0% { transform: translateX(-120%);} 55%,100% { transform: translateX(120%);} }
@keyframes gv-pulse { 0%,100% { box-shadow: 0 0 0 0 rgba(52,211,153,0.5);} 50% { box-shadow: 0 0 0 6px rgba(52,211,153,0);} }
@keyframes gv-ring { from { stroke-dashoffset: var(--gv-circ); } }
</style>
"""


def inject_global_styles() -> None:
    st.markdown(GLOBAL_STYLES, unsafe_allow_html=True)


def render_hero(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="gv-hero">
          <div class="gv-brandrow">
            <div class="gv-brand">
              <span class="gv-brand-logo">C</span>
              <span class="gv-brand-name">cloud<span class="gv-brand-hack">Hack</span></span>
            </div>
            <div class="gv-brand-tag">a cloudHack product</div>
          </div>
          <div class="gv-badge-pill"><span class="gv-dot"></span> AI Swing Lab - Live</div>
          <h1>{html.escape(title)}</h1>
          <p>{html.escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(
        """
        <div class="gv-footer">
          Built with <span class="gv-brand-hack">cloudHack</span> &middot;
          GolfVision AI Swing Lab &middot; orange/purple, all swing.
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(text: str) -> None:
    st.markdown(
        f'<div class="gv-section-title"><span class="gv-accent-bar"></span>{html.escape(text)}</div>',
        unsafe_allow_html=True,
    )


def grade_for(score: float) -> tuple[str, str]:
    if score >= 90:
        return "S", ACCENT_GREEN
    if score >= 80:
        return "A", ACCENT_CYAN
    if score >= 65:
        return "B", ACCENT_CYAN
    if score >= 50:
        return "C", ACCENT_AMBER
    return "D", ACCENT_RED


def render_score_ring(score: float) -> None:
    score = max(0.0, min(100.0, float(score)))
    grade, color = grade_for(score)
    radius = 84
    circ = 2 * 3.14159 * radius
    offset = circ * (1 - score / 100.0)
    st.markdown(
        f"""
        <div class="gv-card" style="display:flex;align-items:center;gap:26px;flex-wrap:wrap;">
          <div style="position:relative;width:200px;height:200px;flex:0 0 auto;">
            <svg width="200" height="200" viewBox="0 0 200 200">
              <defs>
                <linearGradient id="gvgrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stop-color="{ACCENT_CYAN}"/>
                  <stop offset="100%" stop-color="{ACCENT_VIOLET}"/>
                </linearGradient>
              </defs>
              <circle cx="100" cy="100" r="{radius}" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="14"/>
              <circle cx="100" cy="100" r="{radius}" fill="none" stroke="url(#gvgrad)" stroke-width="14"
                stroke-linecap="round" transform="rotate(-90 100 100)"
                stroke-dasharray="{circ:.1f}" stroke-dashoffset="{offset:.1f}"
                style="--gv-circ:{circ:.1f}px; animation: gv-ring 1.4s cubic-bezier(0.16,1,0.3,1) both;"/>
            </svg>
            <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;">
              <div style="font-family:'Space Grotesk';font-size:2.8rem;font-weight:700;line-height:1;">{score:.0f}</div>
              <div style="color:var(--gv-muted);font-size:0.8rem;">/ 100</div>
            </div>
          </div>
          <div style="flex:1 1 200px;">
            <div style="color:var(--gv-muted);font-size:0.8rem;text-transform:uppercase;letter-spacing:0.06em;">Swing Match Grade</div>
            <div style="font-family:'Space Grotesk';font-size:3.4rem;font-weight:700;color:{color};line-height:1;margin:4px 0;">{grade}</div>
            <div style="color:var(--gv-muted);font-size:0.95rem;">Similarity to your selected pro reference</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _level_from_score(score: float) -> tuple[int, float]:
    # Level 1-10 scaled by score, with progress to next level.
    level = int(score // 10) + 1
    level = max(1, min(level, 10))
    progress = (score % 10) / 10.0 if score < 100 else 1.0
    return level, progress


def render_xp_bar(score: float) -> None:
    level, progress = _level_from_score(score)
    pct = int(progress * 100)
    st.markdown(
        f"""
        <div class="gv-card">
          <div class="gv-xp-wrap">
            <div class="gv-xp-head">
              <span>Level {level} Golfer</span>
              <span>{pct}% to Level {min(level + 1, 10)}</span>
            </div>
            <div class="gv-xp-track"><div class="gv-xp-fill" style="width:{pct}%;"></div></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stat_cards(stats: list[tuple[str, str, str]]) -> None:
    cards = ""
    for label, value, color in stats:
        cards += (
            f'<div class="gv-stat"><div class="gv-stat-label">{html.escape(label)}</div>'
            f'<div class="gv-stat-value" style="color:{color};">{html.escape(value)}</div></div>'
        )
    st.markdown(f'<div class="gv-stat-grid">{cards}</div>', unsafe_allow_html=True)


def render_badges(comparisons: list[Any]) -> None:
    """Award badges based on how close each metric is to the pro baseline."""
    catalog = [
        ("tempo_ratio", "Tempo Master", "⏱️"),
        ("head_stability", "Steady Head", "🎯"),
        ("x_factor", "Power Coil", "💪"),
        ("spine_tilt", "Posture Pro", "🧍"),
        ("shoulder_turn", "Full Turn", "🔄"),
        ("lead_arm_extension", "Wide Arc", "📐"),
    ]
    best_error: dict[str, float] = {}
    for cmp in comparisons:
        best_error[cmp.metric] = min(best_error.get(cmp.metric, 1.0), cmp.normalized_error)

    chips = ""
    for metric, name, icon in catalog:
        err = best_error.get(metric)
        earned = err is not None and err < 0.35
        cls = "earned" if earned else "locked"
        lock = "" if earned else " 🔒"
        chips += (
            f'<div class="gv-badge {cls}"><span class="gv-badge-icon">{icon}</span>'
            f'{html.escape(name)}{lock}</div>'
        )
    st.markdown(f'<div class="gv-badges">{chips}</div>', unsafe_allow_html=True)


def render_metric_meters(comparisons: list[Any]) -> None:
    rows = ""
    ranked = sorted(comparisons, key=lambda c: c.normalized_error, reverse=True)
    for cmp in ranked:
        match = max(0.0, 1.0 - cmp.normalized_error) * 100.0
        if cmp.normalized_error >= 0.6:
            color = ACCENT_RED
        elif cmp.normalized_error >= 0.35:
            color = ACCENT_AMBER
        else:
            color = ACCENT_GREEN
        metric_label = cmp.metric.replace("_", " ").title()
        rows += (
            '<div class="gv-meter-row">'
            f'<div class="gv-meter-top"><span class="gv-meter-metric">{html.escape(metric_label)} '
            f'<span style="color:var(--gv-muted);font-weight:400;">({html.escape(cmp.phase)})</span></span>'
            f'<span class="gv-meter-val">you {cmp.user_value:.1f} | pro {cmp.pro_value:.1f}</span></div>'
            f'<div class="gv-meter-track"><div class="gv-meter-fill" '
            f'style="width:{match:.0f}%;background:{color};"></div></div>'
            "</div>"
        )
    st.markdown(f'<div class="gv-card">{rows}</div>', unsafe_allow_html=True)


def render_radar(comparisons: list[Any]) -> None:
    try:
        import plotly.graph_objects as go
    except Exception:
        st.info("Install plotly to see the pro-vs-you radar chart (pip install plotly).")
        return

    if not comparisons:
        return

    labels, you_vals, pro_vals = [], [], []
    for cmp in sorted(comparisons, key=lambda c: c.metric):
        labels.append(cmp.metric.replace("_", " ").title())
        match = max(0.0, 1.0 - cmp.normalized_error) * 100.0
        you_vals.append(match)
        pro_vals.append(100.0)

    if not labels:
        return

    labels.append(labels[0])
    you_vals.append(you_vals[0])
    pro_vals.append(pro_vals[0])

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=pro_vals, theta=labels, fill="toself", name="Pro target",
            line=dict(color=ACCENT_VIOLET, width=2),
            fillcolor="rgba(168,85,247,0.12)",
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=you_vals, theta=labels, fill="toself", name="You",
            line=dict(color=ACCENT_CYAN, width=3),
            fillcolor="rgba(255,106,26,0.20)",
        )
    )
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(255,255,255,0.12)", tickfont=dict(color="#8b97ac")),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.12)", tickfont=dict(color="#e6edf6")),
        ),
        showlegend=True,
        legend=dict(font=dict(color="#e6edf6")),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter"),
        margin=dict(l=40, r=40, t=30, b=30),
        height=420,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_quest_card(idx: int, recommendation: dict[str, Any]) -> None:
    priority = str(recommendation.get("priority", "medium")).lower()
    title = html.escape(str(recommendation.get("title") or recommendation.get("focus", "Priority Focus")))
    metric = html.escape(str(recommendation.get("metric", "")))
    what = html.escape(str(recommendation.get("what_is_happening", recommendation.get("why", ""))))
    why = html.escape(str(recommendation.get("why_it_matters", "")))
    how = html.escape(str(recommendation.get("how_to_improve", "")))

    drills_html = ""
    for drill in recommendation.get("priority_drills", []):
        drills_html += (
            '<div class="gv-drill">'
            f'<div class="gv-drill-name">{html.escape(str(drill.get("name", "")))}</div>'
            f'<div class="gv-drill-meta">{html.escape(str(drill.get("focus_cue", "")))} '
            f'&middot; Reps: {html.escape(str(drill.get("reps", "")))} '
            f'&middot; Equipment: {html.escape(str(drill.get("equipment", "")))}</div>'
            "</div>"
        )

    st.markdown(
        f"""
        <div class="gv-quest">
          <div class="gv-quest-head">
            <span class="gv-quest-title">Quest {idx}: {title}</span>
            <span class="gv-prio {priority}">{priority}</span>
          </div>
          <div class="gv-field"><b>Metric:</b> {metric}</div>
          <div class="gv-field"><b>What is happening:</b> {what}</div>
          <div class="gv-field"><b>Why it matters:</b> {why}</div>
          <div class="gv-field"><b>How to improve:</b> {how}</div>
          {drills_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_routine_timeline(quick_routine: dict[str, Any]) -> None:
    nodes = ""
    for block in quick_routine.get("blocks", []):
        nodes += (
            '<div class="gv-tl-node">'
            f'<div class="gv-tl-title">{html.escape(str(block.get("name", "Block")))} '
            f'<span class="gv-tl-min">{int(block.get("minutes", 0))} min</span></div>'
            f'<div class="gv-tl-body"><b style="color:var(--gv-green);">Goal:</b> {html.escape(str(block.get("goal", "")))}<br>'
            f'{html.escape(str(block.get("instructions", "")))}<br>'
            f'<b style="color:var(--gv-cyan);">Success:</b> {html.escape(str(block.get("success_criteria", "")))}</div>'
            "</div>"
        )
    st.markdown(f'<div class="gv-card"><div class="gv-timeline">{nodes}</div></div>', unsafe_allow_html=True)


def render_week_cards(multiweek_plan: dict[str, Any]) -> None:
    cards = ""
    for week in multiweek_plan.get("weeks", []):
        sessions = ""
        for session in week.get("sessions", []):
            sessions += (
                '<div class="gv-sess">'
                f'<b>{html.escape(str(session.get("day", "Day")))}:</b> {html.escape(str(session.get("focus", "")))}'
                "</div>"
            )
        cards += (
            '<div class="gv-week">'
            f'<span class="gv-week-tag">WEEK {int(week.get("week", 0))}</span>'
            f'<div class="gv-week-theme">{html.escape(str(week.get("theme", "")))}</div>'
            f"{sessions}</div>"
        )
    st.markdown(f'<div class="gv-week-grid">{cards}</div>', unsafe_allow_html=True)


def fire_confetti() -> None:
    components.html(
        """
        <canvas id="gv-confetti" style="position:fixed;inset:0;pointer-events:none;z-index:9999;"></canvas>
        <script>
        const c = document.getElementById('gv-confetti');
        const ctx = c.getContext('2d');
        c.width = window.innerWidth; c.height = window.innerHeight;
        const colors = ['#ff6a1a','#a855f7','#ff9347','#fbbf24','#c084fc'];
        let parts = [];
        for (let i=0;i<140;i++){
          parts.push({x:Math.random()*c.width,y:-20-Math.random()*c.height,
            r:4+Math.random()*6,c:colors[i%colors.length],
            vy:2+Math.random()*4,vx:-2+Math.random()*4,rot:Math.random()*6.28,vr:-0.2+Math.random()*0.4});
        }
        let frames=0;
        function draw(){
          ctx.clearRect(0,0,c.width,c.height);
          parts.forEach(p=>{
            p.y+=p.vy; p.x+=p.vx; p.rot+=p.vr;
            ctx.save(); ctx.translate(p.x,p.y); ctx.rotate(p.rot);
            ctx.fillStyle=p.c; ctx.fillRect(-p.r/2,-p.r/2,p.r,p.r*1.6); ctx.restore();
          });
          frames++;
          if(frames<260){requestAnimationFrame(draw);} else {ctx.clearRect(0,0,c.width,c.height);}
        }
        draw();
        </script>
        """,
        height=0,
    )
