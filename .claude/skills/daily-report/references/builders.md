# builders 变体：AI博主/播客日报

**何时阅读**：执行 `/daily-report builders` 时读取此文件。

---

## 采集方式

### Step 1a: 运行 prepare-digest.js（确定性数据采集）

```bash
cd .claude/skills/daily-report/builders/scripts && node prepare-digest.js 2>/dev/null
```

脚本输出 JSON，包含：
- `x` — AI builders 的近期推文（文本、URL、bio）
- `podcasts` — 播客节目及完整 transcript
- `blogs` — AI 公司官方博客新文
- `youtube` — YouTube 频道新视频
- `prompts` — 各板块的摘要/翻译指导 prompt

首次使用需安装Node.js依赖：
```bash
cd .claude/skills/daily-report/builders/scripts && npm install
```

### Step 1b: LLM 精炼

对 prepare-digest.js 输出的 JSON 进行内容策展和摘要撰写，遵循 prompts/ 目录下的指导：
- 推文：按 `prompts/summarize-tweets.md` 摘要
- 播客：按 `prompts/summarize-podcast.md` 摘要
- 博客：按 `prompts/summarize-blogs.md` 摘要
- 翻译：按 `prompts/translate.md` 翻译

JSON是builders变体的唯一内容源。独立搜索会打断溯源链——每条内容必须追溯到JSON中的原始URL，读者才能验证信息来源。

## 信息源

- **X/Twitter builders**：AI 行业顶级 builder（研究员、创始人、PM、工程师），由 `feeds/feed-x.json` 中心化维护
- **播客**：由 `feeds/feed-podcasts.json` 维护
- **YouTube**：由 `feeds/feed-youtube.json` 维护
- **博客**：由 `feeds/feed-blogs.json` 维护

源列表中心化更新，用户自动获取最新源。

## Wiki摄入

遵循 `references/wiki-ingest.md`（路径 kb/tech-news/），铁律见 `references/wiki-rules.md`。

## 日报结构

- **一、今日亮点**（3-5 条，带 emoji）
- **二、X / Twitter** 🐦 — builder 观点摘要（每条按 标题 → 来源 → 图片 → 内容 排列）
- **三、官方博客** 📰 — 公司官方博文（每条按 标题 → 来源 → 图片 → 内容 排列）
- **四、YouTube 视频** 🎬 — 频道视频摘要（每条按 标题 → 来源 → 图片 → 内容 排列，图片用缩略图）
- **五、Podcasts** 🎙️ — 播客节目摘要（每条按 标题 → 来源 → 内容 排列）
- **六、狐狸点评** 🦊

## 日报标题

飞书："🦊 AI Builders 每日摘要 | YYYY-MM-DD（周X）"
微信："AI Builders 每日摘要 | YYYY-MM-DD"

## 来源标注格式

- 飞书版本：链接格式，`<lark-table>` 支持 `<image>` 嵌图
- 微信版本：纯文本 `<span style="color:#ff6b35;font-weight:bold">`，无 `<a>` 链接