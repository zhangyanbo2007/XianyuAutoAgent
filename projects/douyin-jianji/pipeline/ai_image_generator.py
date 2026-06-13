"""AI图片生成器 - 为每张幻灯片生成背景图"""

import os
import time
import json
import hashlib
import urllib.request
from config import DASHSCOPE_API_KEY, DASHSCOPE_API, DASHSCOPE_MODEL, PROXY


def generate_bg_image(prompt: str, cache_dir: str, index: int = 0,
                      size: str = "1280*720") -> str:
    """
    生成单张AI背景图并返回本地路径

    Args:
        prompt: 图片生成提示词
        cache_dir: 缓存目录
        index: 帧索引
        size: 图片尺寸（wanx2.1-t2i-turbo 支持的16:9尺寸，渲染时再裁剪填充到1080p）

    Returns:
        图片路径，失败返回None
    """
    os.makedirs(cache_dir, exist_ok=True)

    # 缓存键
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:16]
    cache_path = os.path.join(cache_dir, f"bg_{index:03d}_{prompt_hash}.png")

    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 1000:
        return cache_path

    if not DASHSCOPE_API_KEY:
        print("  ⚠ 未设置DASHSCOPE_API_KEY，跳过AI图片生成")
        return None

    # 提交生成任务
    try:
        import requests
        return _generate_with_requests(prompt, cache_path, size)
    except ImportError:
        return _generate_with_urllib(prompt, cache_path, size)


def _generate_with_requests(prompt: str, output_path: str, size: str) -> str:
    """使用requests库生成图片"""
    import requests

    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable",
    }
    payload = {
        "model": DASHSCOPE_MODEL,
        "input": {"prompt": prompt},
        "parameters": {"size": size, "n": 1},
    }

    # 提交任务
    resp = requests.post(f"{DASHSCOPE_API}/services/aigc/text2image/image-synthesis",
                         headers=headers, json=payload, timeout=30)
    data = resp.json()

    if "output" not in data or "task_id" not in data["output"]:
        print(f"  ⚠ 图片生成失败: {data.get('message', 'unknown error')}")
        return None

    task_id = data["output"]["task_id"]

    # 轮询等待完成（最多120秒）
    for _ in range(40):
        time.sleep(3)
        resp = requests.get(f"{DASHSCOPE_API}/tasks/{task_id}",
                           headers={"Authorization": f"Bearer {DASHSCOPE_API_KEY}"},
                           timeout=15)
        result = resp.json()
        status = result.get("output", {}).get("task_status", "")

        if status == "SUCCEEDED":
            results = result.get("output", {}).get("results", [])
            if results and results[0].get("url"):
                img_url = results[0]["url"]
                _download(img_url, output_path)
                return output_path
            break
        elif status == "FAILED":
            print(f"  ⚠ 图片生成任务失败")
            break

    return None


def _generate_with_urllib(prompt: str, output_path: str, size: str) -> str:
    """使用urllib生成图片（备用方案）"""
    import ssl
    ctx = ssl.create_default_context()

    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable",
    }
    payload = json.dumps({
        "model": DASHSCOPE_MODEL,
        "input": {"prompt": prompt},
        "parameters": {"size": size, "n": 1},
    }).encode()

    req = urllib.request.Request(
        f"{DASHSCOPE_API}/services/aigc/text2image/image-synthesis",
        data=payload, headers=headers, method="POST"
    )
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        data = json.loads(resp.read())

    task_id = data.get("output", {}).get("task_id")
    if not task_id:
        return None

    # 轮询
    for _ in range(40):
        time.sleep(3)
        req = urllib.request.Request(
            f"{DASHSCOPE_API}/tasks/{task_id}",
            headers={"Authorization": f"Bearer {DASHSCOPE_API_KEY}"}
        )
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            result = json.loads(resp.read())

        status = result.get("output", {}).get("task_status", "")
        if status == "SUCCEEDED":
            results = result.get("output", {}).get("results", [])
            if results and results[0].get("url"):
                _download(results[0]["url"], output_path)
                return output_path
            break
        elif status == "FAILED":
            break

    return None


def _download(url: str, output_path: str):
    """下载文件"""
    try:
        import requests
        resp = requests.get(url, timeout=60, proxies={"https": PROXY} if PROXY else None)
        with open(output_path, "wb") as f:
            f.write(resp.content)
    except ImportError:
        if PROXY:
            proxy_handler = urllib.request.ProxyHandler({
                'http': PROXY,
                'https': PROXY
            })
            opener = urllib.request.build_opener(proxy_handler)
        else:
            opener = urllib.request.build_opener()

        req = urllib.request.Request(url)
        with opener.open(req, timeout=60) as resp:
            with open(output_path, "wb") as f:
                f.write(resp.read())


def generate_section_bg_images(sections: list, cache_dir: str) -> list:
    """
    为每个段落生成AI背景图

    Args:
        sections: 段落列表
        cache_dir: 缓存目录

    Returns:
        图片路径列表
    """
    os.makedirs(cache_dir, exist_ok=True)
    images = []

    for i, section in enumerate(sections):
        slide = section.get("slide", {})
        bg_prompt = slide.get("data", {}).get("bg_prompt", "")

        if not bg_prompt:
            # 生成默认提示词
            bg_prompt = f"Professional dark tech background, 16:9 aspect ratio"

        print(f"  生成背景图 {i}: {section.get('label', '')}")
        img_path = generate_bg_image(bg_prompt, cache_dir, index=i)
        images.append(img_path)

    return images


if __name__ == "__main__":
    # 测试
    test_sections = [
        {"label": "痛点", "slide": {"data": {"bg_prompt": "solar panel warning sign"}}},
        {"label": "正确顺序", "slide": {"data": {"bg_prompt": "solar permit process"}}},
    ]
    images = generate_section_bg_images(test_sections, "/tmp/test_bg_images")
    print(f"生成了 {len(images)} 张背景图")
