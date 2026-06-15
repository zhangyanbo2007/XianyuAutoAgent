# 抖音视频生成 Pipeline v2 设计文档

## 概述

将现有竖屏视频生成 pipeline 升级为横屏专业信息图视频，对齐参考视频的**视觉风格**（配色、布局、信息图样式），但视频时长保持脚本原始长度。

### 目标

- 输出格式：横屏 1920×1080 (16:9)
- 视频时长：保持脚本原始时长（28-32 秒）
- 视觉风格：专业信息图 + AI 背景图 + 代码渲染文字（对齐参考视频风格）
- 制作成本：~3 元/视频（TTS 1 元 + AI 图 2 元）
- 批量处理：支持多脚本批量生成

### 需求清单

| 需求文件 | 脚本 | 时长 | 参考视频 |
|----------|------|------|----------|
| douyinwenanjiaoben.xlsx | 《光伏前期手续》 | 28秒 | 山东光伏新政 (131秒) |
| 618.xlsx | 《618光伏新政1》 | 28-32秒 | 618光伏新政 (118秒) |
| 618.xlsx | 《618光伏新政2》 | 28-32秒 | 同上 |
| 618.xlsx | 《618光伏新政3》 | 28-32秒 | 同上 |

### 参考视频分析（仅视觉风格参考）

| 视频 | 时长 | 分辨率 | 码率 |
|------|------|--------|------|
| 山东光伏新政 | 131秒 | 816×544 | 259 kb/s |
| 618光伏新政 | 118秒 | 864×576 | 273 kb/s |

**视觉风格提取（用于设计我们的幻灯片）：**
1. 顶部固定标题栏（全程不变）
2. 深色渐变背景（深青蓝 #1a2332）
3. 专业信息图卡片（带图标、色块、数据可视化）
4. 底部字幕条（独立区域，大号白色字幕）
5. 每 5-8 秒切换一张幻灯片
6. 真实照片 + 图表 + 图标混排
7. 结尾 CTA 引导

### 参考视频分析

| 视频 | 时长 | 分辨率 | 码率 |
|------|------|--------|------|
| 山东光伏新政 | 131秒 | 816×544 | 259 kb/s |
| 618光伏新政 | 118秒 | 864×576 | 273 kb/s |

**共同视觉元素：**
1. 顶部固定标题栏（全程不变）
2. 深色渐变背景（深青蓝 #1a2332）
3. 专业信息图卡片（带图标、色块、数据可视化）
4. 底部字幕条（独立区域，大号白色字幕）
5. 每 5-8 秒切换一张幻灯片
6. 真实照片 + 图表 + 图标混排
7. 结尾 CTA 引导

---

## 架构设计

### 数据流

```
Excel脚本 → 脚本解析 → 段落展开 → TTS生成 → AI背景图生成 → 幻灯片合成 → 视频渲染
                          ↓           ↓            ↓              ↓            ↓
                     多段落结构    MiMo TTS    wanx2.1 API    Pillow叠加   FFmpeg合成
                                                                    ↓
                                                              字幕 + BGM
```

### 模块职责

| 模块 | 文件 | 职责 |
|------|------|------|
| 配置 | `config.py` | 分辨率、颜色、字体、API Key |
| 脚本解析 | `script_converter.py` | Excel → JSON，展开为多幻灯片结构 |
| TTS 生成 | `tts_generator.py` | MiMo TTS，生成音频 + 字幕 |
| AI 图片生成 | `ai_image_generator.py` | Dashscope wanx2.1 生成背景图 |
| 幻灯片渲染 | `slide_renderer.py` | Pillow 叠加文字/卡片到背景图 |
| 视频合成 | `video_generator.py` | FFmpeg 合成最终视频 |
| 主流程 | `pipeline.py` | 串联所有模块 |

---

## 详细设计

### 1. 配置系统 (`config.py`)

