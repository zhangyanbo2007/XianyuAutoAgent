#!/usr/bin/env python3
"""Pipeline V8: HTML+CSS slides with charts, rendered via Playwright."""

import os, sys, json, time, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import OUTPUT_DIR, DATA_DIR
from script_generator_v2 import generate_script_v2
from tts_generator import generate_sections_audio, concat_audio
from motion_renderer import render_video_v2
from slide_html import (
    render_title_slide, render_question_slide, render_method_slide,
    render_comparison_slide, render_chart_slide, render_ending_slide,
    render_detail_slide, render_chart_slide_with_bg, render_detail_slide_with_bg,
    make_bar_chart, make_ranking_chart, make_grouped_bar,
    OUTPUT_DIR as SLIDES_DIR
)

def load_paper(slug):
    with open(os.path.join(DATA_DIR, "papers.json")) as f:
        data = json.load(f)
    for p in data["papers"]:
        if p.get("slug") == slug:
            return p
    raise ValueError(f"Paper not found: {slug}")


def run_pipeline(paper_slug):
    start = time.time()
    work_dir = os.path.join(OUTPUT_DIR, paper_slug)
    os.makedirs(work_dir, exist_ok=True)
    slides_dir = os.path.join(work_dir, "slides_v8")
    chart_dir = os.path.join(slides_dir, "_charts")
    os.makedirs(chart_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  Paper V8: {paper_slug}")
    print(f"{'='*60}")

    # 1. Load paper
    print("\n[1/5] Loading paper...")
    paper = load_paper(paper_slug)
    print(f"  {paper['title'][:60]}")

    # 2. Generate script
    print("\n[2/5] Generating script...")
    script_path = os.path.join(work_dir, "script_v8.json")
    if os.path.exists(script_path):
        with open(script_path) as f:
            script = json.load(f)
        print(f"  Using cached: {len(script['sections'])} sections")
    else:
        script = generate_script_v2(paper)
        with open(script_path, "w", encoding="utf-8") as f:
            json.dump(script, f, ensure_ascii=False, indent=2)
        print(f"  Generated: {len(script['sections'])} sections")

    sections = script.get("sections", [])

    # 3. Generate TTS
    print("\n[3/5] Generating TTS...")
    audio_dir = os.path.join(work_dir, "audio_v8")
    tts_sections = [{"label": s.get("label",""), "text": s.get("text",""), "duration_sec": s.get("duration_sec",30)} for s in sections]
    section_results = generate_sections_audio(tts_sections, audio_dir)
    narration = os.path.join(work_dir, "narration_v8.mp3")
    concat_audio(section_results, narration)
    srt_path = os.path.join(work_dir, "narration_v8.srt")
    _merge_srt(section_results, srt_path)

    # Update durations
    for i, r in enumerate(section_results):
        if i < len(sections):
            sections[i]["duration_sec"] = r.get("duration_sec", 30)
    total_audio = sum(r.get("duration_sec", 0) for r in section_results)
    print(f"  Audio: {total_audio:.0f}s ({total_audio/60:.1f}min)")

    # 4. Generate charts
    print("\n[4/5] Generating charts...")
    _generate_charts(sections, chart_dir)

    # 5. Render HTML slides
    print("\n[5/5] Rendering HTML slides...")
    os.makedirs(slides_dir, exist_ok=True)
    slide_files = []
    total = len(sections)

    # Generate AI images for each section
    print("  Generating AI images...")
    ai_images_dir = os.path.join(work_dir, "_ai_images")
    os.makedirs(ai_images_dir, exist_ok=True)
    ai_images = _generate_ai_images(sections, ai_images_dir, paper.get("theme", ""))

    # Generate charts for chart sections
    print("  Generating charts...")
    _generate_charts(sections, chart_dir)

    for i, section in enumerate(sections):
        stype = section.get("type", "detail")
        label = section.get("label", "")
        text = section.get("text", "")

        # Get AI image as base64 if available
        bg_b64 = None
        ai_img = ai_images.get(i)
        if ai_img and os.path.exists(ai_img):
            import base64
            with open(ai_img, "rb") as f:
                bg_b64 = base64.b64encode(f.read()).decode()

        if stype == "title":
            html = render_title_slide(
                script.get("video_title", ""),
                paper.get("title", ""),
                paper.get("theme_label", ""),
                i, total, bg_b64
            )
        elif stype == "question":
            html = render_question_slide(label, text, text[:50], i, total)
        elif stype == "method":
            html = render_method_slide(label, text, i, total)
        elif stype == "comparison":
            html = render_detail_slide(label, text, i, total)
        elif stype == "chart":
            chart_path = os.path.join(chart_dir, f"chart_{i}.png")
            if os.path.exists(chart_path):
                html = render_chart_slide_with_bg(label, chart_path, text[:60], i, total, bg_b64)
            else:
                html = render_detail_slide_with_bg(label, text, i, total, bg_b64)
        elif stype == "ending":
            key_points = [s.get("text", "")[:60] for s in sections if s.get("type") in ("chart","detail","comparison")][:4]
            html = render_ending_slide(script.get("video_title",""), key_points, i, total)
        else:
            html = render_detail_slide_with_bg(label, text, i, total, bg_b64)

        html_path = os.path.join(slides_dir, f"slide_{i:02d}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        slide_files.append(html_path)

    # Render HTML to PNG via Playwright
    print("  Rendering HTML → PNG...")
    _render_html_to_png(slide_files, slides_dir)

    # Build slide list for video renderer
    slides = []
    for i, section in enumerate(sections):
        png_path = os.path.join(slides_dir, f"slide_{i:02d}.png")
        if os.path.exists(png_path):
            slides.append({"path": png_path, "duration_sec": section.get("duration_sec", 30), "type": section.get("type","detail")})

    print(f"  {len(slides)} slides rendered")

    # 6. Render video
    print("\n[6/6] Rendering video...")
    output_path = os.path.join(work_dir, f"{paper_slug}_v8.mp4")
    render_video_v2(slides, narration, output_path, srt_path)

    elapsed = time.time() - start
    size = os.path.getsize(output_path) / (1024*1024)
    duration = _get_duration(output_path)
    print(f"\n{'='*60}")
    print(f"  ✅ V8 Done! ({elapsed:.0f}s)")
    print(f"  {output_path}")
    print(f"  {size:.1f}MB, {duration:.0f}s ({duration/60:.1f}min)")
    print(f"{'='*60}\n")

    # Copy to site
    import shutil
    site_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "videos")
    os.makedirs(site_dir, exist_ok=True)
    dest = os.path.join(site_dir, f"{paper_slug}_v8.mp4")
    shutil.copy2(output_path, dest)
    print(f"Copied to: {dest}")

    return output_path


def _generate_ai_images(sections, ai_images_dir, theme):
    """Generate AI images for each section using Dashscope API."""
    import requests
    import json
    import base64
    import time

    DASHSCOPE_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
    if not DASHSCOPE_KEY:
        print("  ⚠ No DASHSCOPE_API_KEY, skipping AI images")
        return {}

    # Concept-specific prompts for each section type
    concept_prompts = {
        "title": "A massive glowing neon brain split in half: left side organic neurons with golden synapses, right side circuit boards with blue LED pathways, dark space background, cinematic lighting, 4K ultra-detailed",
        "question": "A dramatic scene: green checkmark and purple lightning bolt clashing, giant golden question mark, puzzle pieces scattering, holographic screens showing video, dark background, 4K cinematic",
        "background": "An iceberg rising from dark ocean: above water shows a bright AI camera eye glowing blue, below water shows a massive hidden brain structure with neural pathways, bioluminescent glow, 4K ultra-detailed",
        "method": "A transformation scene: ancient golden book on left dissolving into particles flowing toward a futuristic AI brain on right, luminous data streams connecting them, dark background, 4K cinematic",
        "detail": "A futuristic laboratory with holographic displays showing video clips being analyzed by AI, glowing neural network connections, dark room with blue ambient light, 4K ultra-detailed",
        "chart": "A futuristic holographic dashboard floating in space, showing 3D bar charts and data visualizations with neon glow, dark background, 4K",
        "comparison": "Split comparison: left side organic human brain with golden synapses, right side digital AI processor with blue circuits, glowing VS divider, dark background, 4K cinematic",
        "ending": "A brain made of thousands of glowing particles assembling from scattered points into complete form, warm golden and cyan light, bokeh particles, cinematic depth of field, 4K ultra-detailed",
    }

    # Theme-specific additions
    theme_extra = {
        "safety_governance_and_reliability": "with cybersecurity shields",
        "neuroscience_and_cognitive_science": "with neurons and brain anatomy",
        "multimodal_foundation_models": "with multimodal data streams",
        "reinforcement_learning": "with reward signals",
        "generative_modeling_and_diffusion": "with abstract patterns",
        "robotics_and_embodied_intelligence": "with robotic arms",
        "physics_and_ai_for_science": "with physics equations",
        "agents_and_autonomous_science": "with autonomous agents",
        "chemistry_biology_and_lab_automation": "with molecular structures",
        "reasoning_memory_and_inference_control": "with memory circuits",
        "ai_hardware_and_accelerator_design": "with microchips",
        "math_and_formal_reasoning": "with formulas",
        "interpretability_and_mechanistic_analysis": "with neural pathways",
    }

    results = {}
    for i, section in enumerate(sections):
        stype = section.get("type", "detail")
        label = section.get("label", "")
        text = section.get("text", "")

        # Build prompt
        base_prompt = concept_prompts.get(stype, concept_prompts["detail"])

        # Add label-specific context
        label_lower = label.lower()
        if "干扰" in label or "记忆模式" in label:
            base_prompt = "Two brains: left organic human brain, right digital AI brain, interference waves between, dark background, neon, 4K"
        elif "空间" in label or "定位" in label:
            base_prompt = "A holographic 3D space map floating in dark room, coordinates, location pins, dark background, cyan neon, 4K"
        elif "时间" in label or "顺序" in label:
            base_prompt = "A glowing timeline floating in dark space, events as bright nodes, holographic clock, dark background, 4K"
        elif "排行" in label or "模型" in label:
            base_prompt = "A futuristic leaderboard hologram floating in dark space, glowing bars, dark background, gold neon, 4K"
        elif "架构" in label or "改进" in label:
            base_prompt = "A futuristic neural network architecture, layers connected by glowing pathways, dark background, 4K"

        # Add theme
        theme_key = theme.lower().replace(" ", "_").replace("、", "_").replace("/", "_")
        extra = theme_extra.get(theme_key, "with AI and technology elements")
        base_prompt += f", {extra}"

        print(f"    Image {i}: {label}")
        try:
            img_path = _generate_single_image(base_prompt, ai_images_dir, i)
            if img_path:
                results[i] = img_path
        except Exception as e:
            print(f"    ⚠ Image {i} failed: {e}")

    return results


def _generate_single_image(prompt, cache_dir, index):
    """Generate a single AI image using Dashscope API."""
    import requests
    import json
    import base64
    import time

    DASHSCOPE_KEY = os.environ.get("DASHSCOPE_API_KEY", "")

    # Check cache
    cache_path = os.path.join(cache_dir, f"img_{index:03d}.png")
    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 1000:
        return cache_path

    headers = {
        "Authorization": f"Bearer {DASHSCOPE_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable",
    }
    payload = {
        "model": "wanx2.1-t2i-turbo",
        "input": {"prompt": prompt},
        "parameters": {"size": "1024*576", "n": 1},
    }

    resp = requests.post(
        "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis",
        headers=headers, json=payload, timeout=30,
    )
    data = resp.json()
    task_id = data.get("output", {}).get("task_id")
    if not task_id:
        return None

    # Poll for completion
    for _ in range(30):
        time.sleep(3)
        resp = requests.get(
            f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}",
            headers={"Authorization": f"Bearer {DASHSCOPE_KEY}"},
            timeout=15,
        )
        result = resp.json()
        status = result.get("output", {}).get("task_status", "")
        if status == "SUCCEEDED":
            results = result.get("output", {}).get("results", [])
            if results and results[0].get("url"):
                img_url = results[0]["url"]
                img_resp = requests.get(img_url, timeout=30)
                with open(cache_path, "wb") as f:
                    f.write(img_resp.content)
                return cache_path
            break
        elif status == "FAILED":
            break

    return None


