"""Textless cinematic AI backdrop generation via DashScope (wanx2.1-t2i-turbo).

Each section's ``visual_prompt`` is a purely pictorial, English, no-text prompt.
These backdrops are composited under the code-rendered HTML text overlays.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import time
import urllib.request
from pathlib import Path
from typing import Any

_ENV_LOADED = False


def _load_env() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True
    # Load .env from the repo root
    env_path = Path(__file__).resolve().parents[3] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def _api_key() -> str:
    _load_env()
    return os.environ.get("DASHSCOPE_API_KEY", "")


def _open(url: str, headers: dict | None = None, data: bytes | None = None, method: str = "GET", timeout: int = 30) -> dict:
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return __import__("json").loads(resp.read())


def generate_backdrop(prompt: str, output_path: str, size: str = "1440*810", cache_dir: str | None = None) -> bool:
    """Generate one textless cinematic backdrop image. Returns True on success."""
    key = _api_key()
    if not key:
        print("    [bg] DASHSCOPE_API_KEY not set — skipping backdrop")
        return False

    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        cache_key = hashlib.md5(prompt.encode()).hexdigest()[:12]
        cache_path = os.path.join(cache_dir, f"bg_{cache_key}.png")
        if os.path.exists(cache_path):
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            shutil.copy2(cache_path, output_path)
            return True
    else:
        cache_path = None

    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable",
    }
    body = __import__("json").dumps({
        "model": "wanx2.1-t2i-turbo",
        "input": {"prompt": prompt},
        "parameters": {"size": size, "n": 1},
    }).encode()

    try:
        result = _open(url, headers=headers, data=body, method="POST")
        task_id = result.get("output", {}).get("task_id")
        if not task_id:
            print("    [bg] no task_id returned")
            return False
    except Exception as e:
        print(f"    [bg] submit error: {e}")
        return False

    poll_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
    poll_headers = {"Authorization": f"Bearer {key}"}
    for _ in range(50):
        time.sleep(3)
        try:
            result = _open(poll_url, headers=poll_headers)
            status = result.get("output", {}).get("task_status")
            if status == "SUCCEEDED":
                img_url = result["output"]["results"][0]["url"]
                os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
                urllib.request.urlretrieve(img_url, output_path)
                if cache_path:
                    shutil.copy2(output_path, cache_path)
                return True
            elif status == "FAILED":
                msg = result.get("output", {}).get("message", "")
                print(f"    [bg] generation failed: {msg}")
                return False
        except Exception:
            pass

    print("    [bg] timeout after polling")
    return False


def generate_all_backdrops(
    sections: list[dict[str, Any]],
    out_dir: str | Path,
    cache_dir: str | None = None,
    parallel: int = 1,
) -> dict[int, str]:
    """Generate textless backdrops for every section. Returns {index: path}."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if cache_dir is None:
        cache_dir = str(out_dir / "_cache")
    paths: dict[int, str] = {}
    for i, sec in enumerate(sections):
        prompt = sec.get("visual_prompt", "")
        if not prompt:
            continue
        out_path = out_dir / f"slide_{i:02d}.png"
        if out_path.exists():
            paths[i] = str(out_path)
            print(f"  [bg] Slide {i:02d}: SKIP (exists)")
            continue
        print(f"  [bg] Slide {i:02d}: generating...", end=" ", flush=True)
        if generate_backdrop(prompt, str(out_path), cache_dir=cache_dir):
            print("OK")
            paths[i] = str(out_path)
        else:
            print("FAILED")
    return paths
