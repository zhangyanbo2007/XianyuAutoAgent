# 抖音视频生成 Pipeline v2 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有竖屏视频 pipeline 升级为横屏专业信息图视频，对齐参考视频视觉风格

**Architecture:** AI 生成背景图 + Pillow 渲染文字/卡片 + FFmpeg 合成视频，支持批量处理

**Tech Stack:** Python 3.11, Pillow, Dashscope wanx2.1, MiMo TTS, FFmpeg

---

## 文件结构

```
pipeline/
├── config.py                  # 改：分辨率、颜色、字体、布局
├── script_converter.py        # 改：模板映射、AI提示词
├── tts_generator.py           # 改：合并MiMo逻辑
├── ai_image_generator.py      # 改：重命名+更新提示词
├── slide_renderer.py          # 新：Pillow渲染器
├── slide_templates.py         # 新：模板配置
├── video_generator.py         # 改：横屏、转场、BGM
├── pipeline.py                # 改：批量处理
├── bgm/                       # 新：背景音乐目录
│   └── default.mp3
├── fonts/                     # 新：字体目录
│   └── NotoSansCJKsc-Regular.otf
└── requirements.txt           # 改：更新依赖
```

**删除文件：**
- tts_generator_mimo.py（合并到 tts_generator.py）
- tts_generator_bailian.py（不再需要）
- video_renderer.py（和 video_generator.py 重复）

---

## Task 1: 更新配置文件

**Files:**
- Modify: `pipeline/config.py`

- [ ] **Step 1: 读取当前 config.py**

```bash
cat pipeline/config.py
```

- [ ] **Step 2: 更新 config.py**

替换整个文件内容：

```python
"""抖音视频生成Pipeline配置"""

import os

# 加载.env文件
_this_dir = os.path.dirname(os.path.abspath(__file__))
for _depth in range(5):
    _this_dir = os.path.dirname(_this_dir)
    _env_path = os.path.join(_this_dir, ".env")
    if os.path.exists(_env_path):
        with open(_env_path) as _f:
            for _line in _f:
                _line = _line.strip()
                if "=" in _line and not _line.startswith("#"):
                    _k, _v = _line.split("=", 1)
                    os.environ.setdefault(_k.strip(), _v.strip())
        break

# 小米MiMo TTS配置
API_BASE_URL = "https://token-plan-cn.xiaomimomo.com/v1"
API_KEY = os.environ.get("MIMO_API_KEY", "tp-c1kaznnjsvndkjgih8no34aj4530rk5u9ay61pma0eh3qjhb")
MIMO_TTS_MODEL = "mimo-v2.5-tts"
MIMO_TTS_VOICE = "苏打"  # 男性中文音色

# Dashscope API配置
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
DASHSCOPE_API = "https://dashscope.aliyuncs.com/api/v1"
DASHSCOPE_MODEL = "wanx2.1-t2i-turbo"

# 视频参数（横屏 16:9）
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30

# 色彩体系
COLORS = {
    "bg_primary": (26, 35, 50),      # #1a2332 深青蓝
    "bg_card": (36, 52, 71),         # #243447 卡片背景
    "accent_blue": (0, 212, 255),    # #00d4ff 高亮蓝
    "accent_gold": (255, 215, 0),    # #ffd700 强调金
    "success": (76, 175, 80),        # #4caf50 成功绿
    "warning": (255, 152, 0),        # #ff9800 警告橙
    "danger": (244, 67, 54),         # #f44336 危险红
    "text_primary": (255, 255, 255), # #ffffff 主文字
    "text_secondary": (176, 190, 197), # #b0bec5 次文字
    "divider": (55, 71, 79),         # #37474f 分隔线
}

# 字体配置
FONTS = {
    "title": {"size": 72, "weight": "bold"},
    "subtitle": {"size": 48, "weight": "regular"},
    "body": {"size": 36, "weight": "regular"},
    "data_big": {"size": 96, "weight": "bold"},
    "subtitle_bar": {"size": 60, "weight": "bold"},
    "step_number": {"size": 48, "weight": "bold"},
    "card_title": {"size": 40, "weight": "bold"},
    "card_desc": {"size": 32, "weight": "regular"},
}

# 布局
LAYOUT = {
    "margin": 60,
    "title_bar_height": 100,
    "subtitle_bar_height": 120,
    "content_top": 120,           # 内容区域起始Y
    "content_bottom": 960,        # 内容区域结束Y
    "card_padding": 32,
    "card_gap": 24,
    "card_radius": 16,
}

# 输出目录
OUTPUT_DIR = "./output"

# 代理配置
PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")

# 字体路径
FONT_PATH = os.path.join(os.path.dirname(__file__), "fonts", "NotoSansCJKsc-Regular.otf")

# BGM路径
BGM_DIR = os.path.join(os.path.dirname(__file__), "bgm")
DEFAULT_BGM = os.path.join(BGM_DIR, "default.mp3")
```

- [ ] **Step 3: 验证配置**

```bash
cd pipeline
python3 -c "from config import VIDEO_WIDTH, VIDEO_HEIGHT, COLORS; print(f'分辨率: {VIDEO_WIDTH}x{VIDEO_HEIGHT}'); print(f'颜色数: {len(COLORS)}')"
```

预期输出：
```
分辨率: 1920x1080
颜色数: 10
```

- [ ] **Step 4: Commit**

```bash
git add pipeline/config.py
git commit -m "feat: 更新配置文件 - 横屏1920x1080、颜色体系、字体布局"
```

---

## Task 2: 创建字体和BGM目录

**Files:**
- Create: `pipeline/fonts/` 目录
- Create: `pipeline/bgm/` 目录

- [ ] **Step 1: 创建目录**

```bash
mkdir -p pipeline/fonts pipeline/bgm
```

- [ ] **Step 2: 复制字体文件**

```bash
cp /home/zhangyanbo/.local/share/fonts/NotoSansCJKsc-Regular.otf pipeline/fonts/
```

- [ ] **Step 3: 验证字体**

```bash
ls -la pipeline/fonts/
```

预期输出：
```
NotoSansCJKsc-Regular.otf
```

- [ ] **Step 4: 下载免费BGM**

```bash
# 使用 ffmpeg 生成一个简单的测试BGM（轻快节奏）
ffmpeg -y -f lavfi -i "sine=frequency=440:duration=30" -af "volume=0.3" pipeline/bgm/default.mp3
```

- [ ] **Step 5: 验证BGM**

```bash
ls -la pipeline/bgm/
```

- [ ] **Step 6: Commit**

```bash
git add pipeline/fonts/ pipeline/bgm/
git commit -m "feat: 添加字体和BGM资源文件"
```

---

## Task 3: 更新脚本解析器

