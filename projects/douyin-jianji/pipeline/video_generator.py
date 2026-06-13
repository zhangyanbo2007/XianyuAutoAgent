"""视频生成器 - 将图片、音频、字幕合成为最终视频"""

import os
import subprocess
from config import VIDEO_WIDTH, VIDEO_HEIGHT, FPS, BGM_DIR, DEFAULT_BGM


def _get_ffmpeg():
    """获取ffmpeg路径"""
    try:
        import imageio_ffmpeg
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        if os.path.exists(ffmpeg_path):
            return ffmpeg_path
    except:
        pass
    for p in ["/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg"]:
        if os.path.exists(p):
            return p
    return "ffmpeg"


def _get_duration(ffmpeg, path):
    """获取媒体时长"""
    r = subprocess.run([ffmpeg, "-i", path, "-f", "null", "-"],
                       capture_output=True, text=True)
    for line in r.stderr.split("\n"):
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = parts.split(":")
            return float(h)*3600 + float(m)*60 + float(s)
    return 0.0


def render_video(slides: list, audio_path: str, output_path: str,
                srt_path: str = None, bgm_path: str = None) -> str:
    """
    渲染最终视频

    Args:
        slides: 幻灯片列表 [{"path": ..., "duration_sec": float}]
        audio_path: 完整音频路径
        output_path: 输出视频路径
        srt_path: 可选的字幕文件路径
        bgm_path: 可选的BGM路径

    Returns:
        输出视频路径
    """
    ffmpeg = _get_ffmpeg()
    work_dir = os.path.dirname(output_path)

    # Step 1: 为每个幻灯片创建视频片段
    segment_files = []
    for i, slide in enumerate(slides):
        seg_path = os.path.join(work_dir, f"_seg_{i:03d}.mp4")
        _create_segment(ffmpeg, slide["path"], seg_path, slide["duration_sec"])
        if os.path.exists(seg_path) and os.path.getsize(seg_path) > 0:
            segment_files.append(seg_path)

    if not segment_files:
        raise RuntimeError("没有生成任何视频片段")

    # Step 2: 连接所有片段
    concat_path = os.path.join(work_dir, "_concat_list.txt")
    with open(concat_path, "w") as f:
        for seg in segment_files:
            # 使用绝对路径
            f.write(f"file '{os.path.abspath(seg)}'\n")

    concat_video = os.path.join(work_dir, "_concat.mp4")
    subprocess.run([
        ffmpeg, "-y", "-f", "concat", "-safe", "0",
        "-i", concat_path,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        concat_video,
    ], capture_output=True)

    # Step 3: 合并音频
    combined = os.path.join(work_dir, "_combined.mp4")
    subprocess.run([
        ffmpeg, "-y",
        "-i", concat_video,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-ar", "44100",
        "-shortest",
        combined,
    ], capture_output=True)

    # Step 4: 混入BGM（提供则用文件，否则合成一段克制的氛围垫乐）
    if not (bgm_path and os.path.exists(bgm_path)):
        dur = _get_duration(ffmpeg, combined) or 30.0
        bgm_path = _synth_bgm(ffmpeg, work_dir, dur + 0.5)

    if bgm_path and os.path.exists(bgm_path):
        with_bgm = os.path.join(work_dir, "_with_bgm.mp4")
        subprocess.run([
            ffmpeg, "-y",
            "-i", combined,
            "-i", bgm_path,
            "-filter_complex",
            "[1:a]volume=0.10,afade=t=in:st=0:d=1.2,afade=t=out:st=0:d=0[bg];"
            "[0:a]volume=1.0[v];[v][bg]amix=inputs=2:duration=first:dropout_transition=0",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-ar", "44100",
            with_bgm,
        ], capture_output=True)
        if os.path.exists(with_bgm) and os.path.getsize(with_bgm) > 0:
            os.remove(combined)
            combined = with_bgm

    # Step 5: 烧录字幕（如果可用）
    if srt_path and os.path.exists(srt_path) and os.path.getsize(srt_path) > 0:
        # 将SRT转换为ASS以获得更好的样式
        ass_path = _srt_to_styled_ass(srt_path, work_dir)
        if ass_path:
            result = subprocess.run([
                ffmpeg, "-y",
                "-i", combined,
                "-vf", f"ass={ass_path}",
                "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                "-c:a", "copy",
                output_path,
            ], capture_output=True)
            if result.returncode == 0:
                _cleanup(work_dir, segment_files + [concat_path, concat_video, combined, ass_path])
                return output_path
            _write_subtitle_error(work_dir, result.stderr)

    # 如果字幕烧录失败或没有字幕，直接复制
    import shutil
    shutil.copy2(combined, output_path)
    _cleanup(work_dir, segment_files + [concat_path, concat_video, combined])
    return output_path


def _create_segment(ffmpeg: str, image_path: str, output_path: str,
                    duration: float):
    """创建视频片段"""
    cmd = [
        ffmpeg, "-y",
        "-loop", "1",
        "-i", image_path,
        "-vf", (
            "scale=iw*1.04:ih*1.04,"
            f"zoompan=z='min(zoom+0.0006,1.035)':d=1:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={FPS},format=yuv420p"
        ),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-t", str(duration),
        output_path
    ]
    subprocess.run(cmd, capture_output=True)


