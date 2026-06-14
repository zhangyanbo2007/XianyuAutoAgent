#!/usr/bin/env python3
"""
DAST slide templates - dark sci-fi neon style matching reference video.
Each function returns a self-contained HTML string for one slide type.
All slides are 1920x1080 with Noto Sans SC font.
"""

import html as _html
import json
import base64
import os

# ── Shared CSS ──────────────────────────────────────────────────────

_SHARED_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&display=swap');

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  width: 1920px;
  height: 1080px;
  overflow: hidden;
  font-family: 'Noto Sans SC', 'Microsoft YaHei', sans-serif;
  background: #0a0a0f;
  color: #e0e0e0;
  position: relative;
}

/* Circuit background pattern */
body::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 20% 30%, rgba(0,212,255,0.03) 0%, transparent 50%),
    radial-gradient(circle at 80% 70%, rgba(168,85,247,0.03) 0%, transparent 50%),
    radial-gradient(circle at 50% 50%, rgba(0,255,136,0.02) 0%, transparent 60%);
  pointer-events: none;
}

/* Grid lines overlay */
body::after {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(0,212,255,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,212,255,0.03) 1px, transparent 1px);
  background-size: 60px 60px;
  pointer-events: none;
}

.container {
  width: 1920px;
  height: 1080px;
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  padding: 60px 80px;
}

/* ── Glow effects ── */
.glow-cyan { text-shadow: 0 0 30px rgba(0,212,255,0.7), 0 0 60px rgba(0,212,255,0.3), 0 0 100px rgba(0,212,255,0.15); }
.glow-green { text-shadow: 0 0 30px rgba(0,255,136,0.7), 0 0 60px rgba(0,255,136,0.3), 0 0 100px rgba(0,255,136,0.15); }
.glow-magenta { text-shadow: 0 0 30px rgba(255,0,255,0.7), 0 0 60px rgba(255,0,255,0.3), 0 0 100px rgba(255,0,255,0.15); }
.glow-orange { text-shadow: 0 0 30px rgba(255,136,0,0.7), 0 0 60px rgba(255,136,0,0.3), 0 0 100px rgba(255,136,0,0.15); }
.glow-purple { text-shadow: 0 0 30px rgba(168,85,247,0.7), 0 0 60px rgba(168,85,247,0.3), 0 0 100px rgba(168,85,247,0.15); }

.border-glow {
  border: 1px solid rgba(0,212,255,0.4);
  box-shadow: 0 0 20px rgba(0,212,255,0.2), inset 0 0 20px rgba(0,212,255,0.08);
}

.border-glow-green {
  border: 1px solid rgba(0,255,136,0.4);
  box-shadow: 0 0 20px rgba(0,255,136,0.2), inset 0 0 20px rgba(0,255,136,0.08);
}

.border-glow-magenta {
  border: 1px solid rgba(255,0,255,0.4);
  box-shadow: 0 0 20px rgba(255,0,255,0.2), inset 0 0 20px rgba(255,0,255,0.08);
}

.border-glow-orange {
  border: 1px solid rgba(255,136,0,0.4);
  box-shadow: 0 0 20px rgba(255,136,0,0.2), inset 0 0 20px rgba(255,136,0,0.08);
}

/* ── Subtitle bar ── */
.subtitle-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 30px 80px;
  background: linear-gradient(transparent, rgba(0,0,0,0.85));
  font-size: 28px;
  color: rgba(255,255,255,0.9);
  line-height: 1.6;
  z-index: 10;
}

/* ── Title at top ── */
.slide-title {
  position: absolute;
  top: 40px;
  left: 0;
  right: 0;
  text-align: center;
  font-size: 52px;
  font-weight: 900;
  z-index: 10;
  padding: 0 60px;
}

/* ── Decorative corner brackets ── */
.corner-deco {
  position: absolute;
  width: 30px;
  height: 30px;
  border-color: rgba(0,212,255,0.4);
  border-style: solid;
}
.corner-deco.tl { top: 20px; left: 20px; border-width: 2px 0 0 2px; }
.corner-deco.tr { top: 20px; right: 20px; border-width: 2px 2px 0 0; }
.corner-deco.bl { bottom: 20px; left: 20px; border-width: 0 0 2px 2px; }
.corner-deco.br { bottom: 20px; right: 20px; border-width: 0 2px 2px 0; }

/* ── Accent line ── */
.accent-line {
  width: 120px;
  height: 3px;
  border-radius: 2px;
  margin: 16px 0;
}