**Files:**
- Modify: `pipeline/script_converter.py`

- [ ] **Step 1: 读取当前 script_converter.py**

```bash
cat pipeline/script_converter.py
```

- [ ] **Step 2: 更新 script_converter.py**

替换整个文件内容：

```python
"""将Excel脚本转换为pipeline可用的JSON格式"""

import json
import openpyxl
from typing import List, Dict


def convert_excel_to_script(excel_path: str) -> Dict:
    """
    将Excel脚本转换为pipeline格式的JSON

    Args:
        excel_path: Excel文件路径

    Returns:
        pipeline格式的脚本字典
    """
    wb = openpyxl.load_workbook(excel_path)
    ws = wb.active

    # 提取基本信息
    script = {
        "video_title": "",
        "duration": "",
        "style": "",
        "bgm": "",
        "headline": "",
        "hashtags": "",
        "camera": "",
        "sections": [],
        "execution_tips": {}
    }

    # 遍历所有行
    for row in ws.iter_rows(min_row=1, max_row=ws.max_row, values_only=False):
        row_data = [cell.value for cell in row]

        # 提取标题
        if row_data[0] and "抖音短视频脚本" in str(row_data[0]):
            script["video_title"] = str(row_data[0]).strip()

        # 提取基本信息
        if row_data[0] and "时长" in str(row_data[0]):
            script["duration"] = str(row_data[1]).strip() if row_data[1] else ""
        elif row_data[0] and "风格" in str(row_data[0]):
            script["style"] = str(row_data[1]).strip() if row_data[1] else ""
        elif row_data[0] and "BGM" in str(row_data[0]):
            script["bgm"] = str(row_data[1]).strip() if row_data[1] else ""
        elif row_data[0] and "标题" in str(row_data[0]):
            script["headline"] = str(row_data[1]).strip() if row_data[1] else ""
        elif row_data[0] and "话题" in str(row_data[0]):
            script["hashtags"] = str(row_data[1]).strip() if row_data[1] else ""
        elif row_data[0] and "出镜" in str(row_data[0]):
            script["camera"] = str(row_data[1]).strip() if row_data[1] else ""

        # 提取脚本段落
        if row_data[0] and "-" in str(row_data[0]) and "s" in str(row_data[0]):
            # 解析时间段
            time_str = str(row_data[0]).strip()
            duration_sec = _parse_time_range(time_str)

            # 推断模板类型
            template_type = _infer_template_type(time_str, str(row_data[1] if row_data[1] else ""))

            # 生成AI图片提示词
            bg_prompt = _generate_bg_prompt(template_type, script.get("headline", ""))

            section = {
                "id": len(script["sections"]),
                "type": template_type,
                "duration_sec": duration_sec,
                "label": _extract_label(time_str),
                "text": str(row_data[2]).strip() if row_data[2] else "",
                "visual": str(row_data[1]).strip() if row_data[1] else "",
                "素材建议": str(row_data[4]).strip() if len(row_data) > 4 and row_data[4] else "",
                "slide": {
                    "template": template_type,
                    "data": {
                        "headline": _extract_headline(time_str, str(row_data[1] if row_data[1] else "")),
                        "bg_prompt": bg_prompt,
                    }
                }
            }

            # 根据模板类型添加特定数据
            if template_type == "step_list":
                section["slide"]["data"]["steps"] = _extract_steps(str(row_data[1] if row_data[1] else ""))
            elif template_type == "grid_2x2":
                section["slide"]["data"]["items"] = _extract_grid_items(str(row_data[1] if row_data[1] else ""))

            script["sections"].append(section)

        # 提取执行建议
        if row_data[0] and "评论区预埋" in str(row_data[0]):
            script["execution_tips"]["comments"] = str(row_data[1]).strip() if row_data[1] else ""
        elif row_data[0] and "字幕细节" in str(row_data[0]):
            script["execution_tips"]["subtitle_tips"] = str(row_data[1]).strip() if row_data[1] else ""
        elif row_data[0] and "封面文案" in str(row_data[0]):
            script["execution_tips"]["cover_text"] = str(row_data[1]).strip() if row_data[1] else ""

    return script


def _parse_time_range(time_str: str) -> float:
    """解析时间段，返回时长（秒）"""
    try:
        time_str = time_str.replace("s", "").strip()
        if "-" in time_str:
            parts = time_str.split("-")
            start = float(parts[0].strip())
            end = float(parts[1].strip())
            return end - start
        return 5.0
    except:
        return 5.0


def _extract_label(time_str: str) -> str:
    """从时间段提取标签"""
    try:
        if "(" in time_str and ")" in time_str:
            start = time_str.index("(") + 1
            end = time_str.index(")")
            return time_str[start:end]
        return time_str.replace("s", "").strip()
    except:
        return time_str


def _extract_headline(time_str: str, visual: str) -> str:
    """提取标题文字"""
    label = _extract_label(time_str)

    # 从视觉描述中提取标题
    if "字幕】" in visual:
        # 提取字幕内容
        parts = visual.split("字幕】")
        if len(parts) > 1:
            text = parts[1].strip()
            # 移除emoji和特殊字符
            import re
            text = re.sub(r'[✅📋⚠️🚫💡✨]', '', text)
            return text.strip()[:20]  # 限制长度

    return label


def _infer_template_type(time_str: str, visual: str) -> str:
    """根据时间段和视觉描述推断模板类型"""
    label = _extract_label(time_str).lower()
    visual_lower = visual.lower() if visual else ""

    if "痛点" in label or "悬念" in label or "坑" in visual_lower:
        return "title"
    elif "顺序" in visual_lower or "流程" in visual_lower or "步骤" in visual_lower:
        return "step_list"
    elif "材料" in visual_lower or "清单" in visual_lower or "必备" in visual_lower:
        return "grid_2x2"
    elif "渠道" in visual_lower or "办理" in visual_lower or "申请" in visual_lower:
        return "grid_2x2"
    elif "引导" in label or "评论" in visual_lower or "关注" in visual_lower:
        return "cta"
    else:
        return "data_big"


def _generate_bg_prompt(template_type: str, topic: str) -> str:
    """根据模板类型生成AI图片提示词"""
    prompts = {
        "title": (
            f"Professional dark tech background with {topic} theme, "
            "subtle green energy waves, cinematic lighting, "
            "modern corporate style, 16:9 aspect ratio"
        ),
        "data_big": (
            f"Industrial {topic} scene, aerial view, "
            "professional photography, dark blue tone, "
            "subtle light effects, 16:9 aspect ratio"
        ),
        "grid_2x2": (
            f"Modern {topic} infrastructure, "
            "clean professional background, "
            "dark gradient with accent lighting, 16:9 aspect ratio"
        ),
        "grid_3x1": (
            f"Power grid {topic} system, "
            "professional infographic style, "
            "dark background with highlights, 16:9 aspect ratio"
        ),
        "step_list": (
            f"Step-by-step {topic} process, "
            "professional infographic style, "
            "dark background with highlights, 16:9 aspect ratio"
        ),
        "cta": (
            f"Professional {topic} consultation scene, "
            "trustworthy and reliable mood, "
            "warm accent lighting, 16:9 aspect ratio"
        ),
    }
    return prompts.get(template_type, prompts["data_big"])


def _extract_steps(visual: str) -> list:
    """从视觉描述中提取步骤"""
    import re

    # 尝试匹配 "A → B → C" 格式
    if "→" in visual:
        parts = visual.split("→")
        return [p.strip() for p in parts if p.strip()]

    # 尝试匹配 "A、B、C" 格式
    if "、" in visual:
        parts = visual.split("、")
        return [p.strip() for p in parts if p.strip()]

    # 默认步骤
    return ["步骤1", "步骤2", "步骤3"]


def _extract_grid_items(visual: str) -> list:
    """从视觉描述中提取网格项目"""
    items = []

    # 尝试匹配 "A + B + C" 格式
    if "+" in visual:
        parts = visual.split("+")
        for p in parts:
            p = p.strip()
            if p:
                items.append({"title": p, "desc": ""})

    # 尝试匹配 "A、B、C" 格式
    elif "、" in visual:
        parts = visual.split("、")
        for p in parts:
            p = p.strip()
            if p:
                items.append({"title": p, "desc": ""})

    # 默认项目
    if not items:
        items = [
            {"title": "项目1", "desc": ""},
            {"title": "项目2", "desc": ""},
        ]

    return items


def save_script_to_json(script: Dict, output_path: str):
    """将脚本保存为JSON文件"""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)
    print(f"脚本已保存到: {output_path}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python script_converter.py <excel文件路径> [输出JSON路径]")
        sys.exit(1)

    excel_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "script.json"

    script = convert_excel_to_script(excel_path)
    save_script_to_json(script, output_path)
```

