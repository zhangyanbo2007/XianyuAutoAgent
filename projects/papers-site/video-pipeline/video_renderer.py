"""Render final video from slides + audio using FFmpeg."""

import os
import subprocess
import json as _json


def _get_ffmpeg():
    """Find ffmpeg binary."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        pass
    for path in ["/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg"]:
        if os.path.exists(path):
            return path
    return "ffmpeg"


def render_video(slides: list, audio_path: str, subtitle_path: str,
                 output_path: str, srt_path: str = None) -> str:
    """Render final video from slides and audio.

    Args:
        slides: list of {"path": "...", "duration_sec": float, "type": "..."}
        audio_path: concatenated audio file
        subtitle_path: SRT subtitle file
        output_path: output MP4 path
        srt_path: optional SRT file for hard-burned subtitles
    """
    ffmpeg = _get_ffmpeg()
    work_dir = os.path.dirname(output_path)

    # 1. Create video from slides with durations
    slides_video = os.path.join(work_dir, "_slides.mp4")
    _create_slides_video(ffmpeg, slides, slides_video)

    # 2. Get audio duration
    audio_duration = _get_duration(ffmpeg, audio_path)

    # 3. Adjust video duration to match audio + ending
    total_slide_duration = sum(s["duration_sec"] for s in slides)
    ending_duration = slides[-1]["duration_sec"] if slides else 4.0

    # 4. Combine video + audio
    combined = os.path.join(work_dir, "_combined.mp4")
    subprocess.run([
        ffmpeg, "-y",
        "-i", slides_video,
        "-i", audio_path,
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        combined,
    ], capture_output=True, check=True)

    # 5. Burn subtitles if SRT file exists
    if srt_path and os.path.exists(srt_path):
        # Try ASS subtitle burn first
        ass_path = _srt_to_ass(ffmpeg, srt_path, work_dir)
        success = False
        if ass_path:
            result = subprocess.run([
                ffmpeg, "-y",
                "-i", combined,
                "-vf", f"ass={ass_path}",
                "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                "-c:a", "copy",
                output_path,
            ], capture_output=True)
            success = result.returncode == 0

        if not success:
            # Fallback: no subtitle burn, just rename
            print("  ⚠ Subtitle burn skipped (ffmpeg libass not available)")
            if os.path.exists(combined):
                os.rename(combined, output_path)
    else:
        # No subtitles, just rename
        if os.path.exists(combined):
            os.rename(combined, output_path)

    # Cleanup temp files
    for f in [slides_video, combined]:
        if os.path.exists(f):
            os.remove(f)

    return output_path


def _create_slides_video(ffmpeg: str, slides: list, output_path: str):
    """Create a video from slide images with specified durations."""
    if not slides:
        return

    # Create concat file with per-image durations
    work_dir = os.path.dirname(output_path)
    concat_path = os.path.join(work_dir, "_slides_concat.txt")

    with open(concat_path, "w") as f:
        for slide in slides:
            f.write(f"file '{slide['path']}'\n")
            f.write(f"duration {slide['duration_sec']}\n")
        # Repeat last frame (ffmpeg concat demuxer requirement)
        f.write(f"file '{slides[-1]['path']}'\n")

    subprocess.run([
        ffmpeg, "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_path,
        "-vf", "fps=30,format=yuv420p",
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        output_path,
    ], capture_output=True, check=True)

    if os.path.exists(concat_path):
        os.remove(concat_path)


def _get_duration(ffmpeg: str, media_path: str) -> float:
    """Get duration of a media file."""
    result = subprocess.run([
        ffmpeg, "-i", media_path,
        "-f", "null", "-"
    ], capture_output=True, text=True)

    for line in result.stderr.split("\n"):
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = parts.split(":")
            return float(h) * 3600 + float(m) * 60 + float(s)
    return 0.0


def _srt_to_ass(ffmpeg: str, srt_path: str, work_dir: str) -> str:
    """Convert SRT to ASS with custom styling."""
    ass_path = os.path.join(work_dir, "_subtitle.ass")

    # Read SRT
    with open(srt_path, "r", encoding="utf-8") as f:
        srt_content = f.read()

    # Parse SRT and convert to ASS
    events = _parse_srt(srt_content)
    if not events:
        return None

    ass_header = """[Script Info]
Title: Paper Video Subtitle
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,Noto Sans CJK SC,48,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,1,2,40,40,60,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""

    ass_events = ""
    for start, end, text in events:
        start_ass = _sec_to_ass_time(start)
        end_ass = _sec_to_ass_time(end)
        ass_events += f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{text}\n"

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header + ass_events)

    return ass_path


def _parse_srt(srt_content: str) -> list:
    """Parse SRT content into (start_sec, end_sec, text) tuples."""
    events = []
    blocks = srt_content.strip().split("\n\n")

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue

        # Parse timestamp line
        time_line = lines[1]
        if "-->" not in time_line:
            continue

        parts = time_line.split("-->")
        start = _srt_time_to_sec(parts[0].strip())
        end = _srt_time_to_sec(parts[1].strip())
        text = " ".join(lines[2:]).strip()

        if text:
            events.append((start, end, text))

    return events


def _srt_time_to_sec(time_str: str) -> float:
    """Convert SRT timestamp to seconds."""
    time_str = time_str.replace(",", ".")
    parts = time_str.split(":")
    return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])


def _sec_to_ass_time(seconds: float) -> str:
    """Convert seconds to ASS timestamp (H:MM:SS.cc)."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


if __name__ == "__main__":
    print(f"FFmpeg: {_get_ffmpeg()}")
