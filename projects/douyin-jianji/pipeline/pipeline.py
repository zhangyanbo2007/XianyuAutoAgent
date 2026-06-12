#!/usr/bin/env python3
"""抖音视频生成Pipeline - 从Excel脚本生成完整视频"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# 加载.env文件
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

from config import OUTPUT_DIR, DEFAULT_BGM
from script_converter import convert_excel_to_script, save_script_to_json
from tts_generator import generate_sections_audio, concat_audio
from ai_image_generator import generate_section_bg_images
from slide_renderer import render_slide
from video_generator import render_video


def run_pipeline(excel_path: str, output_name: str = None, voice: str = None):
    """
    运行完整的视频生成流程

    Args:
        excel_path: Excel脚本路径
        output_name: 输出文件名（不含扩展名）
        voice: TTS语音
    """
    start = time.time()

    # 确定输出名称
    if not output_name:
        output_name = os.path.splitext(os.path.basename(excel_path))[0]

    work_dir = os.path.join(OUTPUT_DIR, output_name)
    os.makedirs(work_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  抖音视频生成: {output_name}")
    print(f"{'='*60}")

    # 1. 转换Excel脚本为JSON格式
    print("\n[1/6] 转换Excel脚本...")
    script_path = os.path.join(work_dir, "script.json")
    if os.path.exists(script_path):
        print("  使用缓存的脚本")
        with open(script_path) as f:
            script = json.load(f)
    else:
        script = convert_excel_to_script(excel_path)
        save_script_to_json(script, script_path)

    sections = script.get("sections", [])
    print(f"  段落数: {len(sections)}")
    print(f"  目标时长: {script.get('duration', 'N/A')}")

    # 2. 生成TTS音频
    print("\n[2/6] 生成TTS音频...")
    audio_dir = os.path.join(work_dir, "audio")
    tts_sections = []
    for s in sections:
        tts_sections.append({
            "label": s.get("label", ""),
            "text": s.get("text", ""),
            "duration_sec": s.get("duration_sec", 5),
        })

    section_results = generate_sections_audio(tts_sections, audio_dir, voice=voice)

    full_audio = os.path.join(work_dir, "narration.mp3")
    concat_audio(section_results, full_audio)

    # 生成字幕文件
    full_srt = os.path.join(work_dir, "narration.srt")
    _merge_subtitles(section_results, full_srt)

    total_audio = sum(r.get("duration_sec", 0) for r in section_results)
    print(f"  总音频时长: {total_audio:.1f}秒")

    # 更新段落时长（基于实际音频）
    for i, result in enumerate(section_results):
        if i < len(sections):
            sections[i]["duration_sec"] = result.get("duration_sec", 5)

    # 3. 生成AI背景图
    print("\n[3/6] 生成AI背景图...")
    ai_image_cache = os.path.join(work_dir, "_ai_images")
    bg_images = generate_section_bg_images(sections, ai_image_cache)
    print(f"  生成了 {len(bg_images)}/{len(sections)} 张背景图")

    # 4. 渲染幻灯片
    print("\n[4/6] 渲染幻灯片...")
    slides_dir = os.path.join(work_dir, "slides")
    os.makedirs(slides_dir, exist_ok=True)

    slides = []
    title_text = script.get("headline", output_name)

    for i, (section, bg_img) in enumerate(zip(sections, bg_images)):
        slide_path = os.path.join(slides_dir, f"slide_{i:02d}.png")
        slide_data = section.get("slide", {"template": "data_big", "data": {}})

        render_slide(slide_data, bg_img, slide_path, title_text)

        slides.append({
            "path": slide_path,
            "duration_sec": section.get("duration_sec", 5),
        })

    print(f"  渲染了 {len(slides)} 张幻灯片")

    # 5. 渲染视频
    print("\n[5/6] 渲染视频...")
    output_path = os.path.join(work_dir, f"{output_name}.mp4")

    # 检查BGM
    bgm_path = DEFAULT_BGM if os.path.exists(DEFAULT_BGM) else None

    render_video(slides, full_audio, output_path, full_srt, bgm_path)

    # 6. 清理临时文件
    print("\n[6/6] 清理临时文件...")
    _cleanup_work_dir(work_dir)

    elapsed = time.time() - start
    size = os.path.getsize(output_path) / (1024 * 1024) if os.path.exists(output_path) else 0

    print(f"\n{'='*60}")
    print(f"  ✅ 完成! ({elapsed:.1f}秒)")
    print(f"  输出: {output_path}")
    print(f"  大小: {size:.1f} MB")
    print(f"{'='*60}\n")

    return output_path


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
            f.write(f"{i+1}\n")
            f.write(f"{_sec_to_srt(start)} --> {_sec_to_srt(end)}\n")
            f.write(f"{text}\n\n")


def _srt_to_sec(t):
    t = t.replace(",", ".")
    p = t.split(":")
    return float(p[0])*3600 + float(p[1])*60 + float(p[2])


def _sec_to_srt(s):
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:06.3f}".replace(".", ",")


def _cleanup_work_dir(work_dir: str):
    """清理工作目录中的临时文件"""
    import shutil

    # 删除音频目录中的临时文件
    audio_dir = os.path.join(work_dir, "audio")
    if os.path.exists(audio_dir):
        for f in os.listdir(audio_dir):
            if f.startswith("_"):
                os.remove(os.path.join(audio_dir, f))

    # 删除AI图片缓存目录
    ai_cache = os.path.join(work_dir, "_ai_images")
    if os.path.exists(ai_cache):
        shutil.rmtree(ai_cache)


def run_batch(excel_paths: list):
    """
    批量处理多个Excel脚本

    Args:
        excel_paths: Excel文件路径列表
    """
    print(f"\n{'='*60}")
    print(f"  批量处理 {len(excel_paths)} 个Excel文件")
    print(f"{'='*60}\n")

    results = []
    for excel_path in excel_paths:
        if not os.path.exists(excel_path):
            print(f"  ⚠ 文件不存在: {excel_path}")
            continue

        try:
            output_path = run_pipeline(excel_path)
            results.append({"excel": excel_path, "output": output_path, "status": "success"})
        except Exception as e:
            print(f"  ❌ 处理失败: {excel_path} - {e}")
            results.append({"excel": excel_path, "output": None, "status": "failed"})

    # 打印汇总
    print(f"\n{'='*60}")
    print(f"  批量处理完成")
    print(f"{'='*60}")
    success = sum(1 for r in results if r["status"] == "success")
    print(f"  成功: {success}/{len(results)}")
    for r in results:
        status = "✅" if r["status"] == "success" else "❌"
        print(f"  {status} {r['excel']}")
    print()


def main():
    parser = argparse.ArgumentParser(description="抖音视频生成Pipeline")
    parser.add_argument("excel", nargs="*", help="Excel脚本路径（支持多个）")
    parser.add_argument("--name", "-n", help="输出文件名（不含扩展名）")
    parser.add_argument("--voice", "-v", default=None,
                        help="TTS语音（默认: 苏打）")
    parser.add_argument("--batch", "-b", action="store_true",
                        help="批量处理模式")
    args = parser.parse_args()

    if not args.excel:
        parser.print_help()
        sys.exit(1)

    if args.batch or len(args.excel) > 1:
        run_batch(args.excel)
    else:
        run_pipeline(args.excel[0], args.name, args.voice)


if __name__ == "__main__":
    main()
