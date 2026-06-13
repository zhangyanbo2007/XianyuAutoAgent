"""Generate slides as HTML with inline AI illustrations."""

import os
import json
from PIL import Image, ImageDraw, ImageFont
import subprocess
import uuid

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

VIDEO_W = 1920
VIDEO_H = 1080
FONT_PATH = os.path.expanduser("~/.local/share/fonts/NotoSansCJKsc-Regular.otf")

COLORS = {
    "bg": "#0a0a1a",
    "accent": "#38bdf8",
    "text": "#e2e8f0",
    "muted": "#94a3b8",
}

# Concept illustrations - small inline images for each section type
ILLUSTRATIONS = {
    "title": "🧠",  # Will use emoji as fallback
    "question": "❓",
    "method": "🔬",
    "chart": "📊",
    "comparison": "⚖️",
    "detail": "💡",
    "ending": "🎯",
}

# Section-specific descriptions for AI image generation
SECTION_AI_PROMPTS = {
    0: "A glowing neon brain made of light particles floating in dark space, half organic neural network with colorful synapses, half digital circuit board with microchips, neon blue and cyan glow, 4K",
    1: "A giant green checkmark on the left and a purple lightning bolt on the right, with a large neon question mark in the center, dark background, 4K",
    2: "An iceberg in dark ocean: above water a bright glowing AI camera eye, below water a hidden brain structure, bioluminescent blue glow, 4K",
    3: "A person watching holographic video screens, memory fragments floating around like glowing orbs, some clear, some fading, 4K",
    4: "A magnifying glass examining a glowing AI brain, surface illuminated but deeper layers dark, 4K",
    5: "A transformation: ancient book opens with golden particles flowing to a holographic AI brain, 4K",
    6: "A split brain: left organic with colorful neurons, right digital with circuits, bridge connecting them, 4K",
    7: "Five glowing circular gauges arranged in pentagon pattern, each different color, 4K",
    8: "A test chamber with holographic video screen, clock ticking, question marks floating, 4K",
    9: "Two holographic video screens side by side, interference waves between them, 4K",
    10: "Split screen: left organic brain with golden neurons, right digital processor with circuits, 4K",
    11: "Holographic bar chart showing dramatic drop from 85% to 35%, 4K",
    12: "3D holographic space map with grid sections and location markers, 4K",
    13: "Glowing timeline with events as bright nodes, time flowing left to right, 4K",
    14: "Two movie film strips flowing parallel, central AI brain processing both, 4K",
    15: "Comparison panel: happy green brain at 80%, confused red brain at 27%, 4K",
    16: "Abstract symbols floating in dark space, some sharp and clear, others fading, 4K",
    17: "Radar chart floating in dark space with five dimensions, 4K",
    18: "Brain with selective memory: some areas bright with objects, others dark, 4K",
    19: "Leaderboard hologram with ranked positions and glowing bars, 4K",
    20: "AI assistant in smart home, remembering user preferences as floating cards, 4K",
    21: "Medical diagnostic report for AI memory, test results as glowing cards, 4K",
    22: "Boundary wall: current scope illuminated, unexplored territory beyond, 4K",
    23: "Roadmap with three glowing paths leading forward, 4K",
    24: "Neural network architecture diagram with upgrade arrows, 4K",
    25: "Brain made of light particles assembling into complete form, 4K",
}


def get_font():
    return FONT_PATH if os.path.exists(FONT_PATH) else ""


