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

# Slide-specific prompts matching reference video content exactly
# Each prompt describes the EXACT visual elements including text and diagrams
SLIDE_PROMPTS = {
    # Title: brain with circuit traces, title text included
    0: "A complete slide design on pure black background: top text 'Peking University & UW-Madison' in white, center shows a glowing brain made of circuit traces half gold half blue with lightning bolt, below in large cyan neon text 'AI看视频真的能过目不忘吗？', subtitle '揭秘顶尖大模型的人类级记忆缺陷', small text at bottom, cinematic neon glow style",

    # Question: checkmark vs question mark with text
    1: "A complete slide design on pure black background: large cyan text at top '上下文窗口越来越长，AI记忆力就越来越好？', left side large glowing green checkmark, right side large glowing orange question mark, purple lightning between them, bottom text bar with explanation, neon sci-fi style",

    # Problem: brain network diagram with labels
    2: "A complete slide design on pure black background: large white text at top '我们一直在考大模型的视力，却忽略了脑力', center shows wireframe brain with labels Visual Perception and Reasoning above, memory concepts below, bottom text bar, sci-fi diagram style",

    # Method: transfer diagram with text
    3: "A complete slide design on pure black background: large cyan text at top 'M3Eval：用人类认知心理学来审问AI', left golden book, center cyan arrow labeled Transfer, right blue AI chip, bottom text bar, neon transfer diagram style",

    # Overview: four quadrant diagram with text
    4: "A complete slide design on pure black background: large white text at top '解析记忆的四个切面', center cyan circle with M3Eval, four quadrants: green Divided Attention, cyan Memory Interference, pink Interleaved Events, orange N-Back, bottom text bar, radial diagram style",

    # Test 1 intro: split screen with labels
    5: "A complete slide design on pure black background: large green text at top '测试一：分散注意力（一心多用测试）', two green-bordered frames showing cooking scenes, labels '左边画面：炒肉' and '右边画面：加豆芽', bottom text bar, split screen style",

    # Test 1 result: bar chart with conclusion
    6: "A complete slide design on pure black background: large green text at top '面对双屏，顶级AI瞬间失忆', left side tall green bar at 90% and red bars at 27%, right side conclusion box with text about Attention Confusion, neon data dashboard style",

    # Test 2 intro: interference flow diagram
    7: "A complete slide design on pure black background: large cyan text at top '测试二：记忆干扰（相似内容的覆盖效应）', two flow diagrams with arrows showing retroactive and proactive interference, bottom text bar, neon flowchart style",

    # Test 2 result: balance scale with insight
    8: "A complete slide design on pure black background: large cyan text at top 'AI的记忆覆盖逻辑完全不同于人类', two balance scales comparing Human vs AI interference patterns, bottom insight box with explanation, comparison diagram style",

    # Test 3 intro: film strips
    9: "A complete slide design on pure black background: large magenta text at top '测试三：交错事件（时间线的拼图能力）', two interleaved film strips cyan Case A and magenta Case B, brain at intersection, bottom text bar, film diagram style",

    # Test 3 result: grouped bar chart
    10: "A complete slide design on pure black background: large green text at top '意外发现：重复播放竟能强化AI记忆', grouped bar chart with green and magenta bars showing improvement, right side insight box, neon data chart style",

    # Test 4 intro: N-back sequence
    11: "A complete slide design on pure black background: large orange text at top '测试四：N-Back（符号化与工作记忆容量极限）', sequence boxes B A C with golden arc arrow, bottom text bar, sequence diagram style",

    # Test 4 result: line chart
    12: "A complete slide design on pure black background: large orange text at top '鸿沟再现：大模型缺乏人类级的符号记忆力', line chart with green human line and orange AI lines, 25% baseline, right side findings box, neon chart style",

    # Why crash: brain vs chip
    13: "A complete slide design on pure black background: large red text at top '为什么AI的记忆力会在这里崩盘？', left organized brain, right chaotic AI chip, bottom text bar with technical explanation, comparison style",

    # Summary matrix
    14: "A complete slide design on pure black background: large purple text at top 'M3Eval评估结论矩阵：智能的岔路口', 4x2 matrix with green checkmarks for Human and red X for AI, category labels on left, matrix diagram style",

    # Ranking bars
    15: "A complete slide design on pure black background: large cyan text at top '现役大模型多模态记忆力摸底排行', horizontal bars: cyan GPT-5.4 75.4 and Gemini 70.1, green Qwen 55.4 and InternVL 45.1, orange M3-Agent 25 and VideoLucy 15, ranking dashboard style",

    # Future chip
    16: "A complete slide design on pure black background: large purple text at top '进化的方向：给AI装上真正的海马体', center chip with three arrows: cyan Structured Attention, magenta Temporal Grounding, orange Strategic Forgetting, chip diagram style",

    # Takeaway cards
    17: "A complete slide design on pure black background: large white text at top '我们学到了什么？(Key Takeaways)', three cards: cyan card about context length, magenta card about psychology, orange card about forgetting, card layout style",

    # Ending
    18: "A complete slide design on pure black background: large cyan text '真实的智能，藏在对记忆的重塑之中。', glowing circuit tree with neon branches, subtitle text below, cinematic ending style",
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
