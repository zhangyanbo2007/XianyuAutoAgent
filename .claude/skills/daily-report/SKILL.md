---
name: daily-report
description: 统一日报技能 — 5板块参数切换。Use this skill whenever 用户要求每日/日报/学术追踪/技术资讯/论文追踪/AI新闻/记忆论文/大模型论文/智能体论文/资讯摘要/博主追踪/播客摘要, even if they don't explicitly say 'daily-report'. Covers: memory(深度,记忆系统论文), llm(广度,大模型论文), agent(广度,智能体论文), news(广度,技术资讯一手), builders(广度,AI博主/播客). 也触发于: arxiv digest, paper roundup, tech news today, AI news, what happened in AI, 论文速递, 今日资讯, 每日追踪, 行业动态, follow builders
disable-model-invocation: true
version: 7.1.1
author: Xiaowangzi
trigger: 学术日报, memory学术日报, llm学术日报, agent学术日报, 记忆论文, 大模型日报, 智能体日报, 技术资讯, 行业资讯, 综合资讯, 资讯日报, 每日资讯, AI博主, 博主资讯, 播客摘要, builders, follow builders, ai digest, daily-report, academic-daily-report, memory-academic-daily-report, tech-news-daily-report, follow-builders
---

# 统一日报 v7.1

学术日报 + 技术资讯日报 + AI博主/播客日报合并，通过参数选择板块：

| 参数 | 板块 | 类型 | 定位 | Wiki入库 | 品牌色 | 飞书微信 |
|------|------|------|------|---------|--------|---------|
| `memory` | 记忆系统（🤖🧠🔬三板块） | 学术 | **深度**—核心研究方向 | ✅ kb/papers/ | #4a7c28 | ✅ |
| `llm` | 大模型（🤖） | 学术 | **广度**—保持视野 | ✅ kb/papers/ | #4a7c28 | ✅ |
| `agent` | 智能体/Agent（🧠） | 学术 | **广度**—保持视野 | ✅ kb/papers/ | #4a7c28 | ✅ |
| `news` | 技术资讯（🧠🤖📰💡） | 资讯 | **广度**—一手行业动态 | ✅ kb/tech-news/ | #ff6b35 | ✅ |
| `builders` | AI博主/播客（🐦📺🎙️📰） | 资讯 | **广度**—一手人物观点 | ✅ kb/tech-news/ | #ff6b35 | ✅ |

学术聚焦学术论文（arXiv、期刊、算法创新），资讯聚焦公司官方一手动态（产品发布、技术博客、开源Release、投融资）。

默认无参数时执行 `memory`（深度日报）。

## 使用方式

```
/daily-report          → 记忆系统深度日报（默认）
/daily-report memory   → 记忆系统深度日报
/daily-report llm      → 大模型广度日报
/daily-report agent    → 智能体广度日报
/daily-report news     → 技术资讯日报
/daily-report builders → AI博主/播客日报
```

## 通用配置

| 配置项 | 值 |
|--------|---|
| 凭证 | `config/credentials.json`（飞书/微信AppID和Secret） |
| 微信作者 | 驯狐小王子 |
| 学术品牌色 | #4a7c28 (scholar-green) |
| 资讯品牌色 | #ff6b35 (fox-orange) |
| 代理 | `http://127.0.0.1:7897` |

### Python 环境

首次使用前安装：
```bash
cd .claude/skills/daily-report
uv venv .venv
uv pip install --python .venv/bin/python3 requests feedparser Pillow linkify-it-py
```

所有 Python 脚本用 `.venv/bin/python3`（相对技能目录）执行。

### Node.js 环境（builders变体需要）

```bash
cd .claude/skills/daily-report/builders/scripts && npm install
```

## 通用执行流程

### Step 0: 准备与缓存初始化

```bash
export https_proxy=http://127.0.0.1:7897 http_proxy=http://127.0.0.1:7897
DATE=$(TZ=Asia/Shanghai date +%Y-%m-%d)
BOARD=<memory|llm|agent|news|builders>
WORKSPACE=/home/zhangyanbo/owner/xiaowangzi/projects/daily-report/$DATE/$BOARD
mkdir -p $WORKSPACE
```

缓存检查、progress.json格式、目录结构、文件命名详见 `references/progress-and-cache.md`。

使用 `scripts/progress_manager.py` 管理进度：
```bash
scripts/progress_manager.py init <board> <date> <workspace>
scripts/progress_manager.py update <workspace> <step_key> done|failed
scripts/progress_manager.py check <workspace>
```

### Step 1: 搜索/采集（01_search）

**统一采集脚本** `scripts/collect.py` 替代分散的 WebSearch 和 prepare_digest.py：

```bash
# 学术板块（memory/llm/agent）— arXiv API + RSS + PubMed + OpenReview
.venv/bin/python3 scripts/collect.py --board <board> --date $DATE --output $WORKSPACE/01-search.json

# 资讯板块（news）— RSS + GitHub Releases + HuggingFace
.venv/bin/python3 scripts/collect.py --board news --date $DATE --output $WORKSPACE/01-search.json

# 资讯板块（builders）— 仍用 builders/scripts/prepare-digest.js（Node.js 管道）
cd builders/scripts && node prepare-digest.js 2>/dev/null
```

