#!/usr/bin/env python3
"""
视频切割模块
根据高光分析结果，使用 ffmpeg 精确切割视频片段
支持竖屏适配（横转竖）和字幕烧录
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
# ffprobe: 优先用同目录下的，否则用 ffmpeg -i 代替
FFPROBE_BIN = str(FFMPEG_PATH.parent / "ffprobe") if (FFMPEG_PATH.parent / "ffprobe").exists() \
    else FFMPEG_BIN  # 用 ffmpeg 代替 ffprobe


def load_config():
    import yaml
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def get_video_info(video_path: str) -> dict:
    """获取视频信息（分辨率、时长等）— 使用 moviepy"""
    from moviepy import VideoFileClip

    try:
        clip = VideoFileClip(video_path)
        info = {
            "width": clip.size[0],
            "height": clip.size[1],
            "duration": clip.duration,
            "fps": clip.fps,
        }
        clip.close()
        return info
    except Exception:
        return {}


def clip_segment(video_path: str, start: float, end: float,
                  output_path: str, target_width: int = 1080,
                  target_height: int = 1920) -> bool:
    """
    切割单个视频片段

    Args:
        video_path: 源视频路径
        start: 开始时间（秒）
        end: 结束时间（秒）
        output_path: 输出路径
        target_width: 目标宽度
        target_height: 目标高度

    Returns:
        bool: 是否成功
    """
    video_info = get_video_info(video_path)
    src_w = video_info.get("width", 1920)
    src_h = video_info.get("height", 1080)

    duration = end - start

    # 构建 ffmpeg 滤镜
    vf_filters = []

    # 竖屏适配：横屏视频转竖屏
    if src_w > src_h and target_height > target_width:
        # 横屏转竖屏：裁剪中间部分 + 缩放
        # 目标比例 9:16，源视频可能 16:9
        target_ratio = target_width / target_height  # 0.5625
        src_ratio = src_w / src_h

        if src_ratio > target_ratio:
            # 源视频更宽，需要裁剪左右
            crop_w = int(src_h * target_ratio)
            crop_h = src_h
            crop_x = (src_w - crop_w) // 2
            crop_y = 0
            vf_filters.append(f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y}")
        else:
            # 源视频更高，需要裁剪上下
            crop_w = src_w
            crop_h = int(src_w / target_ratio)
            crop_x = 0
            crop_y = (src_h - crop_h) // 2
            vf_filters.append(f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y}")

        vf_filters.append(f"scale={target_width}:{target_height}")

    # 缩放（如果不是竖屏适配场景）
    if not vf_filters:
        vf_filters.append(f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease")
        vf_filters.append(f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2")

    # 亮度增强（对标专业切片号的明亮画面）
    vf_filters.append("eq=brightness=0.08")

    vf = ",".join(vf_filters)

    cmd = [
        FFMPEG_BIN,
        "-y",  # 覆盖输出
        "-ss", str(start),
        "-t", str(duration),
        "-i", video_path,
        "-vf", vf,
        "-af", "volume=1.5",  # 音频增益，对标专业切片号
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "256k",
        "-ar", "44100",  # 统一音频采样率
        "-ac", "2",      # 立体声
        "-movflags", "+faststart",  # 快速启动，适合网络播放
        "-avoid_negative_ts", "make_zero",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return result.returncode == 0


def generate_output_path(highlight: dict, video_title: str,
                          output_dir: Path, index: int) -> str:
    """生成输出文件路径"""
    # 文件名：序号_切片标题
    safe_title = highlight.get("title", "clip")
    # 移除文件名不安全字符
    safe_title = "".join(c for c in safe_title if c.isalnum() or c in "._- ")
    safe_title = safe_title[:30]  # 截断长标题
    filename = f"{index:02d}_{safe_title}.mp4"
    return str(output_dir / filename)


def clip_all_highlights(highlights_path: str, output_dir: str = None) -> list:
    """
    根据高光分析结果切割所有片段

    Args:
        highlights_path: 高光分析 JSON 文件路径
        output_dir: 输出目录

    Returns:
        list: 切割结果列表
    """
    config = load_config()

    with open(highlights_path) as f:
        data = json.load(f)

    video_path = data["video_path"]
    video_title = data["video_title"]
    highlights = data["highlights"]

    if not highlights:
        print("⚠️  没有高光片段需要切割")
        return []

    # 输出目录
    if output_dir is None:
        clip_config = config.get("clip", {})
        output_dir = SKILL_DIR / config["paths"]["clips"] / video_title
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 读取目标分辨率
    clip_config = config.get("clip", {})
    target_w = clip_config.get("target_width", 1080)
    target_h = clip_config.get("target_height", 1920)

    print(f"✂️  开始切割视频: {video_title}")
    print(f"   高光片段数: {len(highlights)}")
    print(f"   目标分辨率: {target_w}x{target_h}")
    print(f"   输出目录: {output_dir}")

    results = []
    for i, h in enumerate(highlights, 1):
        start = h["start"]
        end = h["end"]
        title = h.get("title", f"clip_{i}")
        duration = end - start

        output_path = generate_output_path(h, video_title, output_dir, i)

        print(f"\n   [{i}/{len(highlights)}] {title}")
        print(f"       时间: {start:.1f}s - {end:.1f}s ({duration:.0f}秒)")

        success = clip_segment(
            video_path=video_path,
            start=start,
            end=end,
            output_path=output_path,
            target_width=target_w,
            target_height=target_h,
        )

        if success:
            file_size = os.path.getsize(output_path) / (1024 * 1024)
            print(f"       ✅ 成功: {output_path} ({file_size:.1f}MB)")
            results.append({
                "success": True,
                "output_path": output_path,
                "highlight": h,
                "file_size_mb": round(file_size, 1),
            })
        else:
            print(f"       ❌ 失败")
            results.append({
                "success": False,
                "highlight": h,
                "error": "ffmpeg 切割失败",
            })

    success_count = sum(1 for r in results if r["success"])
    print(f"\n📊 切割完成: {success_count}/{len(highlights)} 成功")
    return results


def main():
    parser = argparse.ArgumentParser(description="视频高光切割")
    parser.add_argument("highlights", help="高光分析 JSON 文件路径")
    parser.add_argument("--output-dir", "-o", help="输出目录")
    args = parser.parse_args()

    results = clip_all_highlights(args.highlights, args.output_dir)

    failed = [r for r in results if not r["success"]]
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
