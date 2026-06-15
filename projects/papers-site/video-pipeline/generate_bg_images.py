#!/usr/bin/env python3
"""Generate specific AI background images for each DAST slide."""

import os
import sys
import json
import time
import hashlib
import urllib.request

# Load .env
_this_dir = os.path.dirname(os.path.abspath(__file__))
for _depth in range(5):
    _this_dir = os.path.dirname(_this_dir)
    _env_path = os.path.join(_this_dir, ".env")
    if os.path.exists(_env_path):
        with open(_env_path) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
        break

API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output", "dast-video", "bg_images")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Slide-specific prompts based on M3Eval paper content
# Each prompt generates a complete slide design with paper-specific data
SLIDE_PROMPTS = {
    # Title: M3Eval paper introduction
    0: "A complete presentation slide on pure black background: top text 'Peking University & UW-Madison' in white, center shows a glowing brain made of circuit traces half gold half blue with lightning bolt symbol, large cyan neon title text 'M3Eval: 多模态记忆评估', subtitle '基于认知心理学的首个多模态模型记忆评估基准', cinematic neon glow style",

    # Core problem: context window vs memory
    1: "A complete presentation slide on pure black background: large cyan text '上下文窗口越来越长，AI记忆力就越来越好？', left side glowing green checkmark representing context length improvement, right side glowing orange question mark representing memory gaps, purple lightning between them showing the contradiction, neon sci-fi style",

    # Research gap: perception vs memory
    2: "A complete presentation slide on pure black background: large white text '我们一直在考大模型的视力，却忽略了脑力', top shows wireframe brain with labels 'Visual Perception' and 'Reasoning' (what we test), bottom shows memory concepts 'Capacity', 'Fidelity', 'Robustness' (what we miss), sci-fi diagram style",

    # Method: cognitive psychology transfer
    3: "A complete presentation slide on pure black background: large cyan text 'M3Eval：用人类认知心理学来审问AI', left golden book representing psychology experiments, center cyan arrow labeled 'Transfer', right blue AI chip representing multimodal memory evaluation, neon transfer diagram style",

    # Four dimensions overview
    4: "A complete presentation slide on pure black background: large white text '解析记忆的四个切面', center cyan circle with 'M3Eval' text, four colored quadrants: green 'Divided Attention', cyan 'Memory Interference', pink 'Interleaved Events', orange 'N-Back Test', radial diagram style",

    # Test 1: Divided Attention
    5: "A complete presentation slide on pure black background: large green text '测试一：分散注意力（一心多用测试）', two green-bordered frames showing split-screen cooking scenes, labels showing parallel video streams, brain icons above representing attention competition, split screen style",

    # Test 1 result: Human 90% vs AI 27%
    6: "A complete presentation slide on pure black background: large green text '面对双屏，顶级AI瞬间失忆', left side bar chart with tall green bar 'Human 90%' and short red bars 'GPT-5.4 27%', right side conclusion box explaining 'Attention Confusion', neon data dashboard style",

    # Test 2: Memory Interference
    7: "A complete presentation slide on pure black background: large cyan text '测试二：记忆干扰（相似内容的覆盖效应）', two flow diagrams: top shows 'Retroactive: Video A → Similar B → Test A', bottom shows 'Proactive: Video A → Similar B → Test B', neon flowchart style",

    # Test 2 result: Interference patterns differ
    8: "A complete presentation slide on pure black background: large cyan text 'AI的记忆覆盖逻辑完全不同于人类', left balance scale showing Human: Retroactive > Proactive, right balance scale showing AI: Retroactive ≈ Proactive, comparison diagram style",

    # Test 3: Interleaved Events
    9: "A complete presentation slide on pure black background: large magenta text '测试三：交错事件（时间线的拼图能力）', two interleaved film strips (cyan Case A, magenta Case B) crossing in middle, brain at intersection reconstructing stories, film diagram style",

    # Test 3 result: Repeat播放 helps
    10: "A complete presentation slide on pure black background: large green text '意外发现：重复播放竟能强化AI记忆', grouped bar chart showing 6 models with green bars (repeat target) and magenta bars (repeat interfering) both showing improvement, data chart style",

    # Test 4: N-Back
    11: "A complete presentation slide on pure black background: large orange text '测试四：N-Back（符号化与工作记忆容量极限）', sequence boxes showing 'Match? [B] [A] [C]' with golden curved arrow connecting back N steps, sequence diagram style",

    # Test 4 result: Human vs AI symbolic memory
    12: "A complete presentation slide on pure black background: large orange text '鸿沟再现：大模型缺乏人类级的符号记忆力', line chart with green Human line (95%→40%), orange AI lines (50%→22%), dashed 25% random baseline, neon chart style",

    # Why AI fails: noise overload
    13: "A complete presentation slide on pure black background: large red text '为什么AI的记忆力会在这里崩盘？', left shows organized crystalline brain (human selective memory), right shows overflowing chaotic AI chip (noise overload), comparison style",

    # Summary matrix
    14: "A complete presentation slide on pure black background: large purple text 'M3Eval评估结论矩阵：智能的岔路口', 4x2 matrix: rows for Spatial/Temporal/Logic/Abstract, columns Human (green checkmarks) vs AI (red X marks), matrix diagram style",

    # Model ranking
    15: "A complete presentation slide on pure black background: large cyan text '现役大模型多模态记忆力摸底排行', horizontal bars: cyan 'GPT-5.4 75.4' and 'Gemini 70.1', green 'Qwen 55.4' and 'InternVL 45.1', orange 'M3-Agent 25' and 'VideoLucy 15', ranking dashboard style",

    # Future directions
    16: "A complete presentation slide on pure black background: large purple text '进化的方向：给AI装上真正的海马体', center microchip with three arrows: cyan 'Structured Attention', magenta 'Temporal Grounding', orange 'Strategic Forgetting', chip diagram style",

    # Key takeaways
    17: "A complete presentation slide on pure black background: large white text '我们学到了什么？(Key Takeaways)', three cards: cyan 'Context ≠ Memory', magenta 'Psychology as Litmus Test', orange 'Learn to Forget', card layout style",

    # Ending
    18: "A complete presentation slide on pure black background: large cyan text '真实的智能，藏在对记忆的重塑之中。', glowing tree made of circuit traces with neon branches, subtitle about M3Eval revealing AGI path, cinematic ending style",
}


