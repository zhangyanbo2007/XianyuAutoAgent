"""Generate slides with AI images as primary visual, minimal text overlay."""

import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from config import VIDEO_WIDTH, VIDEO_HEIGHT
from image_fetcher import fetch_theme_image
from chart_generator import (
    bar_chart, grouped_bar_chart, line_chart, radar_chart, ranking_chart,
    ACCENT_BLUE, ACCENT_PINK, ACCENT_GREEN, ACCENT_PURPLE, ACCENT_ORANGE
)


def _get_font(size):
    font_paths = [
        os.path.expanduser("~/.local/share/fonts/NotoSansCJKsc-Regular.otf"),
        "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc",
    ]
    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _wrap_text(text, font, max_width):
    lines, current = [], ""
    for char in text:
        test = current + char
        try:
            bbox = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] > max_width and current:
                lines.append(current)
                current = char
            else:
                current = test
        except:
            current = test
    if current:
        lines.append(current)
    return lines


def _prepare_bg(image_path, w=VIDEO_WIDTH, h=VIDEO_HEIGHT):
    """Load and prepare background image."""
    try:
        bg = Image.open(image_path).convert("RGBA")
        bg = bg.resize((w, h), Image.LANCZOS)
        # Slight darkening to make text readable
        bg = ImageEnhance.Brightness(bg).enhance(0.7)
        return bg
    except:
        return Image.new("RGBA", (w, h), (15, 15, 25, 255))


