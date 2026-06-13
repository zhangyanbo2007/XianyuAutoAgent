"""Video pipeline configuration."""

import os

# Load .env file from privacy-engineering root
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

# LLM API (OpenAI-compatible)
API_BASE_URL = "https://token-plan-cn.xiaomimimo.com/v1"
API_KEY = os.environ.get("MIMO_API_KEY", "tp-c1kaznnjsvndkjgih8no34aj4530rk5u9ay61pma0eh3qjhb")
LLM_MODEL = "mimo-v2.5-pro"

# TTS
TTS_VOICE = "zh-CN-XiaoxiaoNeural"  # 女声，清晰自然
TTS_RATE = "+0%"  # 语速调整

# Video
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30
BG_COLOR = "#0f172a"  # 深蓝黑背景
TEXT_COLOR = "#e2e8f0"  # 浅灰文字
ACCENT_COLOR = "#38bdf8"  # 亮蓝高亮
TITLE_COLOR = "#f8fafc"  # 纯白标题

# Paths
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(PROJECT_DIR, "output")
DATA_DIR = os.path.join(os.path.dirname(PROJECT_DIR), "data")
