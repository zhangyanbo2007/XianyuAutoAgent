#!/usr/bin/env python3
"""
《山海经》视频后处理全流程脚本
功能：TTS 配音 → 旁白加速对齐 → 叠加到原BGM → 添加字幕

用法：
  python3 full-pipeline.py <video_path> --subtitles subtitles.json --output output.mp4

subtitles.json 格式：
[
  {"start": 0.0, "end": 3.0, "text": "杻阳之山，有兽鹿蜀"},
  {"start": 2.7, "end": 5.2, "text": "状如马，白首，赤尾"},
  ...
]
"""

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path

from moviepy import (
    VideoFileClip, AudioFileClip, CompositeAudioClip,
    TextClip, CompositeVideoClip
)


def generate_tts(text: str, output_path: str, voice: str = "zh-CN-YunJianNeural",
                 rate: str = "-25%", pitch: str = "-10Hz"):
    """用 edge-tts 生成单句配音"""
    subprocess.run([
        "edge-tts",
        "--voice", voice,
        "--rate", rate,
        "--pitch", pitch,
        "--text", text,
        "--write-media", output_path
    ], check=True)
    return output_path


def speed_up_audio(audio_clip, factor: float):
    """加速音频"""
    return audio_clip.with_speed_scaled(factor)


def create_narration(subtitles, tmp_dir, speed_factor=1.35):
    """
    生成所有旁白片段，按时间轴排列，合并为完整旁白音轨。

    speed_factor: 加速因子，1.3-1.5 之间
    """
    clips = []
    for sub in subtitles:
        text = sub["text"]
        target_start = sub["start"]

        # 生成 TTS
        tts_path = os.path.join(tmp_dir, f"narr_{sub['start']:.1f}.mp3")
        generate_tts(text, tts_path)

        # 加载并加速
        audio = AudioFileClip(tts_path)
        audio_fast = speed_up_audio(audio, speed_factor)
        clips.append(audio_fast.with_start(target_start))

    narration = CompositeAudioClip(clips)
    return narration, clips


def mix_audio(video_path, narration, output_path=None):
    """
    将旁白叠加到原视频BGM上（BGM降至30%音量）
    """
    video = VideoFileClip(video_path)
    bgm = video.audio

    # BGM 降音量
    bgm_quiet = bgm.with_volume_scaled(0.30)

    # 混合
    final_audio = CompositeAudioClip([bgm_quiet, narration])
    final_audio = final_audio.with_duration(video.duration)

    if output_path is None:
        output_path = str(Path(video_path).stem + "_with_audio.mp4")

    final_video = video.with_audio(final_audio)
    final_video.write_videofile(
        output_path,
        codec="libx264", audio_codec="aac", fps=24,
        preset="fast", bitrate="5000k"
    )

    video.close()
    bgm.close()
    bgm_quiet.close()
    final_video.close()

    return output_path


def add_subtitles(video_path, subtitles, output_path=None):
    """
    在视频底部添加字幕
    """
    video = VideoFileClip(video_path)
    w, h = video.size

    subtitle_clips = []
    for sub in subtitles:
        txt = TextClip(
            text=sub["text"],
            font_size=52,
            color='white',
            stroke_color='black',
            stroke_width=4,
            font='NotoSansCJK-Regular',
            text_align='center',
            horizontal_align='center',
            vertical_align='center',
            method='label',
            transparent=True
        )
        duration = sub["end"] - sub["start"]
        txt = txt.with_position(('center', h - 130)).with_duration(duration).with_start(sub["start"])
        subtitle_clips.append(txt)

    final = CompositeVideoClip([video, *subtitle_clips])
    final = final.with_audio(video.audio).with_duration(video.duration)

    if output_path is None:
        output_path = str(Path(video_path).stem + "_with_subs.mp4")

    final.write_videofile(
        output_path,
        codec="libx264", audio_codec="aac", fps=24,
        preset="fast", bitrate="5000k"
    )

    video.close()
    for c in subtitle_clips:
        c.close()
    final.close()

    return output_path


def full_pipeline(video_path, subtitles_json, output_path, speed_factor=1.35):
    """完整流程：TTS → 旁白 → 混合音频 → 字幕"""
    with open(subtitles_json, 'r', encoding='utf-8') as f:
        subtitles = json.load(f)

    tmp_dir = tempfile.mkdtemp(prefix="shanhaijing_")

    # 1. 生成旁白
    print("🎤 生成旁白...")
    narration, clips = create_narration(subtitles, tmp_dir, speed_factor)

    # 2. 混合音频（旁白叠加到原BGM）
    print("🎵 混合音频...")
    audio_video = mix_audio(video_path, narration, os.path.join(tmp_dir, "step2.mp4"))

    # 3. 添加字幕
    print("📝 添加字幕...")
    final_path = add_subtitles(audio_video, subtitles, output_path)

    # 清理
    narration.close()
    for c in clips:
        c.close()

    print(f"\n✅ 完成: {final_path}")
    return final_path


def main():
    parser = argparse.ArgumentParser(description="《山海经》视频后处理全流程")
    parser.add_argument("video_path", help="拼接后的视频文件路径")
    parser.add_argument("--subtitles", required=True, help="字幕 JSON 文件路径")
    parser.add_argument("--output", default=None, help="输出文件路径")
    parser.add_argument("--speed-factor", type=float, default=1.35,
                        help="旁白加速因子 (1.3-1.5)")

    args = parser.parse_args()

    if args.output is None:
        args.output = str(Path(args.video_path).stem + "_final.mp4")

    full_pipeline(args.video_path, args.subtitles, args.output, args.speed_factor)


if __name__ == "__main__":
    main()
