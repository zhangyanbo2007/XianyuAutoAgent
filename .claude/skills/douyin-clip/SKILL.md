# 抖音自动切片 Skill

自动从抖音网红视频中提取高光时刻，生成可直接发布的短视频切片。

## 功能

1. **视频下载** — yt-dlp 下载抖音视频（支持登录 cookies）
2. **语音转写** — Whisper 本地模型，输出带时间戳的文本
3. **高光分析** — Claude API 自动识别搞笑/反转/名场面等精彩片段
4. **视频切割** — ffmpeg 精确切割，自动横转竖适配抖音
5. **字幕烧录** — 自动生成并烧录抖音风格字幕

## 快速开始

### 安装依赖

```bash
cd .claude/skills/douyin-clip
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 配置

编辑 `config.yaml`：

1. 填入关注的创作者抖音链接
2. 配置代理（如需外网访问）
3. 设置 Whisper 模型大小

### 使用方式

#### 方式一：完整流水线（推荐）

```bash
cd .claude/skills/douyin-clip
source .venv/bin/activate

# 处理单个视频
python scripts/pipeline.py https://www.douyin.com/video/xxx

# 指定创作者名称（用于分类）
python scripts/pipeline.py https://www.douyin.com/video/xxx -c "洛杉矶小唐"
```

#### 方式二：从本地视频开始

```bash
python scripts/pipeline.py --local /path/to/video.mp4 -c "子安"
```

#### 方式三：从转写结果开始（调试用）

```bash
python scripts/pipeline.py --from-transcript data/transcripts/xxx.json
```

#### 方式四：分步执行

```bash
# Step 1: 下载
python scripts/download.py https://www.douyin.com/video/xxx -c "洛杉矶小唐"

# Step 2: 转写
python scripts/transcribe.py data/downloads/洛杉矶小唐/video.mp4

# Step 3: 分析高光
python scripts/analyze_highlights.py data/transcripts/video.json

# Step 4: 切割
python scripts/clip_video.py data/highlights/video.json

# Step 5: 加字幕
python scripts/add_subtitles.py data/clips/video/01_xxx.mp4 \
    --transcript data/transcripts/video.json \
    --start 15.5 --end 45.2
```

## 输出结构

```
data/
├── downloads/           # 下载的原始视频
│   └── 洛杉矶小唐/
│       └── xxx.mp4
├── transcripts/         # 转写结果（JSON）
│   └── xxx.json
├── highlights/          # 高光分析结果
│   └── xxx.json
└── clips/               # 最终切片成品
    └── xxx/
        ├── 01_搞笑反转.mp4
        ├── 02_名场面.mp4
        └── ...
```

## 高光识别标准

AI 分析时按以下优先级选择片段：

1. **搞笑/反转** — 有笑点、意外反转
2. **名场面** — 金句、情绪爆发点
3. **完整故事** — 有起因-经过-结果
4. **互动高潮** — 可能引发弹幕讨论
5. **视觉冲击** — 从文字推断有精彩画面

## 配置说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `clip.min_duration` | 最短切片时长（秒） | 15 |
| `clip.max_duration` | 最长切片时长（秒） | 60 |
| `clip.target_width` | 目标宽度（竖屏） | 1080 |
| `clip.target_height` | 目标高度（竖屏） | 1920 |
| `whisper.model_size` | Whisper 模型 | medium |
| `highlight.max_clips_per_video` | 每视频最多切片数 | 8 |

## 注意事项

- 抖音下载可能需要 cookies 认证（用 `--cookies` 参数）
- Whisper medium 模型转写 1 分钟视频约需 30 秒
- Claude API 分析费用约 ¥0.01/分钟视频
- 竖屏适配：横屏视频会自动裁剪为 9:16
- 输出视频使用 H.264 编码，适配抖音上传

## 文件说明

| 文件 | 功能 |
|------|------|
| `pipeline.py` | 主流程管道，串联所有步骤 |
| `download.py` | 视频下载 |
| `transcribe.py` | Whisper 语音转写 |
| `analyze_highlights.py` | AI 高光时刻分析 |
| `clip_video.py` | 视频切割 |
| `add_subtitles.py` | 字幕生成与烧录 |
| `config.yaml` | 配置文件 |