```python
# 视频参数
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30

# 色彩体系
COLORS = {
    "bg_primary": "#1a2332",      # 主背景
    "bg_card": "#243447",         # 卡片背景
    "accent_blue": "#00d4ff",     # 高亮蓝
    "accent_gold": "#ffd700",     # 强调金
    "success": "#4caf50",         # 成功绿
    "warning": "#ff9800",         # 警告橙
    "danger": "#f44336",          # 危险红
    "text_primary": "#ffffff",    # 主文字
    "text_secondary": "#b0bec5",  # 次文字
    "divider": "#37474f",         # 分隔线
}

# 字体配置
FONTS = {
    "title": {"size": 72, "weight": "bold"},
    "subtitle": {"size": 48, "weight": "regular"},
    "body": {"size": 36, "weight": "regular"},
    "data_big": {"size": 96, "weight": "bold"},
    "subtitle_bar": {"size": 60, "weight": "bold"},
}

# 布局
LAYOUT = {
    "margin": 60,
    "title_bar_height": 100,
    "subtitle_bar_height": 120,
    "card_padding": 32,
    "card_gap": 24,
    "card_radius": 16,
}

# API 配置
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
MIMO_API_KEY = os.environ.get("MIMO_API_KEY", "")
```

### 2. 脚本解析器 (`script_converter.py`)

**输入：** Excel 脚本（如 douyinwenanjiaoben.xlsx）

**输出：** JSON 结构，每段对应 1 张幻灯片（不扩写）

```json
{
  "title": "光伏前期手续",
  "duration": "28s",
  "sections": [
    {
      "id": 0,
      "time_range": "0-3s",
      "type": "title",
      "label": "痛点/悬念",
      "text": "装光伏不懂流程？装完不给并网、一分钱收益都拿不到！",
      "visual": "光伏最大坑：先施工、后手续！",
      "duration_sec": 3.0,
      "slide": {
        "template": "title",
        "data": {
          "headline": "光伏最大坑",
          "subtitle": "先施工、后手续！",
          "bg_prompt": "solar panel installation mistake, warning sign, dramatic lighting"
        }
      }
    },
    {
      "id": 1,
      "time_range": "3-10s",
      "type": "explanation",
      "label": "核心新规科普",
      "text": "记住！家用光伏必须先办手续、再施工...",
      "visual": "正确顺序：备案 → 施工 → 并网",
      "duration_sec": 7.0,
      "slide": {
        "template": "step_list",
        "data": {
          "headline": "正确顺序",
          "steps": ["备案", "施工", "并网"],
          "bg_prompt": "solar permit process flow, modern infographic"
        }
      }
    }
  ]
}
```

**解析逻辑：**

```python
def convert_excel_to_script(excel_path: str) -> dict:
    """
    解析 Excel 脚本，每段生成 1 张幻灯片

    规则：
    1. 读取 Excel 中的每个时间段行
    2. 根据内容关键词推断幻灯片模板类型
    3. 从视觉描述中提取 AI 图片提示词
    4. 保持原始时长不变
    """
```

**模板类型推断（根据内容关键词）：**
- "痛点"/"悬念"/"坑" → `title` 模板
- "顺序"/"流程"/"步骤" → `step_list` 模板
- "材料"/"清单"/"必备" → `grid_2x2` 模板
- "渠道"/"办理"/"申请" → `grid_2x2` 模板
- "引导"/"评论"/"关注" → `cta` 模板
- 其他 → `data_big` 模板

### 3. AI 图片生成器 (`ai_image_generator.py`)

**职责：** 为每张幻灯片生成背景图

**API：** Dashscope wanx2.1-t2i-turbo

**提示词模板：**

