#!/usr/bin/env python3
"""
视频切片主流程管道
串联：下载 → 转写 → 分析 → 切割 → 字幕

用法:
  # 单个视频完整流程
  python pipeline.py <douyin_url>

  # 从本地视频开始（跳过下载）
  python pipeline.py --local <video_path>

  # 从转写结果开始（跳过下载和转写）
  python pipeline.py --from-transcript <transcript.json>

  # 批量处理 config 中所有创作者
  python pipeline.py --all
"""
import os
import sys
import json
import argparse
import time
from pathlib import Path
from datetime import datetime

# 路径设置
SKILL_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = Path(__file__).parent
CONFIG_PATH = SKILL_DIR / "config.yaml"

# 确保 ffmpeg 在 PATH 中
FFMPEG_PATH = SKILL_DIR.parent / "video-extract" / "ffmpeg"
if FFMPEG_PATH.exists():
    os.environ["PATH"] = str(FFMPEG_PATH.parent) + os.pathsep + os.environ.get("PATH", "")

# 将 scripts 目录加入 Python 路径
sys.path.insert(0, str(SCRIPTS_DIR))


def load_config():
    import yaml
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def log_step(step: str, message: str):
    """格式化日志输出"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n{'='*60}")
    print(f"⏰ [{timestamp}] Step {step}")
    print(f"{'='*60}")
    print(f"📌 {message}")


def step_download(url: str, creator_name: str = None,
                   cookies_file: str = None) -> dict:
    """Step 1: 下载视频"""
    log_step("1/5", f"下载视频: {url}")

    from download import download_video
    result = download_video(url, creator_name, cookies_file)

    if not result["success"]:
        print(f"❌ 下载失败: {result['error']}")
        return None

    print(f"✅ 下载完成: {result['title']}")
    print(f"📂 文件: {result['files']}")
    return result


def step_transcribe(video_path: str, model_size: str = "medium") -> dict:
    """Step 2: 语音转写"""
    log_step("2/5", f"语音转写: {Path(video_path).name}")

    from transcribe import transcribe_video, save_transcript

    transcript = transcribe_video(video_path, model_size)
    save_transcript(transcript)

    print(f"✅ 转写完成: {transcript['segment_count']} 个片段")
    return transcript


def step_analyze(transcript_path: str) -> list:
    """Step 3: 分析高光时刻"""
    log_step("3/5", "AI 分析高光时刻")

    from analyze_highlights import analyze_transcript_file
    highlights = analyze_transcript_file(transcript_path)

    print(f"✅ 分析完成: 找到 {len(highlights)} 个高光片段")
    return highlights


def step_clip(highlights_path: str) -> list:
    """Step 4: 切割视频"""
    log_step("4/5", "切割视频片段")

    from clip_video import clip_all_highlights
    results = clip_all_highlights(highlights_path)

    success = sum(1 for r in results if r["success"])
    print(f"✅ 切割完成: {success}/{len(results)} 成功")
    return results


def step_add_subtitles(clip_results: list, transcript_path: str) -> list:
    """Step 5: 添加字幕"""
    log_step("5/5", "烧录字幕")

    from add_subtitles import add_subtitles_to_clip

    # 加载高光数据以获取时间偏移
    with open(transcript_path) as f:
        transcript = json.load(f)

    # 找到高光分析文件
    video_title = Path(transcript["video_path"]).stem
    highlight_file = SKILL_DIR / "data" / "highlights" / f"{video_title}.json"

    if not highlight_file.exists():
        print("⚠️  未找到高光分析文件，跳过字幕")
        return clip_results

    with open(highlight_file) as f:
        highlight_data = json.load(f)

    highlights = highlight_data["highlights"]

    results = []
    for i, clip_result in enumerate(clip_results):
        if not clip_result["success"]:
            results.append(clip_result)
            continue

        if i >= len(highlights):
            results.append(clip_result)
            continue

        h = highlights[i]
        # 直接覆盖原文件，不生成 _sub 后缀版本
        add_subtitles_to_clip(
            video_path=clip_result["output_path"],
            transcript_path=transcript_path,
            clip_start=h["start"],
            clip_end=h["end"],
            output_path=clip_result["output_path"],  # 覆盖原文件
        )
        results.append(clip_result)

    return results


def run_pipeline(url: str = None, local_video: str = None,
                  transcript_path: str = None, creator_name: str = None,
                  cookies_file: str = None, skip_subtitles: bool = False) -> dict:
    """
    执行完整切片流程

    Returns:
        dict: {success, clips: [...], summary: str}
    """
    config = load_config()
    whisper_model = config.get("whisper", {}).get("model_size", "medium")

    start_time = time.time()

    # === Step 1: 获取视频 ===
    if transcript_path:
        # 从转写结果开始
        print("⏩ 跳过下载和转写，直接从转写结果开始")
        with open(transcript_path) as f:
            transcript = json.load(f)
        video_path = transcript["video_path"]
        creator_name = creator_name or Path(video_path).parent.name
    elif local_video:
        # 从本地视频开始
        print(f"⏩ 跳过下载，从本地视频开始: {local_video}")
        video_path = local_video
        creator_name = creator_name or "local"
        transcript = step_transcribe(video_path, whisper_model)
        transcript_path = str(SKILL_DIR / "data" / "transcripts" /
                              f"{Path(video_path).stem}.json")
    elif url:
        # 完整流程
        download_result = step_download(url, creator_name, cookies_file)
        if not download_result:
            return {"success": False, "error": "下载失败"}

        video_path = download_result["files"][0] if download_result["files"] else None
        creator_name = download_result.get("uploader", creator_name)

        if not video_path:
            return {"success": False, "error": "未找到下载的文件"}

        transcript = step_transcribe(video_path, whisper_model)
        transcript_path = str(SKILL_DIR / "data" / "transcripts" /
                              f"{Path(video_path).stem}.json")
    else:
        return {"success": False, "error": "请提供 URL、本地视频路径或转写结果路径"}

    # === Step 2: 分析高光 ===
    highlights_path = str(SKILL_DIR / "data" / "highlights" /
                          f"{Path(video_path).stem}.json")

    if not os.path.exists(highlights_path):
        step_analyze(transcript_path)

    # === Step 3: 切割视频 ===
    clip_results = step_clip(highlights_path)

    success_clips = [r for r in clip_results if r["success"]]

    # === Step 4: 字幕 ===
    if not skip_subtitles and success_clips:
        step_add_subtitles(success_clips, transcript_path)

    # === 汇总 ===
    elapsed = time.time() - start_time
    elapsed_min = elapsed / 60

    summary = f"\n{'🎉'*20}\n"
    summary += f"📊 处理完成！\n"
    summary += f"   视频: {Path(video_path).name}\n"
    summary += f"   切片数: {len(success_clips)}/{len(clip_results)}\n"
    summary += f"   耗时: {elapsed_min:.1f} 分钟\n"
    summary += f"\n📂 输出目录: {SKILL_DIR / 'data' / 'clips' / Path(video_path).stem}\n"

    # 列出所有切片
    for i, r in enumerate(success_clips, 1):
        h = r["highlight"]
        summary += f"\n   {i}. {h.get('title', 'untitled')}"
        summary += f" ({h['start']:.0f}s-{h['end']:.0f}s)"
        if h.get("suggested_caption"):
            summary += f"\n      💬 {h['suggested_caption']}"

    summary += f"\n{'🎉'*20}"
    print(summary)

    return {
        "success": True,
        "clips": success_clips,
        "total_clips": len(success_clips),
        "elapsed_minutes": round(elapsed_min, 1),
        "summary": summary,
    }


def main():
    parser = argparse.ArgumentParser(
        description="抖音视频自动切片管道",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 下载并处理一个抖音视频
  python pipeline.py https://www.douyin.com/video/xxx

  # 处理本地视频
  python pipeline.py --local /path/to/video.mp4

  # 从转写结果开始
  python pipeline.py --from-transcript data/transcripts/xxx.json

  # 处理 config 中所有创作者
  python pipeline.py --all
        """
    )
    parser.add_argument("url", nargs="?", help="抖音视频链接")
    parser.add_argument("--local", help="本地视频文件路径（跳过下载）")
    parser.add_argument("--from-transcript", help="从转写结果开始")
    parser.add_argument("--creator", "-c", help="创作者名称")
    parser.add_argument("--cookies", help="Cookies 文件路径")
    parser.add_argument("--no-subs", action="store_true", help="跳过字幕烧录")
    parser.add_argument("--all", action="store_true", help="批量处理 config 中所有创作者")
    args = parser.parse_args()

    if args.all:
        config = load_config()
        for creator in config.get("creators", []):
            url = creator.get("douyin_url", "")
            if not url:
                print(f"⚠️  跳过 {creator['name']}：未配置链接")
                continue
            print(f"\n{'#'*60}")
            print(f"🎬 处理创作者: {creator['name']}")
            print(f"{'#'*60}")
            run_pipeline(
                url=url,
                creator_name=creator["name"],
                cookies_file=args.cookies,
                skip_subtitles=args.no_subs,
            )
    elif args.url:
        run_pipeline(
            url=args.url,
            creator_name=args.creator,
            cookies_file=args.cookies,
            skip_subtitles=args.no_subs,
        )
    elif args.local:
        run_pipeline(
            local_video=args.local,
            creator_name=args.creator,
            skip_subtitles=args.no_subs,
        )
    elif args.from_transcript:
        run_pipeline(
            transcript_path=args.from_transcript,
            creator_name=args.creator,
            skip_subtitles=args.no_subs,
        )
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
