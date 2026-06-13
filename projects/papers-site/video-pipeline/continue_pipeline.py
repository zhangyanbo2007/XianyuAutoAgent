#!/usr/bin/env python3
"""Continue pipeline from existing audio files."""

import os
import sys
import json
import subprocess
import imageio_ffmpeg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "mm80-m3eval-multimodal-memory")
AUDIO_DIR = os.path.join(OUTPUT_DIR, "audio_v2")

def concat_audio():
    """Concatenate audio files."""
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    # Create silence
    silence_path = os.path.join(OUTPUT_DIR, "_silence.mp3")
    subprocess.run([
        ffmpeg, "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
        "-t", "0.5", "-c:a", "libmp3lame", "-q:a", "9", silence_path
    ], capture_output=True)

    # Build concat list
    list_path = os.path.join(OUTPUT_DIR, "_concat.txt")
    with open(list_path, "w") as f:
        for i in range(26):
            mp3 = os.path.join(AUDIO_DIR, f"section_{i:02d}.mp3")
            if os.path.exists(mp3) and os.path.getsize(mp3) > 0:
                f.write(f"file '{mp3}'\n")
                if i < 25:
                    f.write(f"file '{silence_path}'\n")

    # Concatenate
    output = os.path.join(OUTPUT_DIR, "narration_v2.mp3")
    subprocess.run([
        ffmpeg, "-y", "-f", "concat", "-safe", "0",
        "-i", list_path, "-c:a", "libmp3lame", "-q:a", "2", output
    ], capture_output=True)

    # Cleanup
    os.remove(silence_path)
    os.remove(list_path)

    return output

def generate_bgm(duration):
    """Generate simple ambient BGM."""
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    bgm_path = os.path.join(OUTPUT_DIR, "bgm.mp3")

    # Generate a simple ambient tone
    subprocess.run([
        ffmpeg, "-y", "-f", "lavfi", "-i",
        f"sine=frequency=220:duration={duration}",
        "-af", "volume=0.03,lowpass=f=200",
        "-c:a", "libmp3lame", "-q:a", "9", bgm_path
    ], capture_output=True)

    return bgm_path

def merge_audio(narration_path, bgm_path):
    """Merge narration with BGM."""
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    output = os.path.join(OUTPUT_DIR, "narration_mixed.mp3")

    subprocess.run([
        ffmpeg, "-y",
        "-i", narration_path,
        "-i", bgm_path,
        "-filter_complex", "[1:a]volume=0.15[bg];[0:a][bg]amix=inputs=2:duration=first",
        "-c:a", "libmp3lame", "-q:a", "2", output
    ], capture_output=True)

    return output

if __name__ == "__main__":
    print("Concatenating audio...")
    narration = concat_audio()
    print(f"  Narration: {narration}")

    # Get duration
    result = subprocess.run([
        imageio_ffmpeg.get_ffmpeg_exe(), "-i", narration, "-f", "null", "-"
    ], capture_output=True, text=True)
    duration = 0
    for line in result.stderr.split("\n"):
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = parts.split(":")
            duration = float(h)*3600 + float(m)*60 + float(s)
            break
    print(f"  Duration: {duration:.1f}s")

    print("Generating BGM...")
    bgm = generate_bgm(duration)
    print(f"  BGM: {bgm}")

    print("Merging audio...")
    mixed = merge_audio(narration, bgm)
    print(f"  Mixed: {mixed}")

    print("Done!")