def render_html_to_png(html_content, output_path):
    """Render HTML to PNG using playwright."""
    import uuid
    tmp_html = os.path.join(os.path.dirname(output_path), f"_{uuid.uuid4().hex}.html")
    with open(tmp_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    if HAS_PLAYWRIGHT:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context(viewport={"width": VIDEO_W, "height": VIDEO_H})
            page = context.new_page()
            page.goto(f"file://{os.path.abspath(tmp_html)}", wait_until="load")
            page.wait_for_timeout(500)
            page.screenshot(path=output_path)
            context.close()
            browser.close()
    else:
        _render_with_pil(html_content, output_path)

    if os.path.exists(tmp_html):
        os.remove(tmp_html)


def _render_with_pil(html_content, output_path):
    """Fallback PIL renderer."""
    import re
    text = re.sub(r'<[^>]+>', ' ', html_content)
    text = re.sub(r'\s+', ' ', text).strip()
    img = Image.new("RGB", (VIDEO_W, VIDEO_H), (10, 10, 26))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(FONT_PATH, 40)
    except:
        font = ImageFont.load_default()
    words = text[:200].split()
    y = 200
    line = ""
    for word in words:
        test = line + " " + word
        try:
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] > VIDEO_W - 200:
                draw.text((100, y), line.strip(), fill=(226, 232, 240), font=font)
                y += 60
                line = word
            else:
                line = test
        except:
            line += " " + word
    if line.strip():
        draw.text((100, y), line.strip(), fill=(226, 232, 240), font=font)
    img.save(output_path, "PNG")


def _get_illustration_html(section_id):
    """Get inline illustration HTML for a section."""
    prompt = SECTION_AI_PROMPTS.get(section_id, "")
    if not prompt:
        return ""

    # Generate small AI illustration
    try:
        from image_generator import generate_frame_image
        cache_dir = os.path.join(os.path.dirname(__file__), "output", "_ai_small")
        img_path = generate_frame_image(prompt, cache_dir, section_id, size="512*512")
        if img_path and os.path.exists(img_path):
            return f'<img src="file://{os.path.abspath(img_path)}" style="width:320px;height:320px;border-radius:16px;object-fit:cover;opacity:0.9;" />'
    except Exception as e:
        print(f"  ⚠ AI image failed for section {section_id}: {e}")

    return ""


def create_title_slide(video_title, paper_title, theme, output_path):
    """Create title slide with AI background illustration."""
    font_path = get_font()

    # Get AI background
    illustration_html = ""
    try:
        from image_generator import generate_frame_image
        cache_dir = os.path.join(os.path.dirname(__file__), "output", "_ai_bg")
        img_path = generate_frame_image(
            "A glowing neon brain made of light particles floating in dark space, half organic neural network with colorful synapses, half digital circuit board with microchips, neon blue and cyan glow, volumetric fog, particles, 4K ultra-detailed",
            cache_dir, 99, size="1024*576"
        )
        if img_path and os.path.exists(img_path):
            illustration_html = f'<img src="file://{os.path.abspath(img_path)}" style="position:absolute;top:0;left:0;width:100%;height:100%;object-fit:cover;z-index:0;opacity:0.7;" />'
    except:
        pass

    html = f"""<!DOCTYPE html>
<html><head><style>
@font-face {{ font-family: 'NotoSansSC'; src: url('file://{font_path}'); }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ width: {VIDEO_W}px; height: {VIDEO_H}px; background: {COLORS['bg']}; color: {COLORS['text']}; font-family: 'NotoSansSC', sans-serif; display: flex; align-items: center; justify-content: center; text-align: center; position: relative; }}
.text-wrap {{ z-index: 2; position: relative; background: rgba(10,10,26,0.7); border-radius: 20px; padding: 40px 60px; backdrop-filter: blur(10px); }}
.main-text {{ font-size: 52px; font-weight: 700; line-height: 1.4; max-width: 1200px; }}
.paper-name {{ font-size: 22px; color: {COLORS['muted']}; margin-top: 20px; }}
.bottom {{ position: absolute; bottom: 20px; right: 30px; color: #475569; font-size: 14px; z-index: 10; }}
</style></head><body>
{illustration_html}
<div class="text-wrap">
  <div class="main-text">{video_title}</div>
  <div class="paper-name">{paper_title}</div>
</div>
<div class="bottom">DAST Papers · AI解读</div>
</body></html>"""
    render_html_to_png(html, output_path)
    return output_path