/* ── Badge/chip ── */
.chip {
  display: inline-block;
  padding: 6px 18px;
  border-radius: 20px;
  font-size: 20px;
  font-weight: 500;
  letter-spacing: 1px;
}

/* ── Card ── */
.card {
  border-radius: 12px;
  padding: 24px;
  background: rgba(15,23,42,0.8);
  backdrop-filter: blur(10px);
}
"""


# ── Helper ──────────────────────────────────────────────────────────

def _wrap(html_body: str, extra_css: str = "", bg_image_path: str = None) -> str:
    bg_style = ""
    if bg_image_path and os.path.exists(bg_image_path):
        with open(bg_image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        bg_style = f"""
body {{
  background: url('data:image/png;base64,{b64}') center/cover no-repeat;
}}
body::before {{
  background: rgba(0,0,0,0.55);
}}
"""
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>{_SHARED_CSS}{bg_style}{extra_css}</style>
</head><body>{html_body}</body></html>"""


def _accent_bg(color: str, opacity: float = 0.15) -> str:
    return color + hex(int(opacity * 255))[2:].zfill(2)


# ── 1. Title Slide ─────────────────────────────────────────────────

def render_title_slide(section: dict) -> str:
    os_screen = section.get("on_screen", {})
    color = section.get("accent_color", "#00d4ff")
    title = _html.escape(os_screen.get("title", ""))
    subtitle = _html.escape(os_screen.get("subtitle", ""))
    desc = _html.escape(os_screen.get("description", ""))
    english = _html.escape(os_screen.get("english", ""))
    top_label = _html.escape(os_screen.get("top_label", ""))

    return _wrap(f"""
    <div class="corner-deco tl"></div><div class="corner-deco tr"></div>
    <div class="corner-deco bl"></div><div class="corner-deco br"></div>
    <div class="container" style="justify-content: flex-end; align-items: center; text-align: center; padding-bottom: 80px;">
      <div style="font-size: 32px; color: rgba(255,255,255,0.8); letter-spacing: 4px; margin-bottom: 40px; font-weight: 500;">{top_label}</div>
      <div style="font-size: 82px; font-weight: 900; color: {color}; margin-bottom: 20px; letter-spacing: 3px;" class="glow-cyan">{title}</div>
      <div style="font-size: 46px; font-weight: 700; color: rgba(255,255,255,0.95); margin-bottom: 16px;">{subtitle}</div>
      <div style="font-size: 30px; color: rgba(255,255,255,0.7); margin-bottom: 20px;">{desc}</div>
      <div style="font-size: 22px; color: rgba(255,255,255,0.5); letter-spacing: 2px; font-style: italic;">{english}</div>
    </div>
    """, f"""
    .container {{ justify-content: flex-end; align-items: center; text-align: center; padding-bottom: 80px; }}
    """)


# ── 2. Question Slide ──────────────────────────────────────────────

def render_question_slide(section: dict) -> str:
    os_screen = section.get("on_screen", {})
    color = section.get("accent_color", "#00ff88")
    title = _html.escape(os_screen.get("title", ""))

    return _wrap(f"""
    <div class="corner-deco tl"></div><div class="corner-deco tr"></div>
    <div class="corner-deco bl"></div><div class="corner-deco br"></div>
    <div class="container" style="justify-content: center; align-items: center;">
      <div style="font-size: 58px; font-weight: 900; color: #fff; margin-bottom: 60px; text-align: center; max-width: 1400px; line-height: 1.4;">{title}</div>
      <div style="display: flex; gap: 120px; align-items: center; justify-content: center;">
        <div style="text-align: center;">
          <div style="font-size: 180px; color: {color}; line-height: 1;" class="glow-green">✓</div>
        </div>
        <div style="font-size: 100px; color: rgba(255,255,255,0.15);">⚡</div>
        <div style="text-align: center;">
          <div style="font-size: 180px; color: #ff8800; line-height: 1;" class="glow-orange">?</div>
        </div>
      </div>
    </div>
    <div class="subtitle-bar">{_html.escape(section.get('text', ''))}</div>
    """)


# ── 3. Problem / Gap Reveal Slide ──────────────────────────────────