def _generate_charts(sections, chart_dir):
    """Generate charts for chart-type sections."""
    for i, section in enumerate(sections):
        if section.get("type") != "chart":
            continue
        chart_data = section.get("chart_data", {})
        if not chart_data:
            continue
        chart_path = os.path.join(chart_dir, f"chart_{i}.png")
        try:
            chart_type = chart_data.get("type", "bar")
            title = chart_data.get("title", "")
            labels = chart_data.get("labels", [])
            values = chart_data.get("values", [])
            colors = chart_data.get("colors", None)
            if not labels or not values:
                continue
            if chart_type == "bar":
                make_bar_chart(title, labels, values, colors or ["#38b8df8"]*len(labels), chart_path)
            elif chart_type == "ranking":
                make_ranking_chart(title, labels, values, chart_path)
            elif chart_type == "grouped_bar":
                groups = chart_data.get("groups", {})
                make_grouped_bar(title, labels, groups, chart_path)
            print(f"    Chart {i}: {title}")
        except Exception as e:
            print(f"    ⚠ Chart {i} failed: {e}")


def _render_html_to_png(html_files, output_dir):
    """Render HTML files to PNG using Playwright."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})

        for html_path in html_files:
            png_path = html_path.replace(".html", ".png")
            file_url = f"file://{os.path.abspath(html_path)}"
            page.goto(file_url, wait_until="networkidle")
            page.wait_for_timeout(500)
            page.screenshot(path=png_path, full_page=False)

        browser.close()


def _merge_srt(section_results, output_path):
    all_subs = []
    offset = 0.0
    for r in section_results:
        srt = r.get("subtitle_path", "")
        if srt and os.path.exists(srt):
            with open(srt) as f:
                content = f.read()
            for block in content.strip().split("\n\n"):
                lines = block.strip().split("\n")
                if len(lines) < 3 or "-->" not in lines[1]:
                    continue
                parts = lines[1].split("-->")
                start = _srt2sec(parts[0].strip()) + offset
                end = _srt2sec(parts[1].strip()) + offset
                text = " ".join(lines[2:]).strip()
                if text:
                    all_subs.append((start, end, text))
        offset += r.get("duration_sec", 0)

    with open(output_path, "w") as f:
        for i, (s, e, t) in enumerate(all_subs):
            f.write(f"{i+1}\n{_sec2srt(s)} --> {_sec2srt(e)}\n{t}\n\n")


def _srt2sec(t):
    t = t.replace(",", ".")
    p = t.split(":")
    return float(p[0])*3600 + float(p[1])*60 + float(p[2])

def _sec2srt(s):
    h = int(s//3600); m = int((s%3600)//60); sec = s%60
    return f"{h:02d}:{m:02d}:{sec:06.3f}".replace(".", ",")

def _get_duration(path):
    ffmpeg = "/home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/.venv/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
    r = subprocess.run([ffmpeg, "-i", path, "-f", "null", "-"], capture_output=True, text=True)
    for line in r.stderr.split("\n"):
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = parts.split(":")
            return float(h)*3600 + float(m)*60 + float(s)
    return 0.0


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--paper", "-p", required=True)
    args = parser.parse_args()
    run_pipeline(args.paper)
