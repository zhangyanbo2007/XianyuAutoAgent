---
name: shanhaijing-video
description: >
  《山海经》视频制作技能。支持两种输入模式：(A) 图文模式——用户提供山海经原文+插画；
  (B) 纯文本模式——仅有原文文本，无参考图。生成高清中国古风视频，包含 AI 视频生成、
  赵忠祥风格解说配音（保留 AI 背景配乐）、中文字幕。
  使用场景：(1) 用户提供山海经原文+插图，要求制作视频；(2) 用户说"做山海经视频"、"图生视频"；
  (3) 用户提供山海经生物插画，要求生成动态视频；(4) 仅有山海经原文（无图），要求制作视频；
  (5) 制作系列山海经短视频。
  流程：分析故事→确定时长→输出分镜文案（含解说词）→用户确认→
  【图文模式】使用用户插画做 I2V / 【纯文本模式】仅原文无插画直接 T2V 文生视频→
  分段生成视频→截取参考帧→续生下一段→拼接→生成解说配音→叠加旁白到原BGM→添加字幕。
  核心规则：分镜必须先确认再生成；纯文本模式需先生成参考图；段间参考帧必须选角色最清晰的代表性帧；
  每段提示词内部按3-2-2-3节奏分段描述；解说词需控制语速，约2.5-3字/秒；
  旁白叠加到原视频BGM上（BGM降至30%音量），不可替换原配乐。
---

# 《山海经》视频制作技能

## 输入模式

本技能支持两种输入模式，确认后走不同流程：

| 模式 | 输入 | 首段视频生成方式 |
|------|------|--------------------|
| **A. 图文模式** | 原文 + 用户插画 | 图生视频（I2V） |
| **B. 纯文本模式** | 仅原文，无插画 | 文生视频（T2V） |

**模式判断规则：** 用户发了插画 → A 模式（I2V）；仅发文字/原文 → B 模式（T2V 直接文生视频）。主动告知用户当前模式。

## 通用工作流

### Step 1：分析故事

从用户提供的原文（和插画）中提取：
- 山名/地点背景
- 生物外形特征（**关键！后续保持角色一致性**）
- 神奇功效/文化意象
- 环境元素（溪流、矿物、云雾等）

### Step 2：确定时长

以 10 秒为单位，根据内容丰富度灵活决定段数：
- 内容短：1 段（10 秒）
- 内容适中：2 段（20 秒）
- 内容丰富：3 段及以上（30 秒+）

### Step 3：输出分镜文案（含解说词）

**原则：**
- 每段 10 秒内按 **3-2-2-3** 节奏编排：0-3秒从容展开 → 3-5秒节奏加快 → 5-7秒继续推进 → 7-10秒收尾留白
- **解说词控制在约2.5-3字/秒**（10秒段约25-30字），古风简洁
- 每句解说词 4-8 字为主，3-4 秒能读完
- 分镜描述要有时间标注（如「0-3秒」「3-5秒」），按节奏分段
- 最后一个镜头与开场呼应
- 解说词整体连贯，像完整旁白

**⚠️ 必须先输出分镜文案让用户确认，确认后再生成视频。**

**⚠️ 确认时同步确认解说词语速是否合理**——每句字数与对应时间段匹配，
总字数 / 10秒 ≈ 2.5-3 字/秒。

### Step 3.5：确定音乐风格

AI 视频生成模型会自动配乐。生成前可提示期望的风格：
- 中国古风（古琴/箫/笛子为主）
- 神秘空灵（适合奇幻场景）
- 磅礴大气（适合大战/神兽登场）

**规则：** 使用相同的视频生成模型，所有段配乐风格自然一致，不可各段画风突变。

### Step 4：准备首段参考图

根据输入模式选择不同策略：

#### A. 图文模式——使用用户插画

> 注：图片上传复用 `media-to-url` 技能的上传脚本。

```bash
~/.openclaw/skills/media-to-url/scripts/upload-cos.sh <image_path>
```

直接使用用户提供的插画作为第一段参考图。

#### B. 纯文本模式——直接文生视频（T2V）

**当用户没有提供插画时，直接使用文生视频模型（T2V）生成第一段视频。**

