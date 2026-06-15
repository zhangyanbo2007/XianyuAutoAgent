#!/usr/bin/env python3
"""Disguise a QR code by embedding it into a scenic/artistic background."""

import sys
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw, ImageFont
import random
import math


def create_scenic_background(width, height):
    """Create a gradient background with abstract shapes to look like art/photo."""
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    # Warm gradient background (like a sunset/photo)
    for y in range(height):
        r = int(40 + 80 * (y / height))
        g = int(60 + 60 * (y / height))
        b = int(100 + 80 * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Add some decorative circles (bokeh-like effect)
    random.seed(42)
    for _ in range(15):
        cx = random.randint(0, width)
        cy = random.randint(0, height)
        radius = random.randint(20, 80)
        alpha = random.randint(20, 60)
        color = (
            random.randint(100, 255),
            random.randint(100, 255),
            random.randint(100, 255),
        )
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=(*color, alpha),
        )
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    # Add subtle grid lines (looks like a notebook/paper texture)
    draw2 = ImageDraw.Draw(img)
    for x in range(0, width, 40):
        draw2.line([(x, 0), (x, height)], fill=(255, 255, 255, 15), width=1)
    for y in range(0, height, 40):
        draw2.line([(0, y), (width, y)], fill=(255, 255, 255, 15), width=1)

    return img


def disguise_qr(input_path: str, output_path: str):
    img = Image.open(input_path).convert("RGBA")
    orig_w, orig_h = img.size

    # Target: make it ~800x1000 (portrait, like a phone screenshot)
    target_w = 800
    target_h = 1000

    # Create scenic background
    bg = create_scenic_background(target_w, target_h)

    # Resize QR to fit in center area (about 60% of width)
    qr_size = int(target_w * 0.55)
    qr_resized = img.resize((qr_size, qr_size), Image.LANCZOS)

    # Apply slight artistic effect to QR: soften edges, reduce contrast a bit
    qr_gray = qr_resized.convert("L")

    # Make QR semi-transparent and tinted to blend with background
    # Create a color-matched version
    qr_arr = np.array(qr_resized).astype(np.float64)

    # Tint the QR to match background warm tones
    tint_r = np.full_like(qr_arr[:, :, 0], 180)
    tint_g = np.full_like(qr_arr[:, :, 1], 140)
    tint_b = np.full_like(qr_arr[:, :, 2], 120)

    # Where QR is dark (the black modules), use tinted dark color
    # Where QR is light (white), make semi-transparent
    mask = np.mean(qr_arr[:, :, :3], axis=2) < 128  # dark pixels

    for c, tint in enumerate([tint_r, tint_g, tint_b]):
        qr_arr[:, :, c] = np.where(mask, tint * 0.3, qr_arr[:, :, c])

    qr_tinted = Image.fromarray(qr_arr.astype(np.uint8))

    # Add a subtle paper-like texture overlay
    texture = Image.new("RGBA", (qr_size, qr_size), (0, 0, 0, 0))
    tex_draw = ImageDraw.Draw(texture)
    random.seed(123)
    for _ in range(200):
        tx = random.randint(0, qr_size)
        ty = random.randint(0, qr_size)
        ts = random.randint(1, 3)
        tex_draw.rectangle(
            [tx, ty, tx + ts, ty + ts],
            fill=(random.randint(150, 255), random.randint(150, 255), random.randint(150, 255), 30),
        )

    qr_tinted = Image.alpha_composite(qr_tinted, texture)

    # Paste QR onto background with slight rotation for natural look
    # Create a larger canvas to allow rotation
    paste_x = (target_w - qr_size) // 2
    paste_y = (target_h - qr_size) // 2 - 30  # slightly above center

    # Slight rotation (-2 to 2 degrees)
    qr_rotated = qr_tinted.rotate(1.5, expand=True, resample=Image.BICUBIC, fillcolor=(0, 0, 0, 0))

    # Paste with rotation
    bg_rgba = bg.convert("RGBA")
    rot_w, rot_h = qr_rotated.size
    paste_x2 = (target_w - rot_w) // 2
    paste_y2 = (target_h - rot_h) // 2 - 30

    # Add shadow behind QR
    shadow = Image.new("RGBA", (rot_w + 20, rot_h + 20), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rectangle([10, 10, rot_w + 10, rot_h + 10], fill=(0, 0, 0, 40))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=8))

    bg_rgba.paste(shadow, (paste_x2 - 5, paste_y2 + 5), shadow)
    bg_rgba.paste(qr_rotated, (paste_x2, paste_y2), qr_rotated)

    # Add some "handwritten" text at bottom to make it look like a note
    draw_final = ImageDraw.Draw(bg_rgba)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font = ImageFont.load_default()

    # Add decorative elements
    draw_final.text(
        (target_w // 2 - 80, target_h - 100),
        "~ scan me ~",
        fill=(255, 255, 255, 180),
        font=font,
    )

    # Final output
    result = bg_rgba.convert("RGB")

    # Add slight overall blur to blend everything
    result = result.filter(ImageFilter.GaussianBlur(radius=0.5))

    result.save(output_path, quality=95)
    print(f"Saved: {output_path} ({result.size[0]}x{result.size[1]})")


if __name__ == "__main__":
    inp = sys.argv[1] if len(sys.argv) > 1 else "qr_input.png"
    out = sys.argv[2] if len(sys.argv) > 2 else "qr_disguised.png"
    disguise_qr(inp, out)
