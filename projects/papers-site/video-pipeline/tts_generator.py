"""Generate TTS audio using Xiaomi MiMo API (优先) or edge-tts (备选)."""

import asyncio
import os
import time
import base64
import subprocess
import json
from config import API_KEY as MIMO_API_KEY, API_BASE_URL

# MiMo TTS config - use proxy URL
MIMO_TTS_BASE = API_BASE_URL  # token-plan-cn proxy
MIMO_TTS_MODEL = "mimo-v2.5-tts"
MIMO_TTS_VOICE = "苏打"  # 男性中文音色

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 5


def generate_audio(text: str, output_path: str, voice: str = None) -> dict:
    """Generate audio using edge-tts (reliable) with MiMo as fallback.

    Returns:
        {"audio_path": "...", "subtitle_path": "...", "duration_sec": 45.2}
    """
    srt_path = output_path.rsplit(".", 1)[0] + ".srt"

    # Try edge-tts first (more reliable)
    result = _generate_edge_tts(text, output_path)
    if result.get("audio_path") and os.path.exists(result["audio_path"]):
        duration = _get_audio_duration(result["audio_path"])
        _generate_srt_from_text(text, duration, srt_path)
        return {"audio_path": result["audio_path"], "subtitle_path": srt_path, "duration_sec": duration}

    # Fallback to MiMo TTS
    print("    ⚠ edge-tts failed, trying MiMo TTS...")
    result = _generate_mimo_tts(text, output_path, voice or MIMO_TTS_VOICE)
    if result.get("audio_path") and os.path.exists(result["audio_path"]):
        duration = _get_audio_duration(result["audio_path"])
        _generate_srt_from_text(text, duration, srt_path)
        return {"audio_path": result["audio_path"], "subtitle_path": srt_path, "duration_sec": duration}

    return {"audio_path": "", "subtitle_path": "", "duration_sec": 0}


def _generate_mimo_tts(text: str, output_path: str, voice: str) -> dict:
    """Generate audio using MiMo TTS API via proxy."""
    try:
        import requests
        import json

        headers = {
            "Authorization": f"Bearer {MIMO_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": MIMO_TTS_MODEL,
            "messages": [
                {"role": "user", "content": "用科普博主的语气，自然流畅地朗读以下内容"},
                {"role": "assistant", "content": text},
            ],
            "audio": {"format": "wav", "voice": voice},
        }

        resp = requests.post(
            f"{MIMO_TTS_BASE}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,
        )
        data = resp.json()

        # Extract audio from response
        if "choices" in data and data["choices"]:
            message = data["choices"][0].get("message", {})
            audio_info = message.get("audio", {})
            audio_data_b64 = audio_info.get("data", "")

            if audio_data_b64:
                audio_data = base64.b64decode(audio_data_b64)
                # Save as WAV first
                wav_path = output_path.replace(".mp3", ".wav")
                with open(wav_path, "wb") as f:
                    f.write(audio_data)

                # Convert to MP3
                ffmpeg = _get_ffmpeg()
                subprocess.run([
                    ffmpeg, "-y", "-i", wav_path,
                    "-c:a", "libmp3lame", "-q:a", "2",
                    output_path,
                ], capture_output=True)

                # Cleanup WAV
                if os.path.exists(wav_path):
                    os.remove(wav_path)

                return {"audio_path": output_path}

    except Exception as e:
        print(f"    ⚠ MiMo TTS error: {type(e).__name__}: {e}")

    return {}


def _generate_edge_tts(text: str, output_path: str) -> dict:
    """Fallback: Generate audio using edge-tts."""
    try:
        import edge_tts

        proxy = os.environ.get("HTTPS_PROXY")
        communicate = edge_tts.Communicate(text, "zh-CN-YunxiNeural", proxy=proxy, connect_timeout=30)

        async def _gen():
            with open(output_path, "wb") as f:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])

        asyncio.run(_gen())
        return {"audio_path": output_path}

    except Exception as e:
        print(f"    ⚠ edge-tts error: {type(e).__name__}: {e}")

    return {}


def _generate_srt_from_text(text: str, duration: float, srt_path: str):
    """Generate SRT subtitles from text by splitting into sentences."""
    import re

    sentences = re.split(r'(?<=[。！？；.!?;])\s*', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        sentences = [text]

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
    except ImportError:
        import os
        for p in ["/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg"]:
            if os.path.exists(p):
                return p
        return "ffmpeg"


def generate_sections_audio(sections: list, output_dir: str, voice: str = None) -> list:
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

        for attempt in range(MAX_RETRIES):
            try:
                result = generate_audio(text, audio_path, voice)
                if result.get("audio_path") and os.path.exists(result["audio_path"]):
                    result["label"] = section.get("label", f"Section {i}")
                    result["index"] = i
                    results.append(result)
                    break
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    print(f"    ⚠ Attempt {attempt + 1} failed: {type(e).__name__}, retrying...")
                    time.sleep(RETRY_DELAY)
                else:
                    print(f"    ✗ Failed after {MAX_RETRIES} attempts")
                    results.append({"audio_path": "", "subtitle_path": "", "duration_sec": 0,
                                    "label": section.get("label", ""), "index": i})

    return results


def concat_audio(section_results: list, output_path: str, pause_ms: int = 500) -> str:
    """Concatenate section audio files with pauses."""
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    silence_path = os.path.join(os.path.dirname(output_path), "_silence.mp3")
    subprocess.run([
        ffmpeg, "-y", "-f", "lavfi", "-i",
        f"anullsrc=r=24000:cl=mono",
        "-t", str(pause_ms / 1000),
        "-c:a", "libmp3lame", "-q:a", "9",
        silence_path
    ], capture_output=True)

    list_path = os.path.join(os.path.dirname(output_path), "_concat.txt")
    with open(list_path, "w") as f:
        for i, result in enumerate(section_results):
            if result.get("audio_path") and os.path.exists(result["audio_path"]):
                f.write(f"file '{result['audio_path']}'\n")
                if i < len(section_results) - 1:
                    f.write(f"file '{silence_path}'\n")

    subprocess.run([
        ffmpeg, "-y", "-f", "concat", "-safe", "0",
        "-i", list_path,
        "-c:a", "libmp3lame", "-q:a", "2",
        output_path
    ], capture_output=True)

    for f in [silence_path, list_path]:
        if os.path.exists(f):
            os.remove(f)

    return output_path
