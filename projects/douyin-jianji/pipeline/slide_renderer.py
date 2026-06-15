"""幻灯片渲染器 - 在AI背景图上叠加参考视频风格的信息图卡片。

设计目标（对标参考视频）：
- 一致的深蓝科技背景 + 顶部节目标题栏
- 封面 hero 大标题
- 信息图卡片：编号流程、彩色三区、数据大字、材料/渠道网格
- 底部蓝绿色字幕栏，视频合成阶段再叠加同步 ASS 字幕
"""

import os
from PIL import Image, ImageDraw, ImageFont
from config import VIDEO_WIDTH, VIDEO_HEIGHT, COLORS, LAYOUT, FONT_PATH

W, H = VIDEO_WIDTH, VIDEO_HEIGHT
TITLE_BAR_H = 104
CONTENT_TOP = TITLE_BAR_H + 56
CONTENT_BOTTOM = H - 210          # 底部预留给烧录字幕
MARGIN = 96
_FONT_CACHE: dict = {}


# ----------------------------------------------------------------------------
# 公共入口
# ----------------------------------------------------------------------------
def render_slide(slide_data: dict, bg_image_path: str, output_path: str,
                 title_text: str = None):
    """渲染单张幻灯片到 PNG。"""
    template = slide_data.get("template", "policy_explain")
    data = slide_data.get("data", {})
    is_cover = template == "cover_dark"

    img = _prepare_background(bg_image_path, dim=(0.34 if is_cover else 0.6))
    draw = ImageDraw.Draw(img, "RGBA")

    if is_cover:
        _render_cover(draw, data, title_text)
    else:
        _draw_title_bar(draw, title_text or data.get("kicker", ""))
        renderer = {
            "headline_warning": _render_warning,
            "process_flow": _render_process_flow,
            "material_grid": _render_grid,
            "channel_steps": _render_grid,
            "data_release": _render_data,
            "zone_cards": _render_zones,
            "cta_summary": _render_cta,
            "policy_explain": _render_statement,
            "composite": _render_composite,
        }.get(template, _render_statement)
        renderer(draw, data)
        # Section 标签（左上角小徽章）
        section_label = slide_data.get("section_label", "")
        if section_label:
            _draw_section_badge(draw, section_label)
        # Key takeaway footer（底部字幕栏上方）
        key_takeaway = slide_data.get("key_takeaway", "")
        if key_takeaway:
            _draw_key_takeaway(draw, key_takeaway)
        subtitle = slide_data.get("subtitle") or data.get("subtitle")
        if subtitle:
            _draw_subtitle_bar(draw, subtitle)

    img.convert("RGB").save(output_path, "PNG")
    print(f"    幻灯片: {os.path.basename(output_path)} [{template}]")


# ----------------------------------------------------------------------------
# 背景处理
# ----------------------------------------------------------------------------
def _prepare_background(bg_path: str, dim: float = 0.55) -> Image.Image:
    """加载AI背景并裁剪填充，叠加深色渐变保证文字可读。"""
    if bg_path and os.path.exists(bg_path):
        base = Image.open(bg_path).convert("RGB")
        base = _cover_crop(base, W, H)
    else:
        base = _gradient_bg()
    base = base.convert("RGBA")

    # 全局压暗
    veil = Image.new("RGBA", (W, H), (8, 14, 26, int(255 * dim)))
    base = Image.alpha_composite(base, veil)

    # 顶部 + 底部加深的纵向渐变（让标题栏/字幕区更稳）
    grad = Image.new("L", (1, H), 0)
    for y in range(H):
        top = max(0, 150 - int(y * 1.6))           # 顶部
        bottom = max(0, int((y - (H - 320)) * 0.9)) # 底部
        grad.putpixel((0, y), min(210, top + bottom))
    grad = grad.resize((W, H))
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shade.putalpha(grad)
    base = Image.alpha_composite(base, shade)
    return base


def _cover_crop(im: Image.Image, w: int, h: int) -> Image.Image:
    src_ratio = im.width / im.height
    dst_ratio = w / h
    if src_ratio > dst_ratio:
        new_h = h
        new_w = int(h * src_ratio)
    else:
        new_w = w
        new_h = int(w / src_ratio)
    im = im.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - w) // 2
    top = (new_h - h) // 2
    return im.crop((left, top, left + w, top + h))