def create_content_slide(label, text, section_id, output_path):
    """Create content slide with AI illustration as FULL-SCREEN background."""
    font_path = get_font()
    display_text = text[:150] + "..." if len(text) > 150 else text

    # Get AI illustration as full-screen background
    illustration_html = ""
    try:
        from image_generator import generate_frame_image
        cache_dir = os.path.join(os.path.dirname(__file__), "output", "_ai_bg")
        img_path = generate_frame_image(
            SECTION_AI_PROMPTS.get(section_id, "AI concept art, dark background, 4K"),
            cache_dir, section_id, size="1024*576"
        )
        if img_path and os.path.exists(img_path):
            illustration_html = f'<img src="file://{os.path.abspath(img_path)}" style="position:absolute;top:0;left:0;width:100%;height:100%;object-fit:cover;z-index:0;" />'
    except Exception as e:
        print(f"  ⚠ AI bg failed for section {section_id}: {e}")

    html = f"""<!DOCTYPE html>
<html><head><style>
@font-face {{ font-family: 'NotoSansSC'; src: url('file://{font_path}'); }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ width: {VIDEO_W}px; height: {VIDEO_H}px; background: {COLORS['bg']}; color: {COLORS['text']}; font-family: 'NotoSansSC', sans-serif; position: relative; overflow: hidden; }}
.header {{ position: absolute; top: 24px; left: 32px; z-index: 10; }}
.label {{ display: inline-block; background: {COLORS['accent']}; color: #0a0a1a; padding: 6px 16px; border-radius: 8px; font-size: 20px; font-weight: 700; }}
.section-num {{ position: absolute; top: 10px; right: 40px; font-size: 140px; font-weight: 900; color: rgba(56,189,248,0.08); line-height: 1; z-index: 10; }}
.content {{ position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; align-items: center; justify-content: center; z-index: 2; }}
.text-panel {{ background: rgba(10,10,26,0.85); border: 2px solid rgba(56,189,248,0.3); border-radius: 16px; padding: 32px 48px; max-width: 900px; backdrop-filter: blur(8px); }}
.main-text {{ font-size: 40px; font-weight: 700; line-height: 1.6; color: #f0f4f8; }}
.bottom {{ position: absolute; bottom: 20px; right: 30px; color: #475569; font-size: 14px; z-index: 10; }}
</style></head><body>
{illustration_html}
<div class="header"><span class="label">{label}</span></div>
<span class="section-num">#{section_id:02d}</span>
<div class="content">
  <div class="text-panel"><div class="main-text">{display_text}</div></div>
</div>
<div class="bottom">DAST Papers · AI解读</div>
</body></html>"""
    render_html_to_png(html, output_path)
    return output_path


def create_bar_chart_slide(title, categories, values, section_id, output_path):
    """Create bar chart slide with AI background illustration."""
    font_path = get_font()
    max_val = max(values) if values else 1
    chart_colors = ["#38bdf8", "#f472b6", "#4ade80", "#a78bfa", "#fb923c"]
    bars = ""
    for i, (cat, val) in enumerate(zip(categories, values)):
        h = int((val / max_val) * 350)
        c = chart_colors[i % len(chart_colors)]
        bars += f'<div style="display:flex;flex-direction:column;align-items:center;gap:12px;"><div style="font-size:28px;font-weight:900;">{val}%</div><div style="width:120px;height:{h}px;background:{c};border-radius:8px 8px 0 0;"></div><div style="font-size:18px;color:{COLORS["muted"]};text-align:center;max-width:140px;">{cat}</div></div>'

    # No AI background for chart slides - chart needs clean background
    illustration_html = ""

    html = f"""<!DOCTYPE html>
<html><head><style>
@font-face {{ font-family: 'NotoSansSC'; src: url('file://{font_path}'); }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ width: {VIDEO_W}px; height: {VIDEO_H}px; background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3e 50%, #0a0a1a 100%); color: {COLORS['text']}; font-family: 'NotoSansSC', sans-serif; position: relative; }}
.header {{ position: absolute; top: 24px; left: 32px; z-index: 10; }}
.label {{ display: inline-block; background: {COLORS['accent']}; color: #0a0a1a; padding: 6px 16px; border-radius: 8px; font-size: 20px; font-weight: 700; }}
.section-num {{ position: absolute; top: 10px; right: 40px; font-size: 140px; font-weight: 900; color: rgba(56,189,248,0.08); line-height: 1; }}
.content {{ position: absolute; top: 80px; left: 0; right: 0; bottom: 0; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 20px; }}
.title {{ font-size: 36px; font-weight: 700; margin-bottom: 30px; text-align: center; }}
.chart {{ display: flex; align-items: flex-end; gap: 40px; height: 400px; padding: 30px 50px; background: rgba(30,30,60,0.6); border-radius: 16px; border: 1px solid rgba(56,189,248,0.2); }}
.bottom {{ position: absolute; bottom: 20px; right: 30px; color: #475569; font-size: 14px; }}
</style></head><body>
{illustration_html}
<div class="header"><span class="label">实验数据</span></div>
<span class="section-num">#{section_id:02d}</span>
<div class="content">
  <div class="title">{title}</div>
  <div class="chart">{bars}</div>
</div>
<div class="bottom">DAST Papers · AI解读</div>
</body></html>"""
    render_html_to_png(html, output_path)
    return output_path


