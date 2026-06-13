#!/usr/bin/env python3
"""Paper-to-Video Pipeline: Generate video from paper data."""

import argparse
import json
import os
import sys
import time

# Add current dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import OUTPUT_DIR, DATA_DIR
from script_generator import generate_script
from tts_generator import generate_sections_audio, concat_audio
from slide_generator import generate_slides
from video_renderer import render_video


def load_paper(slug: str) -> dict:
    """Load paper data by slug."""
    data_path = os.path.join(DATA_DIR, "papers.json")
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for paper in data["papers"]:
        if paper.get("slug") == slug:
            return paper

    raise ValueError(f"Paper not found: {slug}")


def run_pipeline(paper_slug: str, voice: str = None) -> str:
    """Run the full pipeline for a paper.

    Returns: path to output video
    """
    start_time = time.time()

    # Setup output directory
    work_dir = os.path.join(OUTPUT_DIR, paper_slug)
    os.makedirs(work_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  Paper: {paper_slug}")
    print(f"{'='*60}")

    # Step 1: Load paper
    print("\n[1/5] Loading paper data...")
    paper = load_paper(paper_slug)
    print(f"  Title: {paper['title'][:60]}")
    print(f"  Theme: {paper.get('theme_label', 'N/A')}")

    # Step 2: Generate script
    print("\n[2/5] Generating video script (LLM)...")
    script_path = os.path.join(work_dir, "script.json")

    if os.path.exists(script_path):
        print("  Using cached script")
        with open(script_path) as f:
            script = json.load(f)
    else:
        script = generate_script(paper)
        with open(script_path, "w", encoding="utf-8") as f:
            json.dump(script, f, ensure_ascii=False, indent=2)

    print(f"  Title: {script.get('title', 'N/A')}")
    print(f"  Sections: {len(script.get('sections', []))}")

    # Step 3: Generate TTS audio
    print("\n[3/5] Generating TTS audio...")
    audio_dir = os.path.join(work_dir, "audio")
    sections = script.get("sections", [])

    tts_kwargs = {}
    if voice:
        tts_kwargs["voice"] = voice

    section_results = generate_sections_audio(sections, audio_dir, **tts_kwargs)

    # Concatenate audio
    full_audio_path = os.path.join(work_dir, "narration.mp3")
    concat_audio(section_results, full_audio_path)

    # Merge subtitles
    full_srt_path = os.path.join(work_dir, "narration.srt")
    _merge_subtitles(section_results, full_srt_path)

    total_audio_duration = sum(r.get("duration_sec", 0) for r in section_results)
    print(f"  Total audio: {total_audio_duration:.1f}s")

    # Step 4: Generate slides
    print("\n[4/5] Generating slides...")
    slides_dir = os.path.join(work_dir, "slides")

    # Update section durations based on actual TTS durations
    for i, result in enumerate(section_results):
        if i < len(sections):
            sections[i]["duration_sec"] = result.get("duration_sec", 40)

    slides = generate_slides(script, paper, slides_dir)
    print(f"  Generated {len(slides)} slides")

    # Step 5: Render video
    print("\n[5/5] Rendering video...")
    output_path = os.path.join(work_dir, f"{paper_slug}.mp4")
    render_video(slides, full_audio_path, full_srt_path, output_path, full_srt_path)

    elapsed = time.time() - start_time
    file_size = os.path.getsize(output_path) / (1024 * 1024)

    print(f"\n{'='*60}")
    print(f"  ✅ Done! ({elapsed:.1f}s)")
    print(f"  Output: {output_path}")
    print(f"  Size: {file_size:.1f} MB")
    print(f"{'='*60}\n")

    return output_path


def _merge_subtitles(section_results: list, output_path: str):
    """Merge section SRT files into one with adjusted timestamps."""
    all_subs = []
    offset = 0.0

    for result in section_results:
        srt_path = result.get("subtitle_path", "")
        if not srt_path or not os.path.exists(srt_path):
            offset += result.get("duration_sec", 0)
            continue

        with open(srt_path, "r", encoding="utf-8") as f:
            content = f.read()

        blocks = content.strip().split("\n\n")
        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) < 3:
                continue

            time_line = lines[1]
            if "-->" not in time_line:
                continue

            parts = time_line.split("-->")
            start = _srt_to_sec(parts[0].strip()) + offset
            end = _srt_to_sec(parts[1].strip()) + offset
            text = " ".join(lines[2:]).strip()

            if text:
                all_subs.append((start, end, text))

        offset += result.get("duration_sec", 0)

    # Write merged SRT
    with open(output_path, "w", encoding="utf-8") as f:
        for i, (start, end, text) in enumerate(all_subs):
            f.write(f"{i+1}\n")
            f.write(f"{_sec_to_srt(start)} --> {_sec_to_srt(end)}\n")
            f.write(f"{text}\n\n")


def _srt_to_sec(time_str: str) -> float:
    time_str = time_str.replace(",", ".")
    parts = time_str.split(":")
    return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])


def _sec_to_srt(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")


def main():
    parser = argparse.ArgumentParser(description="Generate video from paper")
    parser.add_argument("--paper", "-p", required=True, help="Paper slug")
    parser.add_argument("--voice", "-v", default=None, help="TTS voice name")
    args = parser.parse_args()

    run_pipeline(args.paper, args.voice)


if __name__ == "__main__":
    main()