def _gradient_bg() -> Image.Image:
    top = COLORS["bg_primary"]
    bot = (10, 16, 30)
    im = Image.new("RGB", (W, H))
    px = im.load()
    for y in range(H):
        t = y / H
        c = tuple(int(top[i] * (1 - t) + bot[i] * t) for i in range(3))
        for x in range(W):
            px[x, y] = c
    return im


# ----------------------------------------------------------------------------
# 模板渲染
# ----------------------------------------------------------------------------
def _render_cover(draw, data, title_text):
    kicker = data.get("kicker") or title_text or ""
    headline = data.get("headline", "")

    # 左上角节目标识
    ax, ay = MARGIN, 150
    draw.rectangle([ax, ay, ax + 14, ay + 56], fill=COLORS["accent_blue"])
    _text(draw, (ax + 32, ay + 4), kicker, "subtitle",
          COLORS["text_primary"], stroke=2)

    # 中部大标题
    font = _font("cover")
    lines = _wrap(draw, headline, font, W - 2 * MARGIN, max_lines=3)
    line_h = 118
    total = len(lines) * line_h
    y = (H - total) // 2 - 20
    for line in lines:
        _text(draw, (MARGIN, y), line, "cover", COLORS["text_primary"], stroke=4)
        y += line_h

    # 强调下划线
    draw.rectangle([MARGIN, y + 8, MARGIN + 260, y + 20], fill=COLORS["accent_gold"])
    _text(draw, (MARGIN, y + 44), "干货科普 · 一文讲透", "body",
          COLORS["accent_blue"], stroke=2)


def _render_warning(draw, data):
    headline = data.get("headline", "")
    cx = W // 2
    # 警示标记（更大）
    _warning_badge(draw, cx, CONTENT_TOP + 90, 80)
    # 大标题
    lines = _wrap(draw, headline, _font("h1"), W - 2 * MARGIN, max_lines=3)
    y = CONTENT_TOP + 240
    for line in lines:
        _ctext(draw, cx, y, line, "h1", COLORS["accent_gold"], stroke=4)
        y += 104
    # 副标题说明（从 body/subtitle 填充）
    body = data.get("body") or data.get("subtitle") or ""
    if body:
        sub_lines = _wrap(draw, body, _font("h2"), W - 2 * MARGIN - 160, max_lines=4)
        y += 30
        for line in sub_lines:
            _ctext(draw, cx, y, line, "h2", COLORS["text_primary"], stroke=2)
            y += 64