- [ ] **Step 3: 验证脚本解析**

```bash
cd pipeline
python script_converter.py ../demand/douyinwenanjiaoben.xlsx /tmp/test_script.json
cat /tmp/test_script.json | python -m json.tool | head -50
```

预期输出：JSON 格式，包含 sections 数组，每个 section 有 slide.template 字段

- [ ] **Step 4: Commit**

```bash
git add pipeline/script_converter.py
git commit -m "feat: 更新脚本解析器 - 模板映射、AI提示词生成"
```

---

## Task 4: 更新TTS生成器

**Files:**
- Modify: `pipeline/tts_generator.py`
- Delete: `pipeline/tts_generator_mimo.py`
- Delete: `pipeline/tts_generator_bailian.py`

- [ ] **Step 1: 读取当前 tts_generator.py**

```bash
cat pipeline/tts_generator.py
```

- [ ] **Step 2: 更新 tts_generator.py**

替换整个文件内容：

```python
"""TTS音频生成器 - 使用小米MiMo TTS生成中文配音"""

import os
import time
import base64
import subprocess
import re
from config import API_KEY as MIMO_API_KEY, API_BASE_URL, MIMO_TTS_MODEL, MIMO_TTS_VOICE

# 重试配置
MAX_RETRIES = 3
RETRY_DELAY = 5  # 秒


def generate_audio(text: str, output_path: str, voice: str = None) -> dict:
    """
    使用小米MiMo TTS生成音频

    Args:
        text: 要转换的文本
        output_path: 输出音频路径
        voice: TTS语音

    Returns:
        {"audio_path": "...", "subtitle_path": "...", "duration_sec": 45.2}
    """
    srt_path = output_path.rsplit(".", 1)[0] + ".srt"

    # 尝试MiMo TTS
    for attempt in range(MAX_RETRIES):
        try:
            import requests

            headers = {
                "Authorization": f"Bearer {MIMO_API_KEY}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": MIMO_TTS_MODEL,
                "messages": [
                    {"role": "user", "content": "用科普博主的语气，自然流畅地朗读以下内容"},
                    {"role": "assistant", "content": text},
                ],
                "audio": {"format": "wav", "voice": voice or MIMO_TTS_VOICE},
            }

            resp = requests.post(
                f"{API_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
            data = resp.json()

            # Extract audio from response
            if "choices" in data and data["choices"]:
                message = data["choices"][0].get("message", {})
                audio_info = message.get("audio", {})
                audio_data_b64 = audio_info.get("data", "")

                if audio_data_b64:
                    audio_data = base64.b64decode(audio_data_b64)
                    # Save as WAV first
                    wav_path = output_path.replace(".mp3", ".wav")
                    with open(wav_path, "wb") as f:
                        f.write(audio_data)

                    # Convert to MP3
                    ffmpeg = _get_ffmpeg()
                    subprocess.run([
                        ffmpeg, "-y", "-i", wav_path,
                        "-c:a", "libmp3lame", "-q:a", "2",
                        output_path,
                    ], capture_output=True)

                    # Cleanup WAV
                    if os.path.exists(wav_path):
                        os.remove(wav_path)

                    # Generate SRT
                    duration = _get_audio_duration(output_path)
                    _generate_srt_from_text(text, duration, srt_path)

                    return {
                        "audio_path": output_path,
                        "subtitle_path": srt_path,
                        "duration_sec": duration,
                    }

        except Exception as e:
            print(f"    ⚠ TTS error: {type(e).__name__}: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)

    # Fallback to edge-tts
    print("    ⚠ MiMo TTS failed, using edge-tts...")
    return _generate_edge_tts(text, output_path, srt_path)


def _generate_edge_tts(text: str, output_path: str, srt_path: str) -> dict:
    """使用edge-tts生成音频"""
    try:
        import edge_tts
        import asyncio

        proxy = os.environ.get("HTTPS_PROXY")
        communicate = edge_tts.Communicate(text, "zh-CN-YunxiNeural", proxy=proxy, connect_timeout=30)

        async def _gen():
            with open(output_path, "wb") as f:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])

        asyncio.run(_gen())

        # Generate SRT
        duration = _get_audio_duration(output_path)
        _generate_srt_from_text(text, duration, srt_path)

        return {
            "audio_path": output_path,
            "subtitle_path": srt_path,
            "duration_sec": duration,
        }

    except Exception as e:
        print(f"    ⚠ edge-tts error: {type(e).__name__}: {e}")
        return {"audio_path": "", "subtitle_path": "", "duration_sec": 0}


def _generate_srt_from_text(text: str, duration: float, srt_path: str):
    """从文本生成SRT字幕"""
    # 按中文句号分割
    sentences = re.split(r'(?<=[。！？；.!?;])\s*', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        sentences = [text]

    # 均匀分配时长
    total_chars = sum(len(s) for s in sentences)
    if total_chars == 0:
        return

    current_time = 0.0
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, sentence in enumerate(sentences):
            proportion = len(sentence) / total_chars
            seg_duration = proportion * duration
            start = current_time
            end = current_time + seg_duration

            f.write(f"{i + 1}\n")
            f.write(f"{_sec_to_srt(start)} --> {_sec_to_srt(end)}\n")
            f.write(f"{sentence}\n\n")

            current_time = end


def _sec_to_srt(seconds: float) -> str:
    """将秒转换为SRT时间戳 (HH:MM:SS,mmm)"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")


def _get_audio_duration(audio_path: str) -> float:
    """使用ffmpeg获取音频时长"""
    ffmpeg = _get_ffmpeg()
    r = subprocess.run([ffmpeg, "-i", audio_path, "-f", "null", "-"],
                       capture_output=True, text=True)
    for line in r.stderr.split("\n"):
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = parts.split(":")
            return float(h) * 3600 + float(m) * 60 + float(s)
    return 0.0


def _get_ffmpeg():
    """获取ffmpeg路径"""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except:
        return "ffmpeg"


def generate_sections_audio(sections: list, output_dir: str, voice: str = None) -> list:
    """
    为每个脚本段落生成音频

    Args:
        sections: 段落列表 [{"label": "...", "text": "...", "duration_sec": ...}]
        output_dir: 输出目录
        voice: TTS语音

    Returns:
        [{"label": ..., "audio_path": ..., "subtitle_path": ..., "duration_sec": ...}]
    """
    os.makedirs(output_dir, exist_ok=True)
    results = []

    for i, section in enumerate(sections):
        text = section.get("text", "")
        if not text:
            continue

        filename = f"section_{i:02d}.mp3"
        audio_path = os.path.join(output_dir, filename)

        print(f"  TTS段落 {i}: {section.get('label', '')} ({len(text)}字符)")
        result = generate_audio(text, audio_path, voice)
        if result:
            result["label"] = section.get("label", f"段落 {i}")
            result["index"] = i
            results.append(result)

    return results


def concat_audio(section_results: list, output_path: str, pause_ms: int = 500) -> str:
    """连接多个音频文件，中间添加停顿"""
    ffmpeg = _get_ffmpeg()

    # 创建静音文件用于停顿
    silence_path = os.path.join(os.path.dirname(output_path), "_silence.mp3")
    subprocess.run([
        ffmpeg, "-y", "-f", "lavfi", "-i",
        f"anullsrc=r=24000:cl=mono",
        "-t", str(pause_ms / 1000),
        "-c:a", "libmp3lame", "-q:a", "9",
        silence_path
    ], capture_output=True)

    # 构建连接列表
    list_path = os.path.join(os.path.dirname(output_path), "_concat.txt")
    with open(list_path, "w") as f:
        for i, result in enumerate(section_results):
            if result.get("audio_path") and os.path.exists(result["audio_path"]):
                f.write(f"file '{result['audio_path']}'\n")
                if i < len(section_results) - 1:
                    f.write(f"file '{silence_path}'\n")

    # 连接音频
    subprocess.run([
        ffmpeg, "-y", "-f", "concat", "-safe", "0",
        "-i", list_path,
        "-c:a", "libmp3lame", "-q:a", "2",
        output_path
    ], capture_output=True)

    # 清理临时文件
    for f in [silence_path, list_path]:
        if os.path.exists(f):
            os.remove(f)

    return output_path
```

