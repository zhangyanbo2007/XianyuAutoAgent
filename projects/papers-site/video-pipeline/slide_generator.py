"""Generate visually rich slides with background images and overlays."""

import os
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from config import VIDEO_WIDTH, VIDEO_HEIGHT, BG_COLOR, TEXT_COLOR, ACCENT_COLOR, TITLE_COLOR
from image_fetcher import fetch_theme_image


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Get a Chinese-capable font."""
    font_paths = [
        os.path.expanduser("~/.local/share/fonts/NotoSansCJKsc-Regular.otf"),
        "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto/NotoSansSC-Regular.otf",
        "/usr/share/fonts/google-noto/NotoSansSC-Regular.otf",
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        "/usr/share/fonts/wqy-zenhei/wqy-zenhei.ttc",
        "/usr/share/fonts/wqy-microhei/wqy-microhei.ttc",
    ]
    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def _hex_to_rgba(hex_color: str, alpha: int = 255) -> tuple:
    return _hex_to_rgb(hex_color) + (alpha,)


def _create_gradient_overlay(width: int, height: int, color: str, direction: str = "left") -> Image.Image:
    """Create a gradient overlay image."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    r, g, b = _hex_to_rgb(color)

    if direction == "left":
        for x in range(width):
            alpha = int(255 * (1 - x / width) * 0.85)
            draw.line([(x, 0), (x, height)], fill=(r, g, b, alpha))
    elif direction == "bottom":
        for y in range(height):
            alpha = int(255 * (y / height) * 0.7)
            draw.line([(0, y), (width, y)], fill=(r, g, b, alpha))
    elif direction == "full":
        draw.rectangle([0, 0, width, height], fill=(r, g, b, int(255 * 0.75)))

    return img


def _prepare_background(image_path: str, width: int = VIDEO_WIDTH, height: int = VIDEO_HEIGHT) -> Image.Image:
    """Load and prepare a background image with dark overlay."""
    try:
        bg = Image.open(image_path).convert("RGBA")
        bg = bg.resize((width, height), Image.LANCZOS)

        # Darken the image
        enhancer = ImageEnhance.Brightness(bg)
        bg = enhancer.enhance(0.3)

        # Add blue tint
        tint = Image.new("RGBA", (width, height), (15, 23, 42, 100))
        bg = Image.alpha_composite(bg, tint)

        return bg
    except Exception:
        # Fallback to solid color
        return Image.new("RGBA", (width, height), _hex_to_rgba(BG_COLOR))


def _draw_rounded_rect(draw, xy, radius, fill):
    """Draw a rounded rectangle."""
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


def _draw_decorative_lines(draw, width: int, height: int):
    """Draw decorative accent lines."""
    # Top accent line
    draw.rectangle([0, 0, width, 4], fill=_hex_to_rgba(ACCENT_COLOR, 180))
    # Bottom accent line
    draw.rectangle([0, height - 4, width, height], fill=_hex_to_rgba(ACCENT_COLOR, 180))


def _draw_corner_decoration(draw, x: int, y: int, size: int = 60, color: str = ACCENT_COLOR):
    """Draw a corner decoration bracket."""
    c = _hex_to_rgba(color, 150)
    t = 3
    draw.rectangle([x, y, x + size, y + t], fill=c)
    draw.rectangle([x, y, x + t, y + size], fill=c)


