# Digest Intro Prompt

You are assembling the final digest from individual source summaries.

## Format

Start with this header (replace [Date] with today's date):

AI Builders 每日摘要 — [Date]

Then organize content with numbered Chinese headers:

一、X / Twitter
二、官方博客
三、YouTube 视频
四、Podcasts

**When delivery method is "wechat", ALL content must be in HTML format** with card-style layout and inline CSS styles. WeChat Official Account articles require HTML (not Markdown). When delivery method is not "wechat", use standard Markdown.

## Mobile-First Card Layout (for WeChat delivery)

WeChat articles are read on phones. Multi-column tables are hard to read on small screens. Instead, use vertical card-style layout with clear visual separation.

**Core principles:**
- NO `<table>` elements — use `<div>` cards stacked vertically
- Full-width single column
- Clear visual hierarchy: section header > item card > metadata
- Generous whitespace for readability on small screens
- Font sizes: body 15px, small text 13px, section headers 17px, title 19px
- Every item is a self-contained card

### Base HTML Structure

```html
<!-- Section header -->
<h2 style="font-size:17px;font-weight:bold;margin:22px 0 12px;border-bottom:2px solid #333;padding-bottom:6px;">一、X / Twitter</h2>

<!-- Channel sub-header (YouTube only) -->
<h3 style="font-size:15px;font-weight:bold;margin:16px 0 10px;color:#555;">YC Startup School</h3>

<!-- Card separator: a thin line between items -->
<div style="height:1px;background:#eee;margin:10px 0;"></div>
```

### Card Styles By Section

#### 一、X / Twitter Card

```
<div style="padding:6px 0;">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
    <span style="font-size:15px;font-weight:bold;color:#333;">Author Name</span>
    <span style="font-size:13px;color:#999;white-space:nowrap;">YYYY-MM-DD</span>
  </div>
  <p style="font-size:15px;color:#555;line-height:1.6;margin:4px 0 6px;">Summary text 2-3 sentences...</p>
  <a href="URL" style="font-size:14px;color:#576b95;">X 原文 ›</a>
</div>
```

#### 二、官方博客 Card

```
<div style="padding:6px 0;">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
    <span style="font-size:13px;color:#888;">Source Name</span>
    <span style="font-size:13px;color:#999;white-space:nowrap;">YYYY-MM-DD</span>
  </div>
  <a href="URL" style="font-size:16px;font-weight:bold;color:#333;text-decoration:none;display:block;margin:2px 0 4px;">Article Title</a>
  <p style="font-size:15px;color:#555;line-height:1.6;margin:4px 0 6px;">Summary 2-3 sentences...</p>
  <a href="URL" style="font-size:14px;color:#576b95;">查看原文 ›</a>
</div>
```

#### 三、YouTube 视频 Card (compact thumbnail + text row)

Keep YouTube cards tight — no separators between videos within the same channel group. Small thumbnail with text to the right.

```
<div style="display:flex;gap:8px;align-items:flex-start;margin-bottom:6px;">
  <a href="URL" style="flex-shrink:0;width:100px;">
    <img src="{wechat_thumbnail_url}" width="100" style="border-radius:4px;display:block;width:100px;height:56px;object-fit:cover;"/>
  </a>
  <div style="flex:1;min-width:0;">
    <a href="URL" style="font-size:14px;font-weight:bold;color:#333;text-decoration:none;display:block;margin-bottom:1px;line-height:1.3;">Chinese Title</a>
    <p style="font-size:13px;color:#666;line-height:1.4;margin:0 0 1px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">Short description one line...</p>
    <span style="font-size:11px;color:#999;">YYYY-MM-DD</span>
  </div>
</div>
```

#### 四、Podcasts Card

```
<div style="padding:6px 0;">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
    <span style="font-size:13px;color:#888;">Podcast Name</span>
    <span style="font-size:13px;color:#999;white-space:nowrap;">YYYY-MM-DD</span>
  </div>
  <a href="URL" style="font-size:16px;font-weight:bold;color:#333;text-decoration:none;display:block;margin:2px 0 4px;">Episode Title</a>
  <p style="font-size:15px;color:#555;line-height:1.6;margin:4px 0 6px;">Remix summary 2-3 sentences...</p>
  <a href="URL" style="font-size:14px;color:#576b95;">播客链接 ›</a>
</div>
```

### Page Header

```html
<p style="font-size:19px;font-weight:bold;text-align:center;margin:20px 0 10px;">AI Builders 每日摘要 — 2026-05-12</p>
<p style="font-size:13px;color:#999;text-align:center;margin:0 0 20px;">2026-05-12 更新</p>
```

### Footer

```html
<p style="text-align:center;color:#bbb;font-size:12px;margin:30px 0 10px;line-height:1.8;">
  Generated through the Follow Builders skill<br>
  <a href="https://github.com/zhangyanbo2007/follow-builders" style="color:#576b95;">github.com/zhangyanbo2007/follow-builders</a>
</p>
```

### Body defaults

```html
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;padding:12px 16px;max-width:640px;margin:0 auto;background:#fff;color:#333;font-size:15px;">
```

## Hyperlinks in WeChat Articles

WeChat Official Account articles support `<a href="URL">text</a>` HTML tags. All external links (X/Twitter, YouTube, blog URLs) work but will show a standard "即将打开外部网页" confirmation dialog — this is expected WeChat behavior and does not require special configuration.

Best practices for links:
- Make titles/headings clickable
- Use descriptive Chinese text + arrow for link labels: `查看原文 ›`, `X 原文 ›`, `播客链接 ›`
- NEVER use bare URLs as link text — always wrap in `<a>` with descriptive text
- Links in titles: use `text-decoration:none;color:#333;` for clean look

## ALL items must include dates

Every content card must display the publication date in YYYY-MM-DD format, placed in the top-right of the card header. Sources without explicit dates should use the feed generation date as fallback.

## Section Specifications

### 一、X / Twitter

Stack cards vertically, separated by thin dividers. Each card:
- Author name (full name, no @handles) on the left, date on the right
- 2-3 sentence summary
- "X 原文 ›" link to the most important tweet URL
- Date source: tweet `createdAt` field. If multiple tweets, use latest. Fallback: Snowflake ID decoding `new Date(Number(BigInt(id) >> 22n) + 1288834974657).toISOString().slice(0,10)`

### 二、官方博客

Stack cards vertically. Each card:
- Source name + date in header
- Article title as clickable link (16px bold)
- 2-3 sentence summary
- "查看原文 ›" link

### 三、YouTube 视频

Group by channel with channel sub-headers. Each card uses flex layout: thumbnail on the left, text on the right.
- Thumbnail: `<img src="{wechat_url}" width="140" style="border-radius:4px;">` — clickable thumbnail linking to video
- Title: translated Chinese title (15px bold) as clickable link
- Description: 1-2 sentence summary (14px, #666)
- Date: 12px, #999
- For WeChat: use WeChat media URLs from thumbnail map, NOT YouTube URLs

### 四、Podcasts

Stack cards vertically. Each card:
- Podcast name + date in header
- Episode title as clickable link
- 2-3 sentence remix summary
- "播客链接 ›" link to episode

## General Rules

- Only include sources that have new content. Skip empty sections.
- Every piece of content MUST have its original source link. No link = do not include.
- NEVER invent or fabricate content. Only use what's in the JSON.
- NEVER make up quotes, opinions, or content.
- Card separators: `<div style="height:1px;background:#eee;margin:10px 0;"></div>` between cards
- First card in each section: no preceding separator