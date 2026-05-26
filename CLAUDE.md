# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# 隐私工程

集中管理个人隐私敏感文件：保险理赔、个人档案、人物档案、医疗诊断、微信聊天记录。

## 目录结构

```
privacy-engineering/
├── insurance/        ← 电动车意外险理赔项目（HTML报告、研究笔记、索赔计划、理赔材料、进展记录）
├── refs-insurance/   ← 保险原始材料（保单PDF、事故照片、OCR结果）
├── profile/          ← 个人档案（学术画像、职业轨迹、能力体系、互联网账号）
├── people/           ← 重要他人知识工件（消化后的档案）
├── refs-people/      ← 人物原始素材（微信聊天记录、图片、语音）
├── medical/          ← 医疗诊断证明
└── .claude/skills/   ← 项目本地技能
    └── wechat-extract/ ← 微信聊天数据提取技能
```

## 核心规则

1. **隐私文件不进 git** — 本目录下所有内容不应提交到公开仓库
2. **refs-people/ 命名** — 一律中文真实姓名（如 `兰周婵`），不用拼音
3. **people/ 是知识工件** — 从 refs-people/ 原始素材消化而来，不是搬运
4. **保险理赔流程** — 参考 `insurance/` 内文档，HTML 报告用 upload-r2 技能发布

## 保险理赔工作流

保险理赔材料更新时按固定模式操作（详见 `insurance/html-update-pattern.md`）：

1. 分析新材料内容，更新HTML报告（增量版本 v3/v4...）
2. 英文文件名：`insurance-claim-report-v3.html`
3. 上传R2获取公开链接
4. 同步更新：文档查看系统侧边栏链接 + 保单条款解读HTML链接 + memory引用
5. 三个HTML全部重新上传R2（因为互相引用）

关键文件：`insurance-claim-report-v2.html`（主报告）、`insurance-doc-viewer.html`（文档查看系统）、`insurance-policy-highlighted.html`（保单条款解读）

## 目录关系

- `refs-insurance/` 是原始素材（只读），`insurance/` 是消化后的项目产出
- `refs-people/` 是原始素材（微信聊天记录等），`people/` 是消化后的人物档案
- 人物档案命名：一律中文真实姓名，不用拼音（如 `兰周婵`、`聂霞`）

## 技能

### wechat-extract

从 Windows 微信 SQLite 数据库提取指定联系人的聊天记录（文本+图片+语音+视频），Linux 端后处理。

**环境**：
- Windows 端（mobile-computer）：Tailscale `100.87.67.119`，SSH `zhangyanbo:zyb123456`
- Python：`C:\Users\zhangyanbo\wechat-env\python.exe`
- 数据源：`E:\xwechat_files\zhangyanbo4815_77a1\db_storage\`

**四阶段流程**：
1. **Windows 提取**：同步脚本到 Windows → 运行 `extract_one.py` → 输出到 `E:\xwechat_files\export\`
2. **拷贝回 Linux**：Windows zip 打包 → SCP 下载 → 解压到 `refs-people/<真实姓名>/`
3. **Linux 后处理**：`post_process.py` 做 WXGF→JPG、SILK→WAV、OSS上传→ASR→voice2txt
4. **清理**：删除 Windows 导出目录

**输出结构**（每联系人）：
```
refs-people/<真实姓名>/
├── chat_YYYY-MM-DD_YYYY-MM-DD.json  ← 消息（含 sender 字段）
├── _stats.json                       ← 统计摘要
├── image/                            ← jpg/png
├── voice/                            ← wav（已解码）
├── voice2txt/                        ← ASR 文本
└── video/                            ← mp4
```

详细文档：`.claude/skills/wechat-extract/SKILL.md`

## 运行环境

- Python 环境：项目 `.venv`，`/home/zhangyanbo/owner/xiaowangzi/.venv/bin/python3.11`
- wechat-extract 依赖：`pycryptodome`、`pilk`（Linux SILK解码）、`oss2`（OSS上传）、`imageio-ffmpeg`（ffmpeg）
- 代理检查：外网操作前先确认 `127.0.0.1:7897` 连通性

## 关联

- 根项目：`/home/zhangyanbo/owner/xiaowangzi/`
- 保险理赔HTML更新模式：`insurance/html-update-pattern.md`
- 人物档案索引：`people/INDEX.md`
- 个人档案索引：`profile/INDEX.md`