**T2V prompt 结构：**

```
video_generate(
  prompt="""中国古代神话山海经风格，中国传统白描水墨画风。
  {山名/地点环境描述}，{生物外形特征详细描述}。
  {0-3秒：画面描述，场景从容展开}
  {3-5秒：画面描述，节奏加快}
  {5-7秒：画面描述，继续推进}
  {7-10秒：画面描述，收尾留白}
  中国古风插画质感，细腻唯美，白描线条微微流动，画面呼吸感十足，电影感，1080P。""",
  model="qwen/wan2.7-t2v",
  durationSeconds=10,
  resolution="1080P",
  aspectRatio="16:9"
)
```

**⚠️ 纯文本模式直接 T2V 生成，不需要先文生图再上传。**

### Step 5：分段生成视频

**核心规则：每段 10 秒，由一个 prompt 生成，不拆分小段拼接。**

Prompt 内部按 **3-2-2-3** 节奏分段描述画面：

#### 第一段

**A. 图文模式（I2V）：**
```
video_generate(
  prompt="""中国古代神话山海经风格，中国传统白描水墨画风。
  {0-3秒：画面描述，场景从容展开}
  {3-5秒：画面描述，节奏加快}
  {5-7秒：画面描述，继续推进}
  {7-10秒：画面描述，收尾留白}
  中国古风插画质感，细腻唯美，白描线条微微流动，画面呼吸感十足，电影感，1080P。""",
  image="<用户插画_cos_url>",
  model="qwen/wan2.7-i2v",
  durationSeconds=10,
  resolution="1080P",
  aspectRatio="16:9"
)
```

**B. 纯文本模式（T2V）：**
```
video_generate(
  prompt="""中国古代神话山海经风格，中国传统白描水墨画风。
  {山名/地点环境描述}，{生物外形特征详细描述}。
  {0-3秒：画面描述，场景从容展开}
  {3-5秒：画面描述，节奏加快}
  {5-7秒：画面描述，继续推进}
  {7-10秒：画面描述，收尾留白}
  中国古风插画质感，细腻唯美，白描线条微微流动，画面呼吸感十足，电影感，1080P。""",
  model="qwen/wan2.7-t2v",
  durationSeconds=10,
  resolution="1080P",
  aspectRatio="16:9"
)
```

#### 第二段及以后（使用前一段的核心参考帧）

**关键：参考帧不是随便截的帧，而是上一段视频中角色最清晰、最完整、最具代表性的那一帧。**

**第二段参考帧优先选上一段的过渡画面**（如第一段结尾的场景转换处），这样两段视觉连贯自然。

提取参考帧：

```python
from moviepy import VideoFileClip
from PIL import Image

v = VideoFileClip("<上一段视频路径>")
# 选择角色最清晰的时间点（通常 4-6 秒处，不是最后一帧）
frame = v.get_frame(5.0)
img = Image.fromarray(frame)
img.save("/tmp/core-reference.jpg")
```

**⚠️ 每一段视频生成完成后，必须主动告知用户，并发送该段的核心参考帧截图给用户看，让用户确认效果。**

**每段完成后通知格式：**
```
第 X 段生成完成！这是本段的核心参考帧：
MEDIA:<参考帧图片路径>
接下来生成第 X+1 段...
```

上传参考帧，生成下一段：

```
video_generate(
  prompt="""中国古代神话山海经风格，中国传统白描水墨画风。
  重要：参考图中的山间溪流场景必须完全保留，白描画风风格不变，跟参考图一模一样，不要改动它的任何外形特征。
  {0-3秒：画面描述，场景从容展开}
  {3-5秒：画面描述，节奏加快}
  {5-7秒：画面描述，继续推进}
  {7-10秒：画面描述，收尾留白}
  中国古风插画质感，与前段风格一致，白描线条流动，高清细腻，1080P。""",
  image="<核心参考帧_cos_url>",
  model="qwen/wan2.7-i2v",
  durationSeconds=10,
  resolution="1080P",
  aspectRatio="16:9"
)
```

**多段视频需要依次生成，每段生成后都截取核心参考帧传给下一段。**