def render_problem_slide(section: dict) -> str:
    os_screen = section.get("on_screen", {})
    color = section.get("accent_color", "#00d4ff")
    title = _html.escape(os_screen.get("title", ""))
    labels_top = os_screen.get("labels_top", [])
    labels_bottom = os_screen.get("labels_bottom", [])

    top_html = "".join(f'<div style="padding:10px 24px; border:1px solid rgba(0,212,255,0.3); border-radius:8px; font-size:24px; color:{color};">{_html.escape(l)}</div>' for l in labels_top)
    bot_html = "".join(f'<div style="padding:10px 24px; border:1px solid rgba(168,85,247,0.3); border-radius:8px; font-size:24px; color:#a855f7;">{_html.escape(l)}</div>' for l in labels_bottom)

    return _wrap(f"""
    <div class="corner-deco tl"></div><div class="corner-deco tr"></div>
    <div class="corner-deco bl"></div><div class="corner-deco br"></div>
    <div class="container" style="justify-content: center; align-items: center;">
      <div style="font-size: 54px; font-weight: 900; color: #fff; margin-bottom: 50px; text-align: center; line-height: 1.4;">{title}</div>
      <div style="display: flex; gap: 40px; margin-bottom: 40px; justify-content: center;">{top_html}</div>
      <div style="width: 600px; height: 2px; background: linear-gradient(90deg, transparent, {color}, transparent); margin: 20px auto;"></div>
      <div style="display: flex; gap: 24px; justify-content: center;">{bot_html}</div>
    </div>
    <div class="subtitle-bar">{_html.escape(section.get('text', ''))}</div>
    """)


# ── 4. Method / Transfer Diagram Slide ─────────────────────────────

def render_method_slide(section: dict) -> str:
    os_screen = section.get("on_screen", {})
    color = section.get("accent_color", "#00d4ff")
    title = _html.escape(os_screen.get("title", ""))
    flow = os_screen.get("flow", [])

    flow_html = ""
    for i, item in enumerate(flow):
        flow_html += f'<div style="padding:16px 32px; background:rgba(0,212,255,0.1); border:1px solid rgba(0,212,255,0.3); border-radius:12px; font-size:26px; color:{color};">{_html.escape(item)}</div>'
        if i < len(flow) - 1:
            flow_html += f'<div style="font-size:48px; color:{color}; display:flex; align-items:center;">→</div>'

    return _wrap(f"""
    <div class="corner-deco tl"></div><div class="corner-deco tr"></div>
    <div class="corner-deco bl"></div><div class="corner-deco br"></div>
    <div class="container" style="justify-content: center; align-items: center;">
      <div style="font-size: 54px; font-weight: 900; color: #fff; margin-bottom: 60px; text-align: center;">{title}</div>
      <div style="display: flex; gap: 24px; align-items: center; justify-content: center;">{flow_html}</div>
    </div>
    <div class="subtitle-bar">{_html.escape(section.get('text', ''))}</div>
    """)


# ── 5. Overview / Four Quadrants Slide ─────────────────────────────

def render_overview_slide(section: dict) -> str:
    os_screen = section.get("on_screen", {})
    title = _html.escape(os_screen.get("title", ""))
    center = _html.escape(os_screen.get("center", "M³Eval"))
    quads = os_screen.get("quadrants", [])
    colors = ["#00ff88", "#00d4ff", "#ff00ff", "#ff8800"]

    quad_html = ""
    for i, q in enumerate(quads[:4]):
        c = colors[i]
        quad_html += f"""
        <div style="flex:1; padding:28px; border-radius:12px; border:1px solid {c}33; background:{c}08;">
          <div style="font-size:22px; color:{c}; font-weight:700; margin-bottom:4px;">{_html.escape(q.get('id',''))}. {_html.escape(q.get('title',''))}</div>
          <div style="font-size:18px; color:rgba(255,255,255,0.5); margin-bottom:6px;">{_html.escape(q.get('en',''))}</div>
          <div style="font-size:20px; color:rgba(255,255,255,0.7);">{_html.escape(q.get('desc',''))}</div>
        </div>"""

    return _wrap(f"""
    <div class="corner-deco tl"></div><div class="corner-deco tr"></div>
    <div class="corner-deco bl"></div><div class="corner-deco br"></div>
    <div class="container" style="justify-content: center; align-items: center;">
      <div style="font-size: 54px; font-weight: 900; color: #fff; margin-bottom: 40px; text-align: center;">{title}</div>
      <div style="position:relative; width:800px; height:800px;">
        <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:160px; height:160px; border-radius:50%; border:2px solid rgba(0,212,255,0.3); display:flex; align-items:center; justify-content:center; font-size:36px; font-weight:900; color:{colors[0]}; background:rgba(0,212,255,0.05);">{center}</div>
        <div style="position:absolute; top:0; left:0; right:50%; bottom:50%; display:flex; align-items:center; justify-content:center;">{quad_html.split('</div>')[0] if len(quads)>0 else ''}</div>
      </div>
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:24px; width:100%; max-width:1400px; margin-top:20px;">{quad_html}</div>
    </div>
    <div class="subtitle-bar">{_html.escape(section.get('text', ''))}</div>
    """)