def create_comparison_slide(title, left_title, right_title, left_items, right_items, section_id, output_path):
    """Create comparison slide with AI background illustration."""
    font_path = get_font()
    left_html = "".join(f'<div style="font-size:22px;line-height:1.6;padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.05);">{item}</div>' for item in left_items)
    right_html = "".join(f'<div style="font-size:22px;line-height:1.6;padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.05);">{item}</div>' for item in right_items)

    # Get AI background for comparison
    illustration_html = ""
    try:
        from image_generator import generate_frame_image
        cache_dir = os.path.join(os.path.dirname(__file__), "output", "_ai_bg")
        img_path = generate_frame_image(
            SECTION_AI_PROMPTS.get(section_id, "balance scale comparison, dark background, 4K"),
            cache_dir, section_id, size="1024*576"
        )
        if img_path and os.path.exists(img_path):
            illustration_html = f'<img src="file://{os.path.abspath(img_path)}" style="position:absolute;top:0;left:0;width:100%;height:100%;object-fit:cover;z-index:0;opacity:0.6;" />'
    except:
        pass

    html = f"""<!DOCTYPE html>
<html><head><style>
@font-face {{ font-family: 'NotoSansSC'; src: url('file://{font_path}'); }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ width: {VIDEO_W}px; height: {VIDEO_H}px; background: {COLORS['bg']}; color: {COLORS['text']}; font-family: 'NotoSansSC', sans-serif; position: relative; }}
.header {{ position: absolute; top: 24px; left: 32px; z-index: 10; }}
.label {{ display: inline-block; background: {COLORS['accent']}; color: #0a0a1a; padding: 6px 16px; border-radius: 8px; font-size: 20px; font-weight: 700; }}
.section-num {{ position: absolute; top: 10px; right: 40px; font-size: 140px; font-weight: 900; color: rgba(56,189,248,0.08); line-height: 1; z-index: 10; }}
.content {{ position: absolute; top: 80px; left: 0; right: 0; bottom: 0; display: flex; flex-direction: column; justify-content: center; padding: 20px 60px; z-index: 2; }}
.title {{ font-size: 36px; font-weight: 700; margin-bottom: 24px; text-align: center; }}
.compare {{ display: flex; gap: 32px; }}
.side {{ flex: 1; border: 2px solid rgba(56,189,248,0.2); border-radius: 16px; padding: 28px; background: rgba(10,10,26,0.75); backdrop-filter: blur(8px); }}
.side h3 {{ font-size: 26px; font-weight: 900; margin-bottom: 12px; }}
.side.left {{ border-color: rgba(56,189,248,0.4); }}
.side.right {{ border-color: rgba(244,114,182,0.4); }}
.bottom {{ position: absolute; bottom: 20px; right: 30px; color: #475569; font-size: 14px; z-index: 10; }}
</style></head><body>
{illustration_html}
<div class="header"><span class="label">对比分析</span></div>
<span class="section-num">#{section_id:02d}</span>
<div class="content">
  <div class="title">{title}</div>
  <div class="compare">
    <div class="side left"><h3 style="color:{COLORS['accent']}">{left_title}</h3>{left_html}</div>
    <div class="side right"><h3 style="color:#f472b6">{right_title}</h3>{right_html}</div>
  </div>
</div>
<div class="bottom">DAST Papers · AI解读</div>
</body></html>"""
    render_html_to_png(html, output_path)
    return output_path