### Step 6：拼接视频

```python
from moviepy import VideoFileClip, concatenate_videoclips

clips = [VideoFileClip(path) for path in video_paths]
final = concatenate_videoclips(clips, method="compose")
final.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24,
                      preset="fast", bitrate="5000k")
```

拼接后的视频**保留了各段 AI 生成的原配乐**，后续步骤在此基础上叠加旁白。

### Step 7：生成解说配音

**声音选择：`zh-CN-YunJianNeural`（低沉男声，接近赵忠祥《动物世界》风格）**

```bash
edge-tts --voice zh-CN-YunJianNeural --rate="-25%" --pitch="-10Hz" \
  --text "解说词" --write-media <output>.mp3
```

逐句生成，每句对应一个时间段。⚠️ **只使用 `-25%` 速率**，其他速率（如 `-15%`）可能导致 NoAudioReceived 错误。

生成后**必须检查每句实际时长**：

```python
from moviepy import AudioFileClip
for i in range(1, 6):
    a = AudioFileClip(f"n{i:02d}.mp3")
    print(f"n{i:02d}.mp3: {a.duration:.2f}s")
    a.close()
```

⚠️ edge-tts `-25%` 速率下，短句（6-8字）实际时长约 3-5 秒，远超预期。20秒视频含 5 句旁白，总时长通常超出视频长度。需要在 Step 8 中用 `with_speed_scaled()` 整体加速适配。

### Step 8：调整旁白时长并叠加到原BGM

**关键：不是替换原配乐，而是将旁白叠加到原BGM上。**

⚠️ **重要：旁白片段不能按预设时间轴放置，必须按实际时长依次排列，否则会重叠！**

```python
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip, TextClip, CompositeVideoClip

# 加载原视频（含BGM）
video = VideoFileClip("<拼接后视频路径>")
bgm = video.audio
bgm_quiet = bgm.with_volume_scaled(0.30)

# 加载旁白片段
narr_files = ["n01.mp3", "n02.mp3", "n03.mp3", "n04.mp3", "n05.mp3"]
narr_clips_raw = [AudioFileClip(f"{NARR_DIR}/{f}") for f in narr_files]

# 计算总时长（含句间 0.1s 间隔）
total_narr = sum(c.duration for c in narr_clips_raw) + 0.4
video_duration = video.duration
target_narr_duration = video_duration - 2.0  # 留 1s 开头 + 1s 结尾
speed_factor = total_narr / target_narr_duration
print(f"旁白总时长: {total_narr:.2f}s, 视频时长: {video_duration:.2f}s, 加速因子: {speed_factor:.3f}")

# 依次排列旁白片段（不重叠！）
start_time = 1.0
narr_final_clips = []
for clip in narr_clips_raw:
    sped = clip.with_speed_scaled(speed_factor)
    narr_final_clips.append(sped.with_start(start_time))
    start_time += sped.duration + 0.1

narration = CompositeAudioClip(narr_final_clips).with_duration(video.duration)
final_audio = CompositeAudioClip([bgm_quiet, narration])
video_with_audio = video.with_audio(final_audio)
```

**加速因子：** 通常 1.1-1.3 之间。如果 > 1.5 说明旁白太多，需要精简解说词。

### Step 9：添加字幕

⚠️ **字幕时间轴必须与旁白实际时长一致**，不能用预设时间。

```python
from moviepy import TextClip, CompositeVideoClip

narr_texts = [
    '再向东三百里，是柢山。',
    '山间多水，无草木。',
    '有鱼鲮，状如牛，蛇尾有翼。',
    '其音如犁牛，冬死夏生。',
    '食之无肿疾，是为鱼鲮。',
]

# 计算每句字幕时间（与旁白加速后一致）
t = 1.0
subtitle_entries = []
for i, (clip, text) in enumerate(zip(narr_clips_raw, narr_texts)):
    sped_dur = clip.duration / speed_factor
    subtitle_entries.append((t, t + sped_dur, text))
    t += sped_dur + 0.1

w, h = video.size
font = 'NotoSansCJK-Regular'
subtitle_clips = []
for start, end, text in subtitle_entries:
    txt = TextClip(
        text=text, font_size=48, color='white',
        stroke_color='black', stroke_width=4,
        font=font,
        text_align='center', horizontal_align='center',
        vertical_align='center', method='label', transparent=True
    )
    txt = txt.with_position(('center', h - 120)).with_duration(end - start).with_start(start)
    subtitle_clips.append(txt)

final = CompositeVideoClip([video_with_audio, *subtitle_clips])
final.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24,
                       preset="fast", bitrate="5000k")
```

