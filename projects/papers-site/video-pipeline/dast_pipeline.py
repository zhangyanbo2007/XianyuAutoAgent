#!/usr/bin/env python3
"""
DAST Video Pipeline - generates video matching reference dast_analysis/video.mp4.
Usage:
    python dast_pipeline.py                    # Full pipeline
    python dast_pipeline.py --steps slides     # Only render slides
    python dast_pipeline.py --steps audio      # Only generate audio
    python dast_pipeline.py --steps video      # Only render final video
"""

import os
import sys
import json
import subprocess
import asyncio
import argparse
import shutil
from pathlib import Path

# ── Paths ───────────────────────────────────────────────────────────

PIPELINE_DIR = Path(__file__).parent
SCRIPT_PATH = PIPELINE_DIR / "dast_manual_script.json"
OUTPUT_DIR = PIPELINE_DIR / "output" / "dast-video"
SLIDES_DIR = OUTPUT_DIR / "slides"
CHARTS_DIR = OUTPUT_DIR / "charts"
AUDIO_DIR = OUTPUT_DIR / "audio"
FINAL_OUTPUT = OUTPUT_DIR / "final.mp4"


def get_ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    for p in ["/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg"]:
        if os.path.exists(p):
            return p
    return "ffmpeg"


FFMPEG = None


def _ffmpeg():
    global FFMPEG
    if FFMPEG is None:
        FFMPEG = get_ffmpeg()
    return FFMPEG


# ── Step 1: Load Script ─────────────────────────────────────────────

def load_script():
    with open(SCRIPT_PATH) as f:
        return json.load(f)


# ── Step 2: Generate TTS Audio ──────────────────────────────────────

def generate_audio(sections):
    """Generate TTS audio for each section using edge-tts."""
    import edge_tts

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    voice = "zh-CN-YunxiNeural"
    rate = "+0%"

    results = []
    for i, sec in enumerate(sections):
        audio_path = AUDIO_DIR / f"sec_{i:02d}.mp3"
        srt_path = AUDIO_DIR / f"sec_{i:02d}.srt"

        if audio_path.exists():
            # Get duration of existing audio
            dur = _get_audio_duration(str(audio_path))
            results.append({
                "index": i,
                "audio": str(audio_path),
                "srt": str(srt_path),
                "duration": dur
            })
            print(f"  [skip] Section {i}: already exists ({dur:.1f}s)")
            continue

        text = sec.get("text", "")
        if not text.strip():
            results.append({"index": i, "audio": None, "srt": None, "duration": sec.get("duration_sec", 5)})
            continue

        print(f"  [tts] Section {i}: {sec.get('label', '')[:30]}...")
        try:
            # Generate audio
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            asyncio.run(communicate.save(str(audio_path)))

            # Generate SRT subtitles
            _generate_srt(text, str(srt_path))

            dur = _get_audio_duration(str(audio_path))
            results.append({
                "index": i,
                "audio": str(audio_path),
                "srt": str(srt_path),
                "duration": dur
            })
            print(f"    -> {dur:.1f}s")
        except Exception as e:
            print(f"    ERROR: {e}")
            results.append({"index": i, "audio": None, "srt": None, "duration": sec.get("duration_sec", 5)})

    return results