def create_title_slide(title: str, subtitle: str, output_path: str,
                       bg_image: str = None) -> str:
    """Create an impressive opening title slide."""
    if bg_image:
        img = _prepare_background(bg_image)
    else:
        img = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), _hex_to_rgba(BG_COLOR))

    draw = ImageDraw.Draw(img)
    _draw_decorative_lines(draw, VIDEO_WIDTH, VIDEO_HEIGHT)

    # Decorative corner brackets
    _draw_corner_decoration(draw, 100, 200, 80)
    _draw_corner_decoration(draw, VIDEO_WIDTH - 180, VIDEO_HEIGHT - 280, 80)

    # Decorative circles
    for cx, cy, r in [(160, 160, 30), (VIDEO_WIDTH - 140, VIDEO_HEIGHT - 240, 25)]:
        draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                     outline=_hex_to_rgba(ACCENT_COLOR, 100), width=2)

    # Horizontal accent line
    line_y = 380
    draw.rectangle([200, line_y, VIDEO_WIDTH - 200, line_y + 3],
                   fill=_hex_to_rgba(ACCENT_COLOR, 200))

    # Title text - large and bold
    font_title = _get_font(58, bold=True)
    wrapped = _wrap_text(title, font_title, VIDEO_WIDTH - 400)
    y = 420
    for line in wrapped:
        bbox = draw.textbbox((0, 0), line, font=font_title)
        tw = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - tw) // 2
        # Text shadow
        draw.text((x + 2, y + 2), line, fill=(0, 0, 0, 120), font=font_title)
        draw.text((x, y), line, fill=_hex_to_rgba(TITLE_COLOR), font=font_title)
        y += 78

    # Subtitle chip
    font_sub = _get_font(28)
    sub_text = f"📊 {subtitle}"
    bbox = draw.textbbox((0, 0), sub_text, font=font_sub)
    tw = bbox[2] - bbox[0]
    chip_x = (VIDEO_WIDTH - tw) // 2 - 20
    chip_y = y + 30
    _draw_rounded_rect(draw, [chip_x, chip_y, chip_x + tw + 40, chip_y + 48],
                       radius=24, fill=_hex_to_rgba(ACCENT_COLOR, 200))
    draw.text((chip_x + 20, chip_y + 8), sub_text,
              fill=_hex_to_rgba(BG_COLOR), font=font_sub)

    # Bottom branding
    font_brand = _get_font(22)
    brand = "AI 论文解读 · DAST Papers"
    bbox = draw.textbbox((0, 0), brand, font=font_brand)
    tw = bbox[2] - bbox[0]
    draw.text(((VIDEO_WIDTH - tw) // 2, VIDEO_HEIGHT - 70), brand,
              fill=_hex_to_rgba("#667085", 180), font=font_brand)

    img.convert("RGB").save(output_path, "PNG")
    return output_path


def create_section_slide(label: str, text: str, section_index: int,
                         total_sections: int, output_path: str,
                         bg_image: str = None, paper_title: str = "") -> str:
    """Create a visually rich content slide."""
    if bg_image:
        img = _prepare_background(bg_image)
    else:
        img = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), _hex_to_rgba(BG_COLOR))

    draw = ImageDraw.Draw(img)
    _draw_decorative_lines(draw, VIDEO_WIDTH, VIDEO_HEIGHT)

    # Left accent bar
    draw.rectangle([0, 0, 6, VIDEO_HEIGHT], fill=_hex_to_rgba(ACCENT_COLOR, 200))

    # Section label chip (top-left)
    font_label = _get_font(26, bold=True)
    bbox = draw.textbbox((0, 0), label, font=font_label)
    lw = bbox[2] - bbox[0] + 32
    lh = bbox[3] - bbox[1] + 16
    _draw_rounded_rect(draw, [60, 60, 60 + lw, 60 + lh],
                       radius=8, fill=_hex_to_rgba(ACCENT_COLOR, 220))
    draw.text((76, 66), label, fill=_hex_to_rgba(BG_COLOR), font=font_label)

    # Progress dots
    dot_y = 60 + lh + 24
    for i in range(total_sections):
        x = 60 + i * 32
        if i <= section_index:
            color = _hex_to_rgba(ACCENT_COLOR, 220)
        else:
            color = _hex_to_rgba("#334155", 150)
        draw.ellipse([x, dot_y, x + 18, dot_y + 18], fill=color)

    # Decorative bracket around text area
    _draw_corner_decoration(draw, 80, 250, 50)
    _draw_corner_decoration(draw, VIDEO_WIDTH - 130, VIDEO_HEIGHT - 300, 50)

    # Main text - large, centered with text wrapping
    font_text = _get_font(44)
    wrapped = _wrap_text(text, font_text, VIDEO_WIDTH - 360)
    total_text_height = len(wrapped) * 65
    start_y = max(300, (VIDEO_HEIGHT - total_text_height) // 2)

    # Text background panel
    panel_x1 = 120
    panel_x2 = VIDEO_WIDTH - 120
    panel_y1 = start_y - 20
    panel_y2 = start_y + total_text_height + 20
    _draw_rounded_rect(draw, [panel_x1, panel_y1, panel_x2, panel_y2],
                       radius=12, fill=(15, 23, 42, 160))

    for i, line in enumerate(wrapped):
        bbox = draw.textbbox((0, 0), line, font=font_text)
        tw = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - tw) // 2
        y = start_y + i * 65
        # Text shadow
        draw.text((x + 1, y + 1), line, fill=(0, 0, 0, 100), font=font_text)
        draw.text((x, y), line, fill=_hex_to_rgba(TEXT_COLOR), font=font_text)

    # Paper title at bottom (small)
    if paper_title:
        font_paper = _get_font(18)
        short_title = paper_title[:60] + ("..." if len(paper_title) > 60 else "")
        draw.text((60, VIDEO_HEIGHT - 50), short_title,
                  fill=_hex_to_rgba("#667085", 150), font=font_paper)

    # Progress bar at bottom
    bar_y = VIDEO_HEIGHT - 12
    draw.rectangle([0, bar_y, VIDEO_WIDTH, bar_y + 12],
                   fill=_hex_to_rgba("#1e293b", 200))
    progress = (section_index + 1) / total_sections
    draw.rectangle([0, bar_y, int(VIDEO_WIDTH * progress), bar_y + 12],
                   fill=_hex_to_rgba(ACCENT_COLOR, 220))

    # Section number indicator
    font_num = _get_font(120, bold=True)
    num_text = f"{section_index + 1:02d}"
    draw.text((VIDEO_WIDTH - 220, 40), num_text,
              fill=_hex_to_rgba(ACCENT_COLOR, 40), font=font_num)

    img.convert("RGB").save(output_path, "PNG")
    return output_path