- [ ] **Step 3: 删除旧文件**

```bash
rm pipeline/tts_generator_mimo.py pipeline/tts_generator_bailian.py
```

- [ ] **Step 4: 验证TTS**

```bash
cd pipeline
python -c "from tts_generator import generate_audio; print('TTS模块导入成功')"
```

- [ ] **Step 5: Commit**

```bash
git add pipeline/tts_generator.py
git rm pipeline/tts_generator_mimo.py pipeline/tts_generator_bailian.py
git commit -m "feat: 简化TTS生成器 - 合并MiMo逻辑，添加edge-tts fallback"
```

---

## Task 5: 更新AI图片生成器

**Files:**
- Modify: `pipeline/image_generator.py` → 重命名为 `pipeline/ai_image_generator.py`

- [ ] **Step 1: 重命名文件**

```bash
mv pipeline/image_generator.py pipeline/ai_image_generator.py
```

- [ ] **Step 2: 读取当前 ai_image_generator.py**

```bash
cat pipeline/ai_image_generator.py
```

- [ ] **Step 3: 更新 ai_image_generator.py**

替换整个文件内容：

```python
"""AI图片生成器 - 为每张幻灯片生成背景图"""

import os
import time
import json
import hashlib
import urllib.request
from config import DASHSCOPE_API_KEY, DASHSCOPE_API, DASHSCOPE_MODEL, PROXY


def generate_bg_image(prompt: str, cache_dir: str, index: int = 0,
                      size: str = "1920*1080") -> str:
    """
    生成单张AI背景图并返回本地路径

    Args:
        prompt: 图片生成提示词
        cache_dir: 缓存目录
        index: 帧索引
        size: 图片尺寸（横屏16:9）

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
```

- [ ] **Step 4: 验证AI图片生成器**

```bash
cd pipeline
python -c "from ai_image_generator import generate_bg_image; print('AI图片生成器模块导入成功')"
```

- [ ] **Step 5: Commit**

```bash
git add pipeline/ai_image_generator.py
git commit -m "feat: 更新AI图片生成器 - 横屏1920x1080，更新提示词模板"
```

---

## Task 6: 创建幻灯片渲染器

**Files:**
- Create: `pipeline/slide_renderer.py`

- [ ] **Step 1: 创建 slide_renderer.py**

