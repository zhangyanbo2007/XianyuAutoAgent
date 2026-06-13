#!/usr/bin/env python3
"""
DAST Frame Comparison Tool - compare generated slides with reference video frames.
Extracts frames from both videos and generates a side-by-side comparison contact sheet.

Usage:
    python dast_compare.py
    python dast_compare.py --reference ../dast_analysis/video.mp4 --generated output/dast-video/final.mp4
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PIPELINE_DIR = Path(__file__).parent
REF_VIDEO = PIPELINE_DIR.parent / "dast_analysis" / "video.mp4"
GEN_VIDEO = PIPELINE_DIR / "output" / "dast-video" / "final.mp4"
COMP_DIR = PIPELINE_DIR / "output" / "comparison"


def get_ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    for p in ["/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg"]:
        if os.path.exists(p):
            return p
    return "ffmpeg"


def extract_frames(video_path: str, output_dir: str, interval: int = 30):
    """Extract frames at regular intervals."""
    os.makedirs(output_dir, exist_ok=True)
    ffmpeg = get_ffmpeg()

    # Get duration
    result = subprocess.run(
        [ffmpeg, "-i", video_path, "-f", "null", "-"],
        capture_output=True, text=True
    )
    duration = 0
    for line in result.stderr.split("\n"):
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = parts.split(":")
            duration = float(h) * 3600 + float(m) * 60 + float(s)
            break

    frames = []
    t = 0
    idx = 0
    while t < duration:
        output = os.path.join(output_dir, f"frame_{idx:03d}.jpg")
        subprocess.run([
            ffmpeg, "-y", "-ss", str(t),
            "-i", video_path,
            "-frames:v", "1", "-q:v", "2",
            output
        ], capture_output=True)
        if os.path.exists(output):
            frames.append({"index": idx, "timestamp": t, "path": output})
        t += interval
        idx += 1

    return frames


def create_comparison_sheet(ref_frames: list, gen_frames: list, output_path: str):
    """Create a side-by-side comparison contact sheet."""
    if not ref_frames or not gen_frames:
        print("Not enough frames for comparison")
        return

    # Use minimum count
    count = min(len(ref_frames), len(gen_frames), 20)  # max 20 rows

    # Load first frame to get dimensions
    sample = Image.open(ref_frames[0]["path"])
    fw, fh = sample.size
    sample.close()

    # Scale down for contact sheet
    thumb_w = 600
    thumb_h = int(fh * thumb_w / fw)

    cols = 3  # ref | label | gen
    row_h = thumb_h + 40  # extra for labels
    total_h = count * row_h + 60  # header
    total_w = thumb_w * 2 + 200  # ref + gap + gen

    sheet = Image.new('RGB', (total_w, total_h), color=(10, 10, 15))
    draw = ImageDraw.Draw(sheet)

    # Try to load font
    try:
        font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 20)
        font_small = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 14)
    except Exception:
        font = ImageFont.load_default()
        font_small = font

    # Header
    draw.text((thumb_w // 2 - 50, 10), "Reference", fill=(0, 212, 255), font=font)
    draw.text((thumb_w + 200 + thumb_w // 2 - 50, 10), "Generated", fill=(0, 255, 136), font=font)

    for i in range(count):
        y = 50 + i * row_h

        # Reference frame
        ref_img = Image.open(ref_frames[i]["path"])
        ref_img = ref_img.resize((thumb_w, thumb_h), Image.LANCZOS)
        sheet.paste(ref_img, (0, y))

        # Label
        ts = ref_frames[i]["timestamp"]
        draw.text((thumb_w + 20, y + thumb_h // 2 - 10),
                  f"{ts:.0f}s", fill=(200, 200, 200), font=font_small)

        # Generated frame
        gen_img = Image.open(gen_frames[i]["path"])
        gen_img = gen_img.resize((thumb_w, thumb_h), Image.LANCZOS)
        sheet.paste(gen_img, (thumb_w + 200, y))

    sheet.save(output_path, quality=90)
    print(f"Comparison sheet saved: {output_path}")


def compute_similarity(img1_path: str, img2_path: str) -> float:
    """Compute structural similarity between two images (0-100%)."""
    try:
        from skimage.metrics import structural_similarity as ssim
        import numpy as np

        img1 = Image.open(img1_path).convert('L').resize((640, 360))
        img2 = Image.open(img2_path).convert('L').resize((640, 360))

        arr1 = np.array(img1)
        arr2 = np.array(img2)

        score = ssim(arr1, arr2)
        return score * 100
    except ImportError:
        # Fallback: simple pixel difference
        img1 = Image.open(img1_path).convert('RGB').resize((320, 180))
        img2 = Image.open(img2_path).convert('RGB').resize((320, 180))

        import numpy as np
        arr1 = np.array(img1, dtype=float)
        arr2 = np.array(img2, dtype=float)
        diff = np.abs(arr1 - arr2).mean()
        return max(0, 100 - diff)


def main():
    parser = argparse.ArgumentParser(description="DAST Frame Comparison")
    parser.add_argument("--reference", default=str(REF_VIDEO))
    parser.add_argument("--generated", default=str(GEN_VIDEO))
    parser.add_argument("--interval", type=int, default=30, help="Frame extraction interval (seconds)")
    args = parser.parse_args()

    COMP_DIR.mkdir(parents=True, exist_ok=True)

    # Extract reference frames
    ref_dir = COMP_DIR / "ref_frames"
    print(f"Extracting reference frames from: {args.reference}")
    if not os.path.exists(args.reference):
        print(f"  Reference video not found: {args.reference}")
        return

    ref_frames = extract_frames(args.reference, str(ref_dir), interval=args.interval)
    print(f"  Extracted {len(ref_frames)} reference frames")

    # Extract generated frames
    gen_dir = COMP_DIR / "gen_frames"
    print(f"Extracting generated frames from: {args.generated}")
    if not os.path.exists(args.generated):
        print(f"  Generated video not found: {args.generated}")
        print("  Run dast_pipeline.py first to generate the video")
        return

    gen_frames = extract_frames(args.generated, str(gen_dir), interval=args.interval)
    print(f"  Extracted {len(gen_frames)} generated frames")

    # Create comparison sheet
    print("\nCreating comparison sheet...")
    sheet_path = COMP_DIR / "comparison_sheet.jpg"
    create_comparison_sheet(ref_frames, gen_frames, str(sheet_path))

    # Compute per-frame similarity
    print("\nComputing similarity scores...")
    count = min(len(ref_frames), len(gen_frames))
    scores = []
    for i in range(count):
        score = compute_similarity(ref_frames[i]["path"], gen_frames[i]["path"])
        scores.append(score)
        ts = ref_frames[i]["timestamp"]
        print(f"  Frame {i} ({ts:.0f}s): {score:.1f}%")

    avg_score = sum(scores) / len(scores) if scores else 0
    print(f"\n{'='*50}")
    print(f"Average similarity: {avg_score:.1f}%")
    print(f"{'='*50}")

    if avg_score >= 80:
        print("✅ Good match with reference video!")
    elif avg_score >= 60:
        print("⚠️  Moderate match - consider adjusting templates")
    else:
        print("❌ Low match - needs significant refinement")


if __name__ == "__main__":
    main()
