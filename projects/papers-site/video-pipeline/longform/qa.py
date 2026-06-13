"""QA reporting for longform generated artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from .models import RenderResult, Timeline, VisualScene


def _timeline_is_contiguous(timeline: Timeline) -> bool:
    for previous, current in zip(timeline.entries, timeline.entries[1:]):
        if abs(previous.end_sec - current.start_sec) > 0.001:
            return False
    return True


def _srt_seconds(value: str) -> float:
    hms, millis = value.split(",")
    h, m, s = hms.split(":")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(millis) / 1000


def _srt_stats(path: Path | None) -> dict[str, float | int]:
    if not path or not path.exists() or path.stat().st_size == 0:
        return {"srt_block_count": 0, "max_subtitle_duration_sec": 0.0}
    block_count = 0
    max_duration = 0.0
    for line in path.read_text(encoding="utf-8").splitlines():
        if "-->" not in line:
            continue
        start, end = [part.strip() for part in line.split("-->")]
        block_count += 1
        max_duration = max(max_duration, _srt_seconds(end) - _srt_seconds(start))
    return {"srt_block_count": block_count, "max_subtitle_duration_sec": round(max_duration, 3)}


def build_qa_report(visual_scenes: list[VisualScene], result: RenderResult, out_dir: Path | str, timeline: Timeline | None = None, srt_path: Path | str | None = None) -> dict:
    out_path = Path(out_dir)
    scene_count = len(visual_scenes)
    anchored = sum(1 for scene in visual_scenes if scene.paper_anchor)
    template_counts = Counter(scene.template for scene in visual_scenes)
    timeline_entries = timeline.entries if timeline else []
    transition_counts = Counter(entry.transition for entry in timeline_entries)
    subtitle = Path(srt_path) if srt_path else None
    subtitle_stats = _srt_stats(subtitle)
    report = {
        "scene_count": scene_count,
        "paper_anchor_coverage": 0.0 if scene_count == 0 else anchored / scene_count,
        "template_count": len(template_counts),
        "template_distribution": dict(sorted(template_counts.items())),
        "html_count": len(result.html_files),
        "png_count": len(result.png_files),
        "contact_sheet": str(result.contact_sheet),
        "missing_html": [str(path) for path in result.html_files if not path.exists()],
        "missing_png": [str(path) for path in result.png_files if not path.exists()],
        "timeline_entry_count": len(timeline_entries),
        "timeline_matches_scene_count": len(timeline_entries) == scene_count,
        "timeline_contiguous": bool(timeline and _timeline_is_contiguous(timeline)),
        "total_duration_sec": 0.0 if timeline is None else timeline.total_duration_sec,
        "transition_sec": 0.0 if timeline is None else timeline.transition_sec,
        "transition_distribution": dict(sorted(transition_counts.items())),
        "srt_path": "" if subtitle is None else str(subtitle),
        "srt_exists": bool(subtitle and subtitle.exists() and subtitle.stat().st_size > 0),
        **subtitle_stats,
    }
    (out_path / "qa_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