```python
"""幻灯片渲染器 - 在AI背景图上叠加文字、卡片、图标"""

import os
from PIL import Image, ImageDraw, ImageFont
from config import (
    VIDEO_WIDTH, VIDEO_HEIGHT, COLORS, FONTS, LAYOUT, FONT_PATH
)


def render_slide(slide_data: dict, bg_image_path: str, output_path: str,
                 title_text: str = None):
    """
    渲染单张幻灯片

    Args:
        slide_data: 幻灯片数据 {"template": "...", "data": {...}}
        bg_image_path: AI背景图路径
        output_path: 输出PNG路径
        title_text: 顶部标题栏文字（可选）
    """
    # 1. 加载AI背景图
    if bg_image_path and os.path.exists(bg_image_path):
        img = Image.open(bg_image_path).convert("RGBA")
        img = img.resize((VIDEO_WIDTH, VIDEO_HEIGHT), Image.LANCZOS)
    else:
        # 创建纯色背景
        img = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), COLORS["bg_primary"] + (255,))

    # 2. 叠加半透明深色遮罩（保证文字可读）
    overlay = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 128))
    img = Image.alpha_composite(img, overlay)

    # 3. 创建绘图对象
    draw = ImageDraw.Draw(img)

    # 4. 渲染顶部标题栏
    if title_text:
        _draw_title_bar(draw, title_text)

    # 5. 根据模板类型渲染内容区域
    template = slide_data.get("template", "data_big")
    data = slide_data.get("data", {})

    if template == "title":
        _render_title_template(draw, data)
    elif template == "grid_2x2":
        _render_grid_2x2_template(draw, data)
    elif template == "grid_3x1":
        _render_grid_3x1_template(draw, data)
    elif template == "data_big":
        _render_data_big_template(draw, data)
    elif template == "step_list":
        _render_step_list_template(draw, data)
    elif template == "cta":
        _render_cta_template(draw, data)
    else:
        _render_data_big_template(draw, data)

    # 6. 保存为PNG
    img = img.convert("RGB")
    img.save(output_path, "PNG")
    print(f"    幻灯片已保存: {output_path}")


def _draw_title_bar(draw: ImageDraw.Draw, title_text: str):
    """绘制顶部标题栏"""
    # 背景条
    draw.rectangle(
        [0, 0, VIDEO_WIDTH, LAYOUT["title_bar_height"]],
        fill=COLORS["bg_primary"] + (200,)
    )

    # 标题文字
    font = _get_font("subtitle")
    bbox = draw.textbbox((0, 0), title_text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (VIDEO_WIDTH - text_width) // 2
    y = (LAYOUT["title_bar_height"] - 48) // 2
    draw.text((x, y), title_text, fill=COLORS["text_primary"], font=font)


def _render_title_template(draw: ImageDraw.Draw, data: dict):
    """渲染标题模板 - 居中大字 + 副标题"""
    headline = data.get("headline", "")
    subtitle = data.get("subtitle", "")

    # 标题
    font_title = _get_font("title")
    bbox = draw.textbbox((0, 0), headline, font=font_title)
    text_width = bbox[2] - bbox[0]
    x = (VIDEO_WIDTH - text_width) // 2
    y = VIDEO_HEIGHT // 2 - 100
    draw.text((x, y), headline, fill=COLORS["accent_gold"], font=font_title)

    # 副标题
    if subtitle:
        font_subtitle = _get_font("subtitle")
        bbox = draw.textbbox((0, 0), subtitle, font=font_subtitle)
        text_width = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - text_width) // 2
        y = VIDEO_HEIGHT // 2 + 50
        draw.text((x, y), subtitle, fill=COLORS["text_primary"], font=font_subtitle)

    # 装饰线
    line_y = VIDEO_HEIGHT // 2 + 120
    draw.rectangle(
        [VIDEO_WIDTH // 2 - 100, line_y, VIDEO_WIDTH // 2 + 100, line_y + 4],
        fill=COLORS["accent_blue"]
    )


def _render_grid_2x2_template(draw: ImageDraw.Draw, data: dict):
    """渲染四宫格模板"""
    items = data.get("items", [])
    headline = data.get("headline", "")

    # 标题
    if headline:
        font = _get_font("subtitle")
        bbox = draw.textbbox((0, 0), headline, font=font)
        text_width = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - text_width) // 2
        draw.text((x, 140), headline, fill=COLORS["text_primary"], font=font)

    # 计算网格位置
    margin = LAYOUT["margin"]
    gap = LAYOUT["card_gap"]
    card_width = (VIDEO_WIDTH - 2 * margin - gap) // 2
    card_height = (VIDEO_HEIGHT - LAYOUT["title_bar_height"] - LAYOUT["subtitle_bar_height"] - 200 - gap) // 2

    positions = [
        (margin, 220),
        (margin + card_width + gap, 220),
        (margin, 220 + card_height + gap),
        (margin + card_width + gap, 220 + card_height + gap),
    ]

    for i, (x, y) in enumerate(positions):
        if i < len(items):
            item = items[i]
            _draw_card(draw, x, y, card_width, card_height, item.get("title", ""), item.get("desc", ""))


def _render_grid_3x1_template(draw: ImageDraw.Draw, data: dict):
    """渲染三列模板（绿/黄/红三区）"""
    items = data.get("items", [])
    headline = data.get("headline", "")

    # 标题
    if headline:
        font = _get_font("subtitle")
        bbox = draw.textbbox((0, 0), headline, font=font)
        text_width = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - text_width) // 2
        draw.text((x, 140), headline, fill=COLORS["text_primary"], font=font)

    # 计算列位置
    margin = LAYOUT["margin"]
    gap = LAYOUT["card_gap"]
    card_width = (VIDEO_WIDTH - 2 * margin - 2 * gap) // 3
    card_height = VIDEO_HEIGHT - LAYOUT["title_bar_height"] - LAYOUT["subtitle_bar_height"] - 200

    colors = [COLORS["success"], COLORS["warning"], COLORS["danger"]]

    for i in range(3):
        x = margin + i * (card_width + gap)
        y = 220
        color = colors[i % len(colors)]

        if i < len(items):
            item = items[i]
            _draw_colored_card(draw, x, y, card_width, card_height,
                             item.get("title", ""), item.get("desc", ""), color)


def _render_data_big_template(draw: ImageDraw.Draw, data: dict):
    """渲染数据突出模板"""
    headline = data.get("headline", "")
    stats = data.get("stats", [])

    # 标题
    if headline:
        font = _get_font("subtitle")
        bbox = draw.textbbox((0, 0), headline, font=font)
        text_width = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - text_width) // 2
        draw.text((x, 140), headline, fill=COLORS["text_primary"], font=font)

    # 数据
    if stats:
        font_data = _get_font("data_big")
        font_label = _get_font("body")

        for i, stat in enumerate(stats):
            value = stat.get("value", "")
            label = stat.get("label", "")
            color_name = stat.get("color", "accent_blue")
            color = COLORS.get(color_name, COLORS["accent_blue"])

            # 计算位置（水平排列）
            total_width = len(stats) * 400
            start_x = (VIDEO_WIDTH - total_width) // 2
            x = start_x + i * 400
            y = VIDEO_HEIGHT // 2 - 50

            # 大数字
            bbox = draw.textbbox((0, 0), value, font=font_data)
            text_width = bbox[2] - bbox[0]
            draw.text((x + (400 - text_width) // 2, y), value, fill=color, font=font_data)

            # 标签
            bbox = draw.textbbox((0, 0), label, font=font_label)
            text_width = bbox[2] - bbox[0]
            draw.text((x + (400 - text_width) // 2, y + 120), label, fill=COLORS["text_secondary"], font=font_label)


def _render_step_list_template(draw: ImageDraw.Draw, data: dict):
    """渲染步骤列表模板"""
    headline = data.get("headline", "")
    steps = data.get("steps", [])

    # 标题
    if headline:
        font = _get_font("subtitle")
        bbox = draw.textbbox((0, 0), headline, font=font)
        text_width = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - text_width) // 2
        draw.text((x, 140), headline, fill=COLORS["text_primary"], font=font)

    # 步骤
    if steps:
        font_step = _get_font("step_number")
        font_text = _get_font("body")

        step_height = 120
        start_y = 250

        for i, step in enumerate(steps):
            y = start_y + i * (step_height + 40)

            # 步骤编号（圆形背景）
            circle_x = VIDEO_WIDTH // 2 - 300
            circle_y = y + 10
            draw.ellipse(
                [circle_x, circle_y, circle_x + 60, circle_y + 60],
                fill=COLORS["accent_blue"]
            )
            draw.text((circle_x + 15, circle_y + 5), str(i + 1),
                     fill=COLORS["text_primary"], font=font_step)

            # 步骤文字
            draw.text((VIDEO_WIDTH // 2 - 200, y + 15), step,
                     fill=COLORS["text_primary"], font=font_text)

            # 连接线（除了最后一步）
            if i < len(steps) - 1:
                line_y = y + step_height
                draw.rectangle(
                    [circle_x + 28, line_y, circle_x + 32, line_y + 40],
                    fill=COLORS["divider"]
                )


def _render_cta_template(draw: ImageDraw.Draw, data: dict):
    """渲染CTA模板"""
    headline = data.get("headline", "评论区留言")
    subtitle = data.get("subtitle", "免费咨询")

    # 标题
    font_title = _get_font("title")
    bbox = draw.textbbox((0, 0), headline, font=font_title)
    text_width = bbox[2] - bbox[0]
    x = (VIDEO_WIDTH - text_width) // 2
    y = VIDEO_HEIGHT // 2 - 100
    draw.text((x, y), headline, fill=COLORS["accent_gold"], font=font_title)

    # 副标题
    if subtitle:
        font_subtitle = _get_font("subtitle")
        bbox = draw.textbbox((0, 0), subtitle, font=font_subtitle)
        text_width = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - text_width) // 2
        y = VIDEO_HEIGHT // 2 + 50
        draw.text((x, y), subtitle, fill=COLORS["text_primary"], font=font_subtitle)


def _draw_card(draw: ImageDraw.Draw, x: int, y: int, w: int, h: int,
               title: str, desc: str):
    """绘制卡片"""
    # 卡片背景
    draw.rounded_rectangle(
        [x, y, x + w, y + h],
        radius=LAYOUT["card_radius"],
        fill=COLORS["bg_card"],
        outline=COLORS["divider"],
        width=2
    )

    # 标题
    font_title = _get_font("card_title")
    draw.text((x + LAYOUT["card_padding"], y + LAYOUT["card_padding"]),
             title, fill=COLORS["accent_blue"], font=font_title)

    # 描述
    if desc:
        font_desc = _get_font("card_desc")
        draw.text((x + LAYOUT["card_padding"], y + LAYOUT["card_padding"] + 50),
                 desc, fill=COLORS["text_secondary"], font=font_desc)


def _draw_colored_card(draw: ImageDraw.Draw, x: int, y: int, w: int, h: int,
                       title: str, desc: str, color: tuple):
    """绘制带颜色的卡片"""
    # 卡片背景
    draw.rounded_rectangle(
        [x, y, x + w, y + h],
        radius=LAYOUT["card_radius"],
        fill=COLORS["bg_card"],
        outline=color,
        width=3
    )

    # 顶部色条
    draw.rectangle(
        [x, y, x + w, y + 8],
        fill=color
    )

    # 标题
    font_title = _get_font("card_title")
    draw.text((x + LAYOUT["card_padding"], y + LAYOUT["card_padding"] + 20),
             title, fill=color, font=font_title)

    # 描述
    if desc:
        font_desc = _get_font("card_desc")
        draw.text((x + LAYOUT["card_padding"], y + LAYOUT["card_padding"] + 70),
                 desc, fill=COLORS["text_secondary"], font=font_desc)


def _get_font(font_type: str) -> ImageFont.FreeTypeFont:
    """获取字体"""
    try:
        font_config = FONTS.get(font_type, FONTS["body"])
        return ImageFont.truetype(FONT_PATH, font_config["size"])
    except Exception as e:
        print(f"  ⚠ 字体加载失败: {e}，使用默认字体")
        return ImageFont.load_default()


if __name__ == "__main__":
    # 测试
    test_data = {
        "template": "title",
        "data": {
            "headline": "测试标题",
            "subtitle": "测试副标题"
        }
    }
    render_slide(test_data, None, "/tmp/test_slide.png", "测试顶部标题")
```

