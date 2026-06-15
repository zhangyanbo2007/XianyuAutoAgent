---
name: wechat-extract
description: 从 Windows 微信 SQLite 数据库提取指定联系人的聊天记录（文本+图片+语音+视频），Linux端后处理（WXGF→JPG + SILK→WAV→ASR）。支持关键词、wxid、备注名、微信号、昵称搜索。
---

# 微信数据提取 — 单联系人

## 核心规则

1. **每次提取前，先把脚本从 Linux 同步到 Windows**（Linux 是源，Windows 是执行端）
2. **密钥提取需覆盖所有数据库**（db_storage 根目录，不是 message 子目录）
3. **语音后处理 (SILK→WAV→ASR) 在 Linux 完成**（pilk 无法在 Windows embeddable Python 编译）
4. **处理完后 wxgf 和 silk 原文件必须删除**，只保留 jpg 和 wav

## 环境

- **Windows**: mobile-computer (Tailscale: `100.87.67.119`, SSH: `zhangyanbo:zyb123456`)
- **数据源**: `E:\xwechat_files\zhangyanbo4815_77a1\db_storage\`（根目录，含 message/、contact/ 等子目录）
- **输出**: `E:\xwechat_files\export\<搜索关键词>\`
- **Python**: `C:\Users\zhangyanbo\wechat-env\python.exe`

## 阶段 1 — Windows 提取

### 步骤 1a — 密钥提取（首次或密钥变更后）

确保 Windows 端 `find_all_keys_windows.py` 的 config.json `db_dir` 指向 **db_storage 根目录**（不是 message 子目录）。这样密钥提取覆盖所有数据库，包括 contact.db。

```bash
sshpass -p zyb123456 ssh -o StrictHostKeyChecking=no zhangyanbo@100.87.67.119 \
  'C:\Users\zhangyanbo\wechat-env\python.exe C:\Users\zhangyanbo\wechat-env\find_all_keys_windows.py'
```

密钥保存在 `C:\Users\zhangyanbo\wechat-env\all_db_keys.json`。`extract_one.py` 自动从此文件加载密钥。

### 步骤 1b — 同步脚本

```bash
sshpass -p zyb123456 scp -o StrictHostKeyChecking=no \
  projects/privacy-engineering/.claude/skills/wechat-extract/scripts/wx_decrypt_utils.py \
  projects/privacy-engineering/.claude/skills/wechat-extract/scripts/extract_one.py \
  projects/privacy-engineering/.claude/skills/wechat-extract/scripts/lookup_contact.py \
  "zhangyanbo@100.87.67.119:C:/Users/zhangyanbo/wechat-env/"
```

### 步骤 1c — 执行提取

搜索支持五种模式：

| 模式 | 示例 | 说明 |
|------|------|------|
| **关键词** | `子晨`、`Sophie` | 搜索 message_content LIKE '%关键词%' |
| **wxid精确** | `wxid_wzd2l8rcya1621` | 直接匹配 Msg_MD5(wxid) |
| **--contact** | `--contact 兰周婵` | 从 contact.db 搜索备注名/微信号/昵称 |
| **--contact 拼音** | `--contact lanzhouchan` | 拼音搜索（remark_quan_pin/quan_pin/pin_yin_initial） |
| **自动回退** | `兰周婵`（不加--contact） | 关键词搜索失败 → 自动回退 contact.db 查找 |
| **排查列表** | `--list` | 列出所有 Msg 表及消息数 |

**常用命令**：

```bash
# 按备注名/微信号/昵称搜索（推荐，最精准）
sshpass -p zyb123456 ssh -o StrictHostKeyChecking=no zhangyanbo@100.87.67.119 \
  'C:\Users\zhangyanbo\wechat-env\python.exe C:\Users\zhangyanbo\wechat-env\extract_one.py --contact 兰周婵'