```python
BG_PROMPTS = {
    "title": (
        "Professional dark tech background with {topic} theme, "
        "subtle green energy waves, cinematic lighting, "
        "modern corporate style, 16:9 aspect ratio"
    ),
    "data": (
        "Industrial {topic} scene, aerial view, "
        "professional photography, dark blue tone, "
        "subtle light effects, 16:9 aspect ratio"
    ),
    "comparison": (
        "Modern {topic} infrastructure, "
        "clean professional background, "
        "dark gradient with accent lighting, 16:9 aspect ratio"
    ),
    "process": (
        "Step-by-step {topic} flow, "
        "professional infographic style, "
        "dark background with highlights, 16:9 aspect ratio"
    ),
    "cta": (
        "Professional {topic} consultation scene, "
        "trustworthy and reliable mood, "
        "warm accent lighting, 16:9 aspect ratio"
    ),
}
```

**生成流程：**
1. 根据幻灯片类型选择提示词模板
2. 填入主题关键词（如"光伏"、"储能"）
3. 调用 Dashscope API 生成图片
4. 缓存到 `_ai_images/` 目录（MD5 命名）
5. 返回本地路径

**尺寸：** 1920×1080（与视频一致）

### 4. 幻灯片渲染器 (`slide_renderer.py`)

**职责：** 在 AI 背景图上叠加文字、卡片、图标

**渲染流程：**

```python
def render_slide(slide_data: dict, bg_image_path: str, output_path: str):
    """
    渲染单张幻灯片

    1. 加载 AI 背景图
    2. 叠加半透明深色遮罩（保证文字可读）
    3. 渲染顶部标题栏
    4. 根据模板类型渲染内容区域
    5. 渲染底部字幕条（可选）
    6. 保存为 PNG
    """
```

**模板实现：**

| 模板 | 渲染逻辑 |
|------|----------|
| `title` | 居中大字 + 副标题 + 装饰线 |
| `grid_2x2` | 四宫格卡片（2×2 网格） |
| `grid_3x1` | 三列卡片（绿/黄/红） |
| `data_big` | 左侧图标 + 右侧大数字 |
| `step_list` | 左侧步骤编号 + 右侧说明文字 |
| `cta` | 居中引导语 + 底部互动提示 |

**卡片渲染：**

```python
def draw_card(draw, x, y, w, h, bg_color, border_color=None):
    """绘制圆角矩形卡片"""
    # 1. 绘制背景
    draw.rounded_rectangle(
        [x, y, x+w, y+h],
        radius=CARD_RADIUS,
        fill=bg_color,
        outline=border_color
    )
    # 2. 绘制内容（标题、正文、图标）
```

**图标绘制：**

用 Pillow 绘制简单几何图形：

```python
def draw_icon(draw, icon_type, x, y, size, color):
    """绘制简单图标"""
    if icon_type == "check":
        # 绿色圆形 + 白色对勾
        draw.ellipse([x, y, x+size, y+size], fill=COLORS["success"])
        draw.text((x+size//4, y+size//4), "✓", fill="white")
    elif icon_type == "warning":
        # 黄色三角形 + 感叹号
        # ...
    elif icon_type == "battery":
        # 电池形状
        # ...
```

### 5. TTS 生成器 (`tts_generator.py`)

**简化：** 仅保留 MiMo TTS + edge-tts fallback

**输入：** 段落文本列表

**输出：** 
- 每段音频文件（section_00.mp3, section_01.mp3, ...）
- 合并音频（narration.mp3）
- 字幕文件（narration.srt）

**字幕生成优化：**
- 按中文标点分割句子
- 根据字符数比例分配时间
- 输出 SRT 格式

### 6. 视频合成器 (`video_generator.py`)

**改造：**
- 分辨率：1920×1080
- 转场效果：幻灯片间淡入淡出
- BGM：混入背景音乐

**FFmpeg 命令：**

