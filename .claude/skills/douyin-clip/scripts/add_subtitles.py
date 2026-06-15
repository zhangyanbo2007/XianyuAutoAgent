#!/usr/bin/env python3
"""
字幕烧录模块
根据转写的时间戳生成 SRT 字幕，并烧录到视频中
支持抖音风格字幕（大号白色字体，底部居中）
"""
import os
import sys
import json
import subprocess
import argparse
from pathlib import Path

# 路径设置
SKILL_DIR = Path(__file__).parent.parent
CONFIG_PATH = SKILL_DIR / "config.yaml"

# ffmpeg 路径
FFMPEG_PATH = SKILL_DIR.parent / "video-extract" / "ffmpeg"
FFMPEG_BIN = str(FFMPEG_PATH) if FFMPEG_PATH.exists() else "ffmpeg"


def load_config():
    import yaml
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def timestamp_to_srt(seconds: float) -> str:
    """将秒数转换为 SRT 时间格式 (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def filter_segments_for_clip(segments: list, start: float, end: float) -> list:
    """筛选出在 [start, end] 范围内的 segments，并调整时间戳"""
    filtered = []
    for seg in segments:
        seg_start = seg["start"]
        seg_end = seg["end"]

        # 检查是否与 [start, end] 有重叠
        if seg_end <= start or seg_start >= end:
            continue

        # 裁剪到范围内
        new_start = max(seg_start, start) - start  # 相对于片段起点
        new_end = min(seg_end, end) - start

        # 过滤掉太短的片段
        if new_end - new_start < 0.3:
            continue

        filtered.append({
            "start": round(new_start, 3),
            "end": round(new_end, 3),
            "text": seg["text"],
        })

    return filtered


def generate_srt(segments: list, output_path: str) -> str:
    """生成 SRT 字幕文件"""
    lines = []
    for i, seg in enumerate(segments, 1):
        start_str = timestamp_to_srt(seg["start"])
        end_str = timestamp_to_srt(seg["end"])
        text = seg["text"]

        lines.append(str(i))
        lines.append(f"{start_str} --> {end_str}")
        lines.append(text)
        lines.append("")

    content = "\n".join(lines)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path

def add_bottom_black_bar(video_path: str, output_path: str, bar_height: int = 180) -> bool:
    """
    在视频底部添加黑色遮盖条，用于遮盖原视频的硬字幕
    """
    cmd = [
        FFMPEG_BIN,
        "-y",
        "-i", video_path,
        "-vf", f"drawbox=x=0:y=ih-{bar_height}:w=iw:h={bar_height}:color=black:t=fill",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "copy",
        "-movflags", "+faststart",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return result.returncode == 0


def burn_subtitles(video_path: str, srt_path: str, output_path: str,
                    font_size: int = 42, font_color: str = "white",
                    outline_color: str = "black", outline_width: int = 3) -> bool:
    """
    将字幕烧录到视频中

    Args:
        video_path: 输入视频
        srt_path: SRT 字幕文件
        output_path: 输出视频
        font_size: 字体大小
        font_color: 字体颜色
        outline_color: 描边颜色
        outline_width: 描边宽度

    Returns:
        bool: 是否成功
    """
    # 使用 ASS 风格的 force_style 来设置抖音竖屏字幕
    # 黄色大号字体 + 宽大黑色背景条，完全遮盖底部原字幕
    force_style = (
        f"FontSize=48,"               # 超大号字体（竖屏必须大）
        f"PrimaryColour=&H0000FFFF,"  # 黄色（ASS: &HBBGGRR）
        f"OutlineColour=&H00000000,"  # 黑色描边
        f"BackColour=&HFF000000,"     # 纯黑色背景（完全遮盖原字幕）
        f"BorderStyle=4,"             # 背景框模式
        f"Outline=0,"                 # 无描边（用背景框代替）
        f"Shadow=0,"
        f"Alignment=2,"               # 底部居中
        f"MarginV=50,"                # 距底部50像素
        f"MarginL=20,"                # 左边距
        f"MarginR=20"                 # 右边距
    )

    # 转义路径中的特殊字符（ffmpeg filter 需要）
    srt_escaped = srt_path.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")

    cmd = [
        FFMPEG_BIN,
        "-y",
        "-i", video_path,
        "-vf", f"subtitles='{srt_escaped}':force_style='{force_style}'",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "copy",  # 音频直接复制
        "-movflags", "+faststart",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return result.returncode == 0


def add_subtitles_to_clip(video_path: str, transcript_path: str,
                           clip_start: float, clip_end: float,
                           output_path: str = None) -> str:
    """
    给切割后的视频片段添加字幕

    Args:
        video_path: 视频片段路径
        transcript_path: 完整转写 JSON 路径
        clip_start: 片段在原视频中的开始时间
        clip_end: 片段在原视频中的结束时间
        output_path: 输出路径

    Returns:
        str: 输出文件路径
    """
    # 加载转写数据
    with open(transcript_path) as f:
        transcript = json.load(f)

    # 筛选范围内的 segments
    segments = filter_segments_for_clip(
        transcript["segments"], clip_start, clip_end
    )

    if not segments:
        print("⚠️  该片段内没有字幕内容")
        return video_path

    # 生成 SRT
    video_stem = Path(video_path).stem
    srt_path = str(Path(video_path).parent / f"{video_stem}.srt")
    generate_srt(segments, srt_path)

    # 输出路径
    if output_path is None:
        output_path = str(Path(video_path).parent / f"{video_stem}_sub.mp4")

    # 烧录字幕（如果输出=输入，用临时文件中转）
    print(f"📝 烧录字幕: {len(segments)} 条")
    if os.path.abspath(output_path) == os.path.abspath(video_path):
        tmp_output = output_path + ".tmp.mp4"
        success = burn_subtitles(video_path, srt_path, tmp_output)
        if success:
            # 添加底部黑条遮盖原视频硬字幕
            final_output = tmp_output + ".final.mp4"
            add_bottom_black_bar(tmp_output, final_output)
            os.replace(final_output, output_path)
            os.remove(tmp_output)
    else:
        success = burn_subtitles(video_path, srt_path, output_path)
        # 添加底部黑条遮盖原视频硬字幕
        if success:
            add_bottom_black_bar(output_path, output_path + ".bar.mp4")
            os.replace(output_path + ".bar.mp4", output_path)

    if success:
        print(f"✅ 字幕烧录完成: {output_path}")
        # 清理 SRT 文件
        if os.path.exists(srt_path):
            os.remove(srt_path)
        return output_path
    else:
        print(f"❌ 字幕烧录失败")
        return video_path


def batch_add_subtitles(clips_dir: str, transcript_path: str):
    """批量给目录中的所有切片添加字幕"""
    clips_dir = Path(clips_dir)

    # 查找高光分析文件（用于获取时间偏移）
    highlight_files = list(clips_dir.parent.parent.glob("highlights/*.json"))
    if not highlight_files:
        print("⚠️  未找到高光分析文件，无法确定时间偏移")
        return

    # 假设 clips 目录名对应视频标题
    video_title = clips_dir.name
    highlight_file = None
    for hf in highlight_files:
        if video_title in hf.stem:
            highlight_file = hf
            break

    if not highlight_file:
        print(f"⚠️  未找到对应 {video_title} 的高光分析文件")
        return

    with open(highlight_file) as f:
        highlight_data = json.load(f)

    # 处理每个切片
    clip_files = sorted(clips_dir.glob("*.mp4"))
    highlights = highlight_data["highlights"]

    for clip_file in clip_files:
        # 匹配切片和高光（按文件名序号）
        try:
            idx = int(clip_file.stem.split("_")[0]) - 1
            if idx >= len(highlights):
                continue
            h = highlights[idx]
        except (ValueError, IndexError):
            continue

        print(f"\n处理: {clip_file.name}")
        add_subtitles_to_clip(
            video_path=str(clip_file),
            transcript_path=transcript_path,
            clip_start=h["start"],
            clip_end=h["end"],
            output_path=str(clip_file),  # 覆盖原文件
        )


def main():
    parser = argparse.ArgumentParser(description="视频字幕烧录")
    parser.add_argument("video", help="视频文件路径")
    parser.add_argument("--transcript", "-t", required=True, help="转写 JSON 文件路径")
    parser.add_argument("--start", type=float, required=True, help="片段在原视频中的开始时间")
    parser.add_argument("--end", type=float, required=True, help="片段在原视频中的结束时间")
    parser.add_argument("--output", "-o", help="输出路径")
    parser.add_argument("--batch", help="批量模式：传入 clips 目录路径")
    args = parser.parse_args()

    if args.batch:
        batch_add_subtitles(args.batch, args.transcript)
    else:
        add_subtitles_to_clip(
            args.video, args.transcript, args.start, args.end, args.output
        )


if __name__ == "__main__":
    main()
