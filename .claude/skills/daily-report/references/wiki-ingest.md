# Wiki摄入通用流程

**何时阅读**：Step 3 Wiki入库时读取此文件，了解统一的摄入流程。不同变体仅路径和frontmatter字段不同。

---

## 学术板块 Wiki摄入（→ kb/papers/）

1. 去重：读取 `kb/papers/INDEX.md`
2. 对每篇新论文：
   - 下载 PDF 到 `refs/papers/`
   - WebFetch 读取论文内容
   - 创建论文摘要页 `kb/papers/papers/`
   - 创建/更新概念页 `kb/papers/concepts/`
   - 创建/更新实体页 `kb/papers/entities/`
   - 每页必须包含 `[text](path)` markdown 链接交叉引用
3. 更新 `kb/papers/INDEX.md` + `kb/papers/LOG.md`

## 资讯板块 Wiki摄入（→ kb/tech-news/）

1. 去重：读取 `kb/tech-news/INDEX.md`
2. 对每条重要资讯/洞察：
   - 保存原文到 `refs/tech-news/`
   - WebFetch 读取原文获取完整细节
   - 创建资讯/洞察分析页 `kb/tech-news/news/`
   - 创建/更新概念页 `kb/tech-news/concepts/`
   - 创建/更新实体页 `kb/tech-news/entities/`
   - 每页必须包含 `[text](path)` markdown 链接交叉引用
3. 更新 `kb/tech-news/INDEX.md` + `kb/tech-news/LOG.md`

## Frontmatter字段对照

| 页面类型 | 学术板块 | 资讯板块 |
|----------|----------|----------|
| 论文/资讯页 | `title, authors, year, venue, tags, arxiv_id, ingested` | `title, source, date, tags, url, ingested` |
| 概念页 | `topic, tags, created` | `topic, tags, created` |
| 实体页 | `name, type, institution, tags, created` | `name, type, company, tags, created` |

## INDEX.md标记

| 板块 | 大模型 | 智能体 | 其他 |
|------|--------|--------|------|
| 学术(kb/papers/) | 🤖 | 🧠 | 🔬 神经科学 |
| 资讯(kb/tech-news/) | 🧠 | 🤖 | 📰 行业要闻 |