def _synth_bgm(ffmpeg: str, work_dir: str, duration: float) -> str:
    """合成一段克制的暖色氛围垫乐（无版权素材时的兜底）。

    低频暖和弦 + 缓慢颤音 + 低通，听感是“氛围”而非旋律，
    最终在混音阶段以很低音量铺在旁白下方。
    """
    out = os.path.join(work_dir, "_bgm_synth.mp3")
    d = max(3.0, float(duration))
    fade_out_st = max(0.0, d - 2.0)
    flt = (
        "[0][1][2]amix=inputs=3:normalize=0,"
        "tremolo=f=0.18:d=0.5,"
        "lowpass=f=520,highpass=f=70,"
        "aecho=0.8:0.6:80:0.25,"
        f"afade=t=in:st=0:d=1.5,afade=t=out:st={fade_out_st:.2f}:d=2.0,"
        "volume=0.5"
    )
    cmd = [
        ffmpeg, "-y",
        "-f", "lavfi", "-i", f"sine=frequency=110:duration={d:.2f}",
        "-f", "lavfi", "-i", f"sine=frequency=165:duration={d:.2f}",
        "-f", "lavfi", "-i", f"sine=frequency=220:duration={d:.2f}",
        "-filter_complex", flt,
        "-ar", "44100", "-ac", "1",
        "-c:a", "libmp3lame", "-q:a", "5",
        out,
    ]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 0:
        return out
    return None


def _write_subtitle_error(work_dir: str, stderr):
    """Persist ASS burn-in errors for quality reports and debugging."""
    error_path = os.path.join(work_dir, "subtitle_burn_error.log")
    if isinstance(stderr, bytes):
        content = stderr.decode("utf-8", errors="replace")
    else:
        content = str(stderr)
    with open(error_path, "w", encoding="utf-8") as f:
        f.write(content)


def _srt_to_styled_ass(srt_path: str, work_dir: str) -> str:
    """将SRT转换为带样式的ASS字幕"""
    ass_path = os.path.join(work_dir, "_styled.ass")

    try:
        with open(srt_path, "r", encoding="utf-8") as f:
            srt_content = f.read()

        # 解析SRT
        blocks = srt_content.strip().split("\n\n")
        subtitles = []
        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) < 3:
                continue
            time_line = lines[1]
            if "-->" not in time_line:
                continue
            start, end = time_line.split("-->")
            text = " ".join(lines[2:]).strip()
            if text:
                subtitles.append((start.strip(), end.strip(), text))

        # 生成ASS（横屏1920x1080，抖音风格底部硬字幕）
        ass_content = """[Script Info]
Title: Douyin Video Subtitles
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Noto Sans CJK SC,62,&H00FFFFFF,&H000000FF,&H00141414,&HA0000000,1,0,0,0,100,100,0.5,0,1,5,2,2,120,120,86,1
Style: Key,Noto Sans CJK SC,62,&H0000E5FF,&H000000FF,&H00141414,&HA0000000,1,0,0,0,100,100,0.5,0,1,5,2,2,120,120,86,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        for start, end, text in subtitles:
            # 转换时间格式
            start_ass = _srt_to_ass_time(start)
            end_ass = _srt_to_ass_time(end)
            ass_content += f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{text}\n"

        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(ass_content)

        return ass_path

    except Exception as e:
        print(f"  ⚠ SRT转ASS失败: {e}")
        return None


def _srt_to_ass_time(srt_time: str) -> str:
    """将SRT时间格式转换为ASS时间格式"""
    # SRT: HH:MM:SS,mmm
    # ASS: H:MM:SS.cc
    srt_time = srt_time.replace(",", ".")
    parts = srt_time.split(":")
    h = int(parts[0])
    m = int(parts[1])
    s = float(parts[2])

    # ASS格式
    return f"{h}:{m:02d}:{s:05.2f}"


def _cleanup(work_dir: str, files: list):
    """清理临时文件"""
    for f in files:
        if os.path.exists(f):
            try:
                os.remove(f)
            except:
                pass


if __name__ == "__main__":
    # 测试
    import sys
    if len(sys.argv) < 4:
        print("用法: python video_generator.py <图片目录> <音频文件> <输出视频>")
        sys.exit(1)

    image_dir = sys.argv[1]
    audio_path = sys.argv[2]
    output_path = sys.argv[3]

    # 获取图片列表
    images = sorted([os.path.join(image_dir, f) for f in os.listdir(image_dir)
                    if f.endswith(('.png', '.jpg', '.jpeg'))])

    # 获取音频时长
    ffmpeg = _get_ffmpeg()
    audio_duration = _get_duration(ffmpeg, audio_path)

    # 计算每个图片的时长
    duration_per_image = audio_duration / len(images) if images else 5

    # 创建幻灯片
    slides = [{"path": img, "duration_sec": duration_per_image} for img in images]

    # 渲染视频
    render_video(slides, audio_path, output_path)
    print(f"视频已生成: {output_path}")
