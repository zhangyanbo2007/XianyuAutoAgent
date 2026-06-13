"""Production readiness and final video rendering helpers."""

from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path
from typing import Any, Callable


class MissingProductionDependency(RuntimeError):
    """Raised when the final MP4 cannot be rendered from the manifest."""


def _read_manifest(manifest_path: Path | str) -> dict[str, Any]:
    return json.loads(Path(manifest_path).read_text(encoding="utf-8"))


def _ffmpeg_path() -> str:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which("ffmpeg") or ""


def _edge_tts_available() -> bool:
    return importlib.util.find_spec("edge_tts") is not None


def _dependency_value(name: str, overrides: dict[str, bool] | None, detector: Callable[[], bool]) -> bool:
    if overrides and name in overrides:
        return bool(overrides[name])
    return detector()


def _report_for_manifest(
    manifest_path: Path | str,
    audio_path: Path | str | None = None,
    dependency_overrides: dict[str, bool] | None = None,
) -> dict[str, Any]:
    manifest_file = Path(manifest_path)
    manifest = _read_manifest(manifest_file)
    slides = manifest.get("slides", [])
    slide_paths = [Path(slide.get("path", "")) for slide in slides]
    missing_slides = [str(path) for path in slide_paths if not path.exists() or path.stat().st_size == 0]

    subtitle_path = Path(manifest.get("subtitle_path", ""))
    subtitle_ready = subtitle_path.exists() and subtitle_path.stat().st_size > 0
    selected_audio = Path(audio_path) if audio_path else Path(manifest.get("audio_output_path", ""))
    audio_ready = selected_audio.exists() and selected_audio.stat().st_size > 0

    ffmpeg_binary = _ffmpeg_path()
    ffmpeg_ready = _dependency_value("ffmpeg", dependency_overrides, lambda: bool(ffmpeg_binary))
    tts_ready = _dependency_value("edge_tts", dependency_overrides, _edge_tts_available)
    slides_ready = bool(slides) and not missing_slides
    narration_sections = manifest.get("narration_sections", [])
    can_generate_audio = bool(narration_sections) and tts_ready
    can_render_final_video = slides_ready and subtitle_ready and audio_ready and ffmpeg_ready

    missing_dependencies = []
    if not ffmpeg_ready:
        missing_dependencies.append("ffmpeg")
    if not tts_ready:
        missing_dependencies.append("edge_tts")

    if not slides_ready or not subtitle_ready:
        next_action = "regenerate_visual_artifacts"
    elif not audio_ready and can_generate_audio:
        next_action = "generate_audio"
    elif not audio_ready:
        next_action = "install_or_configure_tts"
    elif not ffmpeg_ready:
        next_action = "install_ffmpeg"
    elif can_render_final_video:
        next_action = "render_video"
    else:
        next_action = "inspect_report"

    return {
        "manifest_path": str(manifest_file),
        "renderer": manifest.get("renderer", ""),
        "scene_count": len(slides),
        "slides_ready": slides_ready,
        "missing_slides": missing_slides,
        "subtitle_path": str(subtitle_path),
        "subtitle_ready": subtitle_ready,
        "audio_path": str(selected_audio),
        "audio_ready": audio_ready,
        "ffmpeg_path": ffmpeg_binary,
        "ffmpeg_ready": ffmpeg_ready,
        "tts_ready": tts_ready,
        "missing_dependencies": missing_dependencies,
        "can_generate_audio": can_generate_audio,
        "can_render_final_video": can_render_final_video,
        "video_output_path": manifest.get("video_output_path", str(manifest_file.parent / "longform.mp4")),
        "next_action": next_action,
    }


def build_production_readiness(
    manifest_path: Path | str,
    output_path: Path | str | None = None,
    dependency_overrides: dict[str, bool] | None = None,
) -> Path:
    """Write a report that says whether the manifest can become a final MP4."""
    manifest_file = Path(manifest_path)
    report = _report_for_manifest(manifest_file, dependency_overrides=dependency_overrides)
    path = Path(output_path) if output_path else manifest_file.parent / "production_readiness.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _default_renderer() -> Callable[[list[dict[str, Any]], str, str, str, int], str]:
    from motion_renderer import render_video_v2

    return render_video_v2


