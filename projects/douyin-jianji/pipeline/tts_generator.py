"""TTS音频生成器 - 使用小米MiMo TTS生成中文配音"""

import os
import time
import base64
import subprocess
import re
from config import API_KEY as MIMO_API_KEY, API_BASE_URL, MIMO_TTS_MODEL, MIMO_TTS_VOICE

# 重试配置
MAX_RETRIES = 3
RETRY_DELAY = 5  # 秒


def split_subtitle_text(text: str, max_chars: int = 24) -> list[str]:
    """Split narration into short subtitle chunks."""
    if not text:
        return []

    pieces = re.findall(r"[^。！？；，、.!?;]+[。！？；，、.!?;]?", text)
    chunks = []
    for piece in pieces or [text]:
        piece = piece.strip()
        while len(piece) > max_chars:
            chunks.append(piece[:max_chars].strip())
            piece = piece[max_chars:].strip()
        if piece:
            chunks.append(piece)
    return chunks


def generate_audio(text: str, output_path: str, voice: str = None) -> dict:
    """
    使用小米MiMo TTS生成音频

    Args:
        text: 要转换的文本
        output_path: 输出音频路径
        voice: TTS语音

    Returns:
        {"audio_path": "...", "subtitle_path": "...", "duration_sec": 45.2}
    """
    srt_path = output_path.rsplit(".", 1)[0] + ".srt"

    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        duration = _get_audio_duration(output_path)
        if not os.path.exists(srt_path):
            _generate_srt_from_text(text, duration, srt_path)
        return {
            "audio_path": output_path,
            "subtitle_path": srt_path,
            "duration_sec": duration,
            "tts_status": "cached",
        }

    # 尝试MiMo TTS
    for attempt in range(MAX_RETRIES):
        try:
            import requests

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
                "audio": {"format": "wav", "voice": voice or MIMO_TTS_VOICE},
            }

            resp = requests.post(
                f"{API_BASE_URL}/chat/completions",
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

                    # Generate SRT
                    duration = _get_audio_duration(output_path)
                    _generate_srt_from_text(text, duration, srt_path)

                    return {
                        "audio_path": output_path,
                        "subtitle_path": srt_path,
                        "duration_sec": duration,
                        "tts_status": "mimo",
                    }

        except Exception as e:
            print(f"    ⚠ TTS error: {type(e).__name__}: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)

    # Fallback to edge-tts
    print("    ⚠ MiMo TTS failed, using edge-tts...")
    return _generate_edge_tts(text, output_path, srt_path)


def _generate_edge_tts(text: str, output_path: str, srt_path: str) -> dict:
    """使用edge-tts生成音频"""
    try:
        import edge_tts
        import asyncio

        proxy = os.environ.get("HTTPS_PROXY")
        communicate = edge_tts.Communicate(text, "zh-CN-YunxiNeural", proxy=proxy, connect_timeout=30)

        async def _gen():
            with open(output_path, "wb") as f:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])

        asyncio.run(_gen())

        # Generate SRT
        duration = _get_audio_duration(output_path)
        _generate_srt_from_text(text, duration, srt_path)

        return {
            "audio_path": output_path,
            "subtitle_path": srt_path,
            "duration_sec": duration,
            "tts_status": "edge",
        }

    except Exception as e:
        print(f"    ⚠ edge-tts error: {type(e).__name__}: {e}")
        fallback_duration = max(len(text) / 6.0, 1.0)
        _generate_srt_from_text(text, fallback_duration, srt_path)
        return {
            "audio_path": "",
            "subtitle_path": srt_path,
            "duration_sec": 0,
            "tts_status": "missing",
        }


def _generate_srt_from_text(text: str, duration: float, srt_path: str):
    """从文本生成SRT字幕"""
    sentences = split_subtitle_text(text)

    if not sentences:
        sentences = [text]

    # 均匀分配时长
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
    """将秒转换为SRT时间戳 (HH:MM:SS,mmm)"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")


def _get_audio_duration(audio_path: str) -> float:
    """使用ffmpeg获取音频时长"""
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
    """获取ffmpeg路径"""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except:
        return "ffmpeg"


def generate_sections_audio(sections: list, output_dir: str, voice: str = None) -> list:
    """
    为每个脚本段落生成音频

    Args:
        sections: 段落列表 [{"label": "...", "text": "...", "duration_sec": ...}]
        output_dir: 输出目录
        voice: TTS语音

    Returns:
        [{"label": ..., "audio_path": ..., "subtitle_path": ..., "duration_sec": ...}]
    """
    os.makedirs(output_dir, exist_ok=True)
    results = []

    for i, section in enumerate(sections):
        text = section.get("text", "")
        if not text:
            continue

        filename = f"section_{i:02d}.mp3"
        audio_path = os.path.join(output_dir, filename)

        print(f"  TTS段落 {i}: {section.get('label', '')} ({len(text)}字符)")
        result = generate_audio(text, audio_path, voice)
        if result:
            result["label"] = section.get("label", f"段落 {i}")
            result["index"] = i
            results.append(result)

    return results


def concat_audio(section_results: list, output_path: str, pause_ms: int = 500) -> str:
    """连接多个音频文件，中间添加停顿"""
    ffmpeg = _get_ffmpeg()

    # 创建静音文件用于停顿
    silence_path = os.path.join(os.path.dirname(output_path), "_silence.mp3")
    subprocess.run([
        ffmpeg, "-y", "-f", "lavfi", "-i",
        f"anullsrc=r=24000:cl=mono",
        "-t", str(pause_ms / 1000),
        "-c:a", "libmp3lame", "-q:a", "9",
        silence_path
    ], capture_output=True)

    # 构建连接列表
    list_path = os.path.join(os.path.dirname(output_path), "_concat.txt")
    with open(list_path, "w") as f:
        for i, result in enumerate(section_results):
            if result.get("audio_path") and os.path.exists(result["audio_path"]):
                # 使用绝对路径
                f.write(f"file '{os.path.abspath(result['audio_path'])}'\n")
                if i < len(section_results) - 1:
                    f.write(f"file '{os.path.abspath(silence_path)}'\n")

    # 连接音频
    subprocess.run([
        ffmpeg, "-y", "-f", "concat", "-safe", "0",
        "-i", list_path,
        "-c:a", "libmp3lame", "-q:a", "2",
        output_path
    ], capture_output=True)

    # 清理临时文件
    for f in [silence_path, list_path]:
        if os.path.exists(f):
            os.remove(f)

    return output_path
