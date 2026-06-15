#!/usr/bin/env python3
"""
语音转写模块
支持两种后端：
1. 百炼 DashScope ASR API（推荐，paraformer-v2 异步转写）
2. 本地 Whisper 模型（备选，需安装 torch）

输出 JSON 格式，每个 segment 包含 start/end/text
"""
import os
import sys
import json
import time
import argparse
import tempfile
import urllib.request
from pathlib import Path

# 路径设置
SKILL_DIR = Path(__file__).parent.parent
CONFIG_PATH = SKILL_DIR / "config.yaml"

# 设置 ffmpeg 路径（使用 video-extract skill 的）
FFMPEG_PATH = Path(__file__).parent.parent.parent / "video-extract" / "ffmpeg"
if FFMPEG_PATH.exists():
    os.environ["PATH"] = str(FFMPEG_PATH.parent) + os.pathsep + os.environ.get("PATH", "")


def load_config():
    import yaml
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def extract_audio(video_path: str, output_dir: str = None) -> str:
    """从视频提取音频（WAV 格式，16kHz 单声道）"""
    from moviepy import VideoFileClip

    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"视频不存在: {video_path}")

    if output_dir is None:
        output_dir = video_path.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    audio_path = output_dir / f"{video_path.stem}.wav"

    print(f"🎵 提取音频: {video_path.name}")
    clip = VideoFileClip(str(video_path))
    clip.audio.write_audiofile(str(audio_path), fps=16000, nbytes=2, codec='pcm_s16le',
                               logger=None)
    duration = clip.duration
    clip.close()

    print(f"✅ 音频提取完成: {audio_path.name} ({duration:.1f}秒)")
    return str(audio_path)


# ========== 百炼 DashScope ASR API (paraformer-v2 异步转写) ==========

def upload_audio_for_asr(file_path: str) -> str:
    """
    上传音频文件到 COS 获取公网 URL（DashScope ASR 需要可访问的 URL）
    使用 upload-cos skill 的独立 venv
    """
    import subprocess
    skill_dir = Path(__file__).parent.parent.parent
    upload_script = skill_dir / "upload-cos" / "scripts" / "upload.py"
    upload_python = skill_dir / "upload-cos" / ".venv" / "bin" / "python"
    if not upload_script.exists():
        raise FileNotFoundError(f"未找到 upload-cos skill: {upload_script}")

    # 使用 upload-cos 的独立 venv
    cmd = [str(upload_python), str(upload_script), str(file_path)] if upload_python.exists() \
        else ["python3", str(upload_script), str(file_path)]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"COS 上传失败: {result.stderr}")

    # 从输出中提取 URL
    for line in result.stdout.split("\n"):
        if "URL:" in line:
            return line.split("URL:")[-1].strip()
    raise RuntimeError(f"未找到上传 URL: {result.stdout}")


def transcribe_with_dashscope(video_path: str, language: str = "zh") -> dict:
    """
    使用百炼 DashScope paraformer-v2 异步转写 API

    流程：
    1. 提取音频
    2. 上传音频到 DashScope 临时存储
    3. 提交异步转写任务
    4. 轮询等待结果
    5. 下载转写结果（带时间戳）
    """
    import dashscope
    from dashscope.audio.asr import Transcription

    video_path = Path(video_path)

    # 读取 API key
    config = load_config()
    api_key = config.get("dashscope_api_key") or os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("未配置 DashScope API Key")

    dashscope.api_key = api_key

    # 提取音频
    audio_path = extract_audio(str(video_path))

    # 上传音频到 R2 获取公网 URL
    print(f"📤 上传音频到 R2...")
    file_url = upload_audio_for_asr(audio_path)
    print(f"   URL: {file_url[:80]}...")

    # 提交异步转写任务
    print(f"📝 提交 ASR 任务 (paraformer-v2)...")
    task = Transcription.async_call(
        model='paraformer-v2',
        file_urls=[file_url],
        language_hints=[language],
    )

    if task.status_code != 200:
        raise RuntimeError(f"ASR 任务提交失败: {task.status_code} {task.message}")

    task_id = task.output.get('task_id')
    print(f"   任务ID: {task_id}")

    # 轮询等待结果
    print(f"⏳ 等待转写完成...")
    for i in range(60):  # 最多等 3 分钟
        time.sleep(3)
        result = Transcription.fetch(task=task_id)
        status = result.output.get('task_status', 'UNKNOWN') if result.output else 'UNKNOWN'

        if status == 'SUCCEEDED':
            break
        elif status == 'FAILED':
            raise RuntimeError(f"ASR 任务失败: {result.output}")

        if i % 10 == 0 and i > 0:
            print(f"   已等待 {i*3} 秒...")

    # 解析结果
    results = result.output.get('results', [])
    if not results:
        raise RuntimeError("ASR 未返回结果")

    transcription_url = results[0].get('transcription_url')
    if not transcription_url:
        raise RuntimeError("未找到转写结果 URL")

    # 下载转写结果
    print(f"📥 下载转写结果...")
    resp = urllib.request.urlopen(transcription_url)
    asr_result = json.loads(resp.read())

    # 提取带时间戳的 segments
    segments = []
    for transcript in asr_result.get('transcripts', []):
        for sentence in transcript.get('sentences', []):
            seg = {
                "start": round(sentence.get('begin_time', 0) / 1000, 2),
                "end": round(sentence.get('end_time', 0) / 1000, 2),
                "text": sentence.get('text', '').strip(),
            }
            if seg['text']:
                segments.append(seg)

    full_text = " ".join(s["text"] for s in segments)
    duration = segments[-1]["end"] if segments else 0

    output = {
        "video_path": str(video_path),
        "audio_path": audio_path,
        "language": language,
        "engine": "dashscope",
        "model": "paraformer-v2",
        "segments": segments,
        "full_text": full_text,
        "duration": round(duration, 2),
        "segment_count": len(segments),
    }

    print(f"✅ 转写完成: {len(segments)} 个片段, {duration:.1f}秒")
    return output