# ── 6. Test Intro Slide ────────────────────────────────────────────

def render_test_intro_slide(section: dict) -> str:
    os_screen = section.get("on_screen", {})
    color = section.get("accent_color", "#00ff88")
    title = _html.escape(os_screen.get("title", ""))

    # Build visual content based on sub_type
    sub_type = section.get("sub_type", "")
    visual_html = ""

    if sub_type == "divided_attention":
        left_label = _html.escape(os_screen.get("left_label", "左边画面"))
        right_label = _html.escape(os_screen.get("right_label", "右边画面"))
        visual_html = f"""
        <div style="display:flex; gap:40px; justify-content:center; margin-top:30px;">
          <div style="flex:1; max-width:600px; padding:40px; border-radius:16px; border:1px solid {color}44; background:{color}08; text-align:center;">
            <div style="font-size:120px; margin-bottom:16px;">🧑‍🍳</div>
            <div style="font-size:32px; font-weight:700; color:{color};">{left_label}</div>
          </div>
          <div style="display:flex; align-items:center; font-size:64px; color:rgba(255,255,255,0.2);">⚡</div>
          <div style="flex:1; max-width:600px; padding:40px; border-radius:16px; border:1px solid {color}44; background:{color}08; text-align:center;">
            <div style="font-size:120px; margin-bottom:16px;">🧑‍🍳</div>
            <div style="font-size:32px; font-weight:700; color:{color};">{right_label}</div>
          </div>
        </div>"""
    elif sub_type == "memory_interference":
        retro = _html.escape(os_screen.get("retroactive", ""))
        pro = _html.escape(os_screen.get("proactive", ""))
        visual_html = f"""
        <div style="display:flex; flex-direction:column; gap:30px; margin-top:30px; padding:0 100px;">
          <div style="display:flex; align-items:center; gap:20px; padding:24px 32px; border-radius:12px; border:1px solid {color}33; background:{color}08;">
            <div style="font-size:22px; color:{color}; font-weight:700; min-width:200px;">倒摄干扰 (Retroactive)</div>
            <div style="font-size:22px; color:rgba(255,255,255,0.8);">[视频A] → [相似视频B] → 提问视频A</div>
          </div>
          <div style="display:flex; align-items:center; gap:20px; padding:24px 32px; border-radius:12px; border:1px solid {color}33; background:{color}08;">
            <div style="font-size:22px; color:{color}; font-weight:700; min-width:200px;">前摄干扰 (Proactive)</div>
            <div style="font-size:22px; color:rgba(255,255,255,0.8);">[视频A] → [相似视频B] → 提问视频B</div>
          </div>
        </div>"""
    elif sub_type == "interleaved_events":
        visual_html = f"""
        <div style="display:flex; gap:60px; justify-content:center; align-items:center; margin-top:30px;">
          <div style="text-align:center;">
            <div style="font-size:28px; color:#ff00ff; font-weight:700; margin-bottom:8px;">案情A</div>
            <div style="display:flex; gap:8px;">
              <div style="width:80px; height:50px; border-radius:4px; background:rgba(255,0,255,0.2); border:1px solid rgba(255,0,255,0.4);"></div>
              <div style="width:80px; height:50px; border-radius:4px; background:rgba(0,212,255,0.2); border:1px solid rgba(0,212,255,0.4);"></div>
              <div style="width:80px; height:50px; border-radius:4px; background:rgba(255,0,255,0.2); border:1px solid rgba(255,0,255,0.4);"></div>
            </div>
          </div>
          <div style="font-size:48px; color:rgba(255,255,255,0.3);">⟷</div>
          <div style="text-align:center;">
            <div style="font-size:28px; color:#00d4ff; font-weight:700; margin-bottom:8px;">案情B</div>
            <div style="display:flex; gap:8px;">
              <div style="width:80px; height:50px; border-radius:4px; background:rgba(0,212,255,0.2); border:1px solid rgba(0,212,255,0.4);"></div>
              <div style="width:80px; height:50px; border-radius:4px; background:rgba(255,0,255,0.2); border:1px solid rgba(255,0,255,0.4);"></div>
              <div style="width:80px; height:50px; border-radius:4px; background:rgba(0,212,255,0.2); border:1px solid rgba(0,212,255,0.4);"></div>
            </div>
          </div>
        </div>"""
    elif sub_type == "nback_test":
        seq = os_screen.get("sequence", [])
        visual_html = f"""
        <div style="display:flex; gap:24px; justify-content:center; align-items:center; margin-top:40px;">
          <div style="font-size:24px; color:rgba(255,255,255,0.5);">N步之前</div>
          {"".join(f'<div style="width:120px; height:120px; border-radius:12px; border:2px solid {color}55; background:{color}11; display:flex; align-items:center; justify-content:center; font-size:36px; font-weight:700; color:{color};">{_html.escape(s)}</div>' for s in seq)}
        </div>"""

    return _wrap(f"""
    <div class="corner-deco tl"></div><div class="corner-deco tr"></div>
    <div class="corner-deco bl"></div><div class="corner-deco br"></div>
    <div class="container" style="justify-content: flex-start; padding-top: 80px;">
      <div style="font-size: 54px; font-weight: 900; color: #fff; margin-bottom: 20px; text-align: center;">{title}</div>
      <div style="width: 200px; height: 3px; background: {color}; margin: 0 auto 20px;"></div>
      {visual_html}
    </div>
    <div class="subtitle-bar">{_html.escape(section.get('text', ''))}</div>
    """)