# 按微信号搜索
sshpass -p zyb123456 ssh -o StrictHostKeyChecking=no zhangyanbo@100.87.67.119 \
  'C:\Users\zhangyanbo\wechat-env\python.exe C:\Users\zhangyanbo\wechat-env\extract_one.py --contact Izcchanxi'

# 关键词搜索（搜索消息内容）
sshpass -p zyb123456 ssh -o StrictHostKeyChecking=no zhangyanbo@100.87.67.119 \
  'C:\Users\zhangyanbo\wechat-env\python.exe C:\Users\zhangyanbo\wechat-env\extract_one.py 子晨'

# wxid 精确匹配
sshpass -p zyb123456 ssh -o StrictHostKeyChecking=no zhangyanbo@100.87.67.119 \
  'C:\Users\zhangyanbo\wechat-env\python.exe C:\Users\zhangyanbo\wechat-env\extract_one.py wxid_1ui10kq11sp322'

# 单独查询联系人信息（不提取聊天记录）
sshpass -p zyb123456 ssh -o StrictHostKeyChecking=no zhangyanbo@100.87.67.119 \
  'C:\Users\zhangyanbo\wechat-env\python.exe C:\Users\zhangyanbo\wechat-env\lookup_contact.py 兰周婵'
```

**--contact 搜索原理**：
- 解密 `contact.db`，查询 `contact` 表
- 搜索字段：remark（备注名）、alias（微信号）、nick_name（昵称）、remark_quan_pin/quan_pin/pin_yin_initial（拼音）
- 返回 wxid → 计算 MD5(wxid) → 定位 Msg 表 → 提取聊天记录
- sender 字段使用备注名（如"兰周婵"），而不是 wxid

### 输出

```
E:\xwechat_files\export\<搜索关键词>\
  chat_<起>_<止>.json  ← 消息（含日期范围和 sender 字段）
  image/               ← jpg/png/wxgf（wxgf 待 Linux 转换）
  voice/               ← silk（原始，待 Linux 解码+ASR）
  video/               ← mp4
  _stats.json
```

### sender 字段

每条消息都有 `sender` 字段，值为发送者名字：
- `"小王子"` — 自己发的消息（sender_id_map 归属：有 status=2 的 sender_id → 小王子）
- `<备注名/昵称>` — 联系人发的消息（sender_id_map 归属：有 status=4 的 sender_id → 联系人）
- `"system"` — 系统消息（type=10000）

**跨数据库 sender_id 不一致性**：同一个人在不同数据库文件中可能有不同的 `real_sender_id`（如小王子在 message_0.db 里是 id=4，在 message_1/2.db 里是 id=2）。解决方案：先从 status 模式构建 sender_id→名字映射（有 status=2 → 小王子，有 status=4 且无 status=2 → 联系人），再对每条消息用 status 优先 + sender_id_map 回退。status=3 是"已送达"状态，两方都有，不能单独判断归属。

## 阶段 2 — 拷贝回 Linux

```
E:\xwechat_files\export\<搜索关键词>\ → projects/privacy-engineering/refs-people/<真实姓名>/
```

**命名规则**：`projects/privacy-engineering/refs-people/` 和 `projects/privacy-engineering/people/` 目录及文件一律使用中文真实姓名（如 `兰周婵`、`聂霞`），不用拼音（不用 `nie-xia`）。

### 拷贝方法

中文路径的 SCP 可能不稳定。推荐先在 Windows 上 zip 打包，再下载 zip：

```bash
# Windows端打包（在提取脚本中已自动处理）
sshpass -p zyb123456 ssh -o StrictHostKeyChecking=no zhangyanbo@100.87.67.119 \
  'C:\Users\zhangyanbo\wechat-env\python.exe -c "
import zipfile, os; ... zip打包代码 ...
"'

# Linux端下载zip
sshpass -p zyb123456 scp -o StrictHostKeyChecking=no \
  "zhangyanbo@100.87.67.119:E:/xwechat_files/export/<英文名>_data.zip" \
  /tmp/<英文名>_data.zip

