# Upload COS — 腾讯云COS文件上传技能

将本地文件上传到腾讯云COS，返回公开访问链接。支持HTML、图片、文档等任意文件类型。

## 触发方式

- 用户说"上传到腾讯云"、"上传COS"、"publish"、"发布HTML"、"对外链接"
- 用户需要将本地文件转为可公开访问的URL
- `/upload-cos <file_path>`

## 双桶策略

为解决原 bucket 的强制下载策略（`x-cos-force-download: true`），HTML 文件上传到专用 **webpages bucket**，其他文件上传到默认 bucket：

| 文件类型 | 目标 bucket | 浏览域名 | 说明 |
|----------|-------------|----------|------|
| HTML/HTM | `webpages-{appid}` | `cos-website.{region}.myqcloud.com` | 无强制下载，浏览器直接渲染 |
| 其他文件 | `openclaw-{appid}` | `cos.{region}.myqcloud.com` | 普通直链访问 |

## 上传方式

使用 Python SDK (`cos_python_sdk_v5`)，自动从 `~/.cos.yaml` 读取凭证。

### 凭证配置

`~/.cos.yaml` 内容：
```yaml
base:
  secretid: AKIDxxx
  secretkey: xxx
  bucket: openclaw-1257022348
  webpages_bucket: webpages-1257022348
  region: ap-guangzhou
```

### 上传脚本

```bash
.claude/skills/upload-cos/.venv/bin/python3 .claude/skills/upload-cos/scripts/upload.py <file_path> [object_key]
```

- `file_path`: 本地文件路径（必填）
- `object_key`: COS上的目标路径（可选，默认按日期自动生成）
- HTML文件自动上传到 `webpages` bucket，输出可浏览的 `cos-website` 域名链接
- 其他文件上传到默认 bucket，输出直链
- 所有文件自动设置 `ACL: public-read`

### 路径规则

未指定object_key时，自动按日期生成：
`<年>/<月>/<日>/<文件名>`

如：`2026/05/14/neuron-structure.html`

## 输出格式

**HTML文件：**
```
✅ 上传成功
🔗 URL: https://webpages-1257022348.cos-website.ap-guangzhou.myqcloud.com/2026/05/14/neuron-structure.html
🌐 浏览: https://webpages-1257022348.cos-website.ap-guangzhou.myqcloud.com/2026/05/14/neuron-structure.html
💾 下载: https://webpages-1257022348.cos.ap-guangzhou.myqcloud.com/2026/05/14/neuron-structure.html
📋 Markdown: [neuron-structure.html](https://...)
📦 Size: 14.0KB | Type: text/html; charset=utf-8
```

**其他文件：**
```
✅ 上传成功
🔗 URL: https://openclaw-1257022348.cos.ap-guangzhou.myqcloud.com/...
💾 直链: https://openclaw-1257022348.cos.ap-guangzhou.myqcloud.com/...
📋 Markdown: [file](https://...)
📦 Size: 1.2MB | Type: image/png
```

## 依赖

- Skill 独立 `.venv`（`cos_python_sdk_v5, pyyaml`）
- `~/.cos.yaml` 凭证配置（含 `webpages_bucket` 字段）
- `webpages` bucket 需已开启静态网站托管 + public-read ACL