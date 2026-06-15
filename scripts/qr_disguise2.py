#!/usr/bin/env python3
"""Disguise QR code into a scenic landscape photo."""

import sys
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageEnhance, ImageFont
import random
import math


def create_landscape(w, h):
    """Create a beautiful landscape scene."""
    img = Image.new("RGB", (w, h))
    pixels = np.zeros((h, w, 3), dtype=np.uint8)

    # Sky gradient (sunset colors)
    for y in range(h):
        ratio = y / h
        if ratio < 0.45:  # sky
            r = int(20 + 180 * (ratio / 0.45))
            g = int(30 + 120 * (ratio / 0.45))
            b = int(80 + 100 * (1 - ratio / 0.45))
        elif ratio < 0.55:  # horizon glow
            r = int(220 + 35 * ((ratio - 0.45) / 0.1))
            g = int(140 + 60 * ((ratio - 0.45) / 0.1))
            b = int(60 + 40 * ((ratio - 0.45) / 0.1))
        else:  # ground / dark foreground
            t = (ratio - 0.55) / 0.45
            r = int(255 * (1 - t * 0.7))
            g = int(180 * (1 - t * 0.6))
            b = int(80 * (1 - t * 0.5))
        pixels[y, :] = [r, g, b]

    img = Image.fromarray(pixels)
    draw = ImageDraw.Draw(img)

    # Sun circle
    sun_x, sun_y, sun_r = int(w * 0.7), int(h * 0.38), 50
    for i in range(sun_r, 0, -1):
        alpha = int(255 * (1 - i / sun_r) * 0.8)
        color = (255, min(255, 200 + alpha // 5), min(255, 100 + alpha // 3))
        draw.ellipse(
            [sun_x - i, sun_y - i, sun_x + i, sun_y + i], fill=color
        )

    # Mountains
    random.seed(7)
    for layer in range(3):
        base_y = int(h * (0.42 + layer * 0.06))
        shade = 40 + layer * 30
        points = [(0, h)]
        for x in range(0, w + 1, 8):
            noise = random.randint(-30, 30) + int(25 * math.sin(x * 0.008 + layer))
            points.append((x, base_y + noise))
        points.append((w, h))
        draw.polygon(points, fill=(shade, shade + 10, shade + 20))

    # Trees silhouettes
    for _ in range(20):
        tx = random.randint(0, w)
        ty = int(h * 0.55) + random.randint(0, int(h * 0.2))
        th = random.randint(30, 80)
        tw = random.randint(15, 35)
        trunk_w = max(3, tw // 5)
        # trunk
        draw.rectangle(
            [tx - trunk_w // 2, ty, tx + trunk_w // 2, ty + th // 2],
            fill=(20, 25, 15),
        )
        # canopy
        for j in range(3):
            cy = ty + j * (th // 6)
            cw = tw - j * (tw // 5)
            draw.ellipse(
                [tx - cw // 2, cy - th // 8, tx + cw // 2, cy + th // 4],
                fill=(15 + random.randint(0, 20), 30 + random.randint(0, 20), 10),
            )

    # Stars in upper sky
    for _ in range(60):
        sx = random.randint(0, w)
        sy = random.randint(0, int(h * 0.3))
        brightness = random.randint(180, 255)
        draw.point((sx, sy), fill=(brightness, brightness, brightness))

    return img


def disguise_qr(input_path: str, output_path: str):
    # Load and prepare QR
    qr_img = Image.open(input_path).convert("RGBA")
    qr_w, qr_h = qr_img.size

    # Canvas size (portrait phone wallpaper)
    cw, ch = 900, 1400

    # Create landscape background
    bg = create_landscape(cw, ch)

    # Make QR smaller and rotate it slightly, then blend into sky area
    qr_display_size = int(cw * 0.42)
    qr_resized = qr_img.resize((qr_display_size, qr_display_size), Image.LANCZOS)

    # Slight rotation for natural feel
    qr_rotated = qr_resized.rotate(
        2.5, expand=True, resample=Image.BICUBIC, fillcolor=(0, 0, 0, 0)
    )

    # Position: slightly off-center in upper area (sky region)
    rw, rh = qr_rotated.size
    px = (cw - rw) // 2 + 20
    py = int(ch * 0.12)

    # Blend QR into background with low opacity and color tint
    bg_rgba = bg.convert("RGBA")

    # Create a subtle "paper/card" behind QR
    card_pad = 25
    card = Image.new("RGBA", (rw + card_pad * 2, rh + card_pad * 2), (0, 0, 0, 0))
    card_draw = ImageDraw.Draw(card)
    # Rounded rectangle card
    card_draw.rounded_rectangle(
        [0, 0, rw + card_pad * 2 - 1, rh + card_pad * 2 - 1],
        radius=15,
        fill=(255, 255, 255, 160),
    )
    # Add subtle border
    card_draw.rounded_rectangle(
        [0, 0, rw + card_pad * 2 - 1, rh + card_pad * 2 - 1],
        radius=15,
        outline=(200, 200, 200, 100),
        width=2,
    )

    # Paste card then QR onto background
    card_x = px - card_pad
    card_y = py - card_pad
    bg_rgba.paste(card, (card_x, card_y), card)
    bg_rgba.paste(qr_rotated, (px, py), qr_rotated)

    # Add "扫描二维码" text at bottom in Chinese
    draw = ImageDraw.Draw(bg_rgba)
    try:
        # Try to find a Chinese font
        import glob
        cn_fonts = glob.glob("/usr/share/fonts/**/Noto*CJK*.ttf", recursive=True)
        if not cn_fonts:
            cn_fonts = glob.glob("/usr/share/fonts/**/wqy*.ttf", recursive=True)
        if not cn_fonts:
            cn_fonts = glob.glob("/usr/share/fonts/**/*CJK*.otf", recursive=True)
        if cn_fonts:
            font = ImageFont.truetype(cn_fonts[0], 28)
        else:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()

    # Decorative text
    text = "长按识别二维码"
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
    except:
        tw = len(text) * 20
    draw.text(
        ((cw - tw) // 2, ch - 120),
        text,
        fill=(255, 255, 255, 200),
        font=font,
    )

    result = bg_rgba.convert("RGB")

    # Slight overall softening
    result = result.filter(ImageFilter.GaussianBlur(radius=0.3))

    result.save(output_path, quality=95)
    print(f"Saved: {output_path} ({result.size[0]}x{result.size[1]})")


if __name__ == "__main__":
    inp = sys.argv[1] if len(sys.argv) > 1 else "qr_input.png"
    out = sys.argv[2] if len(sys.argv) > 2 else "qr_disguised.png"
    disguise_qr(inp, out)
