#!/usr/bin/env python3
"""Generate daily cover images for WeChat MP articles.

Creates a 900x383 cover image (WeChat recommended ratio 2.35:1) with:
- Gradient background
- Report title (学术资讯 / 综合技术资讯)
- Date overlay
- Decorative accent lines

Usage:
  python3 generate_cover.py --type academic --date 2026-05-13 --output /tmp/cover.png
  python3 generate_cover.py --type tech-news --date 2026-05-13 --output /tmp/cover.png
"""

import argparse
import os
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Dimensions (WeChat 2.35:1 ratio)
WIDTH = 900
HEIGHT = 383

# Font path
FONT_PATH = "/home/xiaowangzi/.local/share/fonts/NotoSansCJKsc-Regular.otf"

# Color schemes per type
COLORS = {
    "academic": {
        "gradient_top": (15, 23, 42),      # Deep navy
        "gradient_bottom": (30, 58, 95),    # Steel blue
        "accent": (56, 189, 248),           # Cyan accent
        "title_color": (255, 255, 255),
        "subtitle_color": (148, 163, 184),
        "date_color": (56, 189, 248),
    },
    "tech-news": {
        "gradient_top": (15, 23, 42),      # Deep navy
        "gradient_bottom": (49, 10, 62),    # Dark purple
        "accent": (255, 107, 53),           # Orange accent (#ff6b35)
        "title_color": (255, 255, 255),
        "subtitle_color": (148, 163, 184),
        "date_color": (255, 107, 53),
    },
    "follow-builders": {
        "gradient_top": (15, 23, 42),      # Deep navy
        "gradient_bottom": (30, 58, 95),    # Steel blue (like academic)
        "accent": (255, 107, 53),           # Orange accent (fox-orange #ff6b35)
        "title_color": (255, 255, 255),
        "subtitle_color": (148, 163, 184),
        "date_color": (255, 107, 53),
    },
}

# Title text per type
TITLE_TEXT = {
    "academic": "大模型/智能体\n一手学术资讯",
    "tech-news": "大模型/智能体\n一手综合技术资讯",
    "follow-builders": "AI Builders\n每日摘要",
}

SUBTITLE_TEXT = {
    "academic": "arXiv · GitHub · HuggingFace",
    "tech-news": "Anthropic · OpenAI · Google · Meta · NVIDIA",
    "follow-builders": "X/Twitter · YouTube · Podcasts · Blogs",
}


def draw_gradient(draw, width, height, top_color, bottom_color):
    """Draw a vertical gradient."""
    for y in range(height):
        ratio = y / height
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))


def draw_accent_lines(draw, width, height, accent_color):
    """Draw decorative horizontal accent lines."""
    # Top thin line
    draw.line([(40, 55), (width - 40, 55)], fill=accent_color, width=1)
    # Bottom thicker line
    draw.line([(40, height - 35), (width - 40, height - 35)], fill=accent_color, width=2)
    # Corner marks
    draw.line([(40, 55), (40, 75)], fill=accent_color, width=2)
    draw.line([(width - 40, 55), (width - 40, 75)], fill=accent_color, width=2)


def generate_cover(report_type: str, date_str: str, output_path: str, custom_title: str = "", custom_subtitle: str = ""):
    """Generate a cover image."""
    colors = COLORS[report_type]

    img = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)

    # Background gradient
    draw_gradient(draw, WIDTH, HEIGHT, colors["gradient_top"], colors["gradient_bottom"])

    # Accent lines
    draw_accent_lines(draw, WIDTH, HEIGHT, colors["accent"])

    # Load fonts
    try:
        font_title = ImageFont.truetype(FONT_PATH, 48)
        font_subtitle = ImageFont.truetype(FONT_PATH, 18)
        font_date = ImageFont.truetype(FONT_PATH, 32)
        font_weekday = ImageFont.truetype(FONT_PATH, 16)
    except OSError:
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()
        font_date = ImageFont.load_default()
        font_weekday = ImageFont.load_default()

    # Title (centered, two lines)
    title = custom_title.replace("\\n", "\n") if custom_title else TITLE_TEXT[report_type]
    lines = title.split("\n")
    title_y = 75
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_title)
        line_width = bbox[2] - bbox[0]
        x = (WIDTH - line_width) // 2
        draw.text((x, title_y), line, fill=colors["title_color"], font=font_title)
        title_y += 58

    # Subtitle (centered below title)
    subtitle = custom_subtitle if custom_subtitle else SUBTITLE_TEXT[report_type]
    bbox = draw.textbbox((0, 0), subtitle, font=font_subtitle)
    sub_width = bbox[2] - bbox[0]
    sub_x = (WIDTH - sub_width) // 2
    draw.text((sub_x, title_y + 8), subtitle, fill=colors["subtitle_color"], font=font_subtitle)

    # Date (right-aligned, bottom area)
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday = weekday_names[date_obj.weekday()]

    date_display = date_str
    bbox = draw.textbbox((0, 0), date_display, font=font_date)
    date_width = bbox[2] - bbox[0]
    date_x = WIDTH - 40 - date_width
    date_y = HEIGHT - 75
    draw.text((date_x, date_y), date_display, fill=colors["date_color"], font=font_date)

    # Weekday (small, below date)
    bbox = draw.textbbox((0, 0), weekday, font=font_weekday)
    wd_width = bbox[2] - bbox[0]
    wd_x = WIDTH - 40 - wd_width
    wd_y = date_y + 38
    draw.text((wd_x, wd_y), weekday, fill=colors["subtitle_color"], font=font_weekday)

    # Small decorative dots (left side)
    dot_color = colors["accent"]
    for i in range(3):
        y_pos = HEIGHT - 70 + i * 18
        draw.ellipse([(50, y_pos), (56, y_pos + 6)], fill=dot_color)

    # Save
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    img.save(output_path, "PNG")
    print(f"Cover image saved to {output_path} ({WIDTH}x{HEIGHT})")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate WeChat MP cover image")
    parser.add_argument("--type", choices=["academic", "tech-news", "follow-builders"], required=True,
                        help="Report type: academic, tech-news, or follow-builders")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                        help="Date string (YYYY-MM-DD)")
    parser.add_argument("--title", default="", help="Override title text (e.g. '记忆系统\\n论文日报')")
    parser.add_argument("--subtitle", default="", help="Override subtitle text")
    parser.add_argument("--output", default="/tmp/cover.png",
                        help="Output PNG file path")

    args = parser.parse_args()
    generate_cover(args.type, args.date, args.output, custom_title=args.title, custom_subtitle=args.subtitle)


if __name__ == "__main__":
    main()