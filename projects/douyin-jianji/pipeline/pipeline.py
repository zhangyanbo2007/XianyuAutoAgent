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

from config import OUTPUT_DIR
from script_converter import convert_excel_to_script, save_script_to_json
from tts_generator import generate_sections_audio, concat_audio
from ai_image_generator import generate_section_bg_images
from video_generator import render_video


def run_pipeline(excel_path: str, output_name: str = None, voice: str = "zh-CN-YunjianNeural"):
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
    print("\n[1/5] 转换Excel脚本...")
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
    print("\n[2/5] 生成TTS音频...")
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
    print(f"  总音频时长: {total_audio:.1f}秒 ({total_audio/60:.1f}分钟)")

    # 更新段落时长（基于实际音频）
    for i, result in enumerate(section_results):
        if i < len(sections):
            sections[i]["duration_sec"] = result.get("duration_sec", 5)

    # 3. 生成AI图片
    print("\n[3/5] 生成AI图片...")
    ai_image_cache = os.path.join(work_dir, "_ai_images")
    theme = script.get("headline", "")
    ai_images = generate_section_bg_images(sections, ai_image_cache)
    print(f"  生成了 {len(ai_images)}/{len(sections)} 张AI图片")

    # 4. 准备幻灯片
    print("\n[4/5] 准备幻灯片...")
    slides = []
    for i, (section, img_path) in enumerate(zip(sections, ai_images)):
        if img_path and os.path.exists(img_path):
            slides.append({
                "path": img_path,
                "duration_sec": section.get("duration_sec", 5),
                "label": section.get("label", f"段落 {i}")
            })
        else:
            print(f"  ⚠ 段落 {i} 没有图片，使用占位图")
            # 创建占位图
            placeholder = os.path.join(ai_image_cache, f"placeholder_{i}.png")
            _create_placeholder_image(placeholder, section.get("label", f"段落 {i}"))
            slides.append({
                "path": placeholder,
                "duration_sec": section.get("duration_sec", 5),
                "label": section.get("label", f"段落 {i}")
            })

    print(f"  准备了 {len(slides)} 张幻灯片")

    # 5. 渲染视频
    print("\n[5/5] 渲染视频...")
    output_path = os.path.join(work_dir, f"{output_name}.mp4")
    render_video(slides, full_audio, output_path, full_srt)

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


def _create_placeholder_image(output_path: str, text: str):
    """创建占位图"""
    from PIL import Image, ImageDraw, ImageFont

    # 创建黑色背景
    img = Image.new("RGB", (1080, 1920), (26, 26, 46))
    draw = ImageDraw.Draw(img)

    # 尝试加载字体
    try:
        font = ImageFont.truetype("/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc", 48)
    except:
        font = ImageFont.load_default()

    # 绘制文本
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (1080 - text_width) // 2
    y = (1920 - text_height) // 2
    draw.text((x, y), text, fill=(255, 255, 255), font=font)

    img.save(output_path)


def main():
    parser = argparse.ArgumentParser(description="抖音视频生成Pipeline")
    parser.add_argument("excel", help="Excel脚本路径")
    parser.add_argument("--name", "-n", help="输出文件名（不含扩展名）")
    parser.add_argument("--voice", "-v", default="zh-CN-YunjianNeural",
                        help="TTS语音（默认: YunjianNeural男声）")
    args = parser.parse_args()

    run_pipeline(args.excel, args.name, args.voice)


if __name__ == "__main__":
    main()
