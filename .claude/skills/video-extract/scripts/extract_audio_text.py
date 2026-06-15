#!/usr/bin/env python3
"""
视频提取音频和文字
- 提取音频 (moviepy)
- 语音转文字 (OpenAI Whisper API / 本地whisper)
"""
import os
import sys
import argparse
from pathlib import Path

# 设置ffmpeg路径（使用skill目录下的）
skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ffmpeg_path = os.path.join(skill_dir, "ffmpeg")
if os.path.exists(ffmpeg_path):
    os.environ["PATH"] = skill_dir + os.pathsep + os.environ.get("PATH", "")


def extract_audio(video_path: str, output_dir: str = None) -> str:
    """从视频提取音频 (WAV格式，16kHz单声道)"""
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

    clip = VideoFileClip(str(video_path))
    clip.audio.write_audiofile(str(audio_path), fps=16000, nbytes=2, codec='pcm_s16le')
    duration = clip.duration
    clip.close()

    print(f"✅ 音频已提取: {audio_path} (时长: {duration:.1f}秒)")
    return str(audio_path)


def transcribe_with_local_whisper(audio_path: str, model_size: str = "medium") -> str:
    """使用本地whisper模型进行语音识别"""
    import whisper
    import torch

    # 尝试用GPU，不行就用CPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"使用设备: {device}，模型: {model_size}")

    model = whisper.load_model(model_size, device=device)
    result = model.transcribe(audio_path, language="zh")
    return result["text"]


def main():
    parser = argparse.ArgumentParser(description="从视频提取音频和文字")
    parser.add_argument("video", help="视频文件路径")
    parser.add_argument("-o", "--output-dir", help="输出目录 (默认: 视频同目录)")
    parser.add_argument("--audio-only", action="store_true", help="只提取音频，不转文字")
    parser.add_argument("--model", default="medium", help="whisper模型大小 (tiny/base/small/medium/large)")

    args = parser.parse_args()

    # 提取音频
    print(f"正在从视频提取音频: {args.video}")
    audio_path = extract_audio(args.video, args.output_dir)

    if args.audio_only:
        print(f"完成! 音频文件: {audio_path}")
        return

    # 语音转文字
    print("正在进行语音识别...")
    try:
        text = transcribe_with_local_whisper(audio_path, args.model)

        # 保存文字
        txt_path = Path(audio_path).with_suffix(".txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"✅ 文字已提取: {txt_path}")
        print(f"\n--- 文字内容 ---\n{text}")

    except Exception as e:
        print(f"❌ 语音识别失败: {e}")
        print(f"音频文件已保存: {audio_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
