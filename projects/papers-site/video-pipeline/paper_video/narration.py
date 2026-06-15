"""TTS narration and timed subtitle generation via edge-tts.

Produces per-section audio (mp3), per-section SRT, a concatenated narration,
and a merged SRT with correct global time offsets.
"""

from __future__ import annotations

import asyncio
import os
import re
import subprocess
import threading
from pathlib import Path
from typing import Any


def _run_async_safe(coro):
    """Run an async coroutine safely, even if an event loop is already running
    (e.g. inside Playwright). Spawns a fresh loop in a daemon thread."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        result = [None]
        exc = [None]
        def _target():
            try:
                result[0] = asyncio.run(coro)
            except Exception as e:
                exc[0] = e
        t = threading.Thread(target=_target, daemon=True)
        t.start()
        t.join(timeout=120)
        if exc[0]:
            raise exc[0]
        return result[0]
    return asyncio.run(coro)


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


def get_audio_duration(audio_path: str) -> float:
    ffmpeg = _ffmpeg()
    try:
        result = subprocess.run(
            [ffmpeg, "-i", audio_path, "-f", "null", "-"],
            capture_output=True, text=True, timeout=15,
        )
        for line in result.stderr.split("\n"):
            if "Duration:" in line:
                parts = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = parts.split(":")
                return float(h) * 3600 + float(m) * 60 + float(s)
    except Exception:
        pass
    return 5.0


def _generate_srt(text: str, output_path: str) -> None:
    """Generate SRT subtitles from a narration text (Chinese sentence splitting)."""
    sentences = re.split(r"(?<=[。！？；\n])", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    with open(output_path, "w", encoding="utf-8") as f:
        for idx, sent in enumerate(sentences, 1):
            duration = max(1.0, len(sent) / 5.0)
            start = _sec_to_srt(0.0)
            end = _sec_to_srt(duration)
            f.write(f"{idx}\n{start} --> {end}\n{sent}\n\n")


def _sec_to_srt(s: float) -> str:
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:06.3f}".replace(".", ",")


def _sec_to_srt_ts(s: float) -> str:
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:06.3f}".replace(".", ",")


def _parse_srt_time(ts: str) -> tuple[float, float]:
    parts = ts.replace(",", ".").strip().split("-->")
    return _ts_to_sec(parts[0].strip()), _ts_to_sec(parts[1].strip())


def _ts_to_sec(ts: str) -> float:
    h, m, s = ts.split(":")
    return float(h) * 3600 + float(m) * 60 + float(s)


def _parse_srt(path: str) -> list[dict]:
    entries = []
    content = Path(path).read_text(encoding="utf-8")
    blocks = content.strip().split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) >= 3:
            start, end = _parse_srt_time(lines[1])
            entries.append({"start": start, "end": end, "text": "\n".join(lines[2:])})
    return entries


def _write_srt(entries: list[dict], output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        for i, e in enumerate(entries, 1):
            start = _sec_to_srt_ts(e["start"])
            end = _sec_to_srt_ts(e["end"])
            f.write(f"{i}\n{start} --> {end}\n{e['text']}\n\n")


# ── public API ──────────────────────────────────────────────────────


def generate_narration(
    sections: list[dict[str, Any]],
    out_dir: str | Path,
    voice: str = "zh-CN-YunxiNeural",
    rate: str = "+0%",
) -> list[dict[str, Any]]:
    """Generate TTS audio + SRT per section. Returns audio_results list."""
    import edge_tts

    out_dir = Path(out_dir)
    audio_dir = out_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for i, sec in enumerate(sections):
        text = sec.get("text", "").strip()
        audio_path = audio_dir / f"sec_{i:02d}.mp3"
        srt_path = audio_dir / f"sec_{i:02d}.srt"

        if not text:
            results.append({
                "index": i,
                "audio": None,
                "srt": None,
                "duration": sec.get("duration_sec", 5),
            })
            continue

        if audio_path.exists():
            dur = get_audio_duration(str(audio_path))
            results.append({
                "index": i,
                "audio": str(audio_path),
                "srt": str(srt_path) if srt_path.exists() else None,
                "duration": dur,
            })
            print(f"  [tts] Slide {i:02d}: SKIP ({dur:.1f}s)")
            continue

        print(f"  [tts] Slide {i:02d}: {sec.get('label', '')[:30]}...", end=" ", flush=True)
        ok = False
        for attempt in range(3):
            try:
                _run_async_safe(edge_tts.Communicate(text, voice, rate=rate).save(str(audio_path)))
                ok = True
                break
            except Exception as e:
                if attempt < 2:
                    print(f"retry...", end=" ", flush=True)
                    import time; time.sleep(2)
                else:
                    print(f"ERROR: {e}")
        if ok:
            _generate_srt(text, str(srt_path))
            dur = get_audio_duration(str(audio_path))
            results.append({
                "index": i,
                "audio": str(audio_path),
                "srt": str(srt_path),
                "duration": dur,
            })
            print(f"{dur:.1f}s")
        else:
            results.append({
                "index": i,
                "audio": None,
                "srt": None,
                "duration": sec.get("duration_sec", 5),
            })

    return results


def concat_narration(audio_results: list[dict], out_path: str) -> None:
    """Concatenate all section audio files with small gaps."""
    ffmpeg = _ffmpeg()
    valid = [r for r in audio_results if r.get("audio") and os.path.exists(r["audio"])]
    if not valid:
        return

    audio_dir = str(Path(out_path).parent)
    silence_path = os.path.join(audio_dir, "silence_500ms.mp3")
    if not os.path.exists(silence_path):
        subprocess.run([
            ffmpeg, "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
            "-t", "0.5", "-q:a", "9", silence_path,
        ], capture_output=True)

    concat_file = os.path.join(audio_dir, "concat_list.txt")
    with open(concat_file, "w") as f:
        for j, r in enumerate(valid):
            f.write(f"file '{r['audio']}'\n")
            if j < len(valid) - 1:
                f.write(f"file '{silence_path}'\n")

    subprocess.run([
        ffmpeg, "-y", "-f", "concat", "-safe", "0",
        "-i", concat_file, "-c", "copy", out_path,
    ], capture_output=True)


def merge_srt(audio_results: list[dict], out_path: str) -> None:
    """Merge per-section SRT files with correct global time offsets."""
    valid = [r for r in audio_results if r.get("srt") and os.path.exists(r["srt"])]
    all_entries = []
    offset = 0.0
    for r in valid:
        entries = _parse_srt(r["srt"])
        for entry in entries:
            entry["start"] += offset
            entry["end"] += offset
            all_entries.append(entry)
        offset += r.get("duration", 5.0) + 0.5
    _write_srt(all_entries, out_path)
