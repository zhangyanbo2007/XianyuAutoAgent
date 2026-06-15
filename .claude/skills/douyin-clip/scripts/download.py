#!/usr/bin/env python3
"""
抖音视频下载模块
使用 yt-dlp 下载抖音视频，支持：
- 单个视频链接下载
- 创作者主页批量下载
- Cookies 认证（绕过登录限制）
"""
import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# 路径设置
SKILL_DIR = Path(__file__).parent.parent
CONFIG_PATH = SKILL_DIR / "config.yaml"


def load_config():
    """加载配置"""
    import yaml
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def get_download_dir(creator_name: str = None) -> Path:
    """获取下载目录"""
    config = load_config()
    base = SKILL_DIR / config["paths"]["downloads"]
    if creator_name:
        base = base / creator_name
    base.mkdir(parents=True, exist_ok=True)
    return base


def ensure_ffmpeg_in_path():
    """确保 ffmpeg 在 PATH 中（使用 video-extract skill 的）"""
    ffmpeg_path = Path(__file__).parent.parent.parent / "video-extract" / "ffmpeg"
    if ffmpeg_path.exists():
        ffmpeg_dir = str(ffmpeg_path.parent)
        if ffmpeg_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")


def build_yt_dlp_cmd(url: str, output_dir: Path, config: dict,
                      cookies_file: str = None, max_videos: int = None) -> list:
    """构建 yt-dlp 命令"""
    ensure_ffmpeg_in_path()
    cmd = [
        "yt-dlp",
        # 输出模板：按创作者/标题命名
        "-o", str(output_dir / "%(uploader)s/%(title)s.%(ext)s"),
        # 优先下载最佳质量
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        # 合并视频和音频
        "--merge-output-format", "mp4",
        # 写入元数据
        "--write-info-json",
        # 不下载缩略图（节省空间）
        "--no-write-thumbnail",
        # 保持原始文件名中的特殊字符
        "--restrict-filenames",
    ]

    # 代理设置
    if config.get("proxy", {}).get("enabled"):
        cmd.extend([
            "--proxy", config["proxy"]["https"],
        ])

    # Cookies
    if cookies_file:
        cmd.extend(["--cookies", cookies_file])

    # 限制下载数量（批量下载时）
    if max_videos:
        cmd.extend(["--playlist-end", str(max_videos)])

    # 抖音特定设置
    cmd.extend([
        # 抖音需要的额外 headers
        "--extractor-args", "douyin:api_hostname=www.douyin.com",
    ])

    cmd.append(url)
    return cmd


def download_video(url: str, creator_name: str = None,
                    cookies_file: str = None, max_videos: int = 1) -> dict:
    """
    下载抖音视频

    Args:
        url: 抖音视频链接或主页链接
        creator_name: 创作者名称（用于分类目录）
        cookies_file: cookies 文件路径
        max_videos: 最多下载几个视频

    Returns:
        dict: {success, video_path, title, duration, ...}
    """
    config = load_config()
    output_dir = get_download_dir(creator_name)

    cmd = build_yt_dlp_cmd(url, output_dir, config, cookies_file, max_videos)

    print(f"📥 开始下载: {url}")
    print(f"📂 输出目录: {output_dir}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 分钟超时
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr,
                "url": url,
            }

        # 解析下载结果，找到最终的合并文件
        merged_file = None
        all_files = []
        for line in result.stdout.split("\n"):
            if "[download] Destination:" in line:
                filepath = line.split("Destination:")[-1].strip()
                all_files.append(filepath)
            elif "[Merger] Merging formats into" in line:
                filepath = line.split('into "')[-1].rstrip('"')
                merged_file = filepath

        # 优先返回合并后的文件，否则返回第一个文件
        downloaded_files = [merged_file] if merged_file else all_files

        # 读取元数据
        metadata = {}
        info_files = list(output_dir.rglob("*.info.json"))
        if info_files:
            latest_info = max(info_files, key=os.path.getmtime)
            with open(latest_info) as f:
                metadata = json.load(f)

        return {
            "success": True,
            "files": downloaded_files,
            "title": metadata.get("title", "unknown"),
            "uploader": metadata.get("uploader", creator_name or "unknown"),
            "duration": metadata.get("duration"),
            "url": url,
            "output_dir": str(output_dir),
        }

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "下载超时（10分钟）", "url": url}
    except Exception as e:
        return {"success": False, "error": str(e), "url": url}


def download_from_config(max_per_creator: int = 1):
    """从 config.yaml 读取创作者列表并批量下载"""
    config = load_config()
    results = []

    for creator in config.get("creators", []):
        url = creator.get("douyin_url", "")
        if not url:
            print(f"⚠️  跳过 {creator['name']}：未配置链接")
            continue

        print(f"\n{'='*50}")
        print(f"🎬 处理创作者: {creator['name']}")
        print(f"{'='*50}")

        result = download_video(
            url=url,
            creator_name=creator["name"],
            max_videos=max_per_creator,
        )
        results.append(result)

        if result["success"]:
            print(f"✅ 下载成功: {result['title']}")
        else:
            print(f"❌ 下载失败: {result['error']}")

    return results


def main():
    parser = argparse.ArgumentParser(description="抖音视频下载")
    parser.add_argument("url", nargs="?", help="抖音视频/主页链接")
    parser.add_argument("--creator", "-c", help="创作者名称（用于分类）")
    parser.add_argument("--cookies", help="Cookies 文件路径")
    parser.add_argument("--max", "-n", type=int, default=1, help="最多下载几个视频")
    parser.add_argument("--all", action="store_true", help="从 config.yaml 批量下载")
    args = parser.parse_args()

    if args.all:
        results = download_from_config(args.max)
        success = sum(1 for r in results if r["success"])
        print(f"\n📊 下载完成: {success}/{len(results)} 成功")
    elif args.url:
        result = download_video(
            url=args.url,
            creator_name=args.creator,
            cookies_file=args.cookies,
            max_videos=args.max,
        )
        if result["success"]:
            print(f"✅ 下载成功: {result['title']}")
            print(f"📂 文件: {result['files']}")
        else:
            print(f"❌ 下载失败: {result['error']}")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