# 解压到 refs-people/
unzip /tmp/<英文名>_data.zip -d projects/privacy-engineering/refs-people/<真实姓名>/
```

## 阶段 3 — Linux 后处理

```bash
.claude/skills/wechat-extract/.venv/bin/python3.11 projects/privacy-engineering/.claude/skills/wechat-extract/scripts/post_process.py projects/privacy-engineering/refs-people/<真实姓名>/
```

## 阶段 4 — 删除 Windows 导出

Linux 后处理 + 验证完成后，删除 Windows 上的导出目录：

```bash
sshpass -p zyb123456 ssh -o StrictHostKeyChecking=no zhangyanbo@100.87.67.119 \
  'cmd /c "rmdir /s /q E:\xwechat_files\export\<搜索关键词>"'
```

## 图片提取优先级

1. `.dat` — 原始图片（首选）
2. `_h.dat` — 高清版本
3. `_t.dat` — 缩略图（标注 `thumbnail: true`，尽量不用）

## contact.db 结构

解密后的 contact.db 有一个 `contact` 表，关键字段：

| 字段 | 说明 | 示例 |
|------|------|------|
| username | wxid | `wxid_1ui10kq11sp322` |
| alias | 微信号 | `lzcchanxi` |
| remark | 备注名 | `兰周婵` |
| nick_name | 昵称 | `地球观察员` |
| remark_quan_pin | 备注全拼 | `lanzhouchan` |
| pin_yin_initial | 备注简拼 | `LZC` |
| quan_pin | 昵称全拼 | `deqiuguanchayuan` |
| head_img_url | 头像URL | `https://wx.qlogo.cn/...` |

## 后处理验证

后处理完的 chat JSON 每条消息必须有 `sender` 字段，多媒体消息还必须有对应字段：

| 消息类型 | 必有字段 | 示例 |
|---------|---------|------|
| **所有类型** | `sender` | `"小王子"` 或 `"兰周婵"` |
| 文本 (type=1) | `content`, `sender` | `"周末有时间不？"`, `"小王子"` |
| 图片 (type=3) | `content`, `media_file`, `media_format` | `"[image: image/xxx.jpg]"`, `"image/xxx.jpg"`, `"jpg"` |
| 语音 (type=34) | `content`（ASR 文本）, `voice_wav`, `voice_txt` | `"这么晚还逛街啊？"`, `"voice/xxx.wav"`, `"voice2txt/xxx.txt"` |
| 视频 (type=43) | `content`, `media_file`, `media_format` | `"[video: video/xxx.mp4]"`, `"video/xxx.mp4"`, `"mp4"` |

**验证命令**：
```bash
python3 -c "
import json, os
d='projects/privacy-engineering/refs-people/<姓名>'
chat = [f for f in os.listdir(d) if f.startswith('chat') and f.endswith('.json')][0]
with open(os.path.join(d,chat)) as f: msgs=json.load(f)
img_ok=sum(1 for m in msgs if m.get('media_format') in ('jpg','png') and os.path.exists(os.path.join(d,m.get('media_file',''))))
voice_ok=sum(1 for m in msgs if m.get('voice_wav') and 'voice_txt' in m and os.path.exists(os.path.join(d,m.get('voice_wav',''))))
video_ok=sum(1 for m in msgs if m.get('media_format')=='mp4' and os.path.exists(os.path.join(d,m.get('media_file',''))))
sender_ok=sum(1 for m in msgs if m.get('sender'))
print(f'sender:{sender_ok}/{len(msgs)} image:{img_ok} voice:{voice_ok} video:{video_ok}')
"
```

## 已知限制

1. **WAL 数据丢失**：只解密主数据库页面，WAL（Write-Ahead Log）文件加密但无法单独解密，近期数据可能缺失
2. **密钥依赖 WeChat 进程**：密钥从 WeChat.exe 进程内存提取，WeChat 必须正在运行