- [ ] **Step 2: 验证幻灯片渲染器**

```bash
cd pipeline
python -c "from slide_renderer import render_slide; print('幻灯片渲染器模块导入成功')"
```

- [ ] **Step 3: 测试渲染**

```bash
cd pipeline
python -c "
from slide_renderer import render_slide
test_data = {
    'template': 'title',
    'data': {
        'headline': '光伏最大坑',
        'subtitle': '先施工、后手续！'
    }
}
render_slide(test_data, None, '/tmp/test_render.png', '光伏前期手续')
print('渲染测试完成')
"
ls -la /tmp/test_render.png
```

- [ ] **Step 4: Commit**

```bash
git add pipeline/slide_renderer.py
git commit -m "feat: 创建幻灯片渲染器 - 6种模板类型，Pillow渲染"
```

---

## Task 7: 删除冗余文件

**Files:**
- Delete: `pipeline/video_renderer.py`

- [ ] **Step 1: 删除 video_renderer.py**

```bash
rm pipeline/video_renderer.py
```

- [ ] **Step 2: Commit**

```bash
git rm pipeline/video_renderer.py
git commit -m "chore: 删除冗余的video_renderer.py"
```

---

## Task 8: 更新视频合成器

**Files:**
- Modify: `pipeline/video_generator.py`

- [ ] **Step 1: 读取当前 video_generator.py**

```bash
cat pipeline/video_generator.py
```

- [ ] **Step 2: 更新 video_generator.py**

替换整个文件内容：