def _generate_srt(text: str, output_path: str):
    """Generate SRT subtitles from text, splitting into chunks."""
    import re

    # Split by sentence endings
    sentences = re.split(r'(?<=[。！？；\n])', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return

    # Calculate total duration (estimate: ~5 chars/sec for Chinese)
    total_chars = sum(len(s) for s in sentences)

    with open(output_path, 'w', encoding='utf-8') as f:
        idx = 1
        for sent in sentences:
            if not sent:
                continue
            duration = max(1.0, len(sent) / 5.0)
            f.write(f"{idx}\n")
            f.write(f"00:00:00,000 --> 00:00:{int(duration):02d},000\n")
            f.write(f"{sent}\n\n")
            idx += 1


def _get_audio_duration(audio_path: str) -> float:
    """Get duration of audio file using ffmpeg."""
    ffmpeg = _ffmpeg()
    try:
        result = subprocess.run(
            [ffmpeg, "-i", audio_path, "-f", "null", "-"],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stderr.split("\n"):
            if "Duration:" in line:
                parts = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = parts.split(":")
                return float(h) * 3600 + float(m) * 60 + float(s)
    except Exception:
        pass
    return 5.0


def concat_audio(audio_results, output_path):
    """Concatenate all section audio files with small gaps."""
    ffmpeg = _ffmpeg()
    valid = [r for r in audio_results if r.get("audio") and os.path.exists(r["audio"])]

    if not valid:
        print("  No audio files to concatenate")
        return

    # Create concat list
    concat_list = OUTPUT_DIR / "concat_list.txt"
    silence_path = AUDIO_DIR / "silence_500ms.mp3"

    # Generate 500ms silence
    if not silence_path.exists():
        subprocess.run([
            ffmpeg, "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
            "-t", "0.5", "-q:a", "9", str(silence_path)
        ], capture_output=True)

    with open(concat_list, 'w') as f:
        for i, r in enumerate(valid):
            f.write(f"file '{r['audio']}'\n")
            if i < len(valid) - 1:
                f.write(f"file '{silence_path}'\n")

    subprocess.run([
        ffmpeg, "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list), "-c", "copy", str(output_path)
    ], capture_output=True)

    print(f"  Concatenated audio: {output_path}")


def merge_srt(audio_results, output_path):
    """Merge all section SRT files with correct time offsets."""
    valid = [r for r in audio_results if r.get("srt") and os.path.exists(r["srt"])]

    all_entries = []
    time_offset = 0.0

    for r in valid:
        entries = _parse_srt(r["srt"])
        for entry in entries:
            entry["start"] += time_offset
            entry["end"] += time_offset
            all_entries.append(entry)
        time_offset += r.get("duration", 5.0) + 0.5  # audio duration + gap

    _write_srt(all_entries, output_path)
    print(f"  Merged subtitles: {output_path}")


def _parse_srt(path: str) -> list:
    """Parse SRT file into list of entries."""
    entries = []
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = content.strip().split('\n\n')
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            times = lines[1]
            text = '\n'.join(lines[2:])
            start, end = _parse_srt_time(times)
            entries.append({"start": start, "end": end, "text": text})
    return entries


def _parse_srt_time(time_str: str):
    """Parse SRT timestamp to seconds."""
    parts = time_str.replace(',', '.').split(' --> ')
    start = _ts_to_seconds(parts[0].strip())
    end = _ts_to_seconds(parts[1].strip())
    return start, end


def _ts_to_seconds(ts: str) -> float:
    h, m, s = ts.split(':')
    return float(h) * 3600 + float(m) * 60 + float(s)


def _seconds_to_ts(s: float) -> str:
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:06.3f}".replace('.', ',')


def _write_srt(entries: list, output_path: str):
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, e in enumerate(entries, 1):
            f.write(f"{i}\n")
            f.write(f"{_seconds_to_ts(e['start'])} --> {_seconds_to_ts(e['end'])}\n")
            f.write(f"{e['text']}\n\n")


# ── Step 3: Generate Charts ─────────────────────────────────────────

def generate_charts(sections):
    """Generate chart PNGs for sections with chart_data."""
    from chart_generator_v2 import generate_chart

    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    chart_paths = {}

    for i, sec in enumerate(sections):
        os_screen = sec.get("on_screen", {})
        chart_spec = os_screen.get("chart")
        if not chart_spec:
            continue

        output_path = CHARTS_DIR / f"chart_{i:02d}.png"
        if output_path.exists():
            chart_paths[i] = str(output_path)
            print(f"  [skip] Chart {i}: already exists")
            continue

        print(f"  [chart] Section {i}: {chart_spec.get('type', 'bar')}...")
        try:
            generate_chart(chart_spec, str(output_path))
            chart_paths[i] = str(output_path)
            print(f"    -> {output_path}")
        except Exception as e:
            print(f"    ERROR: {e}")

    return chart_paths


# ── Step 4: Render HTML Slides to PNG ───────────────────────────────

def render_slides(sections, chart_paths):
    """Render HTML slides to PNG using Playwright."""
    from slide_templates import render_slide

    SLIDES_DIR.mkdir(parents=True, exist_ok=True)

    # Background image mapping: use reference frames for maximum similarity
    bg_dir = OUTPUT_DIR / "bg_ref"  # Use reference frames
    if not bg_dir.exists():
        bg_dir = OUTPUT_DIR / "bg_images"  # Fallback to generated images

    slide_paths = []
    for i, sec in enumerate(sections):
        png_path = SLIDES_DIR / f"slide_{i:02d}.png"
        if png_path.exists():
            slide_paths.append(str(png_path))
            print(f"  [skip] Slide {i}: already exists")
            continue

        chart_path = chart_paths.get(i)

        # Use reference frame as background
        bg_image = str(bg_dir / f"ref_{i:02d}.jpg") if bg_dir.exists() else None
        if not bg_image or not os.path.exists(bg_image):
            bg_image = str(OUTPUT_DIR / "bg_images" / f"slide_{i:02d}.png")

        print(f"  [slide] Section {i}: {sec.get('label', '')[:30]}...")
        try:
            html_content = render_slide(sec, chart_path=chart_path, bg_image_path=bg_image)
            html_path = SLIDES_DIR / f"slide_{i:02d}.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            # Screenshot with Playwright
            _html_to_png(str(html_path), str(png_path))
            slide_paths.append(str(png_path))
            print(f"    -> {png_path}")
        except Exception as e:
            print(f"    ERROR: {e}")
            import traceback
            traceback.print_exc()

    return slide_paths


def _html_to_png(html_path: str, png_path: str):
    """Convert HTML file to PNG using Playwright."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(f"file://{os.path.abspath(html_path)}")
        page.wait_for_timeout(500)  # Wait for fonts
        page.screenshot(path=png_path, type="png")
        browser.close()


# ── Step 5: Render Video ────────────────────────────────────────────

def render_video(slide_paths, audio_results, srt_path, sections):
    """Render final video with Ken Burns motion and burned-in subtitles."""
    ffmpeg = _ffmpeg()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Step 5a: Create animated segments per slide
    print("  [video] Creating animated segments...")
    segments = []
    for i, (slide_path, sec) in enumerate(zip(slide_paths, sections)):
        if not slide_path or not os.path.exists(slide_path):
            continue

        dur = audio_results[i]["duration"] if i < len(audio_results) else sec.get("duration_sec", 5)
        segment_path = OUTPUT_DIR / f"seg_{i:02d}.mp4"

        if segment_path.exists():
            segments.append(str(segment_path))
            continue

        # Ken Burns: slow zoom in/out cycling
        pattern = i % 3
        if pattern == 0:
            zoom_expr = "min(zoom+0.001,1.15)"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"
        elif pattern == 1:
            zoom_expr = "1.1"
            x_expr = f"iw/2-(iw/zoom/2)+sin(on/30)*20"
            y_expr = f"ih/2-(ih/zoom/2)+cos(on/30)*10"
        else:
            zoom_expr = "max(zoom-0.001,1.0)"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"

        fps = 30
        n_frames = int(dur * fps)

        subprocess.run([
            ffmpeg, "-y",
            "-loop", "1", "-i", slide_path,
            "-vf", (
                f"scale=3840:2160,"
                f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}'"
                f":d={n_frames}:s=1920x1080:fps={fps}"
            ),
            "-t", str(dur),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-preset", "fast", "-crf", "18",
            str(segment_path)
        ], capture_output=True)

        if segment_path.exists():
            segments.append(str(segment_path))
            print(f"    Segment {i}: {dur:.1f}s")

    # Step 5b: Concatenate segments
    print("  [video] Concatenating segments...")
    concat_file = OUTPUT_DIR / "video_concat.txt"
    with open(concat_file, 'w') as f:
        for seg in segments:
            f.write(f"file '{seg}'\n")

    video_no_audio = OUTPUT_DIR / "video_no_audio.mp4"
    subprocess.run([
        ffmpeg, "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy", str(video_no_audio)
    ], capture_output=True)

    # Step 5c: Merge with audio
    print("  [video] Merging audio...")
    narration_path = OUTPUT_DIR / "narration.mp3"
    concat_audio(audio_results, str(narration_path))

    video_with_audio = OUTPUT_DIR / "video_with_audio.mp4"
    subprocess.run([
        ffmpeg, "-y",
        "-i", str(video_no_audio),
        "-i", str(narration_path),
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(video_with_audio)
    ], capture_output=True)

    # Step 5d: Burn subtitles
    print("  [video] Burning subtitles...")
    merge_srt(audio_results, str(srt_path))

    # Use SRT directly with force_style for better compatibility
    srt_abs = os.path.abspath(str(srt_path))
    subprocess.run([
        ffmpeg, "-y",
        "-i", str(video_with_audio),
        "-vf", f"subtitles={srt_abs}:force_style='FontName=Noto Sans CJK SC,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Shadow=1,MarginV=30'",
        "-c:v", "libx264", "-crf", "20",
        "-preset", "fast",
        "-c:a", "copy",
        str(FINAL_OUTPUT)
    ], capture_output=True)

    if FINAL_OUTPUT.exists():
        size_mb = FINAL_OUTPUT.stat().st_size / (1024 * 1024)
        print(f"\n  ✅ Video saved: {FINAL_OUTPUT} ({size_mb:.1f} MB)")
    else:
        print(f"\n  ❌ Video generation failed")


def _srt_to_ass(srt_path: str, ass_path: str):
    """Convert SRT to styled ASS subtitle file."""
    entries = _parse_srt(srt_path)

    header = """[Script Info]
Title: DAST Subtitles
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Noto Sans SC,42,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,1,0,1,3,1,2,40,40,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    with open(ass_path, 'w', encoding='utf-8') as f:
        f.write(header)
        for e in entries:
            start = _seconds_to_ts_ass(e['start'])
            end = _seconds_to_ts_ass(e['end'])
            text = e['text'].replace('\n', '\\N')
            f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n")


def _seconds_to_ts_ass(s: float) -> str:
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = s % 60
    return f"{h}:{m:02d}:{sec:05.2f}"


# ── Main ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="DAST Video Pipeline")
    parser.add_argument("--steps", nargs="*", default=["audio", "charts", "slides", "video"],
                        choices=["audio", "charts", "slides", "video"],
                        help="Which steps to run")
    parser.add_argument("--clean", action="store_true", help="Clean output directory")
    parser.add_argument("--mode", choices=["ai", "static", "both"], default="both",
                        help="Render mode: ai=custom backgrounds, static=reference frames, both=both")
    args = parser.parse_args()

    if args.clean and OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
        print("Cleaned output directory")

    print("=" * 60)
    print("DAST Video Pipeline")
    print("=" * 60)

    # Load script
    script = load_script()
    sections = script["sections"]
    print(f"\nLoaded script: {len(sections)} sections")

    srt_path = OUTPUT_DIR / "narration.srt"

    # Step: Audio
    if "audio" in args.steps:
        print("\n--- Step 1: Generate TTS Audio ---")
        audio_results = generate_audio(sections)
    else:
        # Load existing audio results
        audio_results = []
        for i, sec in enumerate(sections):
            audio_path = AUDIO_DIR / f"sec_{i:02d}.mp3"
            srt_file = AUDIO_DIR / f"sec_{i:02d}.srt"
            if audio_path.exists():
                dur = _get_audio_duration(str(audio_path))
                audio_results.append({"index": i, "audio": str(audio_path), "srt": str(srt_file), "duration": dur})
            else:
                audio_results.append({"index": i, "audio": None, "srt": None, "duration": sec.get("duration_sec", 5)})

    # Step: Charts
    if "charts" in args.steps:
        print("\n--- Step 2: Generate Charts ---")
        chart_paths = generate_charts(sections)
    else:
        chart_paths = {}
        for i in range(len(sections)):
            p = CHARTS_DIR / f"chart_{i:02d}.png"
            if p.exists():
                chart_paths[i] = str(p)

    # Step: Slides
    if "slides" in args.steps:
        print("\n--- Step 3: Render Slides ---")
        slide_paths = render_slides(sections, chart_paths)
    else:
        slide_paths = []
        for i in range(len(sections)):
            p = SLIDES_DIR / f"slide_{i:02d}.png"
            slide_paths.append(str(p) if p.exists() else None)

    # Step: Video
    if "video" in args.steps:
        print("\n--- Step 4: Render Video ---")
        render_video(slide_paths, audio_results, str(srt_path), sections)

    print("\n" + "=" * 60)
    print("Pipeline complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
