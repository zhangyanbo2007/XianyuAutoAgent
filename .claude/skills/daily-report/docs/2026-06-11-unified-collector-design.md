# Daily-Report 统一采集脚本设计

日期：2026-06-11
状态：待实施

---

## 背景

当前 daily-report 的 5 个变体（memory/llm/agent/news/builders）采集层存在以下问题：

- **学术变体（memory/llm/agent）**：完全依赖 WebSearch，不稳定、不可复现、覆盖面窄
- **news 变体**：`prepare_digest.py` 只覆盖 4 个 RSS 源，无 RSS 的源靠 WebSearch 逐个搜
- **builders 变体**：Node.js 管道从远程 GitHub 拉配置，与 Python 管道割裂
- **无统一框架**：5 个变体各自采集，技术栈割裂（Python vs Node.js），无法共享逻辑

参考 papers-site 的实际收录数据（1,208 篇论文，27.5% 非 arXiv 来源），当前搜索范围明显不足。

## 目标

构建统一的采集脚本 `collect.py`，覆盖学术 + 资讯两个大类，替代各变体分散的采集逻辑。

核心原则：**确定性优先，WebSearch 补缺**。

## 架构

### 采集策略分层

```
Step 1a: 确定性采集（可复现、可重试）
  ├── arXiv API      ← 学术变体的核心源
  ├── RSS feeds      ← bioRxiv / ACL / Nature / Cell
  ├── PubMed API     ← 生物医学记忆研究
  ├── GitHub Releases ← frameworks 动态
  ├── HuggingFace    ← trending 模型
  └── OpenReview     ← ICLR 等会议论文

Step 1b: WebSearch 补缺（确定性采集覆盖不到的）
  ├── 学术：arXiv API 没搜到的冷门关键词组合
  ├── news：Anthropic/OpenAI/国内厂商等无 RSS 的官方博客
  └── builders：X/Twitter 采集失败时的降级方案
```

80% 走确定性 API/RSS，20% WebSearch 补缺。

### 文件结构

```
.claude/skills/daily-report/scripts/
  collect.py                    ← 统一入口 CLI
  collectors/
    __init__.py
    arxiv.py                    ← arXiv API 采集
    rss.py                      ← 通用 RSS 采集
    pubmed.py                   ← NCBI E-utilities
    openreview.py               ← OpenReview API
    github.py                   ← GitHub Releases
    huggingface.py              ← HF trending
    websearch.py                ← WebSearch 补缺（输出待补缺清单）
  config/
    sources.json                ← 扩展后的统一配置
    credentials.json            ← 不动
```

### CLI 接口

```bash
# 采集学术论文（memory/llm/agent 变体共用）
python scripts/collect.py --board memory --date 2026-06-11 --output $WORKSPACE/01-search.json

# 采集技术资讯
python scripts/collect.py --board news --date 2026-06-11 --output $WORKSPACE/01-search.json

# 只跑确定性采集（不补 WebSearch）
python scripts/collect.py --board memory --no-websearch --output ...

# dry run（只输出采集计划，不实际请求）
python scripts/collect.py --board memory --dry-run
```

`--board` 参数决定调用哪些采集器和关键词配置。

## 统一 JSON 输出格式

```json
{
  "board": "memory",
  "date": "2026-06-11",
  "generated_at": "2026-06-11T16:20:00+08:00",
  "items": [
    {
      "id": "arxiv:2605.16289",
      "title": "Memory-Efficient KV Cache Compression via Adaptive Quantization",
      "url": "https://arxiv.org/abs/2605.16289",
      "authors": ["Chen et al.", "ByteDance"],
      "date": "2026-05-16",
      "source": "arxiv",
      "source_category": "cs.CL",
      "abstract": "We propose...",
      "tags": ["kv-cache", "compression", "memory"],
      "board_match": ["memory", "llm"],
      "collected_by": "arxiv_collector"
    }
  ],
  "stats": {
    "total": 85,
    "by_source": {"arxiv": 45, "biorxiv": 8, "acl": 5, "pubmed": 12},
    "by_board": {"memory": 62, "llm": 40, "agent": 35},
    "errors": []
  }
}
```

关键字段说明：

| 字段 | 说明 |
|------|------|
| `id` | 唯一标识，格式 `{source}:{identifier}`，去重用 |
| `board_match` | 一条论文可匹配多个变体，采集时自动标注 |
| `tags` | 从标题/摘要提取的关键词，供下游分组 |
| `collected_by` | 标记采集器，便于排查 |

## 采集器设计

### arxiv.py — 核心采集器

- 输入：board → 关键词 + arXiv 分类
- arXiv API 查询：`http://export.arxiv.org/api/query`
- 过滤：只保留最近 N 天内的论文（默认 3 天）
- 去重：同一 arXiv ID 只保留一条
- 关键词来源：`config/sources.json` 中的 `keywords` 配置

