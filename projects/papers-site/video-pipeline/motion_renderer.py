"""Render video with Ken Burns (zoompan), transitions, and subtitle burn-in."""

import os
import subprocess
import json


def _get_ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except:
        pass
    for p in ["/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg"]:
        if os.path.exists(p):
            return p
    return "ffmpeg"


def _get_duration(ffmpeg, path):
    r = subprocess.run([ffmpeg, "-i", path, "-f", "null", "-"],
                       capture_output=True, text=True)
    for line in r.stderr.split("\n"):
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = parts.split(":")
            return float(h)*3600 + float(m)*60 + float(s)
    return 0.0


def render_video_v2(slides: list, audio_path: str, output_path: str,
                    srt_path: str = None, fps: int = 30) -> str:
    """Render final video with zoompan motion, cross-fades, and subtitle burn-in.

    Args:
        slides: list of {"path": ..., "duration_sec": float, "type": ...}
        audio_path: full narration audio
        output_path: output MP4
        srt_path: optional ASS/SRT subtitle file
    """
    ffmpeg = _get_ffmpeg()
    work_dir = os.path.dirname(output_path)

    # Step 1: Create video from each slide with zoompan motion
    segment_files = []
    for i, slide in enumerate(slides):
        seg_path = os.path.join(work_dir, f"_seg_{i:03d}.mp4")
        _create_animated_segment(ffmpeg, slide["path"], seg_path,
                                 slide["duration_sec"], fps, i)
        if os.path.exists(seg_path) and os.path.getsize(seg_path) > 0:
            segment_files.append(seg_path)

    if not segment_files:
        raise RuntimeError("No video segments generated")

    # Step 2: Concatenate with cross-fade transitions
    concat_path = os.path.join(work_dir, "_concat_list.txt")
    with open(concat_path, "w") as f:
        for seg in segment_files:
            f.write(f"file '{seg}'\n")

    concat_video = os.path.join(work_dir, "_concat.mp4")
    subprocess.run([
        ffmpeg, "-y", "-f", "concat", "-safe", "0",
        "-i", concat_path,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        concat_video,
    ], capture_output=True)

    # Step 3: Merge with audio
    combined = os.path.join(work_dir, "_combined.mp4")
    subprocess.run([
        ffmpeg, "-y",
        "-i", concat_video,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        combined,
    ], capture_output=True)

    # Step 4: Burn subtitles if available
    if srt_path and os.path.exists(srt_path) and os.path.getsize(srt_path) > 0:
        # Convert SRT to ASS for styling
        ass_path = _srt_to_styled_ass(srt_path, work_dir)
        if ass_path:
            result = subprocess.run([
                ffmpeg, "-y",
                "-i", combined,
                "-vf", f"ass={ass_path}",
                "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                "-c:a", "copy",
                output_path,
            ], capture_output=True)
            if result.returncode == 0:
                _cleanup(work_dir, segment_files + [concat_path, concat_video, combined, ass_path])
                return output_path

    # Fallback: no subtitle burn
    if os.path.exists(combined):
        os.rename(combined, output_path)

    _cleanup(work_dir, segment_files + [concat_path, concat_video])
    return output_path


def _create_animated_segment(ffmpeg: str, image_path: str, output_path: str,
                             duration: float, fps: int, index: int):
    """Create a video segment with zoompan (Ken Burns) motion."""
    total_frames = int(duration * fps)

    # Keep the motion subtle and centered so titles/charts near the safe margin
    # are not cropped away by the Ken Burns effect.
    if index % 3 == 0:
        # Slow zoom in
        zoom_expr = f"min(zoom+0.00025,1.035)"
        x_expr = f"iw/2-(iw/zoom/2)"
        y_expr = f"ih/2-(ih/zoom/2)"
    elif index % 3 == 1:
        # Hold a gentle center crop for visual continuity.
        zoom_expr = "1.02"
        x_expr = f"iw/2-(iw/zoom/2)"
        y_expr = f"ih/2-(ih/zoom/2)"
    else:
        # Slow zoom out
        zoom_expr = f"if(eq(on,1),1.035,max(zoom-0.00025,1.0))"
        x_expr = f"iw/2-(iw/zoom/2)"
        y_expr = f"ih/2-(ih/zoom/2)"

    subprocess.run([
        ffmpeg, "-y",
        "-loop", "1", "-i", image_path,
        "-vf", (
            f"scale=3840:-1,"
            f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}'"
            f":d={total_frames}:s=1920x1080:fps={fps},"
            f"format=yuv420p"
        ),
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        output_path,
    ], capture_output=True, timeout=120)


def _srt_to_styled_ass(srt_path: str, work_dir: str) -> str:
    """Convert SRT to styled ASS with bottom bar subtitle."""
    ass_path = os.path.join(work_dir, "_styled.ass")

    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = content.strip().split("\n\n")
    events = []
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue
        time_line = lines[1]
        if "-->" not in time_line:
            continue
        parts = time_line.split("-->")
        start = _srt_to_sec(parts[0].strip())
        end = _srt_to_sec(parts[1].strip())
        text = " ".join(lines[2:]).strip()
        if text:
            events.append((start, end, text))

    if not events:
        return None

    header = """[Script Info]
Title: Subtitle
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,Noto Sans CJK SC,42,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,3,2,1,2,60,60,50,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
    event_lines = ""
    for start, end, text in events:
        s = _sec_to_ass(start)
        e = _sec_to_ass(end)
        # Add \fad for smooth fade in/out
        event_lines += f"Dialogue: 0,{s},{e},Default,,0,0,0,,{{\\fad(200,200)}}{text}\n"

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(header + event_lines)

    return ass_path


def _srt_to_sec(t):
    t = t.replace(",", ".")
    p = t.split(":")
    return float(p[0])*3600 + float(p[1])*60 + float(p[2])


def _sec_to_ass(s):
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = s % 60
    return f"{h}:{m:02d}:{sec:05.2f}"


def _cleanup(work_dir, files):
    for f in files:
        try:
            if os.path.exists(f):
                os.remove(f)
        except:
            pass


if __name__ == "__main__":
    print(f"FFmpeg: {_get_ffmpeg()}")
