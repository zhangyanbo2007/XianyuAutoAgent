#!/usr/bin/env python3
"""Paper-to-Video Pipeline V2: Professional quality with charts, motion, and branding."""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import OUTPUT_DIR, DATA_DIR
from script_generator_v2 import generate_script_v2
from tts_generator import generate_sections_audio, concat_audio
from slide_generator_v2 import generate_all_slides_v2
from motion_renderer import render_video_v2
from image_generator import generate_section_images
from bgm_generator import generate_ambient_bgm, merge_audio_with_bgm


def load_paper(slug):
    data_path = os.path.join(DATA_DIR, "papers.json")
    with open(data_path) as f:
        data = json.load(f)
    for p in data["papers"]:
        if p.get("slug") == slug:
            return p
    raise ValueError(f"Paper not found: {slug}")


def run_pipeline_v2(paper_slug, voice="zh-CN-YunxiNeural"):
    start = time.time()
    work_dir = os.path.join(OUTPUT_DIR, paper_slug)
    os.makedirs(work_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  Paper V2: {paper_slug}")
    print(f"{'='*60}")

    # 1. Load paper
    print("\n[1/6] Loading paper data...")
    paper = load_paper(paper_slug)
    print(f"  Title: {paper['title'][:60]}")
    print(f"  Theme: {paper.get('theme_label', 'N/A')}")

    # 2. Generate detailed script
    print("\n[2/7] Generating detailed script (15+ sections)...")
    script_path = os.path.join(work_dir, "script_v2.json")
    manual_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manual_script.json")

    if os.path.exists(script_path):
        print("  Using cached script")
        with open(script_path) as f:
            script = json.load(f)
    elif os.path.exists(manual_script_path):
        print("  Using manual script")
        with open(manual_script_path) as f:
            script = json.load(f)
        # Cache it
        with open(script_path, "w", encoding="utf-8") as f:
            json.dump(script, f, ensure_ascii=False, indent=2)
    else:
        script = generate_script_v2(paper)
        with open(script_path, "w", encoding="utf-8") as f:
            json.dump(script, f, ensure_ascii=False, indent=2)

    sections = script.get("sections", [])
    print(f"  Sections: {len(sections)}")
    print(f"  Target duration: {script.get('total_duration_sec', 0)}s ({script.get('total_duration_sec', 0)/60:.1f}min)")

    # 3. Generate TTS audio
    print("\n[3/6] Generating TTS audio...")
    audio_dir = os.path.join(work_dir, "audio_v2")
    tts_sections = []
    for s in sections:
        tts_sections.append({
            "label": s.get("label", ""),
            "text": s.get("text", ""),
            "duration_sec": s.get("duration_sec", 30),
        })

    section_results = generate_sections_audio(tts_sections, audio_dir, voice=voice)

    full_audio = os.path.join(work_dir, "narration_v2.mp3")
    concat_audio(section_results, full_audio)

    # Generate and merge BGM
    print("  Generating ambient BGM...")
    bgm_path = os.path.join(work_dir, "bgm.mp3")
    total_audio = sum(r.get("duration_sec", 0) for r in section_results)
    generate_ambient_bgm(bgm_path, total_audio + 5, volume=0.06)

    mixed_audio = os.path.join(work_dir, "narration_mixed.mp3")
    merge_audio_with_bgm(full_audio, bgm_path, mixed_audio, bgm_volume=0.12)
    print(f"  Mixed narration + BGM")

    full_srt = os.path.join(work_dir, "narration_v2.srt")
    _merge_subtitles(section_results, full_srt)

    print(f"  Total audio: {total_audio:.1f}s ({total_audio/60:.1f}min)")

    # Update section durations based on actual audio
    for i, result in enumerate(section_results):
        if i < len(sections):
            sections[i]["duration_sec"] = result.get("duration_sec", 30)

    # 4. Generate AI images for each frame
    print("\n[4/7] Generating AI illustrations (dashscope wanx2.1)...")
    ai_image_cache = os.path.join(work_dir, "_ai_images")
    theme = paper.get("theme", "")
    ai_images = generate_section_images(sections, ai_image_cache, theme)
    print(f"  Generated {len(ai_images)}/{len(sections)} AI images")

    # 5. Generate slides (with AI images + charts)
    print("\n[5/7] Generating slides with AI backgrounds...")
    slides_dir = os.path.join(work_dir, "slides_v2")
    slides = generate_all_slides_v2(script, paper, slides_dir, ai_images=ai_images)
    print(f"  Generated {len(slides)} slides")

    # 6. Render video with motion
    print("\n[6/7] Rendering video with Ken Burns motion...")
    output_path = os.path.join(work_dir, f"{paper_slug}_v2.mp4")
    render_video_v2(slides, mixed_audio, output_path, full_srt)

    elapsed = time.time() - start
    size = os.path.getsize(output_path) / (1024 * 1024)
    duration = _get_duration(output_path)

    print(f"\n{'='*60}")
    print(f"  ✅ V2 Done! ({elapsed:.1f}s)")
    print(f"  Output: {output_path}")
    print(f"  Size: {size:.1f} MB")
    print(f"  Duration: {duration:.0f}s ({duration/60:.1f}min)")
    print(f"{'='*60}\n")

    return output_path


def _get_duration(path):
    import subprocess
    ffmpeg = _get_ffmpeg()
    r = subprocess.run([ffmpeg, "-i", path, "-f", "null", "-"],
                       capture_output=True, text=True)
    for line in r.stderr.split("\n"):
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = parts.split(":")
            return float(h)*3600 + float(m)*60 + float(s)
    return 0.0


def _get_ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except:
        return "ffmpeg"


def _merge_subtitles(section_results, output_path):
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

    with open(output_path, "w", encoding="utf-8") as f:
        for i, (start, end, text) in enumerate(all_subs):
            f.write(f"{i+1}\n")
            f.write(f"{_sec_to_srt(start)} --> {_sec_to_srt(end)}\n")
            f.write(f"{text}\n\n")


def _srt_to_sec(t):
    t = t.replace(",", ".")
    p = t.split(":")
    return float(p[0])*3600 + float(p[1])*60 + float(p[2])


def _sec_to_srt(s):
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:06.3f}".replace(".", ",")


def main():
    parser = argparse.ArgumentParser(description="Paper-to-Video V2")
    parser.add_argument("--paper", "-p", required=True, help="Paper slug")
    parser.add_argument("--voice", "-v", default="zh-CN-YunjianNeural",
                        help="TTS voice (default: YunjianNeural male)")
    args = parser.parse_args()
    run_pipeline_v2(args.paper, args.voice)


if __name__ == "__main__":
    main()
