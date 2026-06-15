---
name: upload-oss
description: >
  阿里云OSS文件上传技能 — 将本地文件上传到阿里云OSS，返回公开访问链接。
  主要用途：为DashScope语音识别(ASR)等需要OSS音频URL的服务提供文件托管。
  也用于通用文件分享场景。
  使用场景：用户说"上传到阿里云"、"上传OSS"、"oss发布"、"ASR需要音频URL"、
  "百炼需要OSS链接"、"阿里云存储"。
version: 1.0.0
author: Xiaowangzi
trigger: 上传OSS, 上传阿里云, oss发布, ASR音频URL, 百炼OSS, upload-oss
---

# Upload OSS — 阿里云OSS文件上传技能

将本地文件上传到阿里云OSS，返回公开访问链接。主要解决DashScope Transcription API
硬性要求音频URL必须是阿里云OSS地址的问题。

## 为什么需要 OSS

DashScope 语音识别（qwen3-asr-flash 等）的 Transcription API **硬性要求**音频 URL
必须是阿里云 OSS 地址，外部 URL（腾讯云 COS、Cloudflare R2 等）一律报 "url error"。

| 场景 | 是否需要OSS |
|------|------------|
| DashScope ASR 语音识别 | ✅ 必须 |
| DashScope TTS 语音合成 | ✅ 必须 |
| DashScope 批量转录 | ✅ 必须 |
| 通用文件分享 | ⚠️ 可选（R2/COS也可） |

## 触发方式

- 用户说"上传到阿里云"、"上传OSS"、"oss发布"
- DashScope ASR/TTS 需要音频 URL 时自动使用
- `/upload-oss <file_path>`

## 上传方式

```bash
.claude/skills/upload-oss/.venv/bin/python3 .claude/skills/upload-oss/scripts/upload.py <file_path> [object_key]
```

- `file_path`: 本地文件路径（必填）
- `object_key`: OSS上的目标路径（可选，默认按日期自动生成）
- 所有文件自动设置 `ACL: public-read` 和正确的 Content-Type
- Skill 独立 `.venv`（`oss2, pyyaml`）

### 凭证配置

`~/.oss.yaml` 内容：
```yaml
base:
  access_key_id: <your-access-key-id>
  access_key_secret: <your-access-key-secret>
  bucket: <your-bucket-name>
  endpoint: oss-cn-hangzhou.aliyuncs.com
```

### 获取凭证步骤

1. 登录 [阿里云控制台](https://www.aliyun.com)
2. 开通 OSS 服务（如未开通）
3. 创建一个 Bucket（建议选杭州节点 `oss-cn-hangzhou`，与 DashScope 同域）
4. 设置 Bucket ACL 为 `public-read`（公开读，私有写）
5. 在 AccessKey 管理页面创建 AccessKey，记录 `AccessKey ID` 和 `AccessKey Secret`
6. 填入 `~/.oss.yaml`

### 路径规则

未指定object_key时，自动按日期生成：
`<年>/<月>/<日>/<文件名>`

如：`2026/05/24/test_audio.wav`

## 输出格式

```
✅ 上传成功
🔗 URL: https://your-bucket.oss-cn-hangzhou.aliyuncs.com/2026/05/24/test_audio.wav
📋 Markdown: [test_audio.wav](https://your-bucket.oss-cn-hangzhou.aliyuncs.com/2026/05/24/test_audio.wav)
📦 Size: 31.3KB | Type: audio/wav
```

## DashScope ASR 配合使用

上传音频后，直接用返回的 OSS URL 调用 ASR：

```python
from dashscope.audio.asr import Transcription
task = Transcription.call(
    model='qwen3-asr-flash',
    file_urls=['https://your-bucket.oss-cn-hangzhou.aliyuncs.com/2026/05/24/audio.wav'],
)
result = Transcription.wait(task)
```

## 依赖

- Skill 独立 `.venv`（`oss2, pyyaml`）
- `~/.oss.yaml` 凭证配置
- OSS bucket 需开启 public-read ACL