```python
"""视频生成器 - 将图片、音频、字幕合成为最终视频"""

import os
import subprocess
from config import VIDEO_WIDTH, VIDEO_HEIGHT, FPS, BGM_DIR, DEFAULT_BGM


def _get_ffmpeg():
    """获取ffmpeg路径"""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except:
        pass
    for p in ["/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg"]:
        if os.path.exists(p):
            return p
    return "ffmpeg"


def _get_duration(ffmpeg, path):
    """获取媒体时长"""
    r = subprocess.run([ffmpeg, "-i", path, "-f", "null", "-"],
                       capture_output=True, text=True)
    for line in r.stderr.split("\n"):
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = parts.split(":")
            return float(h)*3600 + float(m)*60 + float(s)
    return 0.0


def render_video(slides: list, audio_path: str, output_path: str,
                srt_path: str = None, bgm_path: str = None) -> str:
    """
    渲染最终视频

    Args:
        slides: 幻灯片列表 [{"path": ..., "duration_sec": float}]
        audio_path: 完整音频路径
        output_path: 输出视频路径
        srt_path: 可选的字幕文件路径
        bgm_path: 可选的BGM路径

    Returns:
        输出视频路径
    """
    ffmpeg = _get_ffmpeg()
    work_dir = os.path.dirname(output_path)

    # Step 1: 为每个幻灯片创建视频片段
    segment_files = []
    for i, slide in enumerate(slides):
        seg_path = os.path.join(work_dir, f"_seg_{i:03d}.mp4")
        _create_segment(ffmpeg, slide["path"], seg_path, slide["duration_sec"])
        if os.path.exists(seg_path) and os.path.getsize(seg_path) > 0:
            segment_files.append(seg_path)

    if not segment_files:
        raise RuntimeError("没有生成任何视频片段")

    # Step 2: 连接所有片段
    concat_path = os.path.join(work_dir, "_concat_list.txt")
    with open(concat_path, "w") as f:
        for seg in segment_files:
            f.write(f"file '{seg}'\n")

    concat_video = os.path.join(work_dir, "_concat.mp4")
    subprocess.run([
        ffmpeg, "-y", "-f", "concat", "-safe", "0",
        "-i", concat_path,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        concat_video,
    ], capture_output=True)

    # Step 3: 合并音频
    combined = os.path.join(work_dir, "_combined.mp4")
    subprocess.run([
        ffmpeg, "-y",
        "-i", concat_video,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        combined,
    ], capture_output=True)

    # Step 4: 混入BGM（如果有）
    if bgm_path and os.path.exists(bgm_path):
        with_bgm = os.path.join(work_dir, "_with_bgm.mp4")
        subprocess.run([
            ffmpeg, "-y",
            "-i", combined,
            "-i", bgm_path,
            "-filter_complex", "[1:a]volume=0.15[bg];[0:a][bg]amix=inputs=2:duration=first",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            with_bgm,
        ], capture_output=True)
        if os.path.exists(with_bgm) and os.path.getsize(with_bgm) > 0:
            os.remove(combined)
            combined = with_bgm

    # Step 5: 烧录字幕（如果可用）
    if srt_path and os.path.exists(srt_path) and os.path.getsize(srt_path) > 0:
        # 将SRT转换为ASS以获得更好的样式
        ass_path = _srt_to_styled_ass(srt_path, work_dir)
        if ass_path:
            result = subprocess.run([
                ffmpeg, "-y",
                "-i", combined,
                "-vf", f"ass={ass_path}",
                "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                "-c:a", "copy",
                output_path,
            ], capture_output=True)
            if result.returncode == 0:
                _cleanup(work_dir, segment_files + [concat_path, concat_video, combined, ass_path])
                return output_path

    # 如果字幕烧录失败或没有字幕，直接复制
    import shutil
    shutil.copy2(combined, output_path)
    _cleanup(work_dir, segment_files + [concat_path, concat_video, combined])
    return output_path


def _create_segment(ffmpeg: str, image_path: str, output_path: str,
                    duration: float):
    """创建视频片段"""
    cmd = [
        ffmpeg, "-y",
        "-loop", "1",
        "-i", image_path,
        "-vf", f"fps={FPS},format=yuv420p",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-t", str(duration),
        output_path
    ]
    subprocess.run(cmd, capture_output=True)


def _srt_to_styled_ass(srt_path: str, work_dir: str) -> str:
    """将SRT转换为带样式的ASS字幕"""
    ass_path = os.path.join(work_dir, "_styled.ass")

    try:
        with open(srt_path, "r", encoding="utf-8") as f:
            srt_content = f.read()

        # 解析SRT
        blocks = srt_content.strip().split("\n\n")
        subtitles = []
        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) < 3:
                continue
            time_line = lines[1]
            if "-->" not in time_line:
                continue
            start, end = time_line.split("-->")
            text = " ".join(lines[2:]).strip()
            if text:
                subtitles.append((start.strip(), end.strip(), text))

        # 生成ASS（横屏1920x1080）
        ass_content = """[Script Info]
Title: Douyin Video Subtitles
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Noto Sans CJK SC,60,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,3,1,2,40,40,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        for start, end, text in subtitles:
            # 转换时间格式
            start_ass = _srt_to_ass_time(start)
            end_ass = _srt_to_ass_time(end)
            ass_content += f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{text}\n"

        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(ass_content)

        return ass_path

    except Exception as e:
        print(f"  ⚠ SRT转ASS失败: {e}")
        return None


def _srt_to_ass_time(srt_time: str) -> str:
    """将SRT时间格式转换为ASS时间格式"""
    # SRT: HH:MM:SS,mmm
    # ASS: H:MM:SS.cc
    srt_time = srt_time.replace(",", ".")
    parts = srt_time.split(":")
    h = int(parts[0])
    m = int(parts[1])
    s = float(parts[2])

    # ASS格式
    return f"{h}:{m:02d}:{s:05.2f}"


def _cleanup(work_dir: str, files: list):
    """清理临时文件"""
    for f in files:
        if os.path.exists(f):
            try:
                os.remove(f)
            except:
                pass


if __name__ == "__main__":
    # 测试
    import sys
    if len(sys.argv) < 4:
        print("用法: python video_generator.py <图片目录> <音频文件> <输出视频>")
        sys.exit(1)

    image_dir = sys.argv[1]
    audio_path = sys.argv[2]
    output_path = sys.argv[3]

    # 获取图片列表
    images = sorted([os.path.join(image_dir, f) for f in os.listdir(image_dir)
                    if f.endswith(('.png', '.jpg', '.jpeg'))])

    # 获取音频时长
    ffmpeg = _get_ffmpeg()
    audio_duration = _get_duration(ffmpeg, audio_path)

    # 计算每个图片的时长
    duration_per_image = audio_duration / len(images) if images else 5

    # 创建幻灯片
    slides = [{"path": img, "duration_sec": duration_per_image} for img in images]

    # 渲染视频
    render_video(slides, audio_path, output_path)
    print(f"视频已生成: {output_path}")
```