### rss.py — 通用 RSS 采集器

- 输入：RSS URL 列表（从 sources.json 读取）
- 复用已有的 feedparser 解析逻辑（从 prepare_digest.py 提取）
- 过滤：只保留最近 N 天的条目
- 支持的 RSS 源：bioRxiv、ACL Anthology、Nature、Cell Press 等

### pubmed.py — PubMed 采集器

- NCBI E-utilities API：`esearch` 搜索 + `efetch` 获取详情
- 查询词从 sources.json 配置
- 输出格式对齐统一 JSON schema

### openreview.py — OpenReview 采集器

- API：`https://api.openreview.net/notes`
- 指定 venue（如 ICLR 2026）+ 关键词过滤
- 只保留 memory/llm/agent 相关论文

### github.py — GitHub Releases 采集器

- 从 prepare_digest.py 迁移，逻辑不变
- 遍历 config 中的 repo 列表，获取最近 3 个 release
- 输出格式对齐统一 JSON schema

### huggingface.py — HF Trending 采集器

- 从 prepare_digest.py 迁移，逻辑不变
- `GET https://huggingface.co/api/models?limit=20`
- 输出格式对齐统一 JSON schema

### websearch.py — WebSearch 补缺采集器

- 不直接调 WebSearch API，输出"待补缺清单"
- 补缺清单来源：
  1. 确定性采集中标记为 `needs_followup` 的条目（如 RSS 解析失败的源）
  2. sources.json 中 `needs_websearch` 列表（无 RSS 的官方源）
  3. 学术变体中特定关键词组合的补充搜索
- 输出 `needs_websearch` 列表，每个条目包含 `{source, query, reason}`
- Claude 在 Step 1b 中读取此列表，用 WebSearch 工具逐条补缺，结果追加到 items 数组
- 最终 01-search.json 包含确定性采集 + WebSearch 补缺的合并结果

采集器之间无依赖，可并行执行。每个采集器独立输出 `list[dict]`，collect.py 统一合并去重。

## 去重逻辑

两层去重：

1. **源级去重**（collect.py 内部）：
   - URL 去重：同一 URL 只保留一条
   - arXiv ID 去重：`arxiv:2605.16289` 只保留一条
   - 标题模糊匹配：相似度 > 0.85 视为同一论文

2. **Wiki 级去重**（Step 2）：
   - 读取 `kb/papers/INDEX.md` 和 `kb/tech-news/INDEX.md`
   - 排除已入库条目

两层不冲突。

## sources.json 配置格式

扩展后的完整配置：

