"""Generate or download background music for videos."""

import os
import subprocess


def _get_ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except:
        return "ffmpeg"


def generate_ambient_bgm(output_path: str, duration: float, volume: float = 0.08) -> str:
    """Generate a soft ambient background music using ffmpeg synthesis.

    Creates a gentle, non-distracting ambient pad using sine waves.
    """
    ffmpeg = _get_ffmpeg()

    # Create a soft ambient pad with multiple sine waves
    # Using C major chord frequencies for pleasant sound
    cmd = [
        ffmpeg, "-y",
        "-f", "lavfi", "-i",
        (
            f"sine=frequency=261.63:duration={duration},"  # C4
            f"volume={volume}"
        ),
        "-f", "lavfi", "-i",
        (
            f"sine=frequency=329.63:duration={duration},"  # E4
            f"volume={volume * 0.7}"
        ),
        "-f", "lavfi", "-i",
        (
            f"sine=frequency=392.00:duration={duration},"  # G4
            f"volume={volume * 0.5}"
        ),
        "-f", "lavfi", "-i",
        (
            f"sine=frequency=523.25:duration={duration},"  # C5
            f"volume={volume * 0.3}"
        ),
        "-filter_complex",
        (
            "[0:a][1:a][2:a][3:a]amix=inputs=4:duration=longest,"
            f"afade=t=in:st=0:d=3,afade=t=out:st={duration-3}:d=3,"
            "lowpass=f=2000,highpass=f=100,"
            "aecho=0.8:0.88:60:0.4"
        ),
        "-c:a", "libmp3lame", "-q:a", "4",
        output_path,
    ]

    subprocess.run(cmd, capture_output=True, timeout=60)
    return output_path


def merge_audio_with_bgm(narration_path: str, bgm_path: str, output_path: str,
                         bgm_volume: float = 0.1) -> str:
    """Merge narration with background music.

    BGM is ducked under narration.
    """
    ffmpeg = _get_ffmpeg()

    # Get narration duration to compute fade-out start
    duration = _get_duration(ffmpeg, narration_path)
    fade_out_start = max(0, duration - 3)

    cmd = [
        ffmpeg, "-y",
        "-i", narration_path,
        "-i", bgm_path,
        "-filter_complex",
        (
            f"[1:a]volume={bgm_volume}[bgm];"
            "[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2,"
            f"afade=t=in:st=0:d=1,afade=t=out:st={fade_out_start}:d=3"
        ),
        "-c:a", "libmp3lame", "-q:a", "2",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        # Fallback: just use narration
        print(f"  ⚠ BGM merge failed: {result.stderr[-200:]}")
        import shutil
        shutil.copy2(narration_path, output_path)

    return output_path


def _get_duration(ffmpeg, path):
    r = subprocess.run([ffmpeg, "-i", path, "-f", "null", "-"],
                       capture_output=True, text=True)
    for line in r.stderr.split("\n"):
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = parts.split(":")
            return float(h)*3600 + float(m)*60 + float(s)
    return 0.0


if __name__ == "__main__":
    # Test
    os.makedirs("/tmp/bgm_test", exist_ok=True)
    generate_ambient_bgm("/tmp/bgm_test/ambient.mp3", 60)
    print("Generated test BGM")
