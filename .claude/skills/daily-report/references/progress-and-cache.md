# Progress与缓存管理

**何时阅读**：每次执行daily-report技能时，在Step 0准备阶段读取此文件，了解progress.json格式、缓存恢复逻辑、目录结构和文件命名规范。

---

## 缓存检查与恢复

检查 `$WORKSPACE/progress.json` 是否存在：

- **不存在** → 新执行，初始化 progress.json
- **存在** → 恢复执行：跳过所有 `done` 步骤，从第一个 `pending` 或 `failed` 步骤继续

## progress.json格式

```json
{
  "板块": "<memory|llm|agent|news|builders>",
  "日期": "<YYYY-MM-DD>",
  "steps": {
    "01_search": "pending|done|failed",
    "02_dedup": "pending|done|failed",
    "03_wiki_ingest": "pending|done|failed",
    "04_index_update": "pending|done|failed",
    "05_report_md": "pending|done|failed",
    "06_feishu": "pending|done|failed",
    "07_cover": "pending|done|failed",
    "08_cover_upload": "pending|done|failed",
    "09_wechat_html": "pending|done|failed",
    "10_wechat_draft": "pending|done|failed",
    "11_result": "pending|done|failed"
  }
}
```

学术和资讯板块使用相同step名称，仅`板块`字段不同。

## 初始化

```bash
python3 scripts/progress_manager.py init <board> <date> <workspace>
```

替代heredoc方式。脚本直接生成正确格式的progress.json。

## 更新状态

```bash
# 标记完成
python3 scripts/progress_manager.py update <workspace> <step_key> done

# 标记失败
python3 scripts/progress_manager.py update <workspace> <step_key> failed

# 查看当前状态和下一步
python3 scripts/progress_manager.py check <workspace>
```

## 工作区目录结构

```
projects/daily-report/YYYY-MM-DD/
  memory/          ← 记忆系统深度日报
    progress.json, 01-search.json, 02-new-papers.json, ...
  llm/             ← 大模型广度日报
    progress.json, 01-search.json, 02-new-papers.json, ...
  agent/           ← 智能体广度日报
    progress.json, 01-search.json, 02-new-papers.json, ...
  news/            ← 技术资讯日报
    progress.json, 01-search.json, ...
  builders/        ← AI博主/播客日报
    progress.json, 01-search.json, ...
```

## 工作区文件命名

| 步骤 | 学术板块 | 资讯板块 | 内容 |
|------|----------|----------|------|
| Step 1 | `01-search.json` | `01-search.json` | 搜索/采集结果原始数据 |
| Step 2 | `02-new-papers.json` | `02-dedup.json` | 去重结果 |
| Step 3 | `03-wiki-done.json` | `03-wiki-done.json` | Wiki入库统计 |
| Step 4 | `04-index-update-done.json` | `04-index-update-done.json` | 索引更新记录 |
| Step 5 | `05-report.md` + `05-images/` | `05-report.md` + `05-images/` | 日报全文+图片素材 |
| Step 6 | `06-feishu-url.txt` | `06-feishu-url.txt` | 飞书文档URL |
| Step 7 | `07-cover.png` | `07-cover.png` | 封面图 |
| Step 9 | `09-wechat.html` | `09-wechat.html` | 微信HTML |
| Step 11 | `11-result.txt` | `11-result.txt` | 最终输出摘要 |