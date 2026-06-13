"""Generate concept-specific AI illustrations for each video frame using Dashscope wanx2.1."""

import os
import time
import json
import hashlib
import urllib.request

DASHSCOPE_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
if not DASHSCOPE_KEY:
    # Try reading from .env file - check multiple locations
    for env_dir in [
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    ]:
        env_path = os.path.join(env_dir, ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.startswith("DASHSCOPE_API_KEY="):
                        DASHSCOPE_KEY = line.strip().split("=", 1)[1]
                        break
            if DASHSCOPE_KEY:
                break

DASHSCOPE_API = "https://dashscope.aliyuncs.com/api/v1"
MODEL = "wanx2.1-t2i-turbo"


def generate_frame_image(prompt: str, cache_dir: str, index: int = 0,
                         size: str = "1024*576") -> str:
    """Generate a single AI image and return local path."""
    os.makedirs(cache_dir, exist_ok=True)
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:16]
    cache_path = os.path.join(cache_dir, f"frame_{index:03d}_{prompt_hash}.png")

    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 1000:
        return cache_path

    if not DASHSCOPE_KEY:
        print("  ⚠ No DASHSCOPE_API_KEY")
        return None

    try:
        import requests

        headers = {
            "Authorization": f"Bearer {DASHSCOPE_KEY}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",
        }
        payload = {
            "model": MODEL,
            "input": {"prompt": prompt},
            "parameters": {"size": size, "n": 1},
        }

        resp = requests.post(f"{DASHSCOPE_API}/services/aigc/text2image/image-synthesis",
                             headers=headers, json=payload, timeout=30)
        data = resp.json()

        task_id = data.get("output", {}).get("task_id")
        if not task_id:
            print(f"  ⚠ Image gen failed: {data.get('message', 'unknown')}")
            return None

        for _ in range(40):
            time.sleep(3)
            resp = requests.get(f"{DASHSCOPE_API}/tasks/{task_id}",
                               headers={"Authorization": f"Bearer {DASHSCOPE_KEY}"},
                               timeout=15)
            result = resp.json()
            status = result.get("output", {}).get("task_status", "")

            if status == "SUCCEEDED":
                results = result.get("output", {}).get("results", [])
                if results and results[0].get("url"):
                    _download(results[0]["url"], cache_path)
                    return cache_path
                break
            elif status == "FAILED":
                break

    except Exception as e:
        print(f"  ⚠ Image gen error: {type(e).__name__}: {e}")

    return None


def _download(url: str, output_path: str):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        with open(output_path, "wb") as f:
            f.write(resp.read())


