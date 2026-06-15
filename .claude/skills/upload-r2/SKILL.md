---
name: upload-r2
description: Upload local files to Cloudflare R2 and return publicly accessible URLs. HTML files render directly in browser (no forced download). Use this skill INSTEAD of upload-cos whenever the user says "上传到R2", "上传r2", "r2发布", "分享链接", "给别人看", "浏览器打开", "对外链接", or when the user needs a URL that others can view in browser without downloading. Also use for uploading images, videos, PDFs, and any other files that need public links. Prefer R2 over COS for HTML files because COS forces download while R2 renders inline. Trigger on: "上传", "发布", "publish", "share", "R2", "r2" — always check if the user means R2 vs COS before choosing the skill.
---

# Upload R2 — Cloudflare R2 文件上传技能

将本地文件上传到 Cloudflare R2，返回公开访问链接。HTML 文件直接在浏览器渲染，不会强制下载。

## 为什么选 R2 而非 COS

腾讯 COS 对 2024年1月后创建的桶强制开启下载策略（`Content-Disposition: attachment`），HTML 文件只能下载不能浏览。Cloudflare R2 无此限制，HTML 直接在浏览器渲染。

| 特性 | R2 | COS |
|------|-----|------|
| HTML浏览器渲染 | ✅ 直接渲染 | ❌ 强制下载 |
| 备案要求 | ✅ 无需备案 | ⚠️ 自定义域名需备案 |
| 出流量费用 | ✅ 免费 | ⚠️ 收费 |
| 存储 | 10GB免费 | 收费 |
| 公开访问URL | ✅ `pub-<id>.r2.dev` | ⚠️ 默认域名强制下载 |

**选择原则：HTML 文件一律用 R2；图片/视频等其他文件也可用 R2。只有用户明确说"COS"或"腾讯云"时才用 upload-cos。**

## 触发方式

- 用户说"上传到R2"、"上传r2"、"r2发布"、"分享链接"、"给别人看"
- 用户需要将 HTML 文件转为可直接浏览的公开 URL
- 用户说"浏览器能打开的链接"时优先用此技能而非 upload-cos
- `/upload-r2 <file_path>`
- 上传图片/视频/PDF等任何需要公开链接的文件

## 凭证配置

`~/.r2.yaml` 内容：
```yaml
r2:
  account_id: <your_cloudflare_account_id>
  access_key_id: <r2_api_token_access_key>
  secret_access_key: <r2_api_token_secret_key>
  bucket: xiaowangzi-files
  public_url: https://pub-<bucket_id>.r2.dev
```

### 获取凭证步骤

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com)
2. 左侧菜单 → R2 Object Storage → Manage R2 API Tokens
3. 创建 API Token（权限选"Object Read & Write"）
4. 记录 `Access Key ID` 和 `Secret Access Key`
5. 复制 `Account ID`（Dashboard URL 中的那串字符）
6. 在 R2 bucket 设置中开启 Public Access，记下 `pub-xxx.r2.dev` URL

## 上传方式

```bash
.claude/skills/upload-r2/.venv/bin/python3 .claude/skills/upload-r2/scripts/upload.py <file_path> [object_key]
```

- `file_path`: 本地文件路径（必填）
- `object_key`: R2上的目标路径（可选，默认按日期自动生成）
- 所有文件自动设置正确的 Content-Type
- HTML 文件浏览器直接渲染，不会强制下载

### 路径规则

未指定object_key时，自动按日期生成：
`<年>/<月>/<日>/<文件名>`

如：`2026/05/15/neuron-structure.html`

## 输出格式

```
✅ 上传成功
🔗 URL: https://pub-xxx.r2.dev/2026/05/15/file.html
📋 Markdown: [file.html](https://pub-xxx.r2.dev/2026/05/15/file.html)
📦 Size: 14.0KB | Type: text/html; charset=utf-8
```

## 依赖

- Skill 独立 `.venv`（`boto3, pyyaml`）
- `~/.r2.yaml` 凭证配置
- R2 bucket 需开启 Public Access