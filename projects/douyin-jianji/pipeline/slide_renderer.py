"""幻灯片渲染器 - 在AI背景图上叠加文字、卡片、图标"""

import os
from PIL import Image, ImageDraw, ImageFont
from config import (
    VIDEO_WIDTH, VIDEO_HEIGHT, COLORS, FONTS, LAYOUT, FONT_PATH
)


def render_slide(slide_data: dict, bg_image_path: str, output_path: str,
                 title_text: str = None):
    """
    渲染单张幻灯片

    Args:
        slide_data: 幻灯片数据 {"template": "...", "data": {...}}
        bg_image_path: AI背景图路径
        output_path: 输出PNG路径
        title_text: 顶部标题栏文字（可选）
    """
    # 1. 加载AI背景图
    if bg_image_path and os.path.exists(bg_image_path):
        img = Image.open(bg_image_path).convert("RGBA")
        img = img.resize((VIDEO_WIDTH, VIDEO_HEIGHT), Image.LANCZOS)
    else:
        # 创建纯色背景
        img = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), COLORS["bg_primary"] + (255,))

    # 2. 叠加半透明深色遮罩（保证文字可读）
    overlay = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 128))
    img = Image.alpha_composite(img, overlay)

    # 3. 创建绘图对象
    draw = ImageDraw.Draw(img)

    # 4. 渲染顶部标题栏
    display_title = title_text or slide_data.get("title")
    if display_title:
        _draw_title_bar(draw, display_title)

    # 5. 根据模板类型渲染内容区域
    template = slide_data.get("template", "data_big")
    data = slide_data.get("data", {})

    if template in {"cover_dark", "headline_warning"}:
        _render_title_template(draw, data)
    elif template == "data_release":
        _render_data_big_template(draw, data)
    elif template == "process_flow":
        _render_step_list_template(draw, data)
    elif template == "zone_cards":
        _render_grid_3x1_template(draw, data)
    elif template in {"material_grid", "channel_steps"}:
        _render_grid_2x2_template(draw, data)
    elif template == "cta_summary":
        _render_cta_template(draw, data)
    elif template == "title":
        _render_title_template(draw, data)
    elif template == "grid_2x2":
        _render_grid_2x2_template(draw, data)
    elif template == "grid_3x1":
        _render_grid_3x1_template(draw, data)
    elif template == "data_big":
        _render_data_big_template(draw, data)
    elif template == "step_list":
        _render_step_list_template(draw, data)
    elif template == "cta":
        _render_cta_template(draw, data)
    else:
        _render_data_big_template(draw, data)

    # 6. 渲染底部参考视频式字幕栏
    subtitle = slide_data.get("subtitle") or data.get("subtitle")
    if subtitle:
        _draw_bottom_subtitle_bar(draw, subtitle)

    # 7. 保存为PNG
    img = img.convert("RGB")
    img.save(output_path, "PNG")
    print(f"    幻灯片已保存: {output_path}")


def _draw_title_bar(draw: ImageDraw.Draw, title_text: str):
    """绘制顶部标题栏"""
    # 背景条
    draw.rectangle(
        [0, 0, VIDEO_WIDTH, LAYOUT["title_bar_height"]],
        fill=COLORS["bg_primary"] + (200,)
    )

    # 标题文字
    font = _get_font("subtitle")
    bbox = draw.textbbox((0, 0), title_text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (VIDEO_WIDTH - text_width) // 2
    y = (LAYOUT["title_bar_height"] - 48) // 2
    draw.text((x, y), title_text, fill=COLORS["text_primary"], font=font)


def _draw_bottom_subtitle_bar(draw: ImageDraw.Draw, subtitle: str):
    """绘制底部字幕栏，贴近参考视频样式。"""
    bar_height = LAYOUT.get("subtitle_bar_height", 120)
    y0 = VIDEO_HEIGHT - bar_height
    bar_color = (92, 148, 164, 245)
    draw.rectangle([0, y0, VIDEO_WIDTH, VIDEO_HEIGHT], fill=bar_color)

    font = _get_font("subtitle_bar")
    lines = _wrap_text(draw, subtitle, font, VIDEO_WIDTH - 160)
    line_height = 66
    total_height = len(lines) * line_height
    start_y = y0 + (bar_height - total_height) // 2 - 4

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - text_width) // 2
        y = start_y + i * line_height
        draw.text((x + 3, y + 3), line, fill=(0, 0, 0, 180), font=font)
        draw.text((x, y), line, fill=COLORS["text_primary"], font=font)


def _wrap_text(draw: ImageDraw.Draw, text: str, font: ImageFont.FreeTypeFont,
               max_width: int) -> list:
    """按像素宽度换行。"""
    text = str(text).strip()
    if not text:
        return []

    lines = []
    current = ""
    for char in text:
        candidate = current + char
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = char
    if current:
        lines.append(current)
    return lines[:2]


def _render_title_template(draw: ImageDraw.Draw, data: dict):
    """渲染标题模板 - 居中大字 + 副标题"""
    headline = data.get("headline", "")
    subtitle = data.get("subtitle", "")

    # 装饰元素 - 顶部渐变条
    for i in range(5):
        alpha = 200 - i * 40
        draw.rectangle(
            [0, i * 2, VIDEO_WIDTH, i * 2 + 2],
            fill=COLORS["accent_blue"] + (alpha,)
        )

    # 标题
    font_title = _get_font("title")
    bbox = draw.textbbox((0, 0), headline, font=font_title)
    text_width = bbox[2] - bbox[0]
    x = (VIDEO_WIDTH - text_width) // 2
    y = VIDEO_HEIGHT // 2 - 100
    draw.text((x, y), headline, fill=COLORS["accent_gold"], font=font_title)

    # 副标题
    if subtitle:
        font_subtitle = _get_font("subtitle")
        bbox = draw.textbbox((0, 0), subtitle, font=font_subtitle)
        text_width = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - text_width) // 2
        y = VIDEO_HEIGHT // 2 + 50
        draw.text((x, y), subtitle, fill=COLORS["text_primary"], font=font_subtitle)

    # 装饰线 - 带渐变效果
    line_y = VIDEO_HEIGHT // 2 + 120
    for i in range(3):
        draw.rectangle(
            [VIDEO_WIDTH // 2 - 100 + i * 5, line_y + i * 2,
             VIDEO_WIDTH // 2 + 100 - i * 5, line_y + i * 2 + 4],
            fill=COLORS["accent_blue"] + (200 - i * 50,)
        )


def _render_grid_2x2_template(draw: ImageDraw.Draw, data: dict):
    """渲染四宫格模板"""
    items = data.get("items", [])
    headline = data.get("headline", "")

    # 标题
    if headline:
        font = _get_font("subtitle")
        bbox = draw.textbbox((0, 0), headline, font=font)
        text_width = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - text_width) // 2
        draw.text((x, 140), headline, fill=COLORS["text_primary"], font=font)

    # 计算网格位置
    margin = LAYOUT["margin"]
    gap = LAYOUT["card_gap"]
    card_width = (VIDEO_WIDTH - 2 * margin - gap) // 2
    card_height = (VIDEO_HEIGHT - LAYOUT["title_bar_height"] - LAYOUT["subtitle_bar_height"] - 200 - gap) // 2

    positions = [
        (margin, 220),
        (margin + card_width + gap, 220),
        (margin, 220 + card_height + gap),
        (margin + card_width + gap, 220 + card_height + gap),
    ]

    # 绘制装饰元素
    # 左侧装饰条
    draw.rectangle(
        [margin - 10, 220, margin, 220 + card_height * 2 + gap],
        fill=COLORS["accent_blue"] + (150,)
    )

    # 右侧装饰条
    draw.rectangle(
        [VIDEO_WIDTH - margin, 220, VIDEO_WIDTH - margin + 10, 220 + card_height * 2 + gap],
        fill=COLORS["accent_blue"] + (150,)
    )

    for i, (x, y) in enumerate(positions):
        if i < len(items):
            item = items[i]
            _draw_card(draw, x, y, card_width, card_height, item.get("title", ""), item.get("desc", ""))


def _render_grid_3x1_template(draw: ImageDraw.Draw, data: dict):
    """渲染三列模板（绿/黄/红三区）"""
    items = data.get("items", [])
    headline = data.get("headline", "")

    # 标题
    if headline:
        font = _get_font("subtitle")
        bbox = draw.textbbox((0, 0), headline, font=font)
        text_width = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - text_width) // 2
        draw.text((x, 140), headline, fill=COLORS["text_primary"], font=font)

    # 计算列位置
    margin = LAYOUT["margin"]
    gap = LAYOUT["card_gap"]
    card_width = (VIDEO_WIDTH - 2 * margin - 2 * gap) // 3
    card_height = VIDEO_HEIGHT - LAYOUT["title_bar_height"] - LAYOUT["subtitle_bar_height"] - 200

    colors = [COLORS["success"], COLORS["warning"], COLORS["danger"]]

    for i in range(3):
        x = margin + i * (card_width + gap)
        y = 220
        color = colors[i % len(colors)]

        if i < len(items):
            item = items[i]
            _draw_colored_card(draw, x, y, card_width, card_height,
                             item.get("title", ""), item.get("desc", ""), color)


def _render_data_big_template(draw: ImageDraw.Draw, data: dict):
    """渲染数据突出模板"""
    headline = data.get("headline", "")
    stats = data.get("stats", [])

    # 标题
    if headline:
        font = _get_font("subtitle")
        bbox = draw.textbbox((0, 0), headline, font=font)
        text_width = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - text_width) // 2
        draw.text((x, 140), headline, fill=COLORS["text_primary"], font=font)

    # 数据
    if stats:
        font_data = _get_font("data_big")
        font_label = _get_font("body")

        for i, stat in enumerate(stats):
            value = stat.get("value", "")
            label = stat.get("label", "")
            color_name = stat.get("color", "accent_blue")
            color = COLORS.get(color_name, COLORS["accent_blue"])

            # 计算位置（水平排列）
            total_width = len(stats) * 400
            start_x = (VIDEO_WIDTH - total_width) // 2
            x = start_x + i * 400
            y = VIDEO_HEIGHT // 2 - 50

            # 装饰背景
            draw.rounded_rectangle(
                [x - 20, y - 30, x + 380, y + 180],
                radius=16,
                fill=COLORS["bg_card"] + (150,)
            )

            # 大数字 - 带阴影效果
            bbox = draw.textbbox((0, 0), value, font=font_data)
            text_width = bbox[2] - bbox[0]
            # 阴影
            draw.text((x + (400 - text_width) // 2 + 3, y + 3), value,
                     fill=(0, 0, 0, 100), font=font_data)
            # 主文字
            draw.text((x + (400 - text_width) // 2, y), value, fill=color, font=font_data)

            # 标签
            bbox = draw.textbbox((0, 0), label, font=font_label)
            text_width = bbox[2] - bbox[0]
            draw.text((x + (400 - text_width) // 2, y + 120), label, fill=COLORS["text_secondary"], font=font_label)

            # 装饰线
            draw.rectangle(
                [x + 50, y + 160, x + 350, y + 163],
                fill=color + (150,)
            )


def _render_step_list_template(draw: ImageDraw.Draw, data: dict):
    """渲染步骤列表模板"""
    headline = data.get("headline", "")
    steps = data.get("steps", [])

    # 标题
    if headline:
        font = _get_font("subtitle")
        bbox = draw.textbbox((0, 0), headline, font=font)
        text_width = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - text_width) // 2
        draw.text((x, 140), headline, fill=COLORS["text_primary"], font=font)

    # 步骤
    if steps:
        font_step = _get_font("step_number")
        font_text = _get_font("body")

        step_height = 120
        start_y = 250

        for i, step in enumerate(steps):
            y = start_y + i * (step_height + 40)

            # 步骤编号（圆形背景）- 带渐变效果
            circle_x = VIDEO_WIDTH // 2 - 300
            circle_y = y + 10

            # 外圈渐变
            for j in range(5):
                alpha = 255 - j * 30
                draw.ellipse(
                    [circle_x - j, circle_y - j, circle_x + 60 + j, circle_y + 60 + j],
                    fill=COLORS["accent_blue"] + (alpha,)
                )

            # 内圈
            draw.ellipse(
                [circle_x, circle_y, circle_x + 60, circle_y + 60],
                fill=COLORS["accent_blue"]
            )

            # 步骤编号
            draw.text((circle_x + 15, circle_y + 5), str(i + 1),
                     fill=COLORS["text_primary"], font=font_step)

            # 步骤文字 - 带背景条
            text_x = VIDEO_WIDTH // 2 - 200
            draw.rectangle(
                [text_x - 10, y + 10, text_x + 400, y + 70],
                fill=COLORS["bg_card"] + (200,)
            )
            draw.text((text_x, y + 15), step,
                     fill=COLORS["text_primary"], font=font_text)

            # 连接线（除了最后一步）- 带渐变效果
            if i < len(steps) - 1:
                line_y = y + step_height
                for j in range(3):
                    draw.rectangle(
                        [circle_x + 28 + j, line_y + j * 10,
                         circle_x + 32 - j, line_y + 40 + j * 10],
                        fill=COLORS["accent_blue"] + (200 - j * 60,)
                    )


def _render_cta_template(draw: ImageDraw.Draw, data: dict):
    """渲染CTA模板"""
    headline = data.get("headline", "评论区留言")
    subtitle = data.get("subtitle", "免费咨询")

    # 标题
    font_title = _get_font("title")
    bbox = draw.textbbox((0, 0), headline, font=font_title)
    text_width = bbox[2] - bbox[0]
    x = (VIDEO_WIDTH - text_width) // 2
    y = VIDEO_HEIGHT // 2 - 100
    draw.text((x, y), headline, fill=COLORS["accent_gold"], font=font_title)

    # 副标题
    if subtitle:
        font_subtitle = _get_font("subtitle")
        bbox = draw.textbbox((0, 0), subtitle, font=font_subtitle)
        text_width = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - text_width) // 2
        y = VIDEO_HEIGHT // 2 + 50
        draw.text((x, y), subtitle, fill=COLORS["text_primary"], font=font_subtitle)


def _draw_card(draw: ImageDraw.Draw, x: int, y: int, w: int, h: int,
               title: str, desc: str):
    """绘制卡片"""
    # 卡片背景 - 渐变效果
    for i in range(LAYOUT["card_radius"]):
        alpha = 255 - i * 5
        draw.rounded_rectangle(
            [x + i, y + i, x + w - i, y + h - i],
            radius=LAYOUT["card_radius"] - i,
            fill=COLORS["bg_card"] + (alpha,)
        )

    # 顶部装饰条
    draw.rectangle(
        [x, y, x + w, y + 6],
        fill=COLORS["accent_blue"]
    )

    # 左侧装饰条
    draw.rectangle(
        [x, y, x + 6, y + h],
        fill=COLORS["accent_blue"] + (150,)
    )

    # 标题
    font_title = _get_font("card_title")
    draw.text((x + LAYOUT["card_padding"] + 10, y + LAYOUT["card_padding"] + 10),
             title, fill=COLORS["accent_blue"], font=font_title)

    # 描述
    if desc:
        font_desc = _get_font("card_desc")
        draw.text((x + LAYOUT["card_padding"] + 10, y + LAYOUT["card_padding"] + 60),
                 desc, fill=COLORS["text_secondary"], font=font_desc)

    # 底部装饰线
    draw.rectangle(
        [x + LAYOUT["card_padding"], y + h - 20,
         x + w - LAYOUT["card_padding"], y + h - 18],
        fill=COLORS["divider"]
    )


def _draw_colored_card(draw: ImageDraw.Draw, x: int, y: int, w: int, h: int,
                       title: str, desc: str, color: tuple):
    """绘制带颜色的卡片"""
    # 卡片背景
    draw.rounded_rectangle(
        [x, y, x + w, y + h],
        radius=LAYOUT["card_radius"],
        fill=COLORS["bg_card"],
        outline=color,
        width=3
    )

    # 顶部色条
    draw.rectangle(
        [x, y, x + w, y + 8],
        fill=color
    )

    # 标题
    font_title = _get_font("card_title")
    draw.text((x + LAYOUT["card_padding"], y + LAYOUT["card_padding"] + 20),
             title, fill=color, font=font_title)

    # 描述
    if desc:
        font_desc = _get_font("card_desc")
        draw.text((x + LAYOUT["card_padding"], y + LAYOUT["card_padding"] + 70),
                 desc, fill=COLORS["text_secondary"], font=font_desc)


def _get_font(font_type: str) -> ImageFont.FreeTypeFont:
    """获取字体"""
    try:
        font_config = FONTS.get(font_type, FONTS["body"])
        return ImageFont.truetype(FONT_PATH, font_config["size"])
    except Exception as e:
        print(f"  ⚠ 字体加载失败: {e}，使用默认字体")
        return ImageFont.load_default()


if __name__ == "__main__":
    # 测试
    test_data = {
        "template": "title",
        "data": {
            "headline": "测试标题",
            "subtitle": "测试副标题"
        }
    }
    render_slide(test_data, None, "/tmp/test_slide.png", "测试顶部标题")