def _render_process_flow(draw, data):
    _headline(draw, data.get("headline", ""))
    steps = [s for s in data.get("steps", []) if s][:4]
    if not steps:
        return
    n = len(steps)
    gap = 56
    box_w = min(400, (W - 2 * MARGIN - (n - 1) * gap) // n)
    box_h = 260  # 更高，容纳更多文字
    total = n * box_w + (n - 1) * gap
    x0 = (W - total) // 2
    cy = (CONTENT_TOP + CONTENT_BOTTOM) // 2 + 40
    for i, step in enumerate(steps):
        x = x0 + i * (box_w + gap)
        _rounded(draw, x, cy - box_h // 2, box_w, box_h, 20,
                 fill=(*COLORS["bg_card"], 235), outline=COLORS["accent_blue"], width=3)
        # 编号圆（更大）
        draw.ellipse([x + box_w // 2 - 36, cy - box_h // 2 - 30,
                      x + box_w // 2 + 36, cy - box_h // 2 + 42],
                     fill=COLORS["accent_blue"])
        _ctext(draw, x + box_w // 2, cy - box_h // 2 - 18, str(i + 1),
               "h1", (255, 255, 255), stroke=2)
        # 步骤名（大字）
        step_lines = _wrap(draw, step, _font("h1"), box_w - 40, max_lines=2)
        sy = cy - 50 if len(step_lines) >= 2 else cy - 30
        for j, line in enumerate(step_lines):
            _ctext(draw, x + box_w // 2, sy + j * 64, line, "h1",
                   COLORS["text_primary"], stroke=3)
        # 箭头
        if i < n - 1:
            ax = x + box_w + gap // 2
            _arrow(draw, ax, cy, COLORS["accent_gold"])
    # 底部补充说明文字
    body = data.get("body", "")
    if body:
        by = cy + box_h // 2 + 40
        for line in _wrap(draw, body, _font("h2"), W - 2 * MARGIN - 120, max_lines=2):
            _ctext(draw, W // 2, by, line, "h2", COLORS["text_secondary"], stroke=1)
            by += 52


def _render_grid(draw, data):
    _headline(draw, data.get("headline", ""))
    items = data.get("items", [])[:4]
    if not items:
        return
    n = len(items)
    gap = 36
    card_w = min(420, (W - 2 * MARGIN - (n - 1) * gap) // n)
    card_h = 440  # 更高，填满内容区
    total = n * card_w + (n - 1) * gap
    x0 = (W - total) // 2
    y = CONTENT_TOP + 60  # 紧贴标题下方
    palette = [COLORS["accent_blue"], COLORS["success"], COLORS["accent_gold"], COLORS["warning"]]
    for i, item in enumerate(items):
        x = x0 + i * (card_w + gap)
        accent = palette[i % len(palette)]
        _rounded(draw, x, y, card_w, card_h, 22,
                 fill=(*COLORS["bg_card"], 235), outline=accent, width=3)
        draw.rectangle([x, y, x + card_w, y + 10], fill=accent)
        # 编号徽标（更大）
        draw.ellipse([x + card_w // 2 - 44, y + 50, x + card_w // 2 + 44, y + 138], fill=accent)
        _ctext(draw, x + card_w // 2, y + 66, str(i + 1), "h1", (255, 255, 255), stroke=2)
        # 标题（更大字体）
        title = item.get("title", "")
        tl = _wrap(draw, title, _font("h1"), card_w - 48, max_lines=2)
        ty = y + 180
        for line in tl:
            _ctext(draw, x + card_w // 2, ty, line, "h1", COLORS["text_primary"], stroke=2)
            ty += 64
        # 描述（更多行）
        desc = item.get("desc", "")
        if desc:
            ty += 20
            for line in _wrap(draw, desc, _font("h2"), card_w - 56, max_lines=3):
                _ctext(draw, x + card_w // 2, ty, line, "h2", COLORS["text_secondary"])
                ty += 52
    # 底部补充说明文字
    body = data.get("body", "")
    if body:
        by = y + card_h + 30
        for line in _wrap(draw, body, _font("h2"), W - 2 * MARGIN - 120, max_lines=2):
            _ctext(draw, W // 2, by, line, "h2", COLORS["text_secondary"], stroke=1)
            by += 52


def _render_data(draw, data):
    _headline(draw, data.get("headline", ""))
    stats = data.get("stats", [])[:3]
    if not stats:
        return _render_statement(draw, data)
    n = len(stats)
    gap = 56
    card_w = min(500, (W - 2 * MARGIN - (n - 1) * gap) // n)
    card_h = 440  # 更高
    total = n * card_w + (n - 1) * gap
    x0 = (W - total) // 2
    y = CONTENT_TOP + 60
    for i, st in enumerate(stats):
        x = x0 + i * (card_w + gap)
        color = COLORS.get(st.get("color", "accent_gold"), COLORS["accent_gold"])
        _rounded(draw, x, y, card_w, card_h, 22, fill=(*COLORS["bg_card"], 230),
                 outline=color, width=4)
        # 大数字（更大）
        _ctext(draw, x + card_w // 2, y + 80, st.get("value", ""), "data", color, stroke=5)
        # 分隔线
        draw.rectangle([x + 50, y + 230, x + card_w - 50, y + 235], fill=(*color, 220))
        # 标签（更大字体）
        for j, line in enumerate(_wrap(draw, st.get("label", ""), _font("h2"), card_w - 56, max_lines=3)):
            _ctext(draw, x + card_w // 2, y + 260 + j * 56, line, "h2", COLORS["text_secondary"])


def _render_zones(draw, data):
    _headline(draw, data.get("headline", "并网三色分区"))
    items = data.get("items", [])[:3]
    colors = [COLORS["success"], COLORS["warning"], COLORS["danger"]]
    marks = ["✓", "!", "×"]
    n = max(1, len(items))
    gap = 40
    card_w = (W - 2 * MARGIN - (n - 1) * gap) // n
    card_h = 520  # 更高，填满内容区
    x0 = MARGIN
    y = CONTENT_TOP + 60
    for i, item in enumerate(items):
        x = x0 + i * (card_w + gap)
        color = colors[i % 3]
        _rounded(draw, x, y, card_w, card_h, 22, fill=(*COLORS["bg_card"], 235),
                 outline=color, width=4)
        draw.rectangle([x, y, x + card_w, y + 14], fill=color)
        # 图标（更大）
        draw.ellipse([x + card_w // 2 - 50, y + 50, x + card_w // 2 + 50, y + 150], fill=color)
        _ctext(draw, x + card_w // 2, y + 68, marks[i % 3], "h1", (255, 255, 255), stroke=3)
        # 区域名（更大）
        _ctext(draw, x + card_w // 2, y + 180, item.get("title", ""), "h1", color, stroke=3)
        # 描述（更多行，更大字体）
        ty = y + 270
        for j, line in enumerate(_wrap(draw, item.get("desc", ""), _font("h2"), card_w - 56, max_lines=4)):
            _ctext(draw, x + card_w // 2, ty, line, "h2", COLORS["text_primary"])
            ty += 56


def _render_statement(draw, data):
    _headline(draw, data.get("headline", ""))
    body = data.get("body") or data.get("subtitle") or ""
    if not body:
        return
    # 用更大字体，填满内容区
    font = _font("h1")
    lines = _wrap(draw, body, font, W - 2 * MARGIN - 160, max_lines=6)
    box_h = max(200, len(lines) * 80 + 100)
    y0 = CONTENT_TOP + 60
    _rounded(draw, MARGIN + 40, y0, W - 2 * MARGIN - 80, box_h, 24,
             fill=(*COLORS["bg_card"], 215), outline=COLORS["accent_blue"], width=3)
    draw.rectangle([MARGIN + 40, y0, MARGIN + 56, y0 + box_h], fill=COLORS["accent_blue"])
    ty = y0 + 50
    for line in lines:
        _ctext(draw, W // 2, ty, line, "h1", COLORS["text_primary"], stroke=3)
        ty += 80


def _render_cta(draw, data):
    headline = data.get("headline", "评论区答疑")
    sub = data.get("subtitle", "")
    cx = W // 2
    # 大标题（更大）
    _ctext(draw, cx, CONTENT_TOP + 100, headline, "h1", COLORS["accent_gold"], stroke=5)
    # 副标题（更多行，更大字体）
    if sub:
        lines = _wrap(draw, sub, _font("h2"), W - 2 * MARGIN - 80, max_lines=4)
        ty = CONTENT_TOP + 230
        for line in lines:
            _ctext(draw, cx, ty, line, "h2", COLORS["text_primary"], stroke=2)
            ty += 64
    # 评论提示气泡（更大，更显眼）
    bw, bh = 640, 110
    bx, by = cx - bw // 2, CONTENT_BOTTOM - 170
    _rounded(draw, bx, by, bw, bh, 55, fill=(*COLORS["accent_blue"], 240))
    # 左侧三角
    tri_x = bx + 50
    draw.polygon([(tri_x, by + 36), (tri_x + 36, by + 55), (tri_x, by + 74)],
                 fill=(255, 255, 255))
    _ctext(draw, cx + 24, by + 30, "评论区留言 · 免费答疑", "h1", (255, 255, 255), stroke=2)


def _render_composite(draw, data):
    """复合布局模板：标题 + 正文 + 多栏卡片 + 底部结论，对标参考视频的5层信息帧。"""
    cx = W // 2
    headline = data.get("headline", "")
    body = data.get("body", "")
    items = data.get("items", [])
    stats = data.get("stats", [])
    steps = data.get("steps", [])

    # 1. 标题区（上方1/4）
    if headline:
        lines = _wrap(draw, headline, _font("h1"), W - 2 * MARGIN, max_lines=2)
        y = CONTENT_TOP + 30
        for line in lines:
            _ctext(draw, cx, y, line, "h1", COLORS["accent_gold"], stroke=3)
            y += 80

    # 2. 正文段落（标题下方）
    if body:
        body_lines = _wrap(draw, body, _font("h2"), W - 2 * MARGIN - 120, max_lines=3)
        by = y + 20
        for line in body_lines:
            _ctext(draw, cx, by, line, "h2", COLORS["text_primary"], stroke=1)
            by += 52
        y = by + 20

    # 3. 多栏卡片区（中间）— 所有类型堆叠显示
    if stats:
        # 数据卡片（紧凑）
        n = min(len(stats), 3)
        gap = 48
        card_w = min(460, (W - 2 * MARGIN - (n - 1) * gap) // n)
        card_h = min(180, (CONTENT_BOTTOM - y - 80) // (1 + bool(items) + bool(steps)))
        total = n * card_w + (n - 1) * gap
        x0 = (W - total) // 2
        for i, st in enumerate(stats[:n]):
            x = x0 + i * (card_w + gap)
            color = COLORS.get(st.get("color", "accent_gold"), COLORS["accent_gold"])
            _rounded(draw, x, y, card_w, card_h, 16, fill=(*COLORS["bg_card"], 220),
                     outline=color, width=3)
            _ctext(draw, x + card_w // 2, y + 24, st.get("value", ""), "data", color, stroke=4)
            draw.rectangle([x + 40, y + card_h - 46, x + card_w - 40, y + card_h - 42],
                           fill=(*color, 200))
            for j, line in enumerate(_wrap(draw, st.get("label", ""), _font("body"), card_w - 48, max_lines=2)):
                _ctext(draw, x + card_w // 2, y + card_h - 34 + j * 32, line, "body", COLORS["text_secondary"])
        y += card_h + 16

    if items:
        # 物料/流程卡片（紧凑）
        n = min(len(items), 4)
        gap = 32
        card_w = min(380, (W - 2 * MARGIN - (n - 1) * gap) // n)
        card_h = min(160, (CONTENT_BOTTOM - y - 80) // (1 + bool(steps)))
        total = n * card_w + (n - 1) * gap
        x0 = (W - total) // 2
        palette = [COLORS["accent_blue"], COLORS["success"], COLORS["accent_gold"], COLORS["warning"]]
        for i, item in enumerate(items[:n]):
            x = x0 + i * (card_w + gap)
            accent = palette[i % len(palette)]
            _rounded(draw, x, y, card_w, card_h, 14, fill=(*COLORS["bg_card"], 220),
                     outline=accent, width=2)
            draw.rectangle([x, y, x + card_w, y + 6], fill=accent)
            draw.ellipse([x + card_w // 2 - 22, y + 18, x + card_w // 2 + 22, y + 62], fill=accent)
            _ctext(draw, x + card_w // 2, y + 28, str(i + 1), "body", (255, 255, 255), stroke=2)
            for j, line in enumerate(_wrap(draw, item.get("title", ""), _font("h2"), card_w - 32, max_lines=2)):
                _ctext(draw, x + card_w // 2, y + 76 + j * 40, line, "h2", COLORS["text_primary"], stroke=2)
        y += card_h + 16

    if steps:
        # 步骤流程（紧凑）
        n = min(len(steps), 4)
        gap = 40
        box_w = min(360, (W - 2 * MARGIN - (n - 1) * gap) // n)
        box_h = min(130, CONTENT_BOTTOM - y - 80)
        total = n * box_w + (n - 1) * gap
        x0 = (W - total) // 2
        step_cy = y + box_h // 2
        for i, step in enumerate(steps[:n]):
            x = x0 + i * (box_w + gap)
            _rounded(draw, x, y, box_w, box_h, 14, fill=(*COLORS["bg_card"], 220),
                     outline=COLORS["accent_blue"], width=2)
            draw.ellipse([x + box_w // 2 - 22, y - 10, x + box_w // 2 + 22, y + 34],
                         fill=COLORS["accent_blue"])
            _ctext(draw, x + box_w // 2, y + 2, str(i + 1), "body", (255, 255, 255), stroke=2)
            for j, line in enumerate(_wrap(draw, step, _font("h2"), box_w - 28, max_lines=2)):
                _ctext(draw, x + box_w // 2, y + 50 + j * 38, line, "h2", COLORS["text_primary"], stroke=2)
            if i < n - 1:
                _arrow(draw, x + box_w + gap // 2, step_cy, COLORS["accent_gold"])
        y += box_h + 16

    # 4. 底部结论条
    conclusion = data.get("conclusion", "")
    if conclusion:
        bar_h = 56
        bar_y = CONTENT_BOTTOM - bar_h
        _rounded(draw, MARGIN + 40, bar_y, W - 2 * MARGIN - 80, bar_h, 12,
                 fill=(*COLORS["bg_card"], 200))
        draw.rectangle([MARGIN + 40, bar_y, MARGIN + 56, bar_y + bar_h],
                       fill=COLORS["accent_gold"])
        lines = _wrap(draw, conclusion, _font("h2"), W - 2 * MARGIN - 160, max_lines=1)
        if lines:
            _text(draw, (MARGIN + 74, bar_y + 14), lines[0], "h2",
                  COLORS["accent_gold"], stroke=1)


# ----------------------------------------------------------------------------
# 组件
# ----------------------------------------------------------------------------
def _draw_section_badge(draw, label):
    """左上角 section 标签徽章（标题栏下方）。"""
    bx, by = MARGIN, TITLE_BAR_H + 16
    font = _font("body")
    tw = _measure(draw, label, font)
    pad = 16
    bw = tw + pad * 2
    bh = 38
    _rounded(draw, bx, by, bw, bh, 19, fill=(*COLORS["accent_blue"], 200))
    _text(draw, (bx + pad, by + 6), label, "body", (255, 255, 255), stroke=1)


def _draw_key_takeaway(draw, text):
    """底部关键结论条（字幕栏上方）。"""
    if not text:
        return
    bar_h = 52
    y0 = H - LAYOUT.get("subtitle_bar_height", 120) - bar_h - 8
    _rounded(draw, MARGIN + 40, y0, W - 2 * MARGIN - 80, bar_h, 12,
             fill=(*COLORS["bg_card"], 200))
    draw.rectangle([MARGIN + 40, y0, MARGIN + 52, y0 + bar_h],
                   fill=COLORS["accent_gold"])
    lines = _wrap(draw, text, _font("body"), W - 2 * MARGIN - 160, max_lines=1)
    if lines:
        _text(draw, (MARGIN + 70, y0 + 12), lines[0], "body",
              COLORS["accent_gold"], stroke=1)


def _draw_title_bar(draw, title_text):
    draw.rectangle([0, 0, W, TITLE_BAR_H], fill=(*COLORS["bg_primary"], 215))
    draw.rectangle([0, TITLE_BAR_H, W, TITLE_BAR_H + 4], fill=COLORS["accent_blue"])
    draw.rectangle([MARGIN, 34, MARGIN + 12, 70], fill=COLORS["accent_gold"])
    if title_text:
        line = _wrap(draw, title_text, _font("subtitle"), W - 2 * MARGIN - 40,
                     max_lines=1)[0]
        _text(draw, (MARGIN + 30, 30), line, "subtitle",
              COLORS["text_primary"], stroke=2)


def _headline(draw, text):
    if not text:
        return
    line = _wrap(draw, text, _font("subtitle"), W - 2 * MARGIN, max_lines=1)[0]
    _ctext(draw, W // 2, CONTENT_TOP, line, "subtitle", COLORS["accent_blue"], stroke=2)
    tw = _measure(draw, line, _font("subtitle"))
    draw.rectangle([W // 2 - tw // 2, CONTENT_TOP + 62, W // 2 + tw // 2, CONTENT_TOP + 67],
                   fill=(*COLORS["accent_blue"], 160))


def _draw_subtitle_bar(draw, subtitle=None):
    """绘制底部字幕承托带（蓝绿色半透明）。

    文字不在此烤入：成片阶段由 video_generator 用 ASS 同步烧录旁白，
    与配音逐句对齐，避免与烤入文字重叠。此处仅铺一条提高可读性的承托带。
    """
    bar_h = LAYOUT.get("subtitle_bar_height", 120)
    y0 = H - bar_h
    draw.rectangle([0, y0, W, H], fill=(92, 148, 164, 235))
    draw.rectangle([0, y0, W, y0 + 4], fill=(*COLORS["accent_blue"], 200))


def _warning_badge(draw, cx, cy, r):
    draw.polygon([(cx, cy - r), (cx - r, cy + r), (cx + r, cy + r)],
                 fill=COLORS["warning"], outline=(255, 255, 255))
    _ctext(draw, cx, cy - 18, "!", "h1", (40, 30, 0), stroke=0)


def _arrow(draw, x, y, color):
    draw.line([x - 26, y, x + 14, y], fill=color, width=8)
    draw.polygon([(x + 12, y - 16), (x + 34, y), (x + 12, y + 16)], fill=color)


def _rounded(draw, x, y, w, h, r, fill=None, outline=None, width=1):
    draw.rounded_rectangle([x, y, x + w, y + h], radius=r, fill=fill,
                           outline=outline, width=width)


# ----------------------------------------------------------------------------
# 文本工具
# ----------------------------------------------------------------------------
def _font(key: str) -> ImageFont.FreeTypeFont:
    sizes = {
        "cover": 92, "h1": 72, "subtitle": 46, "h2": 48,
        "body": 32, "data": 84, "step": 40, "subtitle_bar": 52,
    }
    size = sizes.get(key, 36)
    if size not in _FONT_CACHE:
        try:
            _FONT_CACHE[size] = ImageFont.truetype(FONT_PATH, size)
        except Exception:
            _FONT_CACHE[size] = ImageFont.load_default()
    return _FONT_CACHE[size]


def _text(draw, pos, text, key, color, stroke=0):
    font = _font(key)
    draw.text(pos, text, font=font, fill=color,
              stroke_width=stroke, stroke_fill=(0, 0, 0, 200) if stroke else None)


def _ctext(draw, cx, y, text, key, color, stroke=0):
    font = _font(key)
    w = _measure(draw, text, font)
    draw.text((cx - w // 2, y), text, font=font, fill=color,
              stroke_width=stroke, stroke_fill=(0, 0, 0, 210) if stroke else None)


def _measure(draw, text, font) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def _wrap(draw, text, font, max_w, max_lines=None) -> list:
    text = str(text or "").strip()
    if not text:
        return []
    lines, cur = [], ""
    for ch in text:
        if _measure(draw, cur + ch, font) <= max_w or not cur:
            cur += ch
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    if max_lines and len(lines) > max_lines:
        overflow = "".join(lines[max_lines - 1:])
        lines = lines[:max_lines]
        lines[-1] = _ellipsize(draw, overflow, font, max_w)
    elif max_lines and len(lines) == max_lines and _is_orphan_tail(lines[-1]):
        lines = lines[:-1]
        lines[-1] = _ellipsize(draw, lines[-1], font, max_w)
    return lines


def _ellipsize(draw, text, font, max_w) -> str:
    suffix = "..."
    if _measure(draw, suffix, font) > max_w:
        return ""
    value = str(text or "").strip()
    while value and _measure(draw, value + suffix, font) > max_w:
        value = value[:-1]
    return value.rstrip() + suffix


def _is_orphan_tail(text: str) -> bool:
    value = str(text or "").strip()
    if not value:
        return False
    meaningful = value.strip("，。；、,.!?！？:：")
    return len(meaningful) <= 1


if __name__ == "__main__":
    for tpl, data in [
        ("cover_dark", {"kicker": "光伏并网流程解读", "headline": "废止80%红线 50GW项目复活"}),
        ("process_flow", {"headline": "正确顺序", "steps": ["备案", "施工", "并网"]}),
        ("zone_cards", {"headline": "并网三色分区", "items": [
            {"title": "绿区", "desc": "承载力充足，直接备案"},
            {"title": "黄区", "desc": "配储能或安控接入"},
            {"title": "红区", "desc": "电网改造后有序接入"}]}),
    ]:
        render_slide({"template": tpl, "data": data}, None,
                     f"/tmp/slide_{tpl}.png", "光伏政策解读")