```bash
# 1. 每张幻灯片生成视频片段
ffmpeg -loop 1 -i slide_00.png -t 5.0 -vf "fps=30" -c:v libx264 seg_00.mp4

# 2. 连接所有片段（带转场）
ffmpeg -f concat -i list.txt -c:v libx264 concat.mp4

# 3. 合并音频
ffmpeg -i concat.mp4 -i narration.mp3 -c:v copy -c:a aac combined.mp4

# 4. 混入 BGM
ffmpeg -i combined.mp4 -i bgm.mp3 -filter_complex "[1:a]volume=0.2[bg];[0:a][bg]amix" final.mp4

# 5. 烧录字幕
ffmpeg -i final.mp4 -vf "ass=subtitle.ass" output.mp4
```

**字幕样式（ASS）：**

```ass
[V4+ Styles]
Style: Default,Noto Sans CJK SC,60,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,3,1,2,40,40,80,1
```

### 7. 主流程 (`pipeline.py`)

```python
def run_pipeline(excel_path: str, output_name: str = None):
    """
    单个脚本处理流程：

    1. 解析 Excel → JSON（每段 1 张幻灯片）
    2. 生成 TTS 音频
    3. 为每张幻灯片生成 AI 背景图
    4. 渲染幻灯片（叠加文字/卡片）
    5. 合成视频（幻灯片 + 音频 + 字幕 + BGM）
    """

def run_batch(excel_paths: list):
    """
    批量处理多个 Excel 脚本

    支持：
    - 单个 Excel 包含多个脚本（如 618.xlsx 有 3 个）
    - 多个 Excel 文件
    """
```

---

## 文件结构

```
pipeline/
├── config.py                  # 配置
├── script_converter.py        # 脚本解析（改造）
├── tts_generator.py           # TTS（简化）
├── ai_image_generator.py      # AI 图片生成（新建）
├── slide_renderer.py          # 幻灯片渲染（新建）
├── video_generator.py         # 视频合成（改造）
├── pipeline.py                # 主流程（改造）
├── slide_templates/           # 模板配置（新建）
│   ├── title.json
│   ├── grid_2x2.json
│   ├── grid_3x1.json
│   ├── data_big.json
│   ├── step_list.json
│   └── cta.json
├── bgm/                       # 背景音乐
│   └── default.mp3
├── fonts/                     # 字体
│   └── NotoSansCJKsc-Regular.otf
└── requirements.txt           # 依赖更新
```

---

## 依赖更新

```
edge-tts>=6.1.0
openpyxl>=3.1.0
Pillow>=10.0.0
imageio-ffmpeg>=0.4.9
requests>=2.31.0
```

无需新增依赖，现有依赖已覆盖所有功能。

---

## 成本估算

| 项目 | 单价 | 数量 | 总计 |
|------|------|------|------|
| TTS (MiMo) | ~1元 | 1 | 1元 |
| AI 背景图 (wanx2.1) | ~0.3元 | 5-6张 | 1.5-2元 |
| **合计** | | | **~3元/视频** |

**批量成本（4 个视频）：** ~12 元

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Dashscope API 不可用 | 无法生成背景图 | 缓存已生成图片；fallback 到纯色背景 |
| MiMo TTS 失败 | 无配音 | fallback 到 edge-tts |
| 字体缺失 | 文字渲染异常 | 预置字体文件到 fonts/ 目录 |
| 单个 Excel 多脚本解析失败 | 部分视频无法生成 | 逐个脚本处理，失败跳过继续 |
| 批量处理时间过长 | 用户等待 | 缓存机制；可中断恢复 |

---

## 验收标准

1. 输出视频为 1920×1080 横屏格式
2. 视频时长保持脚本原始时长（28-32 秒）
3. 每段对应 1 张信息图幻灯片（共 5-6 张）
4. 所有幻灯片风格统一（色彩、字体、布局）
5. 顶部标题栏全程不变
6. 底部字幕条随配音滚动
7. TTS 配音清晰自然
8. BGM 音量适中（不压配音）
9. 制作成本 ≤5 元/视频
10. 支持批量处理多个脚本
