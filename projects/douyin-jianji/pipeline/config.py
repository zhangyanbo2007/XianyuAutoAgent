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
