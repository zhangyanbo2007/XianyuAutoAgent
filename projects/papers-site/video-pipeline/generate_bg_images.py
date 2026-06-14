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

# Slide-specific prompts matching reference video content
SLIDE_PROMPTS = {
    0: "A glowing neon brain made of colorful circuit board traces, half organic brain half digital circuits, cyan magenta and green neon glow on pure black background, sci-fi aesthetic, no text, cinematic lighting, 4K",
    1: "A large glowing green checkmark on the left and a glowing orange question mark on the right, separated by purple lightning bolts, dark background with scattered digital puzzle pieces and code fragments, sci-fi neon style, no text",
    2: "A glowing neural network brain visualization with cyan wireframe mountains above it, connected by light beams to smaller purple nodes labeled with abstract concepts, dark background with circuit patterns, sci-fi neon style, no text",
    3: "A glowing open book on the left connected by a cyan arrow to a glowing AI brain chip on the right, labeled Transfer, dark background with circuit traces, sci-fi neon style, no text",
    4: "A glowing cyan circle with M3Eval text in the center, surrounded by four quadrant icons: a brain (divided attention), a wave (memory interference), crossing lines (interleaved events), and a sequence (N-back test), dark background with circuit patterns, sci-fi neon style, no text",
    5: "Two side-by-side glowing brain illustrations, left showing a person cooking stir-fry, right showing a person adding bean sprouts, connected by neural pathways, dark background with green neon glow, sci-fi style, no text",
    6: "A dark futuristic bar chart with glowing green bar at 90 percent and two red bars at 27 percent, neon glow effects, dark background with subtle circuit patterns, sci-fi data visualization style, no text",
    7: "Two parallel flow diagrams showing retroactive interference (video A to similar B to test A) and proactive interference (video A to similar B to test B), cyan arrows on dark background, sci-fi neon style, no text",
    8: "Two glowing balance scales side by side, left labeled Human showing retroactive heavier than proactive, right labeled AI showing both equal, cyan and red neon glow, dark background, sci-fi style, no text",
    9: "Two interleaved film strips, one cyan (case A) and one magenta (case B), crossing and mixing in the middle with a glowing brain, dark background with neon glow, sci-fi style, no text",
    10: "A grouped bar chart with multiple models on x-axis, green bars for repeat target and magenta bars for repeat interfering, showing improvement, neon glow on dark background, sci-fi data visualization, no text",
    11: "A glowing N-back sequence diagram with boxes showing B A C and a question mark for match, connected by golden arc arrows, dark background with orange neon glow, sci-fi style, no text",
    12: "A line chart showing human accuracy declining slowly from 95 to 40 percent, AI models dropping sharply to 22 percent, with a 25 percent random baseline, neon green and orange lines on dark background, sci-fi data visualization, no text",
    13: "Split comparison: left side shows a glowing human brain with organized crystalline memory structures, right side shows an AI chip overflowing with colorful chaotic data streams, dark background, red and cyan neon glow, sci-fi style, no text",
    14: "A 4x2 matrix grid with glowing checkmarks on left column (human) and red X marks on right column (AI), with category labels, dark background with purple neon glow, sci-fi style, no text",
    15: "A horizontal ranking bar chart with six glowing bars of different lengths, gold silver and bronze colors for top three, cyan and orange for others, dark background with subtle circuit patterns, sci-fi style, no text",
    16: "A glowing microchip in the center with three arrows pointing outward to different directions: structured attention (cyan), temporal grounding (magenta), strategic forgetting (orange), dark background with circuit traces, sci-fi style, no text",
    17: "Three glowing cards side by side with different colors (cyan, magenta, orange), each with an icon: brain, magnifying glass, and trash can, dark background with subtle glow, sci-fi style, no text",
    18: "A glowing tree made of colorful circuit board traces and neural pathways, branching out with cyan magenta and green neon lights, on pure black background, cinematic sci-fi aesthetic, no text",
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
