"""Render longform visual plans to reviewable artifacts."""

from __future__ import annotations

import base64
import re
from pathlib import Path
from .content_spec import content_labels, content_pair
from .models import RenderResult, VisualScene
from .templates import render_slide_html

_TINY_PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
_TEXT_TOKEN_RE = re.compile(r"[A-Za-z0-9_^./:-]+|[\u4e00-\u9fff]+|[^\s]")
_ASCII_TOKEN_RE = re.compile(r"^[A-Za-z0-9_^./:-]+$")
_CONCEPT_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{3,}")
_CONCEPT_STOPWORDS = {
    "cinematic", "dark", "background", "neon", "with", "text", "readable",
    "watermark", "illustration", "visual", "prompt", "scene", "quality",
    "overlays", "glowing", "holographic", "paper", "finding",
    "method", "problem", "future", "limitation", "takeaway",
}


def _split_long_token(token: str, max_chars: int) -> list[str]:
    if len(token) <= max_chars:
        return [token]
    lines: list[str] = []
    current = ""
    for char in token:
        current += char
        if len(current) >= max_chars or char in "。；！？":
            lines.append(current.strip())
            current = ""
    if current.strip():
        lines.append(current.strip())
    return lines


def _join_wrapped_token(current: str, token: str) -> str:
    if not current:
        return token
    if token == "/":
        return f"{current} /"
    if current.endswith("/"):
        return f"{current} {token}"
    if _ASCII_TOKEN_RE.match(token) and _ASCII_TOKEN_RE.match(current[-1]):
        return f"{current} {token}"
    return f"{current}{token}"


def _wrap_text(value: str, max_chars: int) -> list[str]:
    """Wrap mixed Chinese/English display text without splitting English words."""
    tokens = _TEXT_TOKEN_RE.findall(" ".join(str(value).strip().split()))
    lines: list[str] = []
    current = ""
    for token in tokens:
        for segment in _split_long_token(token, max_chars):
            candidate = _join_wrapped_token(current, segment)
            if current and len(candidate) > max_chars:
                lines.append(current)
                current = segment
            else:
                current = candidate
    if current:
        lines.append(current)
    return lines


def _concept_labels(scene: VisualScene) -> tuple[str, str]:
    return content_pair(scene)


def _concept_list(scene: VisualScene, count: int, fallback: list[str]) -> list[str]:
    values = content_labels(scene, count=count)
    while len(values) < count:
        values.append(fallback[len(values) % len(fallback)])
    return values


def _font_path() -> str | None:
    candidates = [Path.home() / ".local/share/fonts/NotoSansCJKsc-Regular.otf", Path(__file__).resolve().parents[4] / "pipeline/fonts/NotoSansCJKsc-Regular.otf", Path("/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc")]
    for path in candidates:
        if path.exists():
            return str(path)
    return None


def _fit_background(background_path: Path, size: tuple[int, int]):
    from PIL import Image, ImageEnhance, ImageOps

    bg = Image.open(background_path).convert("RGB")
    resampling = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
    bg = ImageOps.fit(bg, size, method=resampling)
    bg = ImageEnhance.Brightness(bg).enhance(0.42)
    return bg


def _render_png(scene: VisualScene, path: Path, background_path: Path | str | None = None) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        path.write_bytes(_TINY_PNG)
        return

    width, height = 1920, 1080
    bg_path = Path(background_path) if background_path else None
    has_background = bool(bg_path and bg_path.exists() and bg_path.stat().st_size > 0)
    img = _fit_background(bg_path, (width, height)) if has_background else Image.new("RGB", (width, height), "#05070d")
    draw = ImageDraw.Draw(img)
    font_file = _font_path()

    def font(size: int):
        return ImageFont.truetype(font_file, size) if font_file else ImageFont.load_default()

    accent = {"cyan": "#22d3ee", "magenta": "#f472b6", "green": "#4ade80", "gold": "#fbbf24"}.get(scene.accent, "#22d3ee")
    palette = [accent, "#f472b6", "#60a5fa", "#fbbf24", "#4ade80"]

    # Background grid is only a fallback decoration. AI backgrounds already
    # carry texture, so the foreground should focus on paper content.
    if not has_background:
        for x in range(120, width, 160):
            draw.line((x, 120, x, height - 170), fill="#0b1220", width=1)
        for y in range(180, height - 170, 120):
            draw.line((72, y, width - 72, y), fill="#0b1220", width=1)
    draw.rectangle((28, 28, width - 28, height - 28), outline=accent, width=3)
    draw.text((72, 58), f"{scene.template} · Scene {scene.index + 1:02d}", fill=accent, font=font(30))
    draw.text((72, 122), scene.title, fill="#f8fafc", font=font(60))

    anchor_lines = _wrap_text(scene.paper_anchor, 24)[:3]
    for i, line in enumerate(anchor_lines):
        draw.text((width - 650, 64 + i * 34), line, fill="#94a3b8", font=font(24))

    visual_box = (120, 275, width - 120, 785)
    if has_background:
        draw.rounded_rectangle(visual_box, radius=30, outline=accent, width=1)
    else:
        draw.rounded_rectangle(visual_box, radius=30, outline=accent, width=3, fill="#07111f")

    def hero_title() -> None:
        left_label, right_label = _concept_labels(scene)
        draw.ellipse((560, 355, 960, 700), fill="#7c4a03", outline="#fbbf24", width=5)
        draw.ellipse((960, 355, 1360, 700), fill="#0c4a6e", outline="#22d3ee", width=5)
        draw.line((960, 380, 960, 690), fill="#f8fafc", width=4)
        for i in range(8):
            y = 395 + i * 36
            draw.arc((600, y, 900, y + 120), 190, 350, fill="#fde68a", width=3)
            draw.line((1000, y + 25, 1300, y + 65), fill="#67e8f9", width=3)
            draw.ellipse((1290, y + 55, 1310, y + 75), fill="#22d3ee")
        draw.text((665, 505), left_label, fill="#fff7ed", font=font(40 if len(left_label) <= 8 else 32))
        draw.text((1035, 505), right_label, fill="#ecfeff", font=font(40 if len(right_label) <= 8 else 32))

    def core_question() -> None:
        left_label, right_label = _concept_labels(scene)
        draw.rounded_rectangle((360, 430, 900, 610), radius=26, fill="#111827", outline="#60a5fa", width=4)
        draw.text((420, 485), left_label, fill="#bfdbfe", font=font(44 if len(left_label) <= 10 else 34))
        draw.text((930, 405), "≠", fill="#f472b6", font=font(112))
        draw.rounded_rectangle((1080, 430, 1540, 610), radius=26, fill="#111827", outline="#fbbf24", width=4)
        draw.text((1160, 485), right_label, fill="#fde68a", font=font(48 if len(right_label) <= 10 else 34))
        for x, y in [(520, 665), (820, 680), (1170, 665), (1430, 685)]:
            draw.ellipse((x, y, x + 34, y + 34), fill=accent)

    def metric_cards() -> None:
        metrics = scene.data.get("metrics") or [{"label": "Scenes", "value": "25"}, {"label": "Anchors", "value": "100%"}]
        for i, item in enumerate(metrics[:4]):
            x = 250 + (i % 2) * 700
            y = 360 + (i // 2) * 210
            draw.rounded_rectangle((x, y, x + 560, y + 165), radius=24, fill="#0f172a", outline=palette[i % len(palette)], width=4)
            draw.text((x + 42, y + 30), str(item.get("value", "")), fill=palette[i % len(palette)], font=font(58))
            draw.text((x + 46, y + 102), str(item.get("label", "")), fill="#cbd5e1", font=font(28))

    def task_matrix() -> None:
        tasks = scene.data.get("tasks") or _concept_list(scene, 4, ["Problem", "Method", "Evidence", "Takeaway"])
        for i, task in enumerate(tasks[:4]):
            x = 260 + (i % 2) * 700
            y = 345 + (i // 2) * 190
            draw.rounded_rectangle((x, y, x + 560, y + 145), radius=18, fill="#0f172a", outline=palette[i], width=4)
            draw.text((x + 36, y + 48), str(task), fill="#f8fafc", font=font(38))

    def bar_finding() -> None:
        raw_bars = scene.data.get("bars")
        if raw_bars:
            bars = [(str(item[0]), int(item[1]), palette[i % len(palette)]) for i, item in enumerate(raw_bars[:4])]
        else:
            bars = [(label, value, palette[i % len(palette)]) for i, (label, value) in enumerate(zip(_concept_list(scene, 4, ["Baseline", "Method", "Ablation", "Result"]), [92, 64, 48, 30]))]
        base_y = 720
        for i, (label, value, color) in enumerate(bars):
            x = 470 + i * 260
            h = int(value * 4.5)
            draw.rounded_rectangle((x, base_y - h, x + 105, base_y), radius=18, fill=color, outline="#e0f2fe", width=2)
            draw.text((x - 5, base_y - h - 55), f"{value}%", fill=color, font=font(36))
            draw.text((x - 20, base_y + 20), label, fill="#cbd5e1", font=font(28))
        draw.line((360, base_y, 1510, base_y), fill="#64748b", width=3)

    def split_comparison() -> None:
        left_label, right_label = _concept_labels(scene)
        panels = [(left_label, "source\nevidence\ntrace", "#fbbf24"), (right_label, "risk\ngap\ndecision", "#22d3ee")]
        for i, (name, lines, color) in enumerate(panels):
            x = 260 + i * 720
            draw.rounded_rectangle((x, 360, x + 600, 690), radius=28, fill="#0f172a", outline=color, width=5)
            draw.text((x + 48, 398), name, fill=color, font=font(58))
            for j, line in enumerate(lines.split("\n")):
                draw.text((x + 70, 500 + j * 56), line, fill="#e5e7eb", font=font(36))
        draw.text((910, 500), "VS", fill="#f472b6", font=font(72))

    def ranking_board() -> None:
        raw_rows = scene.data.get("rows") or scene.data.get("ranking")
        labels = [str(item) for item in raw_rows[:5]] if raw_rows else _concept_list(scene, 5, ["Baseline", "Method", "Ablation", "Variant", "Result"])
        rows = list(zip(labels, [92, 76, 64, 48, 30]))
        for i, (label, value) in enumerate(rows):
            y = 360 + i * 72
            draw.text((330, y), label, fill="#e5e7eb", font=font(30))
            draw.rounded_rectangle((680, y + 8, 680 + value * 8, y + 42), radius=16, fill=palette[i % len(palette)])
            draw.text((1440, y), f"{value}%", fill=palette[i % len(palette)], font=font(30))

    def future_direction() -> None:
        nodes = _concept_list(scene, 3, ["Evidence", "Mechanism", "System"])
        centers = [(520, 535), (960, 535), (1400, 535)]
        for i, ((x, y), label) in enumerate(zip(centers, nodes)):
            draw.ellipse((x - 115, y - 115, x + 115, y + 115), fill="#0f172a", outline=palette[i], width=5)
            for j, line in enumerate(_wrap_text(label, 10)[:2]):
                draw.text((x - 80, y - 28 + j * 42), line, fill="#f8fafc", font=font(30))
            if i < len(centers) - 1:
                draw.line((x + 120, y, centers[i + 1][0] - 120, y), fill=accent, width=6)

    def paper_gap_iceberg() -> None:
        left_label, right_label = _concept_labels(scene)
        draw.polygon([(960, 355), (1320, 715), (600, 715)], fill="#0f172a", outline="#22d3ee")
        draw.line((550, 500, 1370, 500), fill="#60a5fa", width=5)
        draw.text((760, 415), left_label, fill="#bfdbfe", font=font(34))
        draw.text((755, 590), f"{right_label}: hidden evidence", fill="#f8fafc", font=font(34))

    def method_transfer() -> None:
        left_label, right_label = _concept_labels(scene)
        draw.rounded_rectangle((290, 410, 760, 650), radius=22, fill="#0f172a", outline="#fbbf24", width=4)
        draw.text((350, 500), "\n".join(_wrap_text(left_label, 10)[:2]), fill="#fde68a", font=font(38))
        draw.text((880, 490), "→", fill=accent, font=font(100))
        draw.rounded_rectangle((1110, 410, 1580, 650), radius=22, fill="#0f172a", outline="#22d3ee", width=4)
        draw.text((1170, 500), "\n".join(_wrap_text(right_label, 10)[:2]), fill="#cffafe", font=font(38))

    def takeaway_cards() -> None:
        cards = _concept_list(scene, 3, ["Problem", "Method", "Takeaway"])
        for i, label in enumerate(cards):
            x = 300 + i * 450
            draw.rounded_rectangle((x, 405, x + 360, 640), radius=24, fill="#0f172a", outline=palette[i], width=4)
            for j, line in enumerate(_wrap_text(label, 10)[:2]):
                draw.text((x + 60, 470 + j * 52), line, fill="#f8fafc", font=font(38))

    drawers = {
        "hero_title": hero_title,
        "core_question": core_question,
        "metric_cards": metric_cards,
        "task_matrix": task_matrix,
        "bar_finding": bar_finding,
        "split_comparison": split_comparison,
        "ranking_board": ranking_board,
        "future_direction": future_direction,
        "paper_gap_iceberg": paper_gap_iceberg,
        "method_transfer": method_transfer,
        "takeaway_cards": takeaway_cards,
    }
    drawers.get(scene.template, core_question)()

    # The final MP4 burns timed SRT subtitles into the lower band, so the slide
    # itself keeps that region visually quiet to avoid duplicate captions.
    draw.rectangle((72, 820, width - 72, height - 72), fill="#020617")
    draw.text((width - 190, height - 54), f"{scene.index + 1:02d}", fill="#64748b", font=font(28))
    img.save(path)


def _contact_sheet(png_files: list[Path], output_path: Path) -> None:
    try:
        from PIL import Image, ImageDraw
    except Exception:
        output_path.write_bytes(_TINY_PNG)
        return
    thumbs = []
    for path in png_files:
        try:
            img = Image.open(path).convert("RGB")
            img.thumbnail((320, 180))
            thumbs.append((path, img.copy()))
        except Exception:
            continue
    if not thumbs:
        output_path.write_bytes(_TINY_PNG)
        return
    cols = 5
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 340, rows * 220), "#05070d")
    draw = ImageDraw.Draw(sheet)
    for i, (path, img) in enumerate(thumbs):
        x = (i % cols) * 340 + 10
        y = (i // cols) * 220 + 10
        sheet.paste(img, (x, y))
        draw.text((x, y + 184), path.stem, fill="#cbd5e1")
    sheet.save(output_path)


def render_visual_plan(
    visual_scenes: list[VisualScene],
    out_dir: Path | str,
    background_images: dict[int, Path] | None = None,
) -> RenderResult:
    out_path = Path(out_dir)
    html_dir = out_path / "slides_html"
    png_dir = out_path / "slides_png"
    html_dir.mkdir(parents=True, exist_ok=True)
    png_dir.mkdir(parents=True, exist_ok=True)
    html_files: list[Path] = []
    png_files: list[Path] = []
    total = len(visual_scenes)
    for scene in visual_scenes:
        html_path = html_dir / f"slide_{scene.index:02d}.html"
        png_path = png_dir / f"slide_{scene.index:02d}.png"
        html_path.write_text(render_slide_html(scene, total), encoding="utf-8")
        background_path = None if background_images is None else background_images.get(scene.index)
        _render_png(scene, png_path, background_path=background_path)
        html_files.append(html_path)
        png_files.append(png_path)
    contact_sheet = out_path / "contact_sheet.jpg"
    _contact_sheet(png_files, contact_sheet)
    return RenderResult(html_files=html_files, png_files=png_files, contact_sheet=contact_sheet)