def _add_title_overlay(img, title, subtitle=None):
    """Add minimal title overlay at bottom of image."""
    draw = ImageDraw.Draw(img)
    font_title = _get_font(42)

    # Bottom gradient bar for text readability
    bar_height = 180
    for y in range(VIDEO_HEIGHT - bar_height, VIDEO_HEIGHT):
        alpha = int(200 * ((y - (VIDEO_HEIGHT - bar_height)) / bar_height))
        draw.line([(0, y), (VIDEO_WIDTH, y)], fill=(10, 10, 20, alpha))

    # Title text - centered at bottom
    wrapped = _wrap_text(title, font_title, VIDEO_WIDTH - 200)
    y = VIDEO_HEIGHT - bar_height + 20
    for line in wrapped[:2]:  # Max 2 lines
        bbox = draw.textbbox((0, 0), line, font=font_title)
        tw = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - tw) // 2
        draw.text((x+1, y+1), line, fill=(0, 0, 0, 180), font=font_title)
        draw.text((x, y), line, fill=(255, 255, 255, 240), font=font_title)
        y += 55

    # Subtitle if provided
    if subtitle:
        font_sub = _get_font(24)
        bbox = draw.textbbox((0, 0), subtitle, font=font_sub)
        tw = bbox[2] - bbox[0]
        draw.text(((VIDEO_WIDTH - tw) // 2, y + 5), subtitle,
                  fill=(150, 200, 255, 200), font=font_sub)


def _add_label_chip(draw, label):
    """Add section label chip at top-left."""
    font = _get_font(22)
    bbox = draw.textbbox((0, 0), label, font=font)
    lw = bbox[2] - bbox[0] + 24
    draw.rounded_rectangle([20, 20, 20 + lw, 55], radius=8,
                           fill=(56, 189, 248, 200))
    draw.text((32, 26), label, fill=(10, 10, 30, 255), font=font)


def create_title_slide_v2(video_title, paper_title, theme, bg_image, output_path):
    """Create cinematic title slide with AI background."""
    img = _prepare_bg(bg_image) if bg_image else Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (15, 15, 25, 255))

    # Full dark overlay for title readability
    overlay = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 120))
    img = Image.alpha_composite(img, overlay)

    draw = ImageDraw.Draw(img)
    font_title = _get_font(56)

    # Title centered
    wrapped = _wrap_text(video_title, font_title, VIDEO_WIDTH - 300)
    total_h = len(wrapped) * 72
    y = (VIDEO_HEIGHT - total_h) // 2
    for line in wrapped[:3]:
        bbox = draw.textbbox((0, 0), line, font=font_title)
        tw = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - tw) // 2
        draw.text((x+2, y+2), line, fill=(0, 0, 0, 200), font=font_title)
        draw.text((x, y), line, fill=(255, 255, 255, 255), font=font_title)
        y += 72

    # Paper title
    font_sub = _get_font(26)
    short = paper_title[:60] + "..." if len(paper_title) > 60 else paper_title
    bbox = draw.textbbox((0, 0), short, font=font_sub)
    tw = bbox[2] - bbox[0]
    draw.text(((VIDEO_WIDTH - tw) // 2, y + 20), short, fill=(180, 200, 220, 200), font=font_sub)

    # Branding
    font_brand = _get_font(18)
    draw.text((VIDEO_WIDTH - 200, VIDEO_HEIGHT - 40), "DAST Papers · AI解读",
              fill=(100, 120, 140, 150), font=font_brand)

    img.convert("RGB").save(output_path, "PNG")
    return output_path


def create_content_slide_v2(section, paper, bg_image, chart_dir, output_path):
    """Create content slide with AI image as primary visual."""
    label = section.get("label", "")
    text = section.get("text", "")

    img = _prepare_bg(bg_image) if bg_image else Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (15, 15, 25, 255))
    draw = ImageDraw.Draw(img)

    # Add label chip
    _add_label_chip(draw, label)

    # Add title overlay at bottom (SHORT text only)
    short_title = text[:60] + "..." if len(text) > 60 else text
    _add_title_overlay(img, short_title)

    # Branding
    font_brand = _get_font(16)
    draw.text((VIDEO_WIDTH - 200, 20), f"#{section.get('id', 0):02d}",
              fill=(56, 189, 248, 80), font=_get_font(120))

    img.convert("RGB").save(output_path, "PNG")
    return output_path


def create_chart_slide_v2(section, paper, chart_path, bg_image, output_path):
    """Create slide with embedded matplotlib chart."""
    img = _prepare_bg(bg_image) if bg_image else Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (15, 15, 25, 255))
    draw = ImageDraw.Draw(img)

    _add_label_chip(draw, section.get("label", ""))

    # Embed chart centered
    try:
        chart = Image.open(chart_path).convert("RGBA")
        max_w = VIDEO_WIDTH - 200
        max_h = VIDEO_HEIGHT - 200
        ratio = min(max_w / chart.width, max_h / chart.height)
        new_w = int(chart.width * ratio)
        new_h = int(chart.height * ratio)
        chart = chart.resize((new_w, new_h), Image.LANCZOS)
        x = (VIDEO_WIDTH - new_w) // 2
        y = (VIDEO_HEIGHT - new_h) // 2
        img.paste(chart, (x, y), chart)
    except Exception as e:
        print(f"  ⚠ Chart embed failed: {e}")

    font_brand = _get_font(16)
    draw.text((VIDEO_WIDTH - 200, 20), f"#{section.get('id', 0):02d}",
              fill=(56, 189, 248, 80), font=_get_font(120))

    img.convert("RGB").save(output_path, "PNG")
    return output_path


