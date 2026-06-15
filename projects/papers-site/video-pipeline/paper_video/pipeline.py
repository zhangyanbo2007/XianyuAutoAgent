"""Main orchestrator: paper (url/file) → storyboard → video.mp4.

Stages:
  1. ingest      paper_source.ingest_paper  → PaperDoc dict
  2. storyboard  storyboard.generate_storyboard → storyboard.json + storyboard.md
  3. backgrounds backgrounds.generate_all_backdrops → AI cinematic backdrop PNGs
  4. charts      charts.generate_charts → matplotlib chart PNGs
  5. slides      slides.render_slides → HTML + backdrop → PNG via Playwright
  6. narration   narration.generate_narration + concat + merge_srt
  7. assemble    assemble.assemble_video → Ken Burns + mux + burn → final.mp4

Each step is independently re-runnable (idempotent cached outputs).
Steps 3-6 can run in parallel via --steps flag.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .paper_source import ingest_paper
from .storyboard import generate_storyboard, storyboard_to_markdown


def run_pipeline(
    paper_input: str,
    out_dir: str | Path,
    *,
    scene_count: int = 18,
    steps: list[str] | None = None,
    clean: bool = False,
    skip_backgrounds: bool = False,
) -> dict[str, Path]:
    """Run the full paper → video pipeline.

    Returns a dict of output paths keyed by step name.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    all_steps = steps or ["storyboard", "backgrounds", "charts", "slides", "narration", "video"]

    def _exists(name: str) -> bool:
        return name in all_steps

    print("=" * 60)
    print(f"Paper-to-Video Pipeline  →  {out}")
    print("=" * 60)

    # ── 1. Ingest ────────────────────────────────────────────────────
    print("\n[1/7] Ingesting paper...")
    doc = ingest_paper(paper_input)
    print(f"  title:     {doc.get('title', 'n/a')[:80]}")
    print(f"  arxiv_id:  {doc.get('arxiv_id', 'n/a')}")
    print(f"  sources:   {', '.join(doc.get('sources', [])) or 'n/a'}")
    print(f"  full_text: {len(doc.get('full_text', ''))} chars")
    print(f"  urls:      {len(doc.get('urls', []))}")

    # ── 2. Storyboard ────────────────────────────────────────────────
    sb_path = out / "storyboard.json"
    md_path = out / "storyboard.md"

    if _exists("storyboard") and (clean or not sb_path.exists()):
        print(f"\n[2/7] Generating storyboard ({scene_count} scenes)...")
        storyboard = generate_storyboard(doc, scene_count=scene_count)
        sb_path.write_text(json.dumps(storyboard, ensure_ascii=False, indent=2), encoding="utf-8")
        md_path.write_text(storyboard_to_markdown(storyboard), encoding="utf-8")
        print(f"  → {sb_path}")
        print(f"  → {md_path}")
    else:
        print(f"\n[2/7] Loading existing storyboard...")
        if not sb_path.exists():
            print(f"  ERROR: {sb_path} not found. Run step 'storyboard' first.")
            return {"storyboard": sb_path}
        storyboard = json.loads(sb_path.read_text(encoding="utf-8"))
        print(f"  {len(storyboard.get('sections', []))} sections, {storyboard.get('total_duration_sec', 0)}s total")

    sections = storyboard["sections"]

    # ── 3. Backgrounds ───────────────────────────────────────────────
    bg_dir = out / "bg_images"
    bg_images: dict[int, str] | None = None
    if _exists("backgrounds") and not skip_backgrounds:
        print("\n[3/7] Generating AI backdrops...")
        from .backgrounds import generate_all_backdrops
        bg_images = generate_all_backdrops(sections, bg_dir)
        print(f"  {len(bg_images)}/{len(sections)} backdrops generated")
    elif bg_dir.exists():
        bg_images = {i: str(bg_dir / f"slide_{i:02d}.png") for i in range(len(sections))
                     if (bg_dir / f"slide_{i:02d}.png").exists()}
        print(f"\n[3/7] Using {len(bg_images)} existing backdrops")

    # ── 4. Charts ────────────────────────────────────────────────────
    charts_dir = out / "charts"
    chart_paths: dict[int, str] = {}
    if _exists("charts"):
        print("\n[4/7] Generating charts...")
        from .charts import generate_charts
        chart_paths = generate_charts(sections, charts_dir)
        print(f"  {len(chart_paths)} charts generated")
    elif charts_dir.exists():
        chart_paths = {i: str(charts_dir / f"chart_{i:02d}.png")
                       for i in range(len(sections))
                       if (charts_dir / f"chart_{i:02d}.png").exists()}

    # ── 5. Slides ────────────────────────────────────────────────────
    slides_dir = out / "slides"
    slide_paths: dict[int, str] = {}
    if _exists("slides"):
        print("\n[5/7] Rendering slides (HTML → PNG)...")
        from .slides import render_slides
        slide_paths = render_slides(sections, slides_dir, bg_images=bg_images)
        print(f"  {len(slide_paths)} slides rendered")
    elif slides_dir.exists():
        png_dir = slides_dir / "slides_png"
        if png_dir.exists():
            slide_paths = {i: str(png_dir / f"slide_{i:02d}.png")
                           for i in range(len(sections))
                           if (png_dir / f"slide_{i:02d}.png").exists()}
        print(f"\n[5/7] Using {len(slide_paths)} existing slides")

    if not slide_paths:
        print("\n  ERROR: no slides available — cannot proceed to video")
        return {"storyboard": sb_path}

    # ── 6. Narration ─────────────────────────────────────────────────
    narration_dir = out / "narration"
    srt_path = narration_dir / "narration.srt"
    narration_mp3 = narration_dir / "full_narration.mp3"
    audio_results: list[dict] = []

    if _exists("narration"):
        print("\n[6/7] Generating narration (TTS + subtitles)...")
        from .narration import generate_narration, concat_narration, merge_srt

        audio_results = generate_narration(sections, narration_dir)
        valid_audio = [r for r in audio_results if r.get("audio") and Path(r["audio"]).exists()]
        if valid_audio:
            concat_narration(audio_results, str(narration_mp3))
            merge_srt(audio_results, str(srt_path))
            total_dur = sum(r["duration"] for r in audio_results)
            print(f"  Narration: {total_dur:.1f}s ({len(valid_audio)}/{len(sections)} clips)")
        else:
            print("  WARNING: no audio clips generated")
    elif narration_dir.exists():
        print(f"\n[6/7] Using existing narration...")
        for i in range(len(sections)):
            audio_path = narration_dir / "audio" / f"sec_{i:02d}.mp3"
            srt_file = narration_dir / "audio" / f"sec_{i:02d}.srt"
            if audio_path.exists():
                from .narration import get_audio_duration
                audio_results.append({
                    "index": i,
                    "audio": str(audio_path),
                    "srt": str(srt_file) if srt_file.exists() else None,
                    "duration": get_audio_duration(str(audio_path)),
                })
        print(f"  {len(audio_results)} existing audio clips loaded")
    else:
        print(f"\n[6/7] No narration directory found")

    if not srt_path.exists():
        print("  ERROR: narration.srt not found — cannot burn subtitles")
        return {"storyboard": sb_path}

    # ── 7. Assemble video ────────────────────────────────────────────
    if _exists("video"):
        print("\n[7/7] Assembling final video...")
        from .assemble import assemble_video
        final = assemble_video(
            slide_paths, audio_results, str(srt_path), sections, out,
            narration_mp3=str(narration_mp3) if narration_mp3.exists() else None,
        )
    else:
        final = out / "video.mp4"
        print(f"\n[7/7] Video assembly skipped (not in steps)")

    print("\n" + "=" * 60)
    print("Pipeline complete!")
    print("=" * 60)

    return {
        "storyboard_json": sb_path,
        "storyboard_md": md_path,
        "final_video": final,
    }