采集策略：**确定性优先，WebSearch 补缺**。80% 走 arXiv API / RSS / PubMed 等确定性源，20% 由 WebSearch 补缺（输出 `needs_websearch` 清单，Claude 在 Step 1b 中逐条执行）。

关键词配置见 `config/sources.json`，各变体详细范围见 `references/` 目录。

搜索结果保存到 `$WORKSPACE/01-search.json`，更新progress.json。

### Step 2: 去重（02_dedup）

```bash
# 学术板块
.venv/bin/python3 scripts/dedup.py --input $WORKSPACE/01-search.json --board <board> --output $WORKSPACE/02-new-papers.json

# 资讯板块
.venv/bin/python3 scripts/dedup.py --input $WORKSPACE/01-search.json --board news --output $WORKSPACE/02-dedup.json
```

脚本读取 Wiki INDEX.md，按 ID/URL/标题/文件名四重匹配去重。

### Step 3: Wiki入库（03_wiki_ingest）

```bash
.venv/bin/python3 scripts/wiki_ingest.py --input $WORKSPACE/02-new-papers.json --board <board> --date $DATE
```

脚本自动创建论文/资讯页面模板 + 更新 INDEX.md + 更新 LOG.md。Claude 需要补充的内容：
- 读取论文原文（WebFetch），为每篇写中文解读填入 `## Notes` 区域
- 创建/更新概念页 `kb/papers/concepts/` 和实体页 `kb/papers/entities/`
- 添加 `[text](path)` 交叉引用

遵循 `references/wiki-ingest.md` 的统一流程，铁律见 `references/wiki-rules.md`。

### Step 4: 更新索引（04_index_update）

Step 3 的 `wiki_ingest.py` 已自动更新 INDEX.md + LOG.md，此步骤确认更新完整性即可。

### Step 5: 生成日报（05_report_md）

**生成方式：Claude直接消化abstract写中文**。后台agent速度慢（用户已抱怨延迟），Python脚本只能截断英文无法真正理解内容。Claude读取搜索数据的abstract后，逐篇理解并用中文重新表述核心洞察。

**Avoid sed for bulk edits on report files** — Markdown中特殊字符使sed极易造成灾难性损坏（曾一次操作毁掉3个报告文件）。需要修改时用Edit工具精确替换。

日报格式规范详见 `references/report-format.md`。关键规则：

- **标题层级**：`##`板块主节 → `###`子主题分组 → `####`单个条目
- **中文内容**：标题格式"中文解读（英文原标题）"，中文读者更易理解中文内容——理解英文原文后用中文重新表述核心洞察，而非截断粘贴英文（带省略号的英文文本说明没有真正理解原文）
- **图片缓存到本地**：下载到 `$WORKSPACE/05-images/`，用相对路径引用。0字节视为失败，重试换版本号或图片序号
- **来源行日期**：日期是信息溯源的关键要素，所有来源必须标注 `YYYY-MM-DD`
- **板块洞察**：每个主板块末附 `> 💡 **板块洞察：**` 行
- **排版间距**：来源行和图片行之间有空行分隔

---

## === 变体概览 ===

每个变体的详细配置（采集范围、搜索关键词、信息源、Wiki摄入、日报结构、标题格式）在对应reference文件中。运行某变体时只读该变体的reference。

### memory：记忆系统深度日报

深度日报 — 记忆系统论文三板块(🤖🧠🔬)，入库到 kb/papers/。日报含3个板块各有子主题分组+狐狸点评。

👉 运行此变体时读取 `references/memory.md`

### llm：大模型广度日报

广度日报 — 大模型论文(🤖)，入库到 kb/papers/。日报按子主题分组（后训练与对齐、RL与推理优化、微调与知识注入、安全与水印等）+狐狸点评。

👉 运行此变体时读取 `references/llm.md`

### agent：智能体广度日报

广度日报 — 智能体/Agent论文(🧠)，入库到 kb/papers/。日报按子主题分组（Agent框架与架构、Agent训练与自我进化、Agent RL与优化、Agent安全与对抗、Agent评估与基准等）+狐狸点评。

👉 运行此变体时读取 `references/agent.md`

### news：技术资讯日报

资讯日报 — 公司官方一手动态(🧠🤖📰💡)，入库到 kb/tech-news/。运行prepare_digest.py采集RSS/GitHub/HuggingFace，再WebSearch补缺。专注一手官方源——二手媒体（量子位、机器之心、TechCrunch等）重包装信息，直接访问原始公司博客获取更完整细节和配图，避免信息稀释层。

👉 运行此变体时读取 `references/news.md`

### builders：AI博主/播客日报

博主日报 — 人物观点和对话内容(🐦📺🎙️)，入库到 kb/tech-news/。运行prepare-digest.js采集X/Twitter/播客/YouTube/博客。JSON是唯一内容源——独立搜索会打断溯源链，每条内容必须追溯到JSON中的原始URL。

👉 运行此变体时读取 `references/builders.md`

---

## === 发布流程 ===

Steps 6-11（飞书+微信并行发布）详见 `references/delivery.md`。

飞书文档和微信草稿是两条独立并行管道，互不依赖。

## Cron Job

| 板块 | 时间 |
|------|------|
| memory | 每天 8:20 AM |
| llm | 每天 8:30 AM |
| agent | 每天 8:40 AM |
| news | 每天 8:50 AM |
| builders | 每天 9:00 AM |