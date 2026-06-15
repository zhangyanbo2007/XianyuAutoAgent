# 发布流程（Steps 6-11）

**何时阅读**：Step 5日报生成完成后读取此文件，执行飞书+微信并行发布。

---

飞书文档和微信草稿是两条独立并行管道，互不依赖。

## 脚本路径

| 脚本 | 路径 |
|------|------|
| 飞书发布 | `/home/zhangyanbo/owner/xiaowangzi/.claude/skills/feishu-doc-op/scripts/feishu_publish.py` |
| 封面生成 | `/home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/.claude/skills/wechat-mp/scripts/generate_cover.py` |
| MD→微信HTML | `/home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/.claude/skills/wechat-mp/scripts/md2wechat_html.py` |
| 微信发布 | `/home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/.claude/skills/wechat-mp/scripts/wechat_publish.py` |
| 凭证 | `/home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/.claude/skills/daily-report/config/credentials.json` |

## Step 6: 飞书文档（06_feishu）

```bash
python3 /home/zhangyanbo/owner/xiaowangzi/.claude/skills/feishu-doc-op/scripts/feishu_publish.py \
  --input $WORKSPACE/05-report.md \
  --title "<日报标题>" \
  --folder V7FxwTXF6i9kqhkTeGkcxT3DnIf
```

飞书URL保存到 `$WORKSPACE/06-feishu-url.txt`，完成后更新progress.json。

## Step 7-10: 微信公众号草稿

### Step 7: 生成封面图（07_cover）

```bash
.venv/bin/python3 /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/.claude/skills/wechat-mp/scripts/generate_cover.py \
  --type <academic|tech-news> --date YYYY-MM-DD --output $WORKSPACE/07-cover.png
```

学术板块 `--type academic`，资讯板块 `--type tech-news`。

### Step 8-10: 一键生成草稿

`wechat_publish.py` 封装了封面上传 + HTML转换 + 草稿创建的完整流程：

```bash
.venv/bin/python3 /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/.claude/skills/wechat-mp/scripts/wechat_publish.py \
  --input $WORKSPACE/05-report.md \
  --title "<微信标题>" \
  --mode draft \
  --cover-image $WORKSPACE/07-cover.png \
  --config /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/.claude/skills/daily-report/config/credentials.json \
  --proxy http://127.0.0.1:7897
```

脚本自动完成：
1. Markdown → 微信HTML（调用 md2wechat_html.py，自动选主题：学术用 scholar-green，资讯用 fox-orange）
2. 上传封面图到微信素材库 → 获取 thumb_media_id
3. 下载并上传文章内图片到微信（替换外部URL为微信托管URL）
4. 创建草稿到微信草稿箱

### 如果需要手动分步执行

```bash
# Step 9 手动：MD → HTML
.venv/bin/python3 /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/.claude/skills/wechat-mp/scripts/md2wechat_html.py \
  --input $WORKSPACE/05-report.md \
  --output $WORKSPACE/09-wechat.html \
  --theme scholar-green  # 或 fox-orange

# Step 10 手动：HTML → 草稿
.venv/bin/python3 /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/.claude/skills/wechat-mp/scripts/wechat_publish.py \
  --html-input $WORKSPACE/09-wechat.html \
  --title "<微信标题>" \
  --mode draft \
  --cover-image $WORKSPACE/07-cover.png \
  --config /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/.claude/skills/daily-report/config/credentials.json
```

## Step 11: 最终输出（11_result）

- 简明摘要（3-5 条核心要点）
- 飞书文档链接
- 微信草稿箱结果
- 学术板块额外输出 Wiki 采集统计
- 输出保存到 `$WORKSPACE/11-result.txt`
