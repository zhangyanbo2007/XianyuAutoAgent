# 抖音视频生成Pipeline

## TTS解决方案

### 方案一：小米MiMo TTS（推荐）

```python
import os, requests, base64, subprocess

MIMO_API_KEY = os.environ["MIMO_API_KEY"]
MIMO_TTS_BASE = "https://token-plan-cn.xiaomimimo.com/v1"

headers = {
    "Authorization": f"Bearer {MIMO_API_KEY}",
    "Content-Type": "application/json",
}

payload = {
    "model": "mimo-v2.5-tts",
    "messages": [
        {"role": "user", "content": "用科普博主的语气，自然流畅地朗读以下内容"},
        {"role": "assistant", "content": "要合成的文本"}
    ],
    "audio": {"format": "wav", "voice": "苏打"},
}

resp = requests.post(f"{MIMO_TTS_BASE}/chat/completions", headers=headers, json=payload, timeout=60)
data = resp.json()
audio_b64 = data["choices"][0]["message"]["audio"]["data"]
audio_bytes = base64.b64decode(audio_b64)

# 保存为WAV
with open("output.wav", "wb") as f:
    f.write(audio_bytes)

# 用ffmpeg转MP3
subprocess.run(["ffmpeg", "-y", "-i", "output.wav", "-c:a", "libmp3lame", "-q:a", "2", "output.mp3"])
```

### 方案二：阿里云百炼TTS

```python
from dashscope.audio.tts_v2 import SpeechSynthesizer, AudioFormat
import dashscope

dashscope.api_key = "your_api_key"

speech_synthesizer = SpeechSynthesizer(
    model='qwen3-tts-instruct-flash',
    voice='Chelsie',
    format=AudioFormat.DEFAULT,
)

audio = speech_synthesizer.call("要合成的文本")

with open("output.wav", "wb") as f:
    f.write(audio)
```

### 方案三：edge-tts（备选）

```python
import edge_tts
import asyncio

async def generate_tts(text, output_path):
    communicate = edge_tts.Communicate(text, "zh-CN-YunjianNeural")
    await communicate.save(output_path)

asyncio.run(generate_tts("要合成的文本", "output.mp3"))
```

## 运行Pipeline

### 批量生成 demand 目录（推荐）

无外部 TTS 网络时，先跑静音烟测，验证解析、分镜、画面、字幕、视频合成和质量报告：

```bash
cd pipeline
python pipeline.py ../demand --batch --no-tts
```

网络和 TTS Key 可用时，跑完整批量生成：

```bash
cd pipeline
python pipeline.py ../demand --batch
```

### 生成单个 Excel

```bash
cd pipeline
python pipeline.py ../demand/618.xlsx --batch
python pipeline.py ../demand/douyinwenanjiaoben.xlsx --name 光伏前期手续 --no-tts
```

### 输出文件

每条脚本会生成独立输出目录，包含：

- `script.json`：结构化脚本
- `storyboard.json`：参考视频风格分镜
- `narration.mp3`：配音或静音烟测音频
- `narration.srt`：字幕
- `slides/`：信息图页面
- `frames/`：关键帧截图
- `quality_report.json` / `quality_report.md`：质量报告
- `<输出名>.mp4`：最终视频

### 在walle上运行

```bash
ssh zhangyanbo@192.168.28.92
cd ~/owner/xiaowangzi/projects/privacy-engineering/projects/douyin-jianji/pipeline
bash run_on_walle.sh
```

## 可用音色

### 小米MiMo
- 苏打（男性）
- 白桦（男性）
- 冰糖（女性）
- 茉莉（女性）

### 阿里云百炼
- Chelsie
- Ethan
- Sunni

## 注意事项

1. 小米MiMo需要通过token-plan-cn代理访问
2. 百炼TTS需要开通权限
3. edge-tts需要外网访问
4. 所有TTS生成WAV格式，需要ffmpeg转MP3