def generate_image(prompt: str, output_path: str, index: int) -> bool:
    """Generate image using Dashscope wanx2.1 API."""
    import hashlib
    cache_key = hashlib.md5(prompt.encode()).hexdigest()[:12]
    cache_path = os.path.join(OUTPUT_DIR, f"cache_{cache_key}.png")

    if os.path.exists(cache_path):
        import shutil
        shutil.copy(cache_path, output_path)
        return True

    # Submit task
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable"
    }
    data = json.dumps({
        "model": "wanx2.1-t2i-turbo",
        "input": {"prompt": prompt},
        "parameters": {
            "size": "1440*810",
            "n": 1
        }
    }).encode()

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        task_id = result.get("output", {}).get("task_id")
        if not task_id:
            print(f"    No task_id returned")
            return False
    except Exception as e:
        print(f"    Submit error: {e}")
        return False

    # Poll for result
    poll_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
    poll_headers = {"Authorization": f"Bearer {API_KEY}"}

    for attempt in range(40):
        time.sleep(3)
        try:
            req = urllib.request.Request(poll_url, headers=poll_headers)
            resp = urllib.request.urlopen(req, timeout=10)
            result = json.loads(resp.read())
            status = result.get("output", {}).get("task_status")

            if status == "SUCCEEDED":
                img_url = result["output"]["results"][0]["url"]
                urllib.request.urlretrieve(img_url, output_path)
                import shutil
                shutil.copy(output_path, cache_path)
                return True
            elif status == "FAILED":
                print(f"    Failed: {result.get('output', {}).get('message', '')}")
                return False
        except Exception as e:
            pass

    print(f"    Timeout after polling")
    return False


def main():
    if not API_KEY:
        print("ERROR: DASHSCOPE_API_KEY not found in .env")
        return

    print(f"Generating {len(SLIDE_PROMPTS)} background images...")
    print(f"Output: {OUTPUT_DIR}\n")

    success = 0
    for idx, prompt in sorted(SLIDE_PROMPTS.items()):
        output_path = os.path.join(OUTPUT_DIR, f"slide_{idx:02d}.png")
        if os.path.exists(output_path):
            print(f"  [{idx:02d}] SKIP (exists)")
            success += 1
            continue

        print(f"  [{idx:02d}] Generating...", end=" ", flush=True)
        if generate_image(prompt, output_path, idx):
            print("OK")
            success += 1
        else:
            print("FAILED")

    print(f"\nDone: {success}/{len(SLIDE_PROMPTS)} images generated")


if __name__ == "__main__":
    main()
