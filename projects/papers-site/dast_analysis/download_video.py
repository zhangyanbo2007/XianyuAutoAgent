#!/usr/bin/env python3
"""Download original DAST video from YouTube/Bilibili."""

import subprocess
import sys


def download_youtube(url, output="video.mp4"):
    """Download from YouTube using yt-dlp."""
    cmd = [
        "yt-dlp",
        "-f", "best[height<=720]",
        "-o", output,
        url,
    ]
    print(f"Downloading from YouTube...")
    print(f"  URL: {url}")
    print(f"  Output: {output}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  Success!")
    else:
        print(f"  Error: {result.stderr[:200]}")
    return result.returncode == 0


def download_bilibili(url, output="video.mp4"):
    """Download from Bilibili using yt-dlp."""
    cmd = [
        "yt-dlp",
        "-f", "best[height<=720]",
        "-o", output,
        url,
    ]
    print(f"Downloading from Bilibili...")
    print(f"  URL: {url}")
    print(f"  Output: {output}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  Success!")
    else:
        print(f"  Error: {result.stderr[:200]}")
    return result.returncode == 0


def main():
    # Default URLs for the M3Eval paper video
    youtube_url = "https://www.youtube.com/watch?v=FYvXVp63rYg"
    bilibili_url = "https://www.bilibili.com/video/BV1S2Ec6vEhX"

    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = youtube_url

    output = "video.mp4"
    if len(sys.argv) > 2:
        output = sys.argv[2]

    if "youtube.com" in url or "youtu.be" in url:
        download_youtube(url, output)
    elif "bilibili.com" in url or "b23.tv" in url:
        download_bilibili(url, output)
    else:
        print(f"Unknown platform: {url}")
        print("Supported: YouTube, Bilibili")
        sys.exit(1)


if __name__ == "__main__":
    main()
