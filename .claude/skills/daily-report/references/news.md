# news 变体：技术资讯日报

**何时阅读**：执行 `/daily-report news` 时读取此文件。

---

## 采集方式

### Step 1a: 运行 prepare_digest.py（确定性数据采集）

```bash
.venv/bin/python3 scripts/prepare_digest.py
```

脚本输出 JSON，包含：
- RSS feeds 采集到的新闻条目
- GitHub Releases 最近动态
- HuggingFace trending 模型/数据集
- `needs_llm_search` 列表：需要 LLM 补缺的条目

### Step 1b: LLM 补缺

对 `needs_llm_search` 列表中的每项，使用 WebSearch/WebFetch 补充信息：
- WebSearch 搜官方站点：`"Claude site:anthropic.com"`、`"Qwen release site:github.com"` 等
- WebFetch 直接访问各公司官方博客首页提取最新文章
- 每条新闻用 WebFetch 深入阅读公司官方原文，获取完整细节+配图URL
- 仅收录当日官方发布（与日报日期一致）

## 信息源（专注一手官方源）

国际大模型/智能体公司官方：
- Anthropic (`anthropic.com/news`) — Claude系列
- OpenAI (`openai.com/blog`) — GPT系列
- Google/DeepMind (`blog.google`, `deepmind.google`) — Gemini系列
- Meta AI (`ai.meta.com/blog`) — Llama系列
- Microsoft (`blogs.microsoft.com/ai`) — Copilot、Azure AI
- NVIDIA (`nvidia.com/blog`) — GPU、AI基础设施
- Mistral (`mistral.ai/news`) — Mistral系列
- Cohere (`cohere.com/blog`) — 企业AI
- xAI (`x.ai`) — Grok
- HuggingFace (`huggingface.co/blog`) — 开源生态

国内大模型/智能体公司官方：
- 百度/文心、阿里/Qwen、字节/Doubao、腾讯/混元、月之暗面/Kimi
- DeepSeek、智谱/GLM、MiniMax/海螺AI、商汤/日日新、昆仑万维/天工

开源社区：
- GitHub Releases/热门AI项目动态
- HuggingFace 模型页/数据集发布
- LangChain、AutoGen、CrewAI、Dify 等框架官方文档/博客

专注一手官方源。二手媒体（量子位、机器之心、新智元、TechCrunch、Reuters等）重包装信息，直接访问原始公司博客获取更完整细节和配图，避免二手报告的信息稀释层。

## 强制贴图要求

- 每条新闻必须附至少1张图：公司官方配图、产品截图、架构图、数据图表
- 无图可引用的新闻不收录（除非确实无官方配图且信息价值极高）
- 采集时用 WebFetch 读取官方原文，提取文中 `<img>` 标签获取配图URL
- SVG在微信不渲染，webp触发兼容错误(errcode 40137)。优先PNG/JPG。webp版本需用Pillow转PNG

## Wiki摄入

遵循 `references/wiki-ingest.md`（路径 kb/tech-news/），铁律见 `references/wiki-rules.md`。

## 日报结构

- **一、今日亮点**（3-5 条，带 emoji）
- **二、大模型** 🧠 — 基础模型发布、架构创新、开源动态
- **三、智能体/Agent** 🤖 — Agent框架、Computer Use、多智能体、商业化
- **四、行业要闻** 📰 — 重大产品发布、投融资、战略合作、政策监管（**优先展示、详细撰写**）
- **五、狐狸点评** 🦊 — 当日事件综合点评、趋势分析、技术解读

## 日报标题

飞书："🦊 大模型/智能体一手综合技术资讯 | YYYY-MM-DD（周X）"
微信："大模型/智能体一手综合技术资讯 | YYYY-MM-DD"

## 来源标注格式

- 飞书版本：链接格式 `[Anthropic官方博客](URL)`
- 微信版本：纯文本 `<span style="color:#ff6b35;font-weight:bold">`，无 `<a>` 链接（微信不支持外链跳转，URL以纯文本显示完整地址）