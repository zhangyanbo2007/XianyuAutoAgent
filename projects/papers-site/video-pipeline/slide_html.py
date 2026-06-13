"""HTML-based slide generation with CSS art, charts, and professional layouts."""

import os
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from pathlib import Path

# --- Config ---
OUTPUT_DIR = Path(__file__).parent / "output" / "slides_v8"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Chinese font
def _get_font():
    for p in [os.path.expanduser("~/.local/share/fonts/NotoSansCJKsc-Regular.otf"),
              "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc"]:
        if os.path.exists(p):
            return fm.FontProperties(fname=p)
    return fm.FontProperties()

FONT = _get_font()

# --- CSS Templates ---
DARK_BG = "#0a0a0f"
CARD_BG = "#111827"
ACCENT = "#38bdf8"
PINK = "#f472b6"
GREEN = "#4ade80"
PURPLE = "#a78bfa"
ORANGE = "#fb923c"
RED = "#f87171"
TEXT = "#e2e8f0"
MUTED = "#94a3b8"

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700;900&display=swap');
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  width: 1920px; height: 1080px;
  background: {bg};
  font-family: 'Noto Sans SC', sans-serif;
  color: {text};
  overflow: hidden;
  position: relative;
}}
.bg-image {{
  position: absolute; inset: 0;
  background-size: cover; background-position: center;
  opacity: 0.6; filter: blur(1px);
}}
.bg-overlay {{
  position: absolute; inset: 0;
  background: linear-gradient(135deg, rgba(10,10,15,0.95) 0%, rgba(10,10,15,0.7) 50%, rgba(10,10,15,0.95) 100%);
}}
.header {{
  position: absolute; top: 0; left: 0; right: 0;
  height: 4px; background: linear-gradient(90deg, {accent}, {pink}, {purple});
  z-index: 10;
}}
.label {{
  position: absolute; top: 40px; left: 60px;
  background: {accent}; color: #000;
  padding: 8px 20px; border-radius: 8px;
  font-size: 20px; font-weight: 700;
}}
.num {{
  position: absolute; top: 30px; right: 60px;
  font-size: 140px; font-weight: 900;
  color: rgba(56,189,248,0.08);
}}
.title {{
  position: absolute; top: 100px; left: 60px; right: 60px;
  font-size: 48px; font-weight: 900;
  line-height: 1.3;
}}
.content {{
  position: absolute; top: 200px; left: 60px; right: 60px; bottom: 100px;
  display: flex; gap: 40px;
}}
.left {{ flex: 1; display: flex; flex-direction: column; justify-content: center; }}
.right {{ flex: 1; display: flex; align-items: center; justify-content: center; }}
.text-block {{
  background: rgba(17,24,39,0.6);
  border: 1px solid rgba(56,189,248,0.15);
  border-radius: 16px; padding: 30px;
  font-size: 36px; line-height: 1.6;
  font-weight: 700;
}}
.footer {{
  position: absolute; bottom: 30px; left: 60px; right: 60px;
  display: flex; justify-content: space-between; align-items: center;
  color: {muted}; font-size: 16px;
}}
.progress-bar {{
  position: absolute; bottom: 0; left: 0;
  height: 4px; background: {accent};
  transition: width 0.3s;
}}
.icon {{
  width: 80px; height: 80px;
  border-radius: 20px; display: flex;
  align-items: center; justify-content: center;
  font-size: 40px; margin-bottom: 20px;
}}
.grid {{ display: grid; gap: 16px; }}
.grid-2 {{ grid-template-columns: 1fr 1fr; }}
.grid-3 {{ grid-template-columns: 1fr 1fr 1fr; }}
.card {{
  background: rgba(17,24,39,0.6);
  border: 1px solid rgba(56,189,248,0.15);
  border-radius: 12px; padding: 20px;
}}
.card h3 {{ font-size: 20px; margin-bottom: 8px; color: {accent}; }}
.card p {{ font-size: 18px; color: {muted}; }}
.chart-container {{ width: 100%; height: 100%; }}
</style>
</head>
<body>
{body}
</body>
</html>"""


def render_title_slide(video_title, paper_title, theme, index, total, bg_image_b64=None):
    """Render title slide with optional AI background image."""
    bg_html = ""
    if bg_image_b64:
        bg_html = f'<div class="bg-image" style="background-image:url(data:image/png;base64,{bg_image_b64})"></div><div class="bg-overlay"></div>'
    body = f"""
    {bg_html}
    <div class="header"></div>
    <div class="num">00</div>
    <div style="position:absolute;top:200px;left:60px;right:60px;text-align:center;z-index:5;">
      <div style="font-size:56px;font-weight:900;line-height:1.3;margin-bottom:30px;text-shadow:0 2px 20px rgba(0,0,0,0.8);">{video_title}</div>
      <div style="font-size:24px;color:{MUTED};margin-bottom:20px;">{paper_title[:80]}</div>
      <div style="display:inline-block;background:{ACCENT};color:#000;padding:8px 24px;border-radius:999px;font-size:18px;font-weight:700;">{theme}</div>
    </div>
    <div class="footer" style="z-index:5;">
      <span>DAST Papers · AI解读</span>
      <span>01 / {total:02d}</span>
    </div>
    <div class="progress-bar" style="width:{100/total:.1f}%"></div>
    """
    return HTML_TEMPLATE.format(bg=DARK_BG, text=TEXT, accent=ACCENT, pink=PINK, purple=PURPLE, muted=MUTED, body=body)


def render_question_slide(label, text, question, index, total):
    """Render question/introduction slide."""
    body = f"""
    <div class="header"></div>
    <div class="num">{index+1:02d}</div>
    <div class="label">{label}</div>
    <div class="title" style="top:120px;">{question}</div>
    <div class="content" style="top:240px;">
      <div class="left">
        <div class="text-block">{text}</div>
      </div>
      <div class="right">
        <div style="font-size:200px;color:rgba(56,189,248,0.1);">?</div>
      </div>
    </div>
    <div class="footer">
      <span>DAST Papers · AI解读</span>
      <span>{index+1:02d} / {total:02d}</span>
    </div>
    <div class="progress-bar" style="width:{(index+1)*100/total:.1f}%"></div>
    """
    return HTML_TEMPLATE.format(bg=DARK_BG, text=TEXT, accent=ACCENT, pink=PINK, purple=PURPLE, muted=MUTED, body=body)


def render_method_slide(label, text, index, total):
    """Render method slide with flow diagram."""
    body = f"""
    <div class="header"></div>
    <div class="num">{index+1:02d}</div>
    <div class="label">{label}</div>
    <div class="title" style="top:120px;">{label}</div>
    <div class="content" style="top:220px;">
      <div class="left">
        <div class="text-block">{text}</div>
      </div>
      <div class="right">
        <div style="display:flex;align-items:center;gap:20px;">
          <div style="width:120px;height:120px;border-radius:50%;background:rgba(56,189,248,0.15);display:flex;align-items:center;justify-content:center;font-size:48px;">📖</div>
          <div style="font-size:40px;color:{ACCENT};">→</div>
          <div style="width:120px;height:120px;border-radius:50%;background:rgba(244,114,182,0.15);display:flex;align-items:center;justify-content:center;font-size:48px;">🧠</div>
        </div>
      </div>
    </div>
    <div class="footer">
      <span>DAST Papers · AI解读</span>
      <span>{index+1:02d} / {total:02d}</span>
    </div>
    <div class="progress-bar" style="width:{(index+1)*100/total:.1f}%"></div>
    """
    return HTML_TEMPLATE.format(bg=DARK_BG, text=TEXT, accent=ACCENT, pink=PINK, purple=PURPLE, muted=MUTED, body=body)


def render_comparison_slide(label, left_title, right_title, left_items, right_items, index, total):
    """Render comparison slide."""
    left_html = "".join(f'<div style="padding:12px 16px;background:rgba(56,189,248,0.1);border-radius:8px;margin-bottom:8px;"><strong>{k}:</strong> {v}</div>' for k, v in left_items)
    right_html = "".join(f'<div style="padding:12px 16px;background:rgba(244,114,182,0.1);border-radius:8px;margin-bottom:8px;"><strong>{k}:</strong> {v}</div>' for k, v in right_items)
    body = f"""
    <div class="header"></div>
    <div class="num">{index+1:02d}</div>
    <div class="label">{label}</div>
    <div class="content" style="top:120px;">
      <div class="left" style="flex:1;">
        <div style="font-size:32px;font-weight:900;color:{ACCENT};margin-bottom:20px;">{left_title}</div>
        {left_html}
      </div>
      <div style="display:flex;align-items:center;font-size:60px;color:{MUTED};">VS</div>
      <div class="right" style="flex:1;">
        <div style="font-size:32px;font-weight:900;color:{PINK};margin-bottom:20px;">{right_title}</div>
        {right_html}
      </div>
    </div>
    <div class="footer">
      <span>DAST Papers · AI解读</span>
      <span>{index+1:02d} / {total:02d}</span>
    </div>
    <div class="progress-bar" style="width:{(index+1)*100/total:.1f}%"></div>
    """
    return HTML_TEMPLATE.format(bg=DARK_BG, text=TEXT, accent=ACCENT, pink=PINK, purple=PURPLE, muted=MUTED, body=body)


def render_chart_slide(label, chart_path, caption, index, total):
    """Render chart slide with embedded chart image."""
    import base64
    with open(chart_path, "rb") as f:
        chart_b64 = base64.b64encode(f.read()).decode()
    body = f"""
    <div class="header"></div>
    <div class="num">{index+1:02d}</div>
    <div class="label">{label}</div>
    <div class="content" style="top:120px;flex-direction:column;align-items:center;">
      <img src="data:image/png;base64,{chart_b64}" style="max-width:100%;max-height:75vh;border-radius:12px;" />
      <div style="margin-top:16px;font-size:20px;color:{MUTED};text-align:center;">{caption}</div>
    </div>
    <div class="footer">
      <span>DAST Papers · AI解读</span>
      <span>{index+1:02d} / {total:02d}</span>
    </div>
    <div class="progress-bar" style="width:{(index+1)*100/total:.1f}%"></div>
    """
    return HTML_TEMPLATE.format(bg=DARK_BG, text=TEXT, accent=ACCENT, pink=PINK, purple=PURPLE, muted=MUTED, body=body)


def render_ending_slide(video_title, key_points, index, total):
    """Render ending slide."""
    points_html = "".join(f'<div style="padding:14px 20px;background:rgba(56,189,248,0.08);border-left:3px solid {ACCENT};border-radius:0 8px 8px 0;margin-bottom:12px;font-size:22px;">{p}</div>' for p in key_points[:4])
    body = f"""
    <div class="header"></div>
    <div class="num">{index+1:02d}</div>
    <div class="content" style="top:100px;flex-direction:column;align-items:center;justify-content:center;">
      <div style="font-size:52px;font-weight:900;margin-bottom:40px;">核心发现</div>
      {points_html}
      <div style="margin-top:30px;font-size:20px;color:{ACCENT};">papers.dast.ai</div>
    </div>
    <div class="footer">
      <span>DAST Papers · AI解读</span>
      <span>{index+1:02d} / {total:02d}</span>
    </div>
    <div class="progress-bar" style="width:100%"></div>
    """
    return HTML_TEMPLATE.format(bg=DARK_BG, text=TEXT, accent=ACCENT, pink=PINK, purple=PURPLE, muted=MUTED, body=body)


def render_detail_slide(label, text, index, total):
    """Render detail/text slide."""
    body = f"""
    <div class="header"></div>
    <div class="num">{index+1:02d}</div>
    <div class="label">{label}</div>
    <div class="content" style="top:140px;">
      <div class="left" style="flex:1;">
        <div class="text-block" style="font-size:30px;">{text}</div>
      </div>
    </div>
    <div class="footer">
      <span>DAST Papers · AI解读</span>
      <span>{index+1:02d} / {total:02d}</span>
    </div>
    <div class="progress-bar" style="width:{(index+1)*100/total:.1f}%"></div>
    """
    return HTML_TEMPLATE.format(bg=DARK_BG, text=TEXT, accent=ACCENT, pink=PINK, purple=PURPLE, muted=MUTED, body=body)


# --- Chart Generation ---
def make_bar_chart(title, categories, values, colors, output_path):
    """Generate a matplotlib bar chart."""
    fig, ax = plt.subplots(figsize=(16, 9), facecolor=DARK_BG)
    ax.set_facecolor(CARD_BG)
    bars = ax.bar(categories, values, color=colors, width=0.6, edgecolor='none', zorder=3)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.02,
                f'{val:.1f}', ha='center', va='bottom', fontsize=20, fontweight='bold',
                color=TEXT, fontproperties=FONT)
    ax.set_title(title, fontsize=28, fontweight='bold', pad=20, color=TEXT, fontproperties=FONT)
    ax.set_xticklabels(categories, fontproperties=FONT, fontsize=16, color=TEXT)
    ax.tick_params(colors=TEXT)
    ax.grid(axis='y', alpha=0.2, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#334155')
    ax.spines['left'].set_color('#334155')
    ax.set_ylim(0, max(values) * 1.2)
    plt.tight_layout()
    fig.savefig(output_path, dpi=150, facecolor=DARK_BG, bbox_inches='tight')
    plt.close(fig)
    return output_path


def make_ranking_chart(title, models, scores, output_path):
    """Generate horizontal ranking chart."""
    fig, ax = plt.subplots(figsize=(16, 10), facecolor=DARK_BG)
    ax.set_facecolor(CARD_BG)
    colors = [ACCENT] * len(models)
    if len(models) > 0: colors[0] = "#fbbf24"
    if len(models) > 1: colors[1] = "#94a3b8"
    if len(models) > 2: colors[2] = "#fb923c"
    y = np.arange(len(models))
    bars = ax.barh(y, scores, color=colors, height=0.6, edgecolor='none', zorder=3)
    for bar, score in zip(bars, scores):
        ax.text(bar.get_width() + max(scores)*0.01, bar.get_y() + bar.get_height()/2,
                f'{score:.1f}', va='center', fontsize=18, fontweight='bold', color=TEXT, fontproperties=FONT)
    ax.set_yticks(y)
    ax.set_yticklabels(models, fontproperties=FONT, fontsize=18)
    ax.invert_yaxis()
    ax.set_title(title, fontsize=28, fontweight='bold', pad=20, color=TEXT, fontproperties=FONT)
    ax.tick_params(colors=TEXT)
    ax.grid(axis='x', alpha=0.2, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#334155')
    ax.spines['left'].set_color('#334155')
    ax.set_xlim(0, max(scores) * 1.15)
    plt.tight_layout()
    fig.savefig(output_path, dpi=150, facecolor=DARK_BG, bbox_inches='tight')
    plt.close(fig)
    return output_path


def make_grouped_bar(title, categories, groups, output_path):
    """Generate grouped bar chart."""
    fig, ax = plt.subplots(figsize=(16, 9), facecolor=DARK_BG)
    ax.set_facecolor(CARD_BG)
    x = np.arange(len(categories))
    n = len(groups)
    width = 0.8 / n
    color_list = [ACCENT, PINK, GREEN, PURPLE]
    for i, (name, values) in enumerate(groups.items()):
        offset = (i - n/2 + 0.5) * width
        bars = ax.bar(x + offset, values, width, label=name, color=color_list[i % len(color_list)], zorder=3)
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(max(v) for v in groups.values())*0.02,
                    f'{val:.1f}', ha='center', va='bottom', fontsize=12, color=TEXT, fontproperties=FONT)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontproperties=FONT, fontsize=14)
    ax.set_title(title, fontsize=28, fontweight='bold', pad=20, color=TEXT, fontproperties=FONT)
    ax.legend(prop=FONT, fontsize=14, facecolor=CARD_BG, edgecolor='#334155', labelcolor=TEXT)
    ax.tick_params(colors=TEXT)
    ax.grid(axis='y', alpha=0.2, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#334155')
    ax.spines['left'].set_color('#334155')
    plt.tight_layout()
    fig.savefig(output_path, dpi=150, facecolor=DARK_BG, bbox_inches='tight')
    plt.close(fig)
    return output_path


if __name__ == "__main__":
    # Test chart generation
    chart_dir = OUTPUT_DIR / "_charts"
    chart_dir.mkdir(exist_ok=True)
    make_bar_chart(
        "人类 vs AI 记忆准确率",
        ["人类", "GPT-5.4", "Qwen3.5", "InternVL3.5"],
        [90, 27, 35, 15],
        [GREEN, ACCENT, PINK, PURPLE],
        str(chart_dir / "test_bar.png"),
    )
    make_ranking_chart(
        "模型排行榜",
        ["GPT-5.4", "Gemini-3.1", "Qwen3.5-27B", "InternVL3.5-8B"],
        [75.4, 70.1, 55.4, 45.1],
        str(chart_dir / "test_ranking.png"),
    )
    print("Test charts generated")


def render_chart_slide_with_bg(label, chart_path, caption, index, total, bg_image_b64=None):
    """Render chart slide with embedded chart and optional AI background."""
    import base64
    with open(chart_path, "rb") as f:
        chart_b64 = base64.b64encode(f.read()).decode()
    bg_html = ""
    if bg_image_b64:
        bg_html = f'<div class="bg-image" style="background-image:url(data:image/png;base64,{bg_image_b64})"></div><div class="bg-overlay"></div>'
    body = f"""
    {bg_html}
    <div class="header"></div>
    <div class="num">{index+1:02d}</div>
    <div class="label">{label}</div>
    <div class="content" style="top:120px;flex-direction:column;align-items:center;z-index:5;">
      <img src="data:image/png;base64,{chart_b64}" style="max-width:100%;max-height:65vh;border-radius:12px;box-shadow:0 8px 32px rgba(0,0,0,0.4);" />
      <div style="margin-top:16px;font-size:20px;color:{MUTED};text-align:center;">{caption}</div>
    </div>
    <div class="footer" style="z-index:5;">
      <span>DAST Papers · AI解读</span>
      <span>{index+1:02d} / {total:02d}</span>
    </div>
    <div class="progress-bar" style="width:{(index+1)*100/total:.1f}%"></div>
    """
    return HTML_TEMPLATE.format(bg=DARK_BG, text=TEXT, accent=ACCENT, pink=PINK, purple=PURPLE, muted=MUTED, body=body)


def render_detail_slide_with_bg(label, text, index, total, bg_image_b64=None):
    """Render detail slide with optional AI background image."""
    bg_html = ""
    if bg_image_b64:
        bg_html = f'<div class="bg-image" style="background-image:url(data:image/png;base64,{bg_image_b64})"></div><div class="bg-overlay"></div>'
    body = f"""
    {bg_html}
    <div class="header"></div>
    <div class="num">{index+1:02d}</div>
    <div class="label">{label}</div>
    <div class="content" style="top:140px;z-index:5;">
      <div class="left" style="flex:1;">
        <div class="text-block" style="font-size:30px;">{text}</div>
      </div>
    </div>
    <div class="footer" style="z-index:5;">
      <span>DAST Papers · AI解读</span>
      <span>{index+1:02d} / {total:02d}</span>
    </div>
    <div class="progress-bar" style="width:{(index+1)*100/total:.1f}%"></div>
    """
    return HTML_TEMPLATE.format(bg=DARK_BG, text=TEXT, accent=ACCENT, pink=PINK, purple=PURPLE, muted=MUTED, body=body)
