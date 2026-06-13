"""CLI for the longform paper-video pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from .assembly import build_render_manifest
from .fact_pack import build_fact_pack
from .finalize import build_production_readiness
from .llm_planner import plan_longform_with_llm
from .models import PaperFactPack, Scene, VisualScene
from .qa import build_qa_report
from .render import render_visual_plan
from .storyboard import build_storyboard
from .timeline import build_timeline, write_srt
from .visual_assets import generate_visual_assets
from .visual_plan import build_visual_plan


def _pipeline_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def _paper_data_path() -> Path:
    return _pipeline_dir().parent / "data" / "papers.json"


def load_paper_by_slug(slug: str, data_path: Path | None = None) -> dict[str, Any]:
    path = data_path or _paper_data_path()
    data = json.loads(path.read_text(encoding="utf-8"))
    for paper in data.get("papers", []):
        if paper.get("slug") == slug:
            return paper
    raise ValueError(f"paper slug not found: {slug}")


def _write_json(path: Path, value: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, PaperFactPack):
        payload = value.to_dict()
    elif isinstance(value, list):
        payload = [item.to_dict() if isinstance(item, (Scene, VisualScene)) else item for item in value]
    else:
        payload = value
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def run_longform_dry_run(
    paper: dict[str, Any],
    out_dir: Path | str,
    scene_count: int = 28,
    planner: Any | None = None,
    generate_images: bool = False,
    image_generator: Any | None = None,
) -> dict[str, Path]:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    if planner:
        fact_pack, scenes, visual_scenes = planner(paper, scene_count)
    else:
        fact_pack = build_fact_pack(paper)
        scenes = build_storyboard(fact_pack, target_scene_count=scene_count)
        visual_scenes = build_visual_plan(scenes)
    fact_pack_path = _write_json(output / "fact_pack.json", fact_pack)
    storyboard_path = _write_json(output / "storyboard.json", scenes)
    visual_plan_path = _write_json(output / "visual_plan.json", visual_scenes)
    timeline = build_timeline(visual_scenes)
    timeline_path = _write_json(output / "timeline.json", timeline.to_dict())
    srt_path = write_srt(timeline, output / "narration.srt")
    background_images = generate_visual_assets(visual_scenes, output, image_generator=image_generator) if generate_images else None
    render_result = render_visual_plan(visual_scenes, output, background_images=background_images)
    manifest_path = build_render_manifest(visual_scenes, render_result, timeline, srt_path, output)
    readiness_path = build_production_readiness(manifest_path)
    build_qa_report(visual_scenes, render_result, output, timeline=timeline, srt_path=srt_path)
    paths = {"fact_pack": fact_pack_path, "storyboard": storyboard_path, "visual_plan": visual_plan_path, "timeline": timeline_path, "narration_srt": srt_path, "render_manifest": manifest_path, "production_readiness": readiness_path, "qa_report": output / "qa_report.json", "contact_sheet": render_result.contact_sheet}
    if generate_images:
        paths["visual_assets"] = output / "visual_assets.json"
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate paper-grounded longform video planning artifacts")
    parser.add_argument("--paper-slug", required=True)
    parser.add_argument("--scene-count", type=int, default=28)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--llm-plan", action="store_true", help="Use the LLM to generate paper-specific fact pack, storyboard, and visual prompts")
    parser.add_argument("--generate-images", action="store_true", help="Generate cinematic background images from visual prompts")
    args = parser.parse_args()
    paper = load_paper_by_slug(args.paper_slug)
    out_dir = Path(args.output_dir) if args.output_dir else _pipeline_dir() / "output" / args.paper_slug / "longform"
    planner = plan_longform_with_llm if args.llm_plan else None
    paths = run_longform_dry_run(paper, out_dir, scene_count=args.scene_count, planner=planner, generate_images=args.generate_images)
    for name, path in paths.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