# Concept-specific prompts for M3Eval video
SECTION_PROMPTS = {
    # 封面
    0: "A stunning cinematic title card: a glowing human brain made of light particles floating in dark space, half organic neural network with colorful synapses, half digital circuit board with microchips, neon blue and cyan glow, volumetric fog, particles, dark background, 4K ultra-detailed, sci-fi concept art",

    # 核心问题：上下文窗口越来越长，AI记忆力就越来越好？
    1: "A giant glowing green checkmark on the left side and a purple lightning bolt on the right side, with a large neon question mark in the center, holographic data panels and AI neural network visualizations floating around, dark background, dramatic lighting, 4K cinematic",

    # 问题深化：我们一直在考大模型的'视力'，却忽略了'脑力'
    2: "An iceberg metaphor in dark ocean: above the water, a bright glowing AI camera eye represents visual perception, impressive and bright; below the dark water surface, a massive hidden glowing brain structure represents memory and reasoning, barely visible, bioluminescent blue glow, dark ocean, sci-fi atmosphere, 4K ultra-detailed",

    # 核心疑问：想象一下，你看完一段视频后...
    3: "A person watching a holographic video screen in a dark room, with memory fragments floating around like glowing orbs, some clear and bright (remembered), some fading and blurry (forgotten), cinematic lighting, dark background, 4K concept art",

    # 研究缺口：现有基准只关注视觉感知
    4: "A magnifying glass examining a glowing AI brain, but only the surface is illuminated (vision), while the deeper layers remain dark and unexplored (memory), holographic data panels showing test scores, dark background, cyan glow, 4K",

    # M³Eval诞生：首个基于认知心理学的评估基准
    5: "A transformation scene: on the left, a glowing ancient psychology textbook opens with knowledge flowing out as golden particles; on the right, a holographic AI brain absorbs the particles through neural connections, the two sides connected by luminous data streams, dark background, warm gold to cool cyan gradient, 4K concept art",

    # 设计灵感：认知心理学
    6: "A split brain visualization: left side shows organic human brain with colorful neural pathways and memory centers highlighted, right side shows digital AI processor with circuit patterns, a glowing bridge connects them, dark background, blue and purple neon, 4K scientific illustration",

    # 五维度对比：记忆保真度、抗干扰、空间、时间、符号
    7: "A futuristic holographic dashboard floating in dark space, showing five glowing circular gauges arranged in a pentagon pattern, each labeled with a different dimension, connected by luminous data streams, cyan and magenta accents, sci-fi control room aesthetic, 4K",

    # 测试一：记忆保真度
    8: "A test chamber with a holographic video screen playing a movie, and a clock ticking in the corner, after the movie ends, question marks float around asking about details, glowing neural pathways trying to recall, dark room, blue ambient light, 4K cinematic",

    # 测试二：干扰测试
    9: "Two holographic video screens side by side, one showing a cooking scene, the other showing a different scene, with interference waves and static between them, a central AI brain trying to process both, crossing neural connections, dark room, blue and pink neon, 4K",

    # 人类vs AI记忆模式
    10: "A dramatic split-screen comparison: left side shows an organic human brain with golden neural pathways and memory traces, warm light; right side shows a digital AI processor with circuit patterns and data corruption artifacts, cool blue light, a thin glowing line divides them, dark background, 4K cinematic",

    # 干扰影响数据：准确率从85%暴跌到35%
    11: "A futuristic holographic bar chart floating in dark space, showing two bars: one tall green bar at 85% labeled 'before interference', one short red bar at 35% labeled 'after interference', with a dramatic downward arrow between them, glowing data points, dark background, 4K",

    # 测试三：空间定位
    12: "A 3D holographic space map floating in dark room, showing a video frame divided into grid sections with location markers, some sections glowing bright (remembered location), others dim (forgotten), spatial coordinates and crosshairs, dark background, cyan glow, 4K",

    # 测试四：时间顺序
    13: "A glowing timeline floating in dark space, with events marked as bright nodes connected by luminous threads, time flowing from left to right, some events in correct order (green glow), some scrambled (red glow), holographic clock elements, dark background, 4K cinematic",

    # 并行流解缠
    14: "Two separate movie film strips flowing parallel in dark space, each showing different scenes, with a central AI brain trying to keep them separate, neural connections crossing between the strips creating confusion, dark background, blue and red neon, 4K",

    # 并行流测试结果：80%暴跌到27%
    15: "A futuristic holographic comparison panel: left side shows a happy green brain icon at 80% (single stream), right side shows a confused red brain icon at 27% (dual stream), dramatic arrow pointing down, glowing data visualization, dark background, 4K",

    # 测试五：符号记忆
    16: "Abstract symbols and geometric shapes floating in dark space, some symbols sharp and clear with golden glow (remembered), others fading and blurry (forgotten), representing memory of abstract concepts, dark background, purple and cyan glow, 4K",

    # 各维度记忆能力对比
    17: "A futuristic radar chart floating in dark space, showing five dimensions with different scores, the chart glows with neon colors, data points connected by luminous lines, dark background, cyan and magenta accents, 4K data visualization",

    # 模型的选择性失忆
    18: "A brain with selective memory: some areas glowing bright with clear images of objects (car, person), other areas dark with faded abstract concepts, representing selective forgetting, dark background, blue and gold glow, 4K concept art",

    # 模型排行榜
    19: "A futuristic leaderboard hologram floating in dark space, showing ranked positions with glowing bars and numbers, a holographic trophy at the top, models listed with scores, dark background, gold and cyan neon, 4K sci-fi aesthetic",

    # 为何记忆如此关键
    20: "A futuristic AI assistant in a smart home environment, remembering user preferences shown as floating holographic cards, learning from past interactions shown as timeline, dark background, warm and cool neon mix, 4K concept art",

    # 超越单一分数
    21: "A medical-style diagnostic report for AI memory, showing multiple test results as glowing holographic cards, some green (pass), some red (fail), a doctor's clipboard with detailed analysis, dark background, 4K",

    # 当前局限性
    22: "A boundary wall in dark space, with the current test scope illuminated on one side, and unexplored territory (audio, cross-modal) beyond the wall in darkness, representing limitations, dark background, 4K concept art",

    # 未来研究方向
    23: "A futuristic roadmap in dark space, showing three glowing paths leading forward: structured attention, temporal encoding, and strategic forgetting, each path illuminated with different colored neon, dark background, 4K cinematic",

    # 记忆架构改进方向
    24: "A futuristic neural network architecture diagram, showing layers of processing modules with 'insert memory module' labels, upgrade arrows, new memory pathways being built, dark background, blue and green neon glow, 4K technical illustration",

    # 总结
    25: "A glowing brain made of thousands of light particles, slowly assembling from scattered points into a complete glowing form, symbolizing understanding and breakthrough, warm golden and cyan glow, bokeh particles, cinematic depth of field, inspirational mood, 4K ultra-detailed",
}


def generate_section_images(sections: list, cache_dir: str, theme: str = "") -> dict:
    """Generate concept-specific AI images for all sections."""
    results = {}

    for i, section in enumerate(sections):
        prompt = SECTION_PROMPTS.get(i)
        if not prompt:
            # Fallback: use type-based prompt
            prompt = f"A futuristic sci-fi illustration representing {section.get('label', 'concept')}, dark background, neon glow, 4K cinematic"

        print(f"  Generating image {i}: {section.get('label', '')}...")
        img_path = generate_frame_image(prompt, cache_dir, i)

        if img_path:
            results[i] = img_path
            print(f"    ✓ Generated")
        else:
            print(f"    ✗ Failed")

    return results


if __name__ == "__main__":
    # Test with one image
    test_sections = [{"id": 0, "type": "title", "label": "封面", "text": "测试"}]
    results = generate_section_images(test_sections, "/tmp/test_gen_v2")
    print(f"Results: {results}")
