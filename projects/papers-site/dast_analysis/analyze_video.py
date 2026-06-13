#!/usr/bin/env python3
"""Analyze original DAST video: extract frames, metadata, and generate comparison."""

import os
import subprocess
import json
import sys

def get_ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except:
        pass
    for p in ["/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg"]:
        if os.path.exists(p):
            return p
    return "ffmpeg"


def get_video_info(video_path):
    """Get video metadata."""
    ffmpeg = get_ffmpeg()
    r = subprocess.run([ffmpeg, "-i", video_path, "-f", "null", "-"],
                       capture_output=True, text=True)
    info = {}
    for line in r.stderr.split("\n"):
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = parts.split(":")
            info["duration"] = float(h)*3600 + float(m)*60 + float(s)
        if "Stream #" in line and "Video:" in line:
            info["video"] = line.strip()
        if "Stream #" in line and "Audio:" in line:
            info["audio"] = line.strip()
    return info


def extract_frames(video_path, output_dir, interval=30, max_frames=None):
    """Extract frames at regular intervals."""
    os.makedirs(output_dir, exist_ok=True)
    ffmpeg = get_ffmpeg()

    info = get_video_info(video_path)
    duration = info.get("duration", 0)

    timestamps = []
    t = 0
    while t < duration:
        timestamps.append(t)
        t += interval

    if max_frames:
        timestamps = timestamps[:max_frames]

    extracted = []
    for i, ts in enumerate(timestamps):
        output = os.path.join(output_dir, f"frame_{i+1:04d}.jpg")
        subprocess.run([
            ffmpeg, "-y", "-ss", str(ts),
            "-i", video_path,
            "-frames:v", "1",
            "-q:v", "2",
            output
        ], capture_output=True)
        if os.path.exists(output):
            extracted.append({"index": i+1, "timestamp": ts, "path": output})

    return extracted


def main():
    video_path = "video.mp4"
    if len(sys.argv) > 1:
        video_path = sys.argv[1]

    if not os.path.exists(video_path):
        print(f"Error: {video_path} not found")
        return

    print(f"Analyzing: {video_path}")
    info = get_video_info(video_path)
    print(f"Duration: {info.get('duration', 0):.1f}s")
    print(f"Video: {info.get('video', 'N/A')}")
    print(f"Audio: {info.get('audio', 'N/A')}")

    # Extract overview frames (every 30s)
    overview_dir = "frames_overview"
    print(f"\nExtracting overview frames (every 30s)...")
    overview = extract_frames(video_path, overview_dir, interval=30)
    print(f"  Extracted {len(overview)} frames")

    # Extract detail frames (every 5s, first 2 minutes)
    detail_dir = "frames_detail"
    print(f"Extracting detail frames (every 5s, first 120s)...")
    detail = extract_frames(video_path, detail_dir, interval=5, max_frames=24)
    print(f"  Extracted {len(detail)} frames")

    # Save analysis
    analysis = {
        "video": video_path,
        "info": info,
        "overview_frames": len(overview),
        "detail_frames": len(detail),
    }
    with open("analysis.json", "w") as f:
        json.dump(analysis, f, indent=2)

    print(f"\nDone! Analysis saved to analysis.json")


if __name__ == "__main__":
    main()