```json
{
  "proxy": "http://127.0.0.1:7897",
  "date_range_days": 3,
  "arxiv": {
    "categories": {
      "memory": ["cs.AI", "cs.CL", "cs.LG", "cs.NE", "cs.CV", "cs.RO", "cs.SE", "cs.HC", "cs.IR", "stat.ML", "q-bio.NC", "q-bio.BM", "q-bio.QM"],
      "llm": ["cs.CL", "cs.LG", "cs.AI"],
      "agent": ["cs.AI", "cs.CL", "cs.NE", "cs.RO", "cs.HC", "cs.SE"],
      "news": []
    },
    "max_results": 100
  },
  "keywords": {
    "memory": {
      "board1": ["KV cache", "context compression", "long-term dependency", "long context memory", "test-time training", "inference-time compute", "memory-augmented", "context caching"],
      "board2": ["agent memory", "memory architecture", "memory retrieval", "memory compression", "experience replay", "RAG agent", "working memory", "episodic memory", "cognitive architecture", "persistent memory"],
      "board3": ["memory consolidation", "hippocampus", "sleep memory", "synaptic plasticity", "forgetting", "Hopfield", "free energy memory", "engram", "place cell", "grid cell", "memory reconsolidation", "memory interference"]
    },
    "llm": {
      "main": ["large language model", "foundation model", "LLM", "multimodal", "long context", "reasoning", "alignment", "model compression", "efficient inference", "training method"]
    },
    "agent": {
      "main": ["agent", "multi-agent", "tool-use", "planning", "agent memory", "autonomous agent", "computer use", "agent RL", "agent benchmark", "agent security"]
    }
  },
  "rss_feeds": [
    {"url": "https://connect.biorxiv.org/biorxiv_xml.php?subject=neuroscience", "name": "bioRxiv Neuroscience", "category": "academic", "boards": ["memory"]},
    {"url": "https://aclanthology.org/rss/new.xml", "name": "ACL Anthology", "category": "academic", "boards": ["memory", "llm", "agent"]},
    {"url": "https://www.nature.com/nature.rss", "name": "Nature", "category": "journal", "boards": ["memory"]},
    {"url": "https://www.nature.com/nneuro.rss", "name": "Nature Neuroscience", "category": "journal", "boards": ["memory"]},
    {"url": "https://www.cell.com/cell/rss", "name": "Cell Press", "category": "journal", "boards": ["memory"]},
    {"url": "https://blog.google/innovation-and-ai/technology/ai/rss/", "name": "Google AI Blog", "category": "tech", "boards": ["news"]},
    {"url": "https://blogs.nvidia.com/feed/", "name": "NVIDIA Blog", "category": "tech", "boards": ["news"]},
    {"url": "https://huggingface.co/blog/feed.xml", "name": "HuggingFace Blog", "category": "tech", "boards": ["news"]},
    {"url": "https://blogs.microsoft.com/ai/feed/", "name": "Microsoft AI Blog", "category": "tech", "boards": ["news"]}
  ],
  "pubmed": {
    "queries": {
      "memory": ["memory consolidation hippocampus", "synaptic plasticity forgetting", "sleep memory consolidation"]
    },
    "retmax": 50
  },
  "openreview": {
    "venues": ["ICLR.cc/2026/Conference"],
    "keywords": ["memory", "KV cache", "agent memory"]
  },
  "github_repos": [
    {"owner": "langchain-ai", "repo": "langchain", "boards": ["news"]},
    {"owner": "microsoft", "repo": "autogen", "boards": ["news"]},
    {"owner": "crewAIInc", "repo": "crewAI", "boards": ["news"]},
    {"owner": "langgenius", "repo": "dify", "boards": ["news"]}
  ],
  "huggingface": {"limit": 20},
  "needs_websearch": [
    {"source": "Anthropic", "url": "https://anthropic.com/news", "boards": ["news"], "reason": "No RSS feed"},
    {"source": "OpenAI", "url": "https://openai.com/blog", "boards": ["news"], "reason": "No RSS feed"},
    {"source": "Meta AI", "url": "https://ai.meta.com/blog", "boards": ["news"], "reason": "No RSS feed"},
    {"source": "Mistral", "url": "https://mistral.ai/news", "boards": ["news"], "reason": "No RSS feed"},
    {"source": "DeepSeek", "url": "https://deepseek.com", "boards": ["news"], "reason": "No RSS feed, Chinese company"},
    {"source": "Anthropic engineering blog", "url": "https://anthropic.com/engineering", "boards": ["news"], "reason": "No RSS feed"},
    {"source": "冷门学术关键词补搜", "query": "board-specific", "boards": ["memory", "llm", "agent"], "reason": "arXiv API 关键词覆盖不到的边缘方向"}
  ]
}
```

## 与现有流水线的衔接

collect.py 替代 Step 1（搜索/采集），其他步骤不变：

```
之前：
Step 1: Claude 手动 WebSearch → 01-search.json
Step 2: Claude 手动去重

之后：
Step 1: python collect.py --board memory → 01-search.json（自动采集+自动去重）
Step 2: Claude 读 01-search.json + kb/papers/INDEX.md 做 Wiki 入库级去重
```

### 废弃与保留

| 组件 | 状态 | 说明 |
|------|------|------|
| `prepare_digest.py` | 废弃 | 功能被 collect.py 的 github.py + huggingface.py + rss.py 替代 |
| `prepare-digest.js` | 保留 | builders 变体的 X/播客/YouTube 采集不在本次范围 |
| `progress_manager.py` | 保留 | collect.py 执行完后由 Claude 调用更新状态 |
| `validate_report.py` | 保留 | 不动 |

### progress.json 衔接

collect.py 本身不管 progress.json，保持单一职责。执行完后由 Claude 调用：

```bash
python scripts/progress_manager.py update $WORKSPACE 01_search done
```

## 实施计划

按 Phase 增量交付，每完成一个 Phase 可独立使用：

| Phase | 内容 | 覆盖变体 | 依赖 |
|-------|------|---------|------|
| 1 | `arxiv.py` + `rss.py` + `sources.json` 扩展 + `collect.py` 入口 | memory（核心需求） | feedparser（已有） |
| 2 | `pubmed.py` + `openreview.py` | memory 补全 | requests（已有） |
| 3 | `github.py` + `huggingface.py`（从 prepare_digest.py 迁移） | news | requests（已有） |
| 4 | `websearch.py` 补缺清单输出 | 全部 | 无新依赖 |

### Python 依赖

```
# 已有（.venv 中已安装）
requests
feedparser

# 新增（如需）
# 无额外依赖，标准库 + 已有库足够
```

## 不在本次范围

- builders 变体的 Node.js 采集管道（prepare-digest.js）
- 流程编排引擎（progress.json 自动化、自动重试/超时）
- 发布环节改进（feishu-doc-op / wechat-mp）
- Wiki 入库逻辑改动
- 日报格式改动
