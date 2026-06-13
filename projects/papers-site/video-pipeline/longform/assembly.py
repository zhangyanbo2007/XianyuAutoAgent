"""Build final rendering manifests for the longform video pipeline."""

from __future__ import annotations

import json
from pathlib import Path

from .models import RenderResult, Timeline, VisualScene


def build_render_manifest(
    visual_scenes: list[VisualScene],
    render_result: RenderResult,
    timeline: Timeline,
    srt_path: Path | str,
    out_dir: Path | str,
    fps: int = 30,
    resolution: tuple[int, int] = (1920, 1080),
) -> Path:
    """Write the manifest consumed by the motion/video rendering stage."""
    output = Path(out_dir)
    subtitle = Path(srt_path)
    entries_by_index = {entry.scene_index: entry for entry in timeline.entries}
    png_by_position = list(render_result.png_files)

    slides = []
    narration_sections = []
    for position, scene in enumerate(visual_scenes):
        entry = entries_by_index.get(scene.index)
        if entry is None:
            continue
        png_path = png_by_position[position] if position < len(png_by_position) else output / "slides_png" / f"slide_{scene.index:02d}.png"
        duration = round(entry.end_sec - entry.start_sec, 3)
        slides.append({
            "scene_index": scene.index,
            "path": str(png_path),
            "duration_sec": duration,
            "transition": entry.transition,
            "template": scene.template,
            "type": scene.kind,
        })
        narration_sections.append({
            "scene_index": scene.index,
            "label": scene.title,
            "text": scene.narration,
            "duration_sec": duration,
        })

    manifest = {
        "renderer": "motion_renderer.render_video_v2",
        "resolution": list(resolution),
        "fps": fps,
        "slides": slides,
        "narration_sections": narration_sections,
        "narration_text": "\n".join(section["text"] for section in narration_sections),
        "subtitle_path": str(subtitle),
        "audio_output_path": str(output / "narration.mp3"),
        "video_output_path": str(output / "longform.mp4"),
        "total_duration_sec": timeline.total_duration_sec,
        "transition_sec": timeline.transition_sec,
    }
    path = output / "render_manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
