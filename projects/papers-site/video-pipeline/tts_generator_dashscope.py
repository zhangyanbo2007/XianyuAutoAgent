"""Generate TTS audio using Dashscope API (more reliable than edge-tts)."""

import os
import time
import json
import subprocess
from config import DATA_DIR

DASHSCOPE_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
DASHSCOPE_API = "https://dashscope.aliyuncs.com/api/v1"
DASHSCOPE_TTS_ENDPOINT = f"{DASHSCOPE_API}/services/audio/tts/SpeechSynthesizer"
DASHSCOPE_TTS_MODEL = "cosyvoice-v3-flash"
DEFAULT_VOICE = "longxiaochun_v3"


def generate_audio(text: str, output_path: str, voice: str = DEFAULT_VOICE) -> dict:
    """Generate audio using Dashscope TTS API.

    Returns:
        {"audio_path": "...", "subtitle_path": "...", "duration_sec": 45.2}
    """
    srt_path = output_path.rsplit(".", 1)[0] + ".srt"

    if not DASHSCOPE_KEY:
        print("  ⚠ No DASHSCOPE_API_KEY, skipping TTS")
        return {"audio_path": "", "subtitle_path": "", "duration_sec": 0}

    try:
        import requests
    except ImportError:
        return _generate_with_urllib(text, output_path, srt_path, voice)

    return _generate_with_requests(text, output_path, srt_path, voice)


def _generate_with_requests(text: str, output_path: str, srt_path: str, voice: str) -> dict:
    """Generate using requests library."""
    import requests

    headers = {
        "Authorization": f"Bearer {DASHSCOPE_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": DASHSCOPE_TTS_MODEL,
        "input": {
            "text": text,
            "voice": voice,
            "format": "mp3",
            "sample_rate": 24000,
        },
    }

    try:
        resp = requests.post(
            DASHSCOPE_TTS_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=60,
        )
        data = resp.json()

        audio_url = _extract_audio_url(data)
        if audio_url:
            # Download audio
            audio_resp = requests.get(audio_url, timeout=30)
            with open(output_path, "wb") as f:
                f.write(audio_resp.content)

            # Generate SRT from text (simple split)
            duration = _get_audio_duration(output_path)
            _generate_srt_from_text(text, duration, srt_path)

            return {
                "audio_path": output_path,
                "subtitle_path": srt_path,
                "duration_sec": duration,
            }
        else:
            print(f"  ⚠ TTS failed: {data.get('message', 'unknown error')}")
            return {"audio_path": "", "subtitle_path": "", "duration_sec": 0}

    except Exception as e:
        print(f"  ⚠ TTS error: {type(e).__name__}: {e}")
        return {"audio_path": "", "subtitle_path": "", "duration_sec": 0}


def _generate_with_urllib(text: str, output_path: str, srt_path: str, voice: str) -> dict:
    """Generate using urllib (fallback)."""
    import urllib.request
    import ssl

    ctx = ssl.create_default_context()
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_KEY}",
        "Content-Type": "application/json",
    }
    payload = json.dumps({
        "model": DASHSCOPE_TTS_MODEL,
        "input": {
            "text": text,
            "voice": voice,
            "format": "mp3",
            "sample_rate": 24000,
        },
    }).encode()

    try:
        req = urllib.request.Request(
            DASHSCOPE_TTS_ENDPOINT,
            data=payload,
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
            data = json.loads(resp.read())

        audio_url = _extract_audio_url(data)
        if audio_url:
            req = urllib.request.Request(audio_url)
            with urllib.request.urlopen(req, timeout=30) as resp:
                with open(output_path, "wb") as f:
                    f.write(resp.read())

            duration = _get_audio_duration(output_path)
            _generate_srt_from_text(text, duration, srt_path)

            return {
                "audio_path": output_path,
                "subtitle_path": srt_path,
                "duration_sec": duration,
            }
    except Exception as e:
        print(f"  ⚠ TTS urllib error: {type(e).__name__}: {e}")

    return {"audio_path": "", "subtitle_path": "", "duration_sec": 0}


def _extract_audio_url(data: dict) -> str:
    audio = data.get("output", {}).get("audio", {})
    if isinstance(audio, dict):
        return audio.get("url", "")
    if isinstance(audio, str):
        return audio
    return ""


def _generate_srt_from_text(text: str, duration: float, srt_path: str):
    """Generate SRT subtitles from text by splitting into sentences."""
    import re

    # Split by Chinese sentence endings
    sentences = re.split(r'(?<=[。！？；.!?;])\s*', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        sentences = [text]

    # Distribute duration evenly
    total_chars = sum(len(s) for s in sentences)
    if total_chars == 0:
        return

    current_time = 0.0
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, sentence in enumerate(sentences):
            proportion = len(sentence) / total_chars
            seg_duration = proportion * duration
            start = current_time
            end = current_time + seg_duration

            f.write(f"{i + 1}\n")
            f.write(f"{_sec_to_srt(start)} --> {_sec_to_srt(end)}\n")
            f.write(f"{sentence}\n\n")

            current_time = end


def _sec_to_srt(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")


def _get_audio_duration(audio_path: str) -> float:
    ffmpeg = _get_ffmpeg()
    r = subprocess.run([ffmpeg, "-i", audio_path, "-f", "null", "-"],
                       capture_output=True, text=True)
    for line in r.stderr.split("\n"):
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = parts.split(":")
            return float(h) * 3600 + float(m) * 60 + float(s)
    return 0.0


def _get_ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except:
        return "ffmpeg"


def generate_sections_audio(sections: list, output_dir: str, voice: str = DEFAULT_VOICE) -> list:
    """Generate audio for each script section."""
    os.makedirs(output_dir, exist_ok=True)
    results = []

    for i, section in enumerate(sections):
        text = section.get("text", "")
        if not text:
            continue

        filename = f"section_{i:02d}.mp3"
        audio_path = os.path.join(output_dir, filename)

        print(f"  TTS section {i}: {section.get('label', '')} ({len(text)} chars)")
        result = generate_audio(text, audio_path, voice)
        result["label"] = section.get("label", f"Section {i}")
        result["index"] = i
        results.append(result)

    return results


def concat_audio(section_results: list, output_path: str, pause_ms: int = 500) -> str:
    """Concatenate section audio files with pauses."""
    ffmpeg = _get_ffmpeg()

    # Create silence
    silence_path = os.path.join(os.path.dirname(output_path), "_silence.mp3")
    subprocess.run([
        ffmpeg, "-y", "-f", "lavfi", "-i",
        f"anullsrc=r=24000:cl=mono",
        "-t", str(pause_ms / 1000),
        "-c:a", "libmp3lame", "-q:a", "9",
        silence_path
    ], capture_output=True)

    # Build concat list
    list_path = os.path.join(os.path.dirname(output_path), "_concat.txt")
    with open(list_path, "w") as f:
        for i, result in enumerate(section_results):
            if result.get("audio_path") and os.path.exists(result["audio_path"]):
                f.write(f"file '{result['audio_path']}'\n")
                if i < len(section_results) - 1:
                    f.write(f"file '{silence_path}'\n")

    # Concatenate
    subprocess.run([
        ffmpeg, "-y", "-f", "concat", "-safe", "0",
        "-i", list_path,
        "-c:a", "libmp3lame", "-q:a", "2",
        output_path
    ], capture_output=True)

    # Cleanup
    for f in [silence_path, list_path]:
        if os.path.exists(f):
            os.remove(f)

    return output_path
