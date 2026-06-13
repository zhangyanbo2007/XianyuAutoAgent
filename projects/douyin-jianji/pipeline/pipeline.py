#!/usr/bin/env python3
"""抖音视频生成Pipeline - 从Excel脚本生成参考视频风格成片"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path


def load_dotenv():
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()


load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_image_generator import generate_bg_image
from config import OUTPUT_DIR, DEFAULT_BGM
from quality_report import build_quality_report
from script_converter import parse_excel_scripts, save_script_to_json
from slide_renderer import render_slide
from storyboard_planner import plan_storyboard
from tts_generator import generate_sections_audio
from video_generator import render_video, _get_ffmpeg

COVER_SEC = 2.0          # 封面停留（无旁白，仅垫乐）
PAUSE_SEC = 0.4          # 段落间停顿


def collect_input_scripts(input_path) -> list[dict]:
    """Collect parsed scripts from a demand directory or Excel file."""
    path = Path(input_path)
    if path.is_dir():
        excel_files = sorted(
            path.glob("*.xlsx"),
            key=lambda item: (item.name[0].isdigit(), item.name),
        )
    else:
        excel_files = [path]

    scripts = []
    for excel_path in excel_files:
        if excel_path.exists() and excel_path.suffix.lower() == ".xlsx":
            scripts.extend(parse_excel_scripts(excel_path))
    return scripts


def make_output_slug(script: dict) -> str:
    """Create a stable filesystem-safe output name for one script block."""
    title = script.get("program_title") or script.get("headline") or "douyin-video"
    title = re.sub(r"[《》<>:\"/\\|?*]", "", title)
    title = re.sub(r"\s+", "", title)
    title = title.replace("-", "_")
    block_index = script.get("block_index", 0)
    source_stem = Path(script.get("source_file", "")).stem
    if source_stem and source_stem not in title:
        title = f"{source_stem}_{title}"
    return f"{title}_b{block_index:02d}"[:80]


def run_pipeline(excel_path: str, output_name: str = None,
                 voice: str = None, no_tts: bool = False):
    """Run a single Excel file and return the first generated video path."""
    scripts = collect_input_scripts(excel_path)
    if not scripts:
        raise ValueError(f"未找到可生成的视频脚本: {excel_path}")
    output_paths = [
        run_script_pipeline(script, output_name if i == 0 else None, voice, no_tts)
        for i, script in enumerate(scripts[:1])
    ]
    return output_paths[0]


def run_script_pipeline(script: dict, output_name: str = None,
                        voice: str = None, no_tts: bool = False) -> str:
    """Generate one video from one parsed script block."""
    start = time.time()
    output_name = output_name or make_output_slug(script)
    work_dir = Path(OUTPUT_DIR) / output_name
    work_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'=' * 60}")
    print(f"  抖音视频生成: {output_name}")
    print(f"{'=' * 60}")

    script_path = work_dir / "script.json"
    save_script_to_json(script, str(script_path))

    storyboard = plan_storyboard(script)
    storyboard_path = work_dir / "storyboard.json"
    storyboard_path.write_text(json.dumps(storyboard, ensure_ascii=False, indent=2), encoding="utf-8")

    audio_dir = work_dir / "audio"
    audio_dir.mkdir(exist_ok=True)
    narration_path = work_dir / "narration.mp3"
    srt_path = work_dir / "narration.srt"
    ffmpeg = _get_ffmpeg()

    hero_bg = dark_bg = None
    if no_tts:
        tts_status = "silent_smoke"
        total_duration = _storyboard_duration(storyboard)
        _write_storyboard_srt(storyboard, srt_path)
        _create_silent_audio(narration_path, total_duration)
    else:
        # AI 背景：一张 hero（封面）+ 一张统一深蓝信息图底（对标参考视频1）
        bg_dir = work_dir / "_ai_images"
        hero_bg = generate_bg_image(storyboard.get("hero_prompt", ""), str(bg_dir), index=0)
        dark_bg = generate_bg_image(storyboard.get("dark_prompt", ""), str(bg_dir), index=1)
        print(f"  AI背景: hero={'OK' if hero_bg else 'fallback'} dark={'OK' if dark_bg else 'fallback'}")

        section_results = generate_sections_audio(script.get("sections", []), str(audio_dir), voice=voice)
        sec_audio = {r.get("index", n): r for n, r in enumerate(section_results)}
        sec_start, total_dur = _assemble_audio(ffmpeg, work_dir, sec_audio,
                                               script.get("sections", []), narration_path)
        _assign_shot_durations(storyboard.get("shots", []), sec_start, total_dur)
        _merge_subtitles_offset(sec_audio, sec_start, srt_path)
        tts_status = _summarize_tts_status(section_results)
        if not narration_path.exists() or narration_path.stat().st_size == 0:
            _write_storyboard_srt(storyboard, srt_path)
            _create_silent_audio(narration_path, _storyboard_duration(storyboard))
            tts_status = "missing"

    slides = _render_storyboard_slides(storyboard, work_dir, hero_bg, dark_bg)
    output_path = work_dir / f"{output_name}.mp4"
    bgm_path = DEFAULT_BGM if os.path.exists(DEFAULT_BGM) else None
    render_video(slides, str(narration_path), str(output_path), str(srt_path), bgm_path)
    _extract_key_frames(output_path, work_dir / "frames")

    build_quality_report(
        output_dir=work_dir,
        script=script,
        storyboard=storyboard,
        video_path=output_path,
        audio_path=narration_path,
        subtitle_path=srt_path,
        tts_status=tts_status,
    )

    elapsed = time.time() - start
    size = output_path.stat().st_size / (1024 * 1024) if output_path.exists() else 0
    print(f"  完成: {output_path} ({size:.1f} MB, {elapsed:.1f}s)")
    return str(output_path)


def run_demand_directory(demand_dir: str, voice: str = None,
                         no_tts: bool = False) -> list[dict]:
    """Generate videos for every script block in a demand directory."""
    scripts = collect_input_scripts(demand_dir)
    results = []
    for script in scripts:
        try:
            output_path = run_script_pipeline(script, None, voice, no_tts)
            results.append({"script": script, "output": output_path, "status": "success"})
        except Exception as exc:
            print(f"  处理失败: {script.get('program_title', '')} - {exc}")
            results.append({"script": script, "output": None, "status": "failed", "error": str(exc)})
    return results


def run_batch(input_paths: list, voice: str = None,
              no_tts: bool = False) -> list[dict]:
    """Batch process Excel files or demand directories."""
    results = []
    for input_path in input_paths:
        path = Path(input_path)
        if path.is_dir():
            results.extend(run_demand_directory(str(path), voice=voice, no_tts=no_tts))
        else:
            for script in collect_input_scripts(path):
                try:
                    output_path = run_script_pipeline(script, None, voice, no_tts)
                    results.append({"script": script, "output": output_path, "status": "success"})
                except Exception as exc:
                    results.append({"script": script, "output": None, "status": "failed", "error": str(exc)})
    return results


def _render_storyboard_slides(storyboard: dict, work_dir: Path,
                              hero_bg: str = None, dark_bg: str = None) -> list[dict]:
    slides_dir = work_dir / "slides"
    slides_dir.mkdir(exist_ok=True)
    slides = []
    title_text = storyboard.get("title", "")

    for i, shot in enumerate(storyboard.get("shots", [])):
        slide_path = slides_dir / f"slide_{i:02d}.png"
        bg = hero_bg if shot.get("bg_role") == "hero" else dark_bg
        render_slide(shot, bg, str(slide_path), title_text)
        slides.append({"path": str(slide_path), "duration_sec": shot.get("duration_sec", 3.0)})
    return slides


def _assemble_audio(ffmpeg, work_dir: Path, sec_audio: dict,
                    sections: list, out_path: Path) -> dict:
    """拼接 封面留白 + 各段配音 + 段间停顿，返回 {section_index: start_sec}。"""
    import subprocess
    cover_sil = _silence(ffmpeg, work_dir, COVER_SEC, "_sil_cover.mp3")
    pause_sil = _silence(ffmpeg, work_dir, PAUSE_SEC, "_sil_pause.mp3")

    ordered = [i for i in range(len(sections))
               if i in sec_audio and sec_audio[i].get("audio_path")
               and os.path.exists(sec_audio[i]["audio_path"])]
    parts = [cover_sil]
    sec_start, t = {}, COVER_SEC
    for n, i in enumerate(ordered):
        sec_start[i] = t
        parts.append(sec_audio[i]["audio_path"])
        t += sec_audio[i].get("duration_sec", 0)
        if n < len(ordered) - 1:
            parts.append(pause_sil)
            t += PAUSE_SEC

    list_path = work_dir / "_audio_concat.txt"
    with open(list_path, "w") as f:
        for p in parts:
            f.write(f"file '{os.path.abspath(p)}'\n")
    subprocess.run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(list_path),
                    "-c:a", "libmp3lame", "-q:a", "2", str(out_path)], capture_output=True)
    for p in (cover_sil, pause_sil, str(list_path)):
        if os.path.exists(p):
            os.remove(p)
    return sec_start, t


def _silence(ffmpeg, work_dir: Path, seconds: float, name: str) -> str:
    import subprocess
    path = str(work_dir / name)
    subprocess.run([ffmpeg, "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                    "-t", str(seconds), "-c:a", "libmp3lame", "-q:a", "9", path],
                   capture_output=True)
    return path


def _assign_shot_durations(shots: list, sec_start: dict, total_dur: float):
    """精确铺满音轨时间线：每段视觉跨度=该段起点到下一段起点（吸收段间停顿），
    末段铺到音轨结尾；段内分镜均分。这样视觉与配音/字幕严格对齐、无累积漂移。"""
    from collections import defaultdict
    by_sec = defaultdict(list)
    for sh in shots:
        by_sec[sh.get("section_id", 0)].append(sh)

    ordered = sorted((sid for sid in sec_start), key=lambda s: sec_start[s])
    for pos, sid in enumerate(ordered):
        start = sec_start[sid]
        end = sec_start[ordered[pos + 1]] if pos + 1 < len(ordered) else total_dur
        group = by_sec.get(sid, [])
        if not group:
            continue
        each = round(max(1.0, (end - start) / len(group)), 3)
        for sh in group:
            sh["duration_sec"] = each

    for sh in by_sec.get(-1, []):       # 封面
        sh["duration_sec"] = COVER_SEC


def _merge_subtitles_offset(sec_audio: dict, sec_start: dict, out_path):
    """合并各段字幕，按 sec_start 偏移（含封面留白与段间停顿）。"""
    subs = []
    for i, res in sec_audio.items():
        if i not in sec_start:
            continue
        srt = res.get("subtitle_path", "")
        if not srt or not os.path.exists(srt):
            continue
        with open(srt, encoding="utf-8") as f:
            for block in f.read().strip().split("\n\n"):
                lines = block.strip().split("\n")
                if len(lines) < 3 or "-->" not in lines[1]:
                    continue
                a, b = lines[1].split("-->")
                subs.append((_srt_to_sec(a.strip()) + sec_start[i],
                             _srt_to_sec(b.strip()) + sec_start[i],
                             " ".join(lines[2:]).strip()))
    subs.sort()
    with open(out_path, "w", encoding="utf-8") as f:
        for n, (s, e, txt) in enumerate(subs, 1):
            f.write(f"{n}\n{_sec_to_srt(s)} --> {_sec_to_srt(e)}\n{txt}\n\n")


def _storyboard_duration(storyboard: dict) -> float:
    return sum(float(shot.get("duration_sec") or 0) for shot in storyboard.get("shots", []))


def _write_storyboard_srt(storyboard: dict, output_path: Path):
    offset = 0.0
    with open(output_path, "w", encoding="utf-8") as f:
        for i, shot in enumerate(storyboard.get("shots", []), start=1):
            duration = float(shot.get("duration_sec") or 3.0)
            subtitle = shot.get("subtitle") or shot.get("data", {}).get("headline", "")
            f.write(f"{i}\n")
            f.write(f"{_sec_to_srt(offset)} --> {_sec_to_srt(offset + duration)}\n")
            f.write(f"{subtitle}\n\n")
            offset += duration


def _create_silent_audio(output_path: Path, duration: float):
    ffmpeg = _get_ffmpeg()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess_args = [
        ffmpeg, "-y",
        "-f", "lavfi",
        "-i", "anullsrc=r=44100:cl=mono",
        "-t", str(max(duration, 1.0)),
        "-c:a", "libmp3lame",
        "-q:a", "4",
        str(output_path),
    ]
    import subprocess
    subprocess.run(subprocess_args, capture_output=True)


def _extract_key_frames(video_path: Path, frames_dir: Path):
    if not video_path.exists():
        return
    frames_dir.mkdir(exist_ok=True)
    ffmpeg = _get_ffmpeg()
    import subprocess
    for second in (1, 5, 10):
        out = frames_dir / f"frame_{second:02d}.jpg"
        subprocess.run([
            ffmpeg, "-y", "-ss", str(second), "-i", str(video_path),
            "-frames:v", "1", str(out),
        ], capture_output=True)


def _summarize_tts_status(section_results: list[dict]) -> str:
    statuses = {result.get("tts_status", "missing") for result in section_results}
    if not statuses:
        return "missing"
    if len(statuses) == 1:
        return next(iter(statuses))
    return "+".join(sorted(statuses))


def _merge_subtitles(section_results: list, output_path: str):
    """合并所有段落的字幕"""
    all_subs = []
    offset = 0.0

    for result in section_results:
        srt_path = result.get("subtitle_path", "")
        if not srt_path or not os.path.exists(srt_path):
            offset += result.get("duration_sec", 0)
            continue

        with open(srt_path, "r", encoding="utf-8") as f:
            content = f.read()

        blocks = content.strip().split("\n\n")
        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) < 3:
                continue
            time_line = lines[1]
            if "-->" not in time_line:
                continue
            parts = time_line.split("-->")
            start = _srt_to_sec(parts[0].strip()) + offset
            end = _srt_to_sec(parts[1].strip()) + offset
            text = " ".join(lines[2:]).strip()
            if text:
                all_subs.append((start, end, text))

        offset += result.get("duration_sec", 0)

    with open(output_path, "w", encoding="utf-8") as f:
        for i, (start, end, text) in enumerate(all_subs):
            f.write(f"{i + 1}\n")
            f.write(f"{_sec_to_srt(start)} --> {_sec_to_srt(end)}\n")
            f.write(f"{text}\n\n")


def _srt_to_sec(t):
    t = t.replace(",", ".")
    p = t.split(":")
    return float(p[0]) * 3600 + float(p[1]) * 60 + float(p[2])


def _sec_to_srt(s):
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:06.3f}".replace(".", ",")


def main():
    parser = argparse.ArgumentParser(description="抖音视频生成Pipeline")
    parser.add_argument("inputs", nargs="*", help="Excel脚本路径或demand目录")
    parser.add_argument("--name", "-n", help="单脚本输出文件名（不含扩展名）")
    parser.add_argument("--voice", "-v", default=None, help="TTS语音（默认: 苏打）")
    parser.add_argument("--batch", "-b", action="store_true", help="批量处理模式")
    parser.add_argument("--no-tts", action="store_true", help="跳过外部TTS，生成静音烟测视频")
    args = parser.parse_args()

    if not args.inputs:
        parser.print_help()
        sys.exit(1)

    if args.batch or len(args.inputs) > 1 or Path(args.inputs[0]).is_dir():
        run_batch(args.inputs, voice=args.voice, no_tts=args.no_tts)
    else:
        run_pipeline(args.inputs[0], args.name, args.voice, args.no_tts)


if __name__ == "__main__":
    main()