def _manifest_narration_sections(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    sections = [section for section in manifest.get("narration_sections", []) if section.get("text")]
    if sections:
        return sections
    text = manifest.get("narration_text", "").strip()
    return [{"scene_index": 0, "label": "narration", "text": text}] if text else []


def _concat_audio_segments(segment_paths: list[Path], output_path: Path | str) -> Path:
    if not segment_paths:
        raise ValueError("no audio segments to concatenate")
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        import imageio_ffmpeg

        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
    concat_file = output.parent / "_audio_concat.txt"
    concat_file.write_text("".join(f"file '{path.as_posix()}'\n" for path in segment_paths), encoding="utf-8")
    try:
        import subprocess

        result = subprocess.run(
            [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(output)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0 or not output.exists() or output.stat().st_size == 0:
            result = subprocess.run(
                [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c:a", "libmp3lame", "-q:a", "2", str(output)],
                capture_output=True,
                text=True,
                check=False,
            )
        if result.returncode != 0:
            raise RuntimeError(result.stderr[-1000:])
    finally:
        concat_file.unlink(missing_ok=True)
    return output


def _write_edge_tts(text: str, output_path: Path | str, voice: str) -> Path:
    import asyncio
    import edge_tts

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    async def _run() -> None:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(path))

    asyncio.run(_run())
    return path


def generate_audio_from_manifest(
    manifest_path: Path | str,
    output_path: Path | str | None = None,
    voice: str = "zh-CN-YunxiNeural",
    tts_writer: Callable[[str, Path | str, str], Path] | None = None,
    audio_joiner: Callable[[list[Path], Path | str], Path] | None = None,
) -> Path:
    """Generate narration audio from a render manifest, one scene at a time."""
    manifest_file = Path(manifest_path)
    manifest = _read_manifest(manifest_file)
    sections = _manifest_narration_sections(manifest)
    if not sections:
        raise ValueError("manifest has no narration text")
    target = Path(output_path) if output_path else Path(manifest.get("audio_output_path", manifest_file.parent / "narration.mp3"))
    segment_dir = target.parent / "audio_segments"
    segment_dir.mkdir(parents=True, exist_ok=True)
    writer = tts_writer or _write_edge_tts
    segment_paths: list[Path] = []
    for i, section in enumerate(sections):
        text = section.get("text", "").strip()
        if not text:
            continue
        segment_path = segment_dir / f"section_{i:02d}.mp3"
        result = Path(writer(text, segment_path, voice))
        if not result.exists() or result.stat().st_size == 0:
            raise RuntimeError(f"audio generation did not create a non-empty segment: {result}")
        segment_paths.append(result)
    joiner = audio_joiner or _concat_audio_segments
    output = Path(joiner(segment_paths, target))
    if not output.exists() or output.stat().st_size == 0:
        raise RuntimeError(f"audio concatenation did not create a non-empty file: {output}")
    return output


def _media_duration(path: Path | str) -> float:
    try:
        import imageio_ffmpeg

        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
    import subprocess

    result = subprocess.run([ffmpeg, "-i", str(path), "-f", "null", "-"], capture_output=True, text=True, check=False)
    for line in result.stderr.split("\n"):
        if "Duration:" in line:
            parts = line.split("Duration:", 1)[1].split(",", 1)[0].strip()
            h, m, s = parts.split(":")
            return float(h) * 3600 + float(m) * 60 + float(s)
    raise RuntimeError(f"could not read media duration: {path}")


def retime_manifest_to_audio_segments(
    manifest_path: Path | str,
    duration_probe: Callable[[Path | str], float] | None = None,
) -> Path:
    """Retarget slide durations and SRT timestamps to generated per-scene audio."""
    from .models import Timeline, TimelineEntry
    from .timeline import write_srt

    manifest_file = Path(manifest_path)
    manifest = _read_manifest(manifest_file)
    slides = manifest.get("slides", [])
    sections = _manifest_narration_sections(manifest)
    segment_dir = manifest_file.parent / "audio_segments"
    probe = duration_probe or _media_duration
    durations: list[float] = []
    for i, _slide in enumerate(slides):
        segment_path = segment_dir / f"section_{i:02d}.mp3"
        if not segment_path.exists() or segment_path.stat().st_size == 0:
            raise FileNotFoundError(f"missing audio segment: {segment_path}")
        durations.append(round(float(probe(segment_path)), 3))

    cursor = 0.0
    entries: list[TimelineEntry] = []
    for i, (slide, duration) in enumerate(zip(slides, durations)):
        slide["duration_sec"] = duration
        start = round(cursor, 3)
        end = round(start + duration, 3)
        text = sections[i].get("text", "") if i < len(sections) else ""
        entries.append(TimelineEntry(scene_index=int(slide.get("scene_index", i)), start_sec=start, end_sec=end, transition=slide.get("transition", "crossfade"), narration=text))
        cursor = end

    total = round(sum(durations), 3)
    manifest["slides"] = slides
    manifest["total_duration_sec"] = total
    timeline = Timeline(entries=entries, total_duration_sec=total, transition_sec=float(manifest.get("transition_sec", 0.45)))
    timeline_path = manifest_file.parent / "audio_aligned_timeline.json"
    timeline_path.write_text(json.dumps(timeline.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    write_srt(timeline, manifest.get("subtitle_path", manifest_file.parent / "narration.srt"))
    manifest["audio_aligned_timeline_path"] = str(timeline_path)
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_file


def render_video_from_manifest(
    manifest_path: Path | str,
    audio_path: Path | str | None = None,
    output_path: Path | str | None = None,
    renderer: Callable[[list[dict[str, Any]], str, str, str, int], str] | None = None,
    dependency_overrides: dict[str, bool] | None = None,
) -> Path:
    """Render a final MP4 from a longform render manifest."""
    manifest = _read_manifest(manifest_path)
    report = _report_for_manifest(manifest_path, audio_path=audio_path, dependency_overrides=dependency_overrides)
    if not report["can_render_final_video"]:
        raise MissingProductionDependency(f"cannot render final video; next_action={report['next_action']}; missing={report['missing_dependencies']}")

    selected_audio = str(Path(audio_path) if audio_path else Path(report["audio_path"]))
    selected_output = Path(output_path) if output_path else Path(report["video_output_path"])
    selected_output.parent.mkdir(parents=True, exist_ok=True)
    selected_renderer = renderer or _default_renderer()
    result = selected_renderer(
        manifest.get("slides", []),
        selected_audio,
        str(selected_output),
        manifest.get("subtitle_path", ""),
        int(manifest.get("fps", 30)),
    )
    return Path(result)