**字幕样式：白色文字 + 黑色 4px 描边，底部居中，距底 120px，字体大小 48。**

### Step 10：提取参考帧

从第一段视频中提取参考帧用于第二段生成：

```bash
# 使用 imageio-ffmpeg 自带的 ffmpeg
FFMPEG=$(python3 -c "from imageio_ffmpeg import get_ffmpeg_exe; print(get_ffmpeg_exe())")
$FFMPEG -i <第一段视频> -ss 00:00:05 -vframes 1 -y /tmp/ref_frame.png
```

⚠️ 优先提取 **4-6 秒处**的帧，通常是角色最清晰的位置。不要用最后一帧。

## 核心规则

1. **必须先确认再生成** — 分镜文案（含解说词）输出后等用户确认
2. **纯文本模式直接 T2V** — 无参考图时，直接用文生视频模型生成，不需要先出图
3. **每段生成完必须通知用户** — 发送视频 + 核心参考帧截图，让用户确认效果，不行就重新生成
4. **避免大幅度动作导致角色变形** — 提示词中避免复杂形变动作（如翅膀大幅展开），优先保持角色形象稳定
5. **参考帧必须精选** — 选角色最清晰、最具代表性的帧，不是最后一帧
6. **每段一个 prompt** — 不拆分成多个小视频拼接，prompt 内部按时间分段描述
7. **每段标准时长 10 秒** — 固定标准
8. **段内节奏 3-2-2-3** — 开头 3 秒从容，中间 2+2 秒紧凑，结尾 3 秒留白
9. **角色形象一致** — 提示词强调"跟参考图一模一样"，避免复杂形变动作
10. **配乐风格统一** — 使用相同模型生成各段，配乐风格自然一致
11. **解说词控制语速** — 约 2.5-3 字/秒，10 秒段约 25-30 字
12. **旁白叠加不替换** — 保留原视频 AI 生成的 BGM，旁白叠加其上（BGM 30% 音量）
13. **默认 1080P 16:9**
14. **默认视频模型 qwen/wan2.7-i2v**
15. **纯文本模式默认模型 qwen/wan2.7-t2v** — 直接文生视频
16. **配音用 YunJianNeural** — rate 固定 `-25%`, pitch `-10Hz`，其他速率可能报 NoAudioReceived
17. **旁白时长控制** — edge-tts `-25%` 速率下，短句实际时长 3-5 秒，需用 `with_speed_scaled()` 适配视频时长
18. **字幕时间轴 = 旁白实际时长** — 不能用预设时间，必须根据加速后的旁白时长动态计算
19. **参考帧提取用 imageio-ffmpeg 自带 ffmpeg** — `python3 -c "from imageio_ffmpeg import get_ffmpeg_exe; print(get_ffmpeg_exe())"`
20. **输出原文+译文** — 成品完成后，发送原文和译文，角色描述用 emoji 高亮

## 节奏方案说明

对于《山海经》这种"慢节奏+古风+需要看懂细节"的内容，**3-2-2-3 是最合适的节奏**。

前 3 秒建立视觉锚点（观众需要时间认出画面内容），中间 4 秒推进叙事，
后 3 秒留白与余韵（特别是"佩之宜子孙"这类点题金句，需要空间沉淀）。

其他方案：2-3-2-3 适合战斗/追逐；2-2-3-3 适合渐进式展示。

## 参考文档

- 分镜模板与提示词范例：见 [references/storyboard-template.md](references/storyboard-template.md)
- 参考帧提取指南：见 [references/core-frame-extraction.md](references/core-frame-extraction.md)
- 完整制作流程脚本：见 [scripts/full-pipeline.py](scripts/full-pipeline.py)