def create_ending_slide_v2(video_title, key_points, paper, bg_image, output_path):
    """Create ending slide."""
    img = _prepare_bg(bg_image) if bg_image else Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (15, 15, 25, 255))

    # Dark overlay
    overlay = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 140))
    img = Image.alpha_composite(img, overlay)

    draw = ImageDraw.Draw(img)

    # "核心发现" header
    font_header = _get_font(48)
    header = "核心发现"
    bbox = draw.textbbox((0, 0), header, font=font_header)
    tw = bbox[2] - bbox[0]
    draw.text(((VIDEO_WIDTH - tw) // 2, 150), header, fill=(255, 255, 255, 255), font=font_header)

    # Accent line
    draw.rectangle([VIDEO_WIDTH//2 - 80, 220, VIDEO_WIDTH//2 + 80, 223], fill=(56, 189, 248, 200))

    # Key points - large text
    font_point = _get_font(32)
    colors = [(56, 189, 248), (244, 114, 182), (74, 222, 128), (167, 139, 250)]
    y = 260
    for i, point in enumerate(key_points[:3]):
        color = colors[i % len(colors)]
        wrapped = _wrap_text(f"• {point[:50]}", font_point, VIDEO_WIDTH - 300)
        for line in wrapped[:2]:
            draw.text((100, y), line, fill=color + (240,), font=font_point)
            y += 45
        y += 15

    # Branding
    font_brand = _get_font(18)
    draw.text((VIDEO_WIDTH - 200, VIDEO_HEIGHT - 40), "DAST Papers · AI解读",
              fill=(100, 120, 140, 150), font=font_brand)

    img.convert("RGB").save(output_path, "PNG")
    return output_path


def generate_all_slides_v2(script, paper, output_dir, ai_images=None):
    """Generate all slides."""
    os.makedirs(output_dir, exist_ok=True)
    chart_dir = os.path.join(output_dir, "_charts")
    os.makedirs(chart_dir, exist_ok=True)

    sections = script.get("sections", [])
    theme = paper.get("theme", "")

    # Use AI images if available, fallback to Unsplash
    bg_images = []
    for i in range(len(sections)):
        if ai_images and i in ai_images:
            bg_images.append(ai_images[i])
        else:
            img = fetch_theme_image(theme, i, os.path.join(output_dir, "_bg"))
            bg_images.append(img)

    slides = []
    for section in sections:
        sid = section.get("id", 0)
        stype = section.get("type", "detail")
        output_path = os.path.join(output_dir, f"slide_{sid:02d}.png")
        bg = bg_images[sid] if sid < len(bg_images) else None

        if stype == "title":
            create_title_slide_v2(
                script.get("video_title", ""),
                paper.get("title", ""),
                paper.get("theme_label", ""),
                bg, output_path,
            )
        elif stype == "ending":
            key_points = [s.get("text", "")[:50] for s in sections
                          if s.get("type") in ("chart", "detail")][:3]
            create_ending_slide_v2(
                script.get("video_title", ""),
                key_points, paper, bg, output_path,
            )
        elif stype == "chart":
            chart_data = section.get("chart_data", {})
            chart_path = os.path.join(chart_dir, f"chart_{sid}.png")
            _generate_chart(chart_data, chart_path)
            if os.path.exists(chart_path):
                create_chart_slide_v2(section, paper, chart_path, bg, output_path)
            else:
                create_content_slide_v2(section, paper, bg, chart_dir, output_path)
        else:
            create_content_slide_v2(section, paper, bg, chart_dir, output_path)

        slides.append({
            "path": output_path,
            "duration_sec": section.get("duration_sec", 30),
            "type": stype,
        })

    return slides


def _generate_chart(chart_data, output_path):
    """Generate matplotlib chart from data."""
    if not chart_data:
        return
    chart_type = chart_data.get("type", "bar")
    title = chart_data.get("title", "")
    labels = chart_data.get("labels", [])
    values = chart_data.get("values", [])
    colors = chart_data.get("colors", None)
    if not labels or not values:
        return
    try:
        if chart_type == "bar":
            bar_chart(title, labels, values, colors, output_path=output_path)
        elif chart_type == "grouped_bar":
            grouped_bar_chart(title, labels, chart_data.get("groups", {}), output_path=output_path)
        elif chart_type == "line":
            line_chart(title, labels, chart_data.get("series", {}), output_path=output_path)
        elif chart_type == "radar":
            radar_chart(title, labels, chart_data.get("series", {}), output_path=output_path)
        elif chart_type == "ranking":
            ranking_chart(title, labels, values, colors, output_path=output_path)
    except Exception as e:
        print(f"  ⚠ Chart failed: {e}")


if __name__ == "__main__":
    print("Slide generator v2 ready")
