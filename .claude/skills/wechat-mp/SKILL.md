---
name: wechat-mp
description: WeChat Official Account (微信公众号) article publishing — convert markdown to WeChat-compatible HTML with theme presets, callout syntax, and frontend-design aesthetics, create drafts, and publish articles via MP API.
trigger: 微信公众号, wechat mp, wechat-mp, 公众号发布, 微信日报, 微信草稿
---

# wechat-mp Skill

微信公众号文章生成与发布工具。

## 设计理念

融合 frontend-design 技能的美学原则（大胆排版、独特色彩、空间构图、视觉细节），在微信严格约束下（无script/外部CSS/动画，仅内联样式）重新表达。

核心实现方式：
- **Typography**: 主题差异化字体栈（Georgia/宋体/楷体等微信webview支持的字体）
- **Color & Theme**: gradient 渐变背景、圆角、阴影、主题色体系
- **Spatial**: section 嵌套、margin/padding 层次、视觉分区
- **Visual**: CSS-only 装饰分割线、gradient 装饰条、圆角卡片

## 主题预设系统

四套主题预设，适应不同内容类型：

| 主题 | 主题名 | 适用场景 | 字体栈 | 特征 |
|---|---|---|---|---|
| `fox-orange` | 狐狸橙增强版 | 技术日报、常规文章 | Georgia + PingFang SC (serif-mixed) | 温暖活力，gradient 橙色装饰 |
| `midnight-ink` | 深蓝墨色 | 深度思考、文学、哲学 | Georgia + SimSun (宋体 serif) | 深邃墨色，琥珀金点缀 |
| `b612-starlight` | 小王子星光 | 创作类、叙事类、哲学随笔 | KaiTi + PingFang SC (楷体圆润) | 梦幻星空，星光黄点缀 |
| `scholar-green` | 学院绿 | 学术笔记、经典文献、研究 | SimSun + KaiTi (宋体楷体) | 古朴素雅，宣纸底色，翠绿 |

### 增强版视觉元素（所有主题共享结构，颜色按主题变化）

| 元素 | 增强方式 |
|---|---|
| h1 | 居中，主题色 |
| h2 | 前方 gradient 装饰条（`<section style="gradient bar">`） |
| blockquote | gradient 渐变背景 + 圆角8px + 阴影（替代 plain gray bg + left border） |
| strong | 主题色 + 微下划线装饰 |
| hr → decorative-divider | 主题色渐变装饰符号（◇ ◇ ◇ / ★ ★ ★） |
| table | 圆角8px + overflow:hidden + gradient header + 阴影 |
| 狐狸点评 | gradient 圆角卡片风格 |

### 主题选择

```bash
python3 scripts/md2wechat_html.py --input <md> --output <html> --theme fox-orange
python3 scripts/md2wechat_html.py --input <md> --output <html> --theme midnight-ink
python3 scripts/md2wechat_html.py --input <md> --output <html> --theme b612-starlight
python3 scripts/md2wechat_html.py --input <md> --output <html> --theme scholar-green
```

默认主题：`fox-orange`

## Callout 语法

Markdown 中支持三种特殊 callout 语法，自动转为带色圆角提示卡片：

| Markdown 语法 | 转为 | 主题色效果 |
|---|---|---|
| `> !提示 内容` | 绿色 tip-callout | gradient 绿色背景 + 圆角 |
| `> !警告 内容` | 红色 warning-callout | gradient 红/橙色背景 + 圆角 |
| `> !信息 内容` | 蓝色 info-callout | gradient 蓝色背景 + 圆角 |

也支持英文关键字：`> !tip`, `> !warning`, `> !info`

多行 callout：连续的 `>` 行会合并为同一 callout 块。

示例：
```markdown
> !提示 记忆巩固需要睡眠周期，而非简单的数据存储。
> 连续行会被合并到同一个提示块中。

> !警告 不可跳过睡眠阶段直接进入下一个认知循环。
```

## 当前阶段（未认证号 → 本地模式）

未认证号无法调用微信草稿/发布 API（2025年7月起限制），当前采用**本地生成**模式：
- 将 Markdown 转换为微信兼容 HTML（内联 CSS + 主题预设），保存到本地文件
- HTML 文件可直接粘贴到公众号后台编辑器（源代码模式）
- Markdown 文件可用于 135编辑器等第三方排版工具

## 认证后（一键切换 → API 模式）

认证后只需：
1. 在 `.openclaw/.env` 填入 `WECHAT_MP_APPID` 和 `WECHAT_MP_SECRET`
2. 在 `~/.wechat-mp/config.json` 将 `mode` 改为 `"draft"` 或 `"publish"`
3. 上传封面图获得 `cover_media_id`（使用 `wechat_api.py upload-cover`）

## 核心工具

### md2wechat_html.py — Markdown → 微信兼容 HTML