def create_ending_slide(title: str, paper_url: str, output_path: str,
                        bg_image: str = None) -> str:
    """Create the ending slide."""
    if bg_image:
        img = _prepare_background(bg_image)
    else:
        img = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), _hex_to_rgba(BG_COLOR))

    draw = ImageDraw.Draw(img)
    _draw_decorative_lines(draw, VIDEO_WIDTH, VIDEO_HEIGHT)

    # "感谢观看" large text
    font_big = _get_font(56, bold=True)
    text = "感谢观看"
    bbox = draw.textbbox((0, 0), text, font=font_big)
    tw = bbox[2] - bbox[0]
    draw.text(((VIDEO_WIDTH - tw) // 2 + 2, 332), text,
              fill=(0, 0, 0, 120), font=font_big)
    draw.text(((VIDEO_WIDTH - tw) // 2, 330), text,
              fill=_hex_to_rgba(TITLE_COLOR), font=font_big)

    # Accent line
    draw.rectangle([VIDEO_WIDTH // 2 - 100, 420, VIDEO_WIDTH // 2 + 100, 423],
                   fill=_hex_to_rgba(ACCENT_COLOR, 200))

    # Paper title
    font_title = _get_font(30)
    wrapped = _wrap_text(title, font_title, VIDEO_WIDTH - 300)
    y = 460
    for line in wrapped:
        bbox = draw.textbbox((0, 0), line, font=font_title)
        tw = bbox[2] - bbox[0]
        draw.text(((VIDEO_WIDTH - tw) // 2, y), line,
                  fill=_hex_to_rgba(TEXT_COLOR), font=font_title)
        y += 48

    # URL chip
    if paper_url:
        font_url = _get_font(22)
        bbox = draw.textbbox((0, 0), paper_url, font=font_url)
        tw = bbox[2] - bbox[0]
        chip_x = (VIDEO_WIDTH - tw) // 2 - 16
        chip_y = y + 30
        _draw_rounded_rect(draw, [chip_x, chip_y, chip_x + tw + 32, chip_y + 40],
                           radius=20, fill=_hex_to_rgba(ACCENT_COLOR, 180))
        draw.text((chip_x + 16, chip_y + 7), paper_url,
                  fill=_hex_to_rgba(BG_COLOR), font=font_url)

    img.convert("RGB").save(output_path, "PNG")
    return output_path


def generate_slides(script: dict, paper: dict, output_dir: str) -> list:
    """Generate all slides with background images."""
    os.makedirs(output_dir, exist_ok=True)
    sections = script.get("sections", [])
    theme = paper.get("theme", "")
    slides = []

    # Pre-fetch background images
    print("  Fetching background images...")
    bg_images = []
    for i in range(len(sections) + 2):
        img_path = fetch_theme_image(theme, i, os.path.join(output_dir, "_bg"))
        bg_images.append(img_path)

    # 1. Title slide
    title_path = os.path.join(output_dir, "slide_00_title.png")
    create_title_slide(
        script.get("title", paper.get("title", "")),
        paper.get("theme_label", ""),
        title_path,
        bg_image=bg_images[0],
    )
    slides.append({"path": title_path, "duration_sec": 3.0, "type": "title"})

    # 2. Section slides
    for i, section in enumerate(sections):
        slide_path = os.path.join(output_dir, f"slide_{i+1:02d}_section.png")
        create_section_slide(
            section.get("label", ""),
            section.get("text", ""),
            i,
            len(sections),
            slide_path,
            bg_image=bg_images[i + 1] if i + 1 < len(bg_images) else None,
            paper_title=paper.get("title", ""),
        )
        slides.append({
            "path": slide_path,
            "duration_sec": section.get("duration_sec", 40),
            "type": "section",
        })

    # 3. Ending slide
    ending_path = os.path.join(output_dir, f"slide_{len(sections)+1:02d}_ending.png")
    detail_url = paper.get("detail_url", "")
    full_url = f"https://papers.dast.ai/{detail_url}" if detail_url else ""
    create_ending_slide(
        paper.get("title", ""), full_url, ending_path,
        bg_image=bg_images[-1] if bg_images else None,
    )
    slides.append({"path": ending_path, "duration_sec": 4.0, "type": "ending"})

    return slides


def _wrap_text(text: str, font, max_width: int) -> list:
    """Wrap text to fit within max_width pixels."""
    lines = []
    current_line = ""

    for char in text:
        test_line = current_line + char
        try:
            bbox = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]
        except Exception:
            width = len(test_line) * 20

        if width > max_width and current_line:
            lines.append(current_line)
            current_line = char
        else:
            current_line = test_line

    if current_line:
        lines.append(current_line)

    return lines


if __name__ == "__main__":
    os.makedirs("/tmp/slides_test", exist_ok=True)
    create_title_slide(
        "AI评分系统竟能被'欺骗'？揭秘强化学习中的奖励陷阱！",
        "安全、治理与可靠性",
        "/tmp/slides_test/title.png",
    )
    create_section_slide(
        "问题引入",
        "你有没有想过，AI在学习过程中可能会作弊？想象一下，一个评分系统被模型巧妙利用，获得高分但实际质量不佳。",
        0, 4,
        "/tmp/slides_test/section.png",
    )
    print("Done! Check /tmp/slides_test/")
