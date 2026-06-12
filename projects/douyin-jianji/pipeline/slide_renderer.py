#!/usr/bin/env python3
"""幻灯片渲染器 - 将slide数据+背景图渲染为最终幻灯片PNG"""

from PIL import Image, ImageDraw, ImageFont
import os


def render_slide(slide_data: dict, bg_image_path: str, output_path: str, title_text: str = ""):
    """
    渲染单张幻灯片

    Args:
        slide_data: 幻灯片数据（template, data等）
        bg_image_path: 背景图片路径
        output_path: 输出PNG路径
        title_text: 标题文本
    """
    # 加载背景图
    if bg_image_path and os.path.exists(bg_image_path):
        img = Image.open(bg_image_path).convert("RGB")
    else:
        img = Image.new("RGB", (1080, 1920), (26, 26, 46))

    draw = ImageDraw.Draw(img)
    w, h = img.size

    # 尝试加载字体
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/google-noto-cjk/NotoSansCJK-Bold.ttc", 48)
        body_font = ImageFont.truetype("/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc", 36)
    except Exception:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()

    # 绘制标题
    if title_text:
        bbox = draw.textbbox((0, 0), title_text, font=title_font)
        tw = bbox[2] - bbox[0]
        x = (w - tw) // 2
        draw.text((x, 60), title_text, fill=(255, 255, 255), font=title_font)

    # 绘制slide数据
    template = slide_data.get("template", "data_big")
    data = slide_data.get("data", {})

    if template == "data_big" and data:
        y_offset = h // 3
        for key, value in data.items():
            text = f"{key}: {value}"
            bbox = draw.textbbox((0, 0), text, font=body_font)
            tw = bbox[2] - bbox[0]
            x = (w - tw) // 2
            draw.text((x, y_offset), text, fill=(255, 255, 255), font=body_font)
            y_offset += 60

    img.save(output_path, "PNG")