# ========== 本地 Whisper ==========

def transcribe_with_whisper(video_path: str, model_size: str = "medium",
                             language: str = "zh") -> dict:
    """使用本地 Whisper 模型转写"""
    import whisper

    video_path = Path(video_path)
    audio_path = extract_audio(str(video_path))

    print(f"🧠 加载 Whisper 模型: {model_size}")
    model = whisper.load_model(model_size)

    print(f"📝 开始转写: {video_path.name}")
    result = model.transcribe(audio_path, language=language, verbose=False)

    segments = []
    for seg in result.get("segments", []):
        segments.append({
            "start": round(seg["start"], 2),
            "end": round(seg["end"], 2),
            "text": seg["text"].strip(),
        })

    full_text = " ".join(s["text"] for s in segments)
    duration = segments[-1]["end"] if segments else 0

    output = {
        "video_path": str(video_path),
        "audio_path": audio_path,
        "language": language,
        "engine": "whisper",
        "model_size": model_size,
        "segments": segments,
        "full_text": full_text,
        "duration": round(duration, 2),
        "segment_count": len(segments),
    }

    print(f"✅ 转写完成: {len(segments)} 个片段, {duration:.1f}秒")
    return output


# ========== 统一入口 ==========

def transcribe_video(video_path: str, engine: str = "auto",
                     model_size: str = "medium", language: str = "zh") -> dict:
    """统一转写入口"""
    if engine == "dashscope":
        return transcribe_with_dashscope(video_path, language)
    elif engine == "whisper":
        return transcribe_with_whisper(video_path, model_size, language)
    else:
        config = load_config()
        if config.get("dashscope_api_key") or os.environ.get("DASHSCOPE_API_KEY"):
            try:
                return transcribe_with_dashscope(video_path, language)
            except Exception as e:
                print(f"⚠️  DashScope ASR 失败: {e}")
                print("   回退到本地 Whisper...")
                return transcribe_with_whisper(video_path, model_size, language)
        else:
            print("⚠️  未配置 DashScope API Key，使用本地 Whisper")
            return transcribe_with_whisper(video_path, model_size, language)


def save_transcript(transcript: dict, output_dir: str = None) -> str:
    """保存转写结果为 JSON"""
    if output_dir is None:
        output_dir = SKILL_DIR / load_config()["paths"]["transcripts"]
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    video_name = Path(transcript["video_path"]).stem
    output_path = output_dir / f"{video_name}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(transcript, f, ensure_ascii=False, indent=2)

    print(f"💾 转写结果已保存: {output_path}")
    return str(output_path)


def main():
    parser = argparse.ArgumentParser(description="视频语音转写")
    parser.add_argument("video", help="视频文件路径")
    parser.add_argument("--engine", "-e", default="auto",
                        choices=["dashscope", "whisper", "auto"])
    parser.add_argument("--model", "-m", default="medium")
    parser.add_argument("--language", "-l", default="zh")
    parser.add_argument("--output-dir", "-o")
    parser.add_argument("--no-save", action="store_true")
    args = parser.parse_args()

    transcript = transcribe_video(args.video, args.engine, args.model, args.language)

    if not args.no_save:
        save_transcript(transcript, args.output_dir)

    print(f"\n📊 转写摘要:")
    print(f"   引擎: {transcript.get('engine')}")
    print(f"   时长: {transcript['duration']}秒")
    print(f"   片段数: {transcript['segment_count']}")
    print(f"   前200字: {transcript['full_text'][:200]}...")


if __name__ == "__main__":
    main()