# ── 7. Data Result (Bar Chart) Slide ───────────────────────────────

def render_data_result_slide(section: dict, chart_path: str = None) -> str:
    os_screen = section.get("on_screen", {})
    color = section.get("accent_color", "#00ff88")
    title = _html.escape(os_screen.get("title", ""))
    conclusion = _html.escape(os_screen.get("conclusion", ""))
    root_cause = _html.escape(os_screen.get("root_cause", ""))

    chart_img = ""
    if chart_path and os.path.exists(chart_path):
        with open(chart_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        chart_img = f'<img src="data:image/png;base64,{b64}" style="max-height:500px;">'

    return _wrap(f"""
    <div class="corner-deco tl"></div><div class="corner-deco tr"></div>
    <div class="corner-deco bl"></div><div class="corner-deco br"></div>
    <div class="container" style="justify-content: flex-start; padding-top: 60px;">
      <div style="font-size: 50px; font-weight: 900; color: {color}; margin-bottom: 30px; text-align: center;" class="glow-green">{title}</div>
      <div style="display: flex; gap: 40px; align-items: flex-start;">
        <div style="flex: 1.2; display: flex; justify-content: center;">{chart_img}</div>
        <div style="flex: 0.8; padding: 30px; border-radius: 16px; border: 1px solid {color}33; background: {color}08;">
          <div style="font-size: 24px; color: rgba(255,255,255,0.9); margin-bottom: 16px; line-height: 1.6;">{conclusion}</div>
          <div style="font-size: 22px; color: {color}; line-height: 1.6; font-weight: 500;">{root_cause}</div>
        </div>
      </div>
    </div>
    """)


# ── 8. Comparison (Balance Scale) Slide ────────────────────────────

def render_comparison_slide(section: dict) -> str:
    os_screen = section.get("on_screen", {})
    color = section.get("accent_color", "#00d4ff")
    title = _html.escape(os_screen.get("title", ""))
    human = os_screen.get("human_side", {})
    ai = os_screen.get("ai_side", {})
    insight = _html.escape(os_screen.get("insight", ""))

    return _wrap(f"""
    <div class="corner-deco tl"></div><div class="corner-deco tr"></div>
    <div class="corner-deco bl"></div><div class="corner-deco br"></div>
    <div class="container" style="justify-content: flex-start; padding-top: 60px;">
      <div style="font-size: 50px; font-weight: 900; color: {color}; margin-bottom: 40px; text-align: center;">{title}</div>
      <div style="display: flex; gap: 60px; justify-content: center; margin-bottom: 40px;">
        <div style="flex: 1; max-width: 700px; text-align: center;">
          <div style="font-size: 36px; font-weight: 700; color: #00ff88; margin-bottom: 20px;">{_html.escape(human.get('label',''))}</div>
          <div style="display: flex; justify-content: space-around; align-items: center; padding: 30px; border-radius: 16px; border: 1px solid rgba(0,255,136,0.2); background: rgba(0,255,136,0.05);">
            <div style="font-size: 22px; color: rgba(255,255,255,0.8);">{_html.escape(human.get('left',''))}</div>
            <div style="font-size: 60px;">⚖️</div>
            <div style="font-size: 22px; color: rgba(255,255,255,0.8);">{_html.escape(human.get('right',''))}</div>
          </div>
          <div style="font-size: 22px; color: #00ff88; margin-top: 12px; font-weight: 600;">{_html.escape(human.get('balance',''))}</div>
        </div>
        <div style="flex: 1; max-width: 700px; text-align: center;">
          <div style="font-size: 36px; font-weight: 700; color: #ff4444; margin-bottom: 20px;">{_html.escape(ai.get('label',''))}</div>
          <div style="display: flex; justify-content: space-around; align-items: center; padding: 30px; border-radius: 16px; border: 1px solid rgba(255,68,68,0.2); background: rgba(255,68,68,0.05);">
            <div style="font-size: 22px; color: rgba(255,255,255,0.8);">{_html.escape(ai.get('left',''))}</div>
            <div style="font-size: 60px;">⚖️</div>
            <div style="font-size: 22px; color: rgba(255,255,255,0.8);">{_html.escape(ai.get('right',''))}</div>
          </div>
          <div style="font-size: 22px; color: #ff4444; margin-top: 12px; font-weight: 600;">{_html.escape(ai.get('balance',''))}</div>
        </div>
      </div>
      <div style="padding: 24px 40px; border-radius: 12px; border: 1px solid {color}33; background: {color}08; max-width: 1400px; margin: 0 auto;">
        <div style="font-size: 24px; color: rgba(255,255,255,0.9); line-height: 1.7;">{insight}</div>
      </div>
    </div>
    """)


# ── 9. Chart Result Slide ──────────────────────────────────────────

def render_chart_result_slide(section: dict, chart_path: str = None) -> str:
    os_screen = section.get("on_screen", {})
    color = section.get("accent_color", "#00ff88")
    title = _html.escape(os_screen.get("title", ""))
    insight = _html.escape(os_screen.get("insight", ""))
    findings = os_screen.get("findings", [])

    chart_img = ""
    if chart_path and os.path.exists(chart_path):
        with open(chart_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        chart_img = f'<img src="data:image/png;base64,{b64}" style="max-height:550px;">'

    findings_html = ""
    if findings:
        findings_html = '<div style="margin-top: 16px;">' + "".join(
            f'<div style="font-size:20px; color:rgba(255,255,255,0.8); margin-bottom:6px;">• {_html.escape(f)}</div>'
            for f in findings
        ) + '</div>'

    return _wrap(f"""
    <div class="corner-deco tl"></div><div class="corner-deco tr"></div>
    <div class="corner-deco bl"></div><div class="corner-deco br"></div>
    <div class="container" style="justify-content: flex-start; padding-top: 50px;">
      <div style="font-size: 48px; font-weight: 900; color: {color}; margin-bottom: 24px; text-align: center;">{title}</div>
      <div style="display: flex; gap: 40px; align-items: flex-start;">
        <div style="flex: 1.3; display: flex; justify-content: center;">{chart_img}</div>
        <div style="flex: 0.7; padding: 28px; border-radius: 16px; border: 1px solid {color}33; background: {color}08;">
          <div style="font-size: 22px; color: rgba(255,255,255,0.9); line-height: 1.7;">{insight}</div>
          {findings_html}
        </div>
      </div>
    </div>
    """)


# ── 10. Summary Matrix Slide ───────────────────────────────────────

def render_summary_slide(section: dict) -> str:
    os_screen = section.get("on_screen", {})
    color = section.get("accent_color", "#a855f7")
    title = _html.escape(os_screen.get("title", ""))
    rows = os_screen.get("rows", [])

    rows_html = ""
    for r in rows:
        rows_html += f"""
        <tr>
          <td style="padding:18px 24px; font-size:24px; font-weight:700; color:{color}; border-bottom:1px solid rgba(255,255,255,0.1);">{_html.escape(r.get('dim',''))}</td>
          <td style="padding:18px 24px; font-size:22px; color:{r.get('human_color','#00ff88')}; border-bottom:1px solid rgba(255,255,255,0.1);">{_html.escape(r.get('human',''))}</td>
          <td style="padding:18px 24px; font-size:22px; color:{r.get('ai_color','#ff4444')}; border-bottom:1px solid rgba(255,255,255,0.1);">{_html.escape(r.get('ai',''))}</td>
        </tr>"""

    return _wrap(f"""
    <div class="corner-deco tl"></div><div class="corner-deco tr"></div>
    <div class="corner-deco bl"></div><div class="corner-deco br"></div>
    <div class="container" style="justify-content: center; align-items: center;">
      <div style="font-size: 50px; font-weight: 900; color: {color}; margin-bottom: 40px; text-align: center;" class="glow-purple">{title}</div>
      <table style="width: 100%; max-width: 1500px; border-collapse: collapse;">
        <thead>
          <tr>
            <th style="padding:16px 24px; font-size:26px; color:rgba(255,255,255,0.5); text-align:left; border-bottom:2px solid rgba(255,255,255,0.15);"></th>
            <th style="padding:16px 24px; font-size:26px; color:#00ff88; text-align:left; border-bottom:2px solid rgba(255,255,255,0.15);">人类 (Human)</th>
            <th style="padding:16px 24px; font-size:26px; color:#ff4444; text-align:left; border-bottom:2px solid rgba(255,255,255,0.15);">AI</th>
          </tr>
        </thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
    """)


# ── 11. Ranking Slide ──────────────────────────────────────────────

def render_ranking_slide(section: dict) -> str:
    os_screen = section.get("on_screen", {})
    color = section.get("accent_color", "#00d4ff")
    title = _html.escape(os_screen.get("title", ""))
    baseline = _html.escape(os_screen.get("baseline", ""))
    tiers = os_screen.get("tiers", [])

    max_score = 100
    tiers_html = ""
    for tier in tiers:
        tier_name = _html.escape(tier.get("tier", ""))
        models_html = ""
        for m in tier.get("models", []):
            name = _html.escape(m.get("name", ""))
            score = m.get("score", 0)
            mc = m.get("color", color)
            pct = min(score / max_score * 100, 100)
            models_html += f"""
            <div style="margin-bottom: 14px;">
              <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                <span style="font-size:24px; color:rgba(255,255,255,0.9);">{name}</span>
                <span style="font-size:24px; font-weight:700; color:{mc};">{score}</span>
              </div>
              <div style="width:100%; height:28px; background:rgba(255,255,255,0.05); border-radius:14px; overflow:hidden;">
                <div style="width:{pct}%; height:100%; background:linear-gradient(90deg, {mc}, {mc}aa); border-radius:14px; box-shadow: 0 0 12px {mc}44;"></div>
              </div>
            </div>"""
        tiers_html += f"""
        <div style="margin-bottom: 28px;">
          <div style="font-size: 22px; color: {color}; font-weight: 700; margin-bottom: 14px; padding: 8px 16px; border-left: 3px solid {color}; background: {color}08;">{tier_name}</div>
          {models_html}
        </div>"""

    return _wrap(f"""
    <div class="corner-deco tl"></div><div class="corner-deco tr"></div>
    <div class="corner-deco bl"></div><div class="corner-deco br"></div>
    <div class="container" style="justify-content: flex-start; padding-top: 50px;">
      <div style="font-size: 50px; font-weight: 900; color: {color}; margin-bottom: 12px; text-align: center;">{title}</div>
      <div style="text-align: right; font-size: 20px; color: rgba(255,255,255,0.4); margin-bottom: 20px; padding-right: 40px;">{baseline}</div>
      <div style="max-width: 1200px; margin: 0 auto; width: 100%;">{tiers_html}</div>
    </div>
    """)


# ── 12. Future Directions Slide ────────────────────────────────────

def render_future_slide(section: dict) -> str:
    os_screen = section.get("on_screen", {})
    color = section.get("accent_color", "#a855f7")
    title = _html.escape(os_screen.get("title", ""))
    dirs = os_screen.get("directions", [])

    dirs_html = ""
    for d in dirs:
        dc = d.get("color", color)
        dirs_html += f"""
        <div style="flex:1; padding:30px; border-radius:16px; border:1px solid {dc}44; background:{dc}08; text-align:center;">
          <div style="font-size:28px; font-weight:700; color:{dc}; margin-bottom:8px;">{_html.escape(d.get('title',''))}</div>
          <div style="font-size:20px; color:rgba(255,255,255,0.5); margin-bottom:12px; font-style:italic;">{_html.escape(d.get('en',''))}</div>
          <div style="font-size:22px; color:rgba(255,255,255,0.8); line-height:1.6;">{_html.escape(d.get('desc',''))}</div>
        </div>"""

    return _wrap(f"""
    <div class="corner-deco tl"></div><div class="corner-deco tr"></div>
    <div class="corner-deco bl"></div><div class="corner-deco br"></div>
    <div class="container" style="justify-content: center; align-items: center;">
      <div style="font-size: 50px; font-weight: 900; color: {color}; margin-bottom: 50px; text-align: center;" class="glow-purple">{title}</div>
      <div style="display: flex; gap: 30px; width: 100%; max-width: 1600px;">{dirs_html}</div>
    </div>
    """)


# ── 13. Takeaway Cards Slide ───────────────────────────────────────

def render_takeaway_slide(section: dict) -> str:
    os_screen = section.get("on_screen", {})
    color = section.get("accent_color", "#00d4ff")
    title = _html.escape(os_screen.get("title", ""))
    cards = os_screen.get("cards", [])

    cards_html = ""
    for c in cards:
        cc = c.get("color", color)
        cards_html += f"""
        <div style="flex:1; padding:36px; border-radius:16px; border:1px solid {cc}44; background:linear-gradient(180deg, {cc}11, transparent);">
          <div style="font-size:30px; font-weight:700; color:{cc}; margin-bottom:16px; line-height:1.4;">{_html.escape(c.get('title',''))}</div>
          <div style="font-size:22px; color:rgba(255,255,255,0.8); line-height:1.7;">{_html.escape(c.get('desc',''))}</div>
        </div>"""

    return _wrap(f"""
    <div class="corner-deco tl"></div><div class="corner-deco tr"></div>
    <div class="corner-deco bl"></div><div class="corner-deco br"></div>
    <div class="container" style="justify-content: center; align-items: center;">
      <div style="font-size: 50px; font-weight: 900; color: #fff; margin-bottom: 50px; text-align: center;">{title}</div>
      <div style="display: flex; gap: 30px; width: 100%; max-width: 1600px;">{cards_html}</div>
    </div>
    """)


# ── 14. Ending Slide ───────────────────────────────────────────────

def render_ending_slide(section: dict) -> str:
    os_screen = section.get("on_screen", {})
    color = section.get("accent_color", "#00d4ff")
    title = _html.escape(os_screen.get("title", ""))
    subtitle = _html.escape(os_screen.get("subtitle", ""))

    return _wrap(f"""
    <div class="corner-deco tl"></div><div class="corner-deco tr"></div>
    <div class="corner-deco bl"></div><div class="corner-deco br"></div>
    <div class="container" style="justify-content: center; align-items: center; text-align: center;">
      <div style="font-size: 160px; margin-bottom: 40px; opacity: 0.3;">🧠</div>
      <div style="font-size: 64px; font-weight: 900; color: {color}; margin-bottom: 30px; line-height: 1.4;" class="glow-cyan">{title}</div>
      <div class="accent-line" style="background: {color}; margin: 0 auto 30px;"></div>
      <div style="font-size: 28px; color: rgba(255,255,255,0.6); max-width: 1200px; line-height: 1.8;">{subtitle}</div>
    </div>
    """)


# ── Dispatcher ──────────────────────────────────────────────────────

_TEMPLATE_MAP = {
    "title": render_title_slide,
    "question": render_question_slide,
    "problem": render_problem_slide,
    "method": render_method_slide,
    "overview": render_overview_slide,
    "test_intro": render_test_intro_slide,
    "data_result": render_data_result_slide,
    "comparison": render_comparison_slide,
    "chart_result": render_chart_result_slide,
    "summary": render_summary_slide,
    "ranking": render_ranking_slide,
    "future": render_future_slide,
    "takeaway": render_takeaway_slide,
    "ending": render_ending_slide,
}


def render_slide(section: dict, chart_path: str = None, bg_image_path: str = None) -> str:
    """Render a slide HTML from a section dict. Returns self-contained HTML string.

    If bg_image_path is provided and is a complete slide image (contains text),
    render it directly without overlay. Otherwise use template with text overlay.
    """
    slide_type = section.get("type", "detail")

    # If we have a complete slide image, render it directly (no text overlay)
    if bg_image_path and os.path.exists(bg_image_path):
        with open(bg_image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  width: 1920px; height: 1080px; overflow: hidden;
  background: url('data:image/png;base64,{b64}') center/contain no-repeat #0a0a0f;
}}
</style>
</head><body></body></html>"""

    # Fallback to template-based rendering
    renderer = _TEMPLATE_MAP.get(slide_type, render_problem_slide)
    if slide_type in ("data_result", "chart_result"):
        return renderer(section, chart_path=chart_path)
    return renderer(section)
