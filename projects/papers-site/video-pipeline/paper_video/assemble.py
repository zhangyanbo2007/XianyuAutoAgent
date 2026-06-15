"""Video assembly: Ken Burns animated segments → concat → mux audio → burn subtitles → final.mp4.

Reuses the battle-tested ffmpeg pipeline from dast_pipeline.py.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any


def _ffmpeg() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    for p in ["/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg"]:
        if os.path.exists(p):
            return p
    return "ffmpeg"


def _ken_burns_filter(i: int, dur: float, fps: int = 30) -> str:
    """Three alternating Ken Burns patterns (zoom-in, pan, zoom-out)."""
    n_frames = int(dur * fps)
    pattern = i % 3
    if pattern == 0:
        zoom = "min(zoom+0.001,1.15)"
        x = "iw/2-(iw/zoom/2)"
        y = "ih/2-(ih/zoom/2)"
    elif pattern == 1:
        zoom = "1.1"
        x = "iw/2-(iw/zoom/2)+sin(on/30)*20"
        y = "ih/2-(ih/zoom/2)+cos(on/30)*10"
    else:
        zoom = "max(zoom-0.001,1.0)"
        x = "iw/2-(iw/zoom/2)"
        y = "ih/2-(ih/zoom/2)"
    return (
        f"scale=3840:2160,"
        f"zoompan=z='{zoom}':x='{x}':y='{y}'"
        f":d={n_frames}:s=1920x1080:fps={fps}"
    )


def _render_segments(
    slide_paths: dict[int, str],
    audio_results: list[dict],
    sections: list[dict[str, Any]],
    out_dir: Path,
) -> list[str]:
    """Create one animated MP4 per slide. Returns list of segment paths."""
    ffmpeg = _ffmpeg()
    seg_dir = out_dir / "segments"
    seg_dir.mkdir(parents=True, exist_ok=True)
    segments = []

    for i, sec in enumerate(sections):
        slide = slide_paths.get(i)
        if not slide or not os.path.exists(slide):
            continue
        dur = audio_results[i]["duration"] if i < len(audio_results) else sec.get("duration_sec", 5)
        seg_path = seg_dir / f"seg_{i:02d}.mp4"
        if seg_path.exists():
            segments.append(str(seg_path))
            continue
        vf = _ken_burns_filter(i, dur)
        subprocess.run([
            ffmpeg, "-y",
            "-loop", "1", "-i", slide,
            "-vf", vf,
            "-t", str(dur),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-preset", "fast", "-crf", "18",
            str(seg_path),
        ], capture_output=True)
        if seg_path.exists():
            segments.append(str(seg_path))
            print(f"    seg {i:02d}: {dur:.1f}s")
    return segments


def _concat_segments(segments: list[str], out_dir: Path) -> Path:
    ffmpeg = _ffmpeg()
    concat_file = out_dir / "segments.txt"
    with open(concat_file, "w") as f:
        for seg in segments:
            f.write(f"file '{seg}'\n")
    video_no_audio = out_dir / "video_no_audio.mp4"
    subprocess.run([
        ffmpeg, "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_file), "-c", "copy", str(video_no_audio),
    ], capture_output=True)
    return video_no_audio


def _mux_audio(video_no_audio: Path, narration_mp3: Path, out_dir: Path) -> Path:
    ffmpeg = _ffmpeg()
    video_with_audio = out_dir / "video_with_audio.mp4"
    subprocess.run([
        ffmpeg, "-y",
        "-i", str(video_no_audio), "-i", str(narration_mp3),
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(video_with_audio),
    ], capture_output=True)
    return video_with_audio


def _burn_subtitles(video_with_audio: Path, srt_path: Path, final_output: Path) -> None:
    ffmpeg = _ffmpeg()
    srt_abs = str(srt_path.resolve())
    subprocess.run([
        ffmpeg, "-y",
        "-i", str(video_with_audio),
        "-vf", (
            f"subtitles={srt_abs}:"
            "force_style='FontName=Noto Sans CJK SC,FontSize=22,"
            "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
            "Outline=2,Shadow=1,MarginV=30'"
        ),
        "-c:v", "libx264", "-crf", "20",
        "-preset", "fast",
        "-c:a", "copy",
        str(final_output),
    ], capture_output=True)


# ── public entry ────────────────────────────────────────────────────


def assemble_video(
    slide_paths: dict[int, str],
    audio_results: list[dict],
    srt_path: str,
    sections: list[dict[str, Any]],
    out_dir: str | Path,
    narration_mp3: str | None = None,
) -> Path | None:
    """Full assembly pipeline → final video.mp4. Returns final path or None."""
    out = Path(out_dir)
    final_output = out / "video.mp4"

    print("  [video] Rendering Ken Burns segments...")
    segments = _render_segments(slide_paths, audio_results, sections, out)
    if not segments:
        print("  [video] No segments — aborting")
        return None

    print("  [video] Concatenating segments...")
    video_no_audio = _concat_segments(segments, out)

    if not video_no_audio.exists():
        print("  [video] Concat failed")
        return None

    print("  [video] Merging audio...")
    if narration_mp3 and os.path.exists(narration_mp3):
        video_with_audio = _mux_audio(video_no_audio, Path(narration_mp3), out)
    else:
        video_with_audio = video_no_audio

    print("  [video] Burning subtitles...")
    _burn_subtitles(video_with_audio, Path(srt_path), final_output)

    if final_output.exists():
        size_mb = final_output.stat().st_size / (1024 * 1024)
        print(f"\n  ✅ Video saved: {final_output} ({size_mb:.1f} MB)")
        # Clean up intermediate files
        for f in (out / "video_no_audio.mp4", out / "video_with_audio.mp4", out / "segments.txt"):
            f.unlink(missing_ok=True)
        seg_dir = out / "segments"
        if seg_dir.exists():
            import shutil
            shutil.rmtree(seg_dir, ignore_errors=True)
        return final_output
    else:
        print("\n  ❌ Video generation failed")
        return None
