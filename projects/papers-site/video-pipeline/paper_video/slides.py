"""HTML slide → PNG rendering via Playwright, with composite AI backdrops.

Reads the high-quality templates from ``slide_templates.render_slide``
(dark sci-fi neon style) and composites the textless AI background behind
all code-rendered text overlays.
"""

from __future__ import annotations

import os
import sys
import base64
from pathlib import Path
from typing import Any

_PARENT = str(Path(__file__).resolve().parents[1])
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

from slide_templates import render_slide as _render_html


def _png_to_data_uri(png_path: str) -> str:
    with open(png_path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


def _compose_section_with_bg(section: dict, bg_path: str | None) -> str:
    """Render the HTML slide with a textless AI background composited under the text overlays."""
    # Use the existing slide_templates renderer (handles bg_image_path for full-bleed).
    # But we *don't* want full-bleed when we have a backdrop — we want text on top.
    # So we use the normal renderer and inject the background via CSS.
    on_screen = section.get("on_screen", {})
    slide_type = section.get("type", "problem")

    # For AI backdrops, we inject the background image as a CSS background
    # and let the template draw text on top.
    if bg_path and os.path.exists(bg_path):
        # Use the non-image code path (renders text overlays via template)
        html = _render_html(section)
        # Inject the background behind the text
        b64 = _png_to_data_uri(bg_path)
        injected_css = f"""
body {{
  background: url('{b64}') center/cover no-repeat !important;
}}
body::before {{
  background: rgba(0,0,0,0.55) !important;
}}
"""
        html = html.replace("/* circuit pattern */", "")
        html = html.replace("</style>", f"{injected_css}</style>")
        return html
    else:
        return _render_html(section)


def render_slides(
    sections: list[dict[str, Any]],
    out_dir: str | Path,
    bg_images: dict[int, str] | None = None,
) -> dict[int, str]:
    """Render HTML slides → PNG. Returns {index: png_path}."""
    out_dir = Path(out_dir)
    slides_html_dir = out_dir / "slides_html"
    slides_png_dir = out_dir / "slides_png"
    slides_html_dir.mkdir(parents=True, exist_ok=True)
    slides_png_dir.mkdir(parents=True, exist_ok=True)

    from playwright.sync_api import sync_playwright

    slide_paths: dict[int, str] = {}
    browser = None

    try:
        browser = sync_playwright().start().chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})

        for i, sec in enumerate(sections):
            html_path = slides_html_dir / f"slide_{i:02d}.html"
            png_path = slides_png_dir / f"slide_{i:02d}.png"

            if png_path.exists():
                slide_paths[i] = str(png_path)
                print(f"  [slide] Slide {i:02d}: SKIP (exists)")
                continue

            bg = bg_images.get(i) if bg_images else None
            print(f"  [slide] Slide {i:02d}: {sec.get('label', '')[:30]}...", end=" ", flush=True)

            try:
                html = _compose_section_with_bg(sec, bg)
                html_path.write_text(html, encoding="utf-8")
                page.goto(f"file://{html_path.resolve()}")
                page.wait_for_timeout(600)
                page.screenshot(path=str(png_path), type="png")
                slide_paths[i] = str(png_path)
                print("OK")
            except Exception as e:
                print(f"ERROR: {e}")
    finally:
        if browser:
            browser.close()

    return slide_paths
