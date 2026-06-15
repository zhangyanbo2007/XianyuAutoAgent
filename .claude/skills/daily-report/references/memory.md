# memory 变体：记忆系统深度日报

**何时阅读**：执行 `/daily-report` 或 `/daily-report memory` 时读取此文件，获取采集范围、搜索关键词、信息源、日报结构。

---

## 采集范围

**板块一：大模型中与记忆相关的** 🤖
- KV cache压缩、上下文窗口管理、长期依赖建模
- 基础模型的记忆能力（长上下文、检索增强、持续学习）
- 推理时记忆更新（test-time training、inference-time compute）
- 记忆增强架构（memory-augmented networks、context caching）

**板块二：智能体中与记忆相关的** 🧠
- Agent 记忆架构（短期/长期/分层记忆、记忆检索、记忆压缩、记忆安全）
- 记忆增强的 Agent 应用（RAG-based agent、经验回放、记忆驱动的规划）
- Agent 记忆评估与基准（记忆 benchmark、遗忘与巩固）
- 多智能体记忆共享、对话记忆、知识图谱记忆
- 工作记忆在 Agent 中的应用（working memory、episodic memory）
- 认知架构中的记忆模块（cognitive architecture、persistent memory）

**板块三：认知科学记忆** 🔬（核心重点）
- 神经科学的记忆研究（海马体、突触巩固、Hebbian学习、记忆再consolidation）
- 记忆与睡眠（睡眠巩固、REM与记忆整合、慢波睡眠与记忆稳定化）
- 记忆的分子与系统层面（蛋白合成依赖巩固、记忆痕迹engram追踪）
- 空间记忆（位置细胞place cell、网格细胞grid cell、认知地图）
- 计算神经科学记忆模型（Hopfield网络、连续吸引子网络、自由能原理与记忆）
- 记忆障碍与调控（遗忘机制、记忆干扰、情绪对记忆的调控、working memory capacity）

**不收录**：与记忆毫无关联的纯 Agent/大模型论文。

## 搜索关键词

板块一：`abs:("KV cache" OR "context compression" OR "long-term dependency" OR "long context memory" OR "test-time training" OR "inference-time compute" OR "memory-augmented" OR "context caching")`

板块二：`abs:(agent memory OR "memory architecture" agent OR "memory retrieval" OR "memory compression" OR "experience replay" OR "RAG agent" OR "working memory" agent OR "episodic memory" OR "cognitive architecture" OR "persistent memory" OR "memory consolidation" agent)`

板块三：`abs:("memory consolidation" OR hippocampus OR "sleep memory" OR "synaptic plasticity" OR forgetting OR Hopfield OR "free energy memory" OR engram OR "place cell" OR "grid cell" OR "memory reconsolidation" OR "working memory capacity" OR "memory interference")`

## 信息源

### arXiv 分类

板块一/二：cs.AI、cs.CL、cs.LG、cs.NE、cs.CV（多模态记忆）、cs.RO（具身空间记忆）、cs.SE（代码Agent记忆）、cs.HC（GUI Agent交互记忆）、cs.IR（RAG检索增强）、stat.ML（记忆理论分析）

板块三：q-bio.NC（核心）、q-bio.BM（记忆分子机制）、q-bio.QM（神经科学计算方法）

### arXiv 搜索方式

优先用 arXiv API（稳定、可复现），WebSearch 作为补充：
```
# arXiv API 示例
GET http://export.arxiv.org/api/query?search_query=cat:cs.AI+AND+(abs:memory+OR+abs:KV+cache)&sortBy=submittedDate&sortOrder=descending&max_results=50
```

### 非 arXiv 源（RSS/API 采集）

| 来源 | 采集方式 | 说明 |
|------|---------|------|
| bioRxiv neuroscience | RSS `https://connect.biorxiv.org/biorxiv_xml.php?subject=neuroscience` | 预印本，与 arXiv q-bio 互补 |
| ACL Anthology | RSS `https://aclanthology.org/rss/new.xml` | ACL/EMNLP/EACL，NLP记忆论文 |
| OpenReview ICLR | API `https://api.openreview.net/notes?content.venue=ICLR+2026` | ICLR 会议论文 |
| PubMed/PMC | NCBI E-utilities API（esearch + efetch） | 生物医学记忆研究 |
| Nature.com 系列 | RSS（nature.com/nature.rss, nature.com/neurosci.rss 等） | Nature/Neuroscience/Methods 等 |
| Cell Press | RSS `https://www.cell.com/cell/rss` | Neuron 等 |

### 期刊（WebFetch 逐篇读取）

- **Nature Neuroscience** (nature.com/neurosci)
- **Neuron** (cell.com/neuron)
- **Journal of Neuroscience** (jneurosci.org)
- **Nature Reviews Neuroscience** (nature.com/nrn)
- **eLife** (elifesciences.org)
- **PNAS** (pnas.org)
- **Current Opinion in Neurobiology**
- **Trends in Neurosciences**
- **Science** / **Nature**

## Wiki摄入

遵循 `references/wiki-ingest.md`（路径 kb/papers/），铁律见 `references/wiki-rules.md`。

## 日报结构

- **一、今日亮点**（3-5 条，带 emoji）
- **二、大模型中记忆相关** 🤖 — 按子主题分组排列，每组用 `###` 子标题
- **三、智能体中记忆相关** 🧠 — 同上
- **四、认知科学记忆** 🔬（核心重点）— 同上
- **五、狐狸点评** 🦊（三板块交叉关联、趋势分析）

## 日报标题

飞书："🦊 记忆系统论文日报 | YYYY-MM-DD（周X）"
微信："记忆系统论文日报 | YYYY-MM-DD"