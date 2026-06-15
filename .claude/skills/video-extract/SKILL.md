---
name: video-extract
description: 从视频文件提取音频并进行语音识别(ASR)转文字，支持OpenAI Whisper API和本地whisper模型。
---

# 视频音频文字提取

从视频文件中提取音频并进行语音识别。

## 核心规则

1. **隐私文件不进 git** — 提取的内容属于隐私数据
2. **输出位置** — 默认保存在视频同目录

## 环境

- **Python**: `.claude/skills/video-extract/.venv/bin/python`
- **ffmpeg**: `.claude/skills/video-extract/ffmpeg` (静态编译版，已内置)
- **依赖**: moviepy (音频提取), openai-whisper (语音识别)

## 使用方法

### 基础命令

```bash
# 提取音频和文字 (默认使用whisper medium模型)
.claude/skills/video-extract/.venv/bin/python .claude/skills/video-extract/scripts/extract_audio_text.py <视频路径>

# 只提取音频，不转文字
.claude/skills/video-extract/.venv/bin/python .claude/skills/video-extract/scripts/extract_audio_text.py <视频路径> --audio-only

# 指定输出目录
.claude/skills/video-extract/.venv/bin/python .claude/skills/video-extract/scripts/extract_audio_text.py <视频路径> -o <输出目录>
```

### 模型选择

```bash
# tiny - 最快，准确度一般
.claude/skills/video-extract/.venv/bin/python .claude/skills/video-extract/scripts/extract_audio_text.py <视频路径> --model tiny

# base - 快速，比tiny好一点
.claude/skills/video-extract/.venv/bin/python .claude/skills/video-extract/scripts/extract_audio_text.py <视频路径> --model base

# small - 中等速度和准确度
.claude/skills/video-extract/.venv/bin/python .claude/skills/video-extract/scripts/extract_audio_text.py <视频路径> --model small

# medium - 较慢，更准确（推荐）
.claude/skills/video-extract/.venv/bin/python .claude/skills/video-extract/scripts/extract_audio_text.py <视频路径> --model medium

# large - 最慢，最准确
.claude/skills/video-extract/.venv/bin/python .claude/skills/video-extract/scripts/extract_audio_text.py <视频路径> --model large
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `video` | 视频文件路径 | 必填 |
| `-o, --output-dir` | 输出目录 | 视频同目录 |
| `--audio-only` | 只提取音频 | false |
| `--model` | whisper模型大小 | medium |

## 输出文件

```
<视频同目录>/
  <视频名>.wav    ← 音频文件 (16kHz, 单声道)
  <视频名>.txt    ← 识别的文字内容
```

## 示例

### 处理红鸟挑战营视频

```bash
.venv/bin/python3.11 .claude/skills/video-extract/scripts/extract_audio_text.py \
  "refs/refs-people/小王子/红鸟挑战营/相关视频/file_v3_0012b_80f7e4d3-1ef0-4736-a4a5-cbd8117128ag.mp4"
```

### 批量处理目录下所有视频

```bash
for f in refs/红鸟挑战营/*.mp4; do
  .venv/bin/python3.11 .claude/skills/video-extract/scripts/extract_audio_text.py "$f"
done
```

## 已知限制

1. **ffmpeg依赖** — 需要系统安装ffmpeg
2. **API费用** — OpenAI Whisper API 按分钟计费
3. **本地模型** — 需要额外安装 openai-whisper 和足够显存
4. **长视频** — API有25MB文件大小限制，超长视频需分段