- [ ] **Step 3: 验证视频合成器**

```bash
cd pipeline
python -c "from video_generator import render_video; print('视频合成器模块导入成功')"
```

- [ ] **Step 4: Commit**

```bash
git add pipeline/video_generator.py
git commit -m "feat: 更新视频合成器 - 横屏、BGM混入、字幕样式"
```

---

## Task 9: 更新主流程

**Files:**
- Modify: `pipeline/pipeline.py`

- [ ] **Step 1: 读取当前 pipeline.py**

```bash
cat pipeline/pipeline.py
```

- [ ] **Step 2: 更新 pipeline.py**

替换整个文件内容：

```python
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
```

- [ ] **Step 3: 验证主流程**

```bash
cd pipeline
python -c "from pipeline import run_pipeline, run_batch; print('主流程模块导入成功')"
```

- [ ] **Step 4: Commit**

```bash
git add pipeline/pipeline.py
git commit -m "feat: 更新主流程 - 批量处理、新的渲染流程"
```

---

## Task 10: 更新运行脚本

**Files:**
- Modify: `pipeline/run_on_walle.sh`

- [ ] **Step 1: 更新 run_on_walle.sh**

替换整个文件内容：

```bash
#!/bin/bash
# 抖音视频生成 - 一键运行脚本（在walle上执行）
# 使用方法: bash run_on_walle.sh

set -e

echo "=========================================="
echo "  抖音视频生成 Pipeline v2"
echo "=========================================="

# 配置
WORK_DIR="/home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/projects/douyin-jianji/pipeline"
VENV_DIR="$WORK_DIR/.venv"
DEMAND_DIR="$WORK_DIR/../demand"

# 检查Python
echo "[1/5] 检查Python环境..."
if ! command -v python3.11 &> /dev/null; then
    echo "❌ Python 3.11未安装"
    exit 1
fi
echo "✅ Python 3.11已安装"

# 创建虚拟环境
echo "[2/5] 创建虚拟环境..."
if [ ! -d "$VENV_DIR" ]; then
    cd "$WORK_DIR"
    python3.11 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    echo "✅ 虚拟环境已创建"
else
    echo "✅ 虚拟环境已存在"
    source "$VENV_DIR/bin/activate"
fi

# 检查环境变量
echo "[3/5] 检查环境变量..."
if [ -z "$MIMO_API_KEY" ]; then
    echo "⚠️  MIMO_API_KEY未设置，将使用默认Key"
    export MIMO_API_KEY="tp-c1kaznnjsvndkjgih8no34aj4530rk5u9ay61pma0eh3qjhb"
fi

# 运行Pipeline（批量处理所有需求）
echo "[4/5] 运行视频生成Pipeline..."
cd "$WORK_DIR"

# 处理所有Excel文件
python pipeline.py "$DEMAND_DIR/douyinwenanjiaoben.xlsx" "$DEMAND_DIR/618.xlsx" --batch

# 检查输出
echo "[5/5] 检查输出文件..."
OUTPUT_DIR="$WORK_DIR/output"
if [ -d "$OUTPUT_DIR" ]; then
    echo "✅ 视频已生成:"
    find "$OUTPUT_DIR" -name "*.mp4" -exec ls -lh {} \;
else
    echo "❌ 视频生成失败"
    exit 1
fi

# 完成
echo "=========================================="
echo "  所有视频生成完成!"
echo "=========================================="
```

- [ ] **Step 2: 添加执行权限**

```bash
chmod +x pipeline/run_on_walle.sh
```

- [ ] **Step 3: Commit**

```bash
git add pipeline/run_on_walle.sh
git commit -m "feat: 更新运行脚本 - 批量处理所有需求"
```

---

## Task 11: 更新依赖文件

**Files:**
- Modify: `pipeline/requirements.txt`

- [ ] **Step 1: 更新 requirements.txt**

```bash
cat > pipeline/requirements.txt << 'EOF'
edge-tts>=6.1.0
openpyxl>=3.1.0
Pillow>=10.0.0
imageio-ffmpeg>=0.4.9
requests>=2.31.0
EOF
```

- [ ] **Step 2: Commit**

```bash
git add pipeline/requirements.txt
git commit -m "chore: 更新依赖文件"
```

---

## Task 12: 完整测试

**Files:**
- Test: 全流程测试

- [ ] **Step 1: 激活虚拟环境**

```bash
cd pipeline
source .venv/bin/activate
```

- [ ] **Step 2: 测试单个脚本**

```bash
python pipeline.py ../demand/douyinwenanjiaoben.xlsx --name 光伏前期手续
```

预期输出：
```
============================================================
  抖音视频生成: 光伏前期手续
============================================================

[1/6] 转换Excel脚本...
  段落数: 5
  目标时长: 约 30 秒

[2/6] 生成TTS音频...
  TTS段落 0: 痛点/悬念 (45字符)
  ...

[3/6] 生成AI背景图...
  生成背景图 0: 痛点/悬念
  ...

[4/6] 渲染幻灯片...
  幻灯片已保存: ...
  ...

[5/6] 渲染视频...
  ...

[6/6] 清理临时文件...

============================================================
  ✅ 完成! (XX.X秒)
  输出: output/光伏前期手续/光伏前期手续.mp4
  大小: X.X MB
============================================================
```

- [ ] **Step 3: 验证输出**

```bash
ls -la output/光伏前期手续/
ffprobe output/光伏前期手续/光伏前期手续.mp4 2>&1 | grep -E "Duration|Stream"
```

预期输出：
```
Duration: 00:00:28.xx
Stream #0:0: Video: h264, yuv420p, 1920x1080
Stream #0:1: Audio: aac
```

- [ ] **Step 4: 测试批量处理**

```bash
python pipeline.py ../demand/douyinwenanjiaoben.xlsx ../demand/618.xlsx --batch
```

- [ ] **Step 5: 最终Commit**

```bash
git add -A
git commit -m "feat: 完成Pipeline v2 - 横屏专业信息图视频生成"
```

---

## 完成清单

- [ ] Task 1: 更新配置文件
- [ ] Task 2: 创建字体和BGM目录
- [ ] Task 3: 更新脚本解析器
- [ ] Task 4: 更新TTS生成器
- [ ] Task 5: 更新AI图片生成器
- [ ] Task 6: 创建幻灯片渲染器
- [ ] Task 7: 删除冗余文件
- [ ] Task 8: 更新视频合成器
- [ ] Task 9: 更新主流程
- [ ] Task 10: 更新运行脚本
- [ ] Task 11: 更新依赖文件
- [ ] Task 12: 完整测试