def create_data_cards_slide(title, cards, section_id, output_path):
    font_path = get_font()
    cards_html = ""
    for card in cards:
        cards_html += f'<div style="border:1px solid rgba(56,189,248,0.2);border-radius:12px;padding:24px;text-align:center;flex:1;"><div style="font-size:48px;font-weight:900;color:{COLORS["accent"]};">{card["value"]}</div><div style="font-size:18px;color:{COLORS["muted"]};margin-top:8px;">{card["label"]}</div></div>'

    html = f"""<!DOCTYPE html>
<html><head><style>
@font-face {{ font-family: 'NotoSansSC'; src: url('file://{font_path}'); }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ width: {VIDEO_W}px; height: {VIDEO_H}px; background: {COLORS['bg']}; color: {COLORS['text']}; font-family: 'NotoSansSC', sans-serif; position: relative; }}
.header {{ position: absolute; top: 24px; left: 32px; z-index: 10; }}
.label {{ display: inline-block; background: {COLORS['accent']}; color: #0a0a1a; padding: 6px 16px; border-radius: 8px; font-size: 20px; font-weight: 700; }}
.section-num {{ position: absolute; top: 10px; right: 40px; font-size: 140px; font-weight: 900; color: rgba(56,189,248,0.08); line-height: 1; }}
.content {{ position: absolute; top: 80px; left: 0; right: 0; bottom: 0; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 20px; }}
.title {{ font-size: 36px; font-weight: 700; margin-bottom: 30px; text-align: center; }}
.cards {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; width: 100%; max-width: 1200px; }}
.bottom {{ position: absolute; bottom: 20px; right: 30px; color: #475569; font-size: 14px; }}
</style></head><body>
<div class="header"><span class="label">数据概览</span></div>
<span class="section-num">#{section_id:02d}</span>
<div class="content">
  <div class="title">{title}</div>
  <div class="cards">{cards_html}</div>
</div>
<div class="bottom">DAST Papers · AI解读</div>
</body></html>"""
    render_html_to_png(html, output_path)
    return output_path


def create_ending_slide(key_points, output_path):
    font_path = get_font()
    colors = ["#38bdf8", "#f472b6", "#4ade80"]
    points_html = ""
    for i, point in enumerate(key_points[:3]):
        c = colors[i % len(colors)]
        points_html += f'<div style="display:flex;align-items:center;gap:16px;font-size:24px;margin:12px 0;padding:16px 24px;border-left:4px solid {c};background:rgba(255,255,255,0.03);border-radius:0 12px 12px 0;max-width:1000px;width:100%;"><span style="color:{c};font-size:28px;">●</span><span>{point}</span></div>'

    html = f"""<!DOCTYPE html>
<html><head><style>
@font-face {{ font-family: 'NotoSansSC'; src: url('file://{font_path}'); }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ width: {VIDEO_W}px; height: {VIDEO_H}px; background: {COLORS['bg']}; color: {COLORS['text']}; font-family: 'NotoSansSC', sans-serif; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; }}
.main-text {{ font-size: 48px; font-weight: 700; margin-bottom: 30px; }}
.bottom {{ position: absolute; bottom: 20px; right: 30px; color: #475569; font-size: 14px; }}
</style></head><body>
<div class="main-text">核心发现</div>
{points_html}
<div class="bottom">DAST Papers · AI解读</div>
</body></html>"""
    render_html_to_png(html, output_path)
    return output_path