微信会剥离 `<style>` 标签和 JS，所以所有 CSS 必须内联。此工具将 markdown 转为内联 CSS 的 HTML，支持主题预设和 callout 语法。

```bash
python3 scripts/md2wechat_html.py \
  --input <markdown-file> \
  --output <html-file> \
  --theme fox-orange \
  --strip-frontmatter \
  --check-limits
```

参数：
- `--input`: 输入 markdown 文件路径
- `--output`: 输出 HTML 文件路径
- `--theme`: 主题预设（fox-orange/midnight-ink/b612-starlight/scholar-green），默认 fox-orange
- `--style`: CSS 样式文件路径（legacy 模式，默认使用内置 wechat-style.css）
- `--strip-frontmatter`: 去掉 YAML frontmatter
- `--check-limits`: 检查微信内容大小限制（< 20,000 字符 / < 1MB）
- `--json`: 输出 JSON 格式结果（含元数据、主题信息）

### wechat_publish.py — 发布编排器

整合 markdown→HTML 转换和微信 API 操作：

```bash
# 本地模式（当前阶段）- 默认 fox-orange 主题
python3 scripts/wechat_publish.py \
  --input <md-file> \
  --mode local \
  --config ~/.wechat-mp/config.json

# 本地模式 - 指定主题
python3 scripts/wechat_publish.py \
  --input <md-file> \
  --mode local \
  --theme b612-starlight \
  --config ~/.wechat-mp/config.json

# 草稿模式（认证后）
python3 scripts/wechat_publish.py \
  --input <md-file> \
  --title "文章标题" \
  --mode draft \
  --config ~/.wechat-mp/config.json

# 发布模式（认证后）
python3 scripts/wechat_publish.py \
  --input <md-file> \
  --title "文章标题" \
  --mode publish \
  --config ~/.wechat-mp/config.json
```

### wechat_api.py — 微信 MP API 封装（认证后启用）

```bash
python3 scripts/wechat_api.py get-token --config ~/.wechat-mp/config.json
python3 scripts/wechat_api.py upload-cover --filepath <image> --config ~/.wechat-mp/config.json
python3 scripts/wechat_api.py create-draft --title "标题" --content-file <html> --thumb-media-id <id> --config ~/.wechat-mp/config.json
python3 scripts/wechat_api.py publish-draft --media-id <id> --config ~/.wechat-mp/config.json
python3 scripts/wechat_api.py check-status --publish-id <id> --config ~/.wechat-mp/config.json
```

## 微信 MP API 约束

| 约束 | 限制 |
|------|------|
| 标题 | ≤ 64 字符 |
| 正文 HTML | ≤ 20,000 字符 / ≤ 1MB |
| `<script>` | 被剥离 |
| `<style>` | 被剥离 |
| 外部图片 URL | 被过滤，必须先用 `uploadimg` API 上传 |
| 封面图 | 需先上传为永久素材获得 `thumb_media_id` |
| 发布 | 异步操作，需轮询状态 |
| 未认证号 | 无法调用草稿/发布 API |

## CSS 样式

主题文件：`config/themes/` 目录下的四个主题 CSS
- `fox-orange.css`: 狐狸橙增强版（gradient 背景、圆角卡片、装饰分割线）
- `midnight-ink.css`: 深蓝墨色（深色主题、琥珀金、宋体）
- `b612-starlight.css`: 小王子星光（星空紫蓝渐变、星光黄、楷体）
- `scholar-green.css`: 学院绿（宣纸底色、翠绿、宋体楷体）

Legacy 样式：`config/wechat-style.css`（保留向后兼容）

## 配置文件

### ~/.wechat-mp/config.json

```json
{
  "mode": "local",
  "appid_env_key": "WECHAT_MP_APPID",
  "secret_env_key": "WECHAT_MP_SECRET",
  "cover_media_id": "",
  "author": "狐狸技术日报",
  "output_dir": "/home/xiaowangzi/.openclaw/workspace-fox-research/wechat-daily",
  "css_template": "/code/owner/xiaowangzi/.claude/skills/wechat-mp/config/wechat-style.css",
  "token_cache_path": "~/.wechat-mp/token_cache.json"
}
```

### .openclaw/.env（凭证，认证后启用）

```
# WeChat MP (公众号) — 认证后填写
# WECHAT_MP_APPID=wx_your_appid
# WECHAT_MP_SECRET=your_secret
```

## 微信发布流程

### 完整流程（草稿→发布）
1. `get_access_token()` → 获取 token（缓存 2 小时）
2. `upload_permanent_material()` → 上传封面图 → 获得 `thumb_media_id`
3. markdown → HTML（md2wechat_html.py，指定 --theme）
4. `create_draft()` → 创建草稿 → 获得 `media_id`
5. （可选）`publish_draft()` → 提交发布 → 获得 `publish_id`
6. （可选）`check_publish_status()` → 轮询发布状态