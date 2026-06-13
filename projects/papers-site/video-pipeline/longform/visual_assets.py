"""Generate cinematic visual assets from longform visual prompts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from .models import VisualScene

ImageGenerator = Callable[[str, Path | str, int], Path | str | None]


def _default_image_generator(prompt: str, cache_dir: Path | str, index: int) -> Path | None:
    from image_generator import generate_frame_image

    result = generate_frame_image(prompt, str(cache_dir), index=index, size="1024*576")
    return Path(result) if result else None


def generate_visual_assets(
    visual_scenes: list[VisualScene],
    out_dir: Path | str,
    image_generator: ImageGenerator | None = None,
) -> dict[int, Path]:
    """Generate or fetch per-scene cinematic background images."""
    output = Path(out_dir)
    cache_dir = output / "cinematic_assets"
    cache_dir.mkdir(parents=True, exist_ok=True)
    generator = image_generator or _default_image_generator
    assets: dict[int, Path] = {}
    manifest_assets: dict[str, dict[str, str]] = {}

    for scene in visual_scenes:
        if not scene.visual_prompt.strip():
            continue
        generated = generator(scene.visual_prompt, cache_dir, scene.index)
        if not generated:
            continue
        path = Path(generated)
        if path.exists() and path.stat().st_size > 0:
            assets[scene.index] = path
            manifest_assets[str(scene.index)] = {
                "path": str(path),
                "prompt": scene.visual_prompt,
                "title": scene.title,
            }

    manifest = {
        "scene_count": len(visual_scenes),
        "asset_count": len(assets),
        "assets": manifest_assets,
    }
    (output / "visual_assets.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return assets
