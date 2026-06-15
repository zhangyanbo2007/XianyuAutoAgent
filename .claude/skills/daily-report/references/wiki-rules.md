# Wiki铁律

**何时阅读**：Step 3 Wiki入库和Step 4 索引更新时读取此文件。学术板块和资讯板块共享同一铁律。

---

1. **refs/ 只读** — refs/papers/（学术）和 refs/tech-news/（资讯）只添加不删除，原始参考资料不可变
2. **每次操作更新 INDEX.md + LOG.md** — 入库、修改、删除操作必须同步更新对应板块的索引和日志
3. **`[text](path)` markdown 链接交叉引用** — 每个wiki页面必须包含指向其他相关页面的markdown链接，复利累积的引擎
4. **Wiki frontmatter 格式不同于 kb/ 其他页面** — wiki子系统有独立的frontmatter格式（见 `references/wiki-ingest.md` 字段对照表），不与kb/主区域frontmatter混用