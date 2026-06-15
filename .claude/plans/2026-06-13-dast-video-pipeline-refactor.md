# Pipeline 重构计划：匹配参考视频

## 目标
重构 `video-pipeline/`，使其根据论文 `dast_analysis/paper_url.txt` (arxiv 2606.05008) 生成的视频，与 `dast_analysis/video.mp4` 在内容和形式上一致。

## 参考视频分析（22 slides，~10 min）

### 视觉风格
- **背景**: 深色科幻风 (#0a0a0f ~ #0f172a)，带发光电路/神经网络纹理
- **主色调**: 青色(#00d4ff)、绿色(#00ff88)、品红(#ff00ff)、橙色(#ff8800)、紫色(#a855f7)
- **字体**: 思源黑体/等线，大标题加粗，层次分明
- **动效**: Ken Burns 缩放 + 字幕烧录

### 22 Slides 内容结构
| # | 类型 | 标题 | 配色 |
|---|------|------|------|
| 1 | title | AI看视频真的能"过目不忘"吗？ | 青色 |
| 2 | question | 上下文窗口越来越长，AI记忆力就越来越好吗？ | 绿色 |
| 3 | problem | 我们一直在考大模型的"视力"，却忽略了"脑力" | 青色 |
| 4 | method | M³Eval：用人类认知心理学来"审问"AI | 青色 |
| 5 | overview | 解析记忆的四个切面 | 多色四象限 |
| 6 | test_intro | 测试一：分散注意力（"一心多用"测试） | 绿色 |
| 7 | data_result | 面对双屏，顶级AI瞬间"失忆" | 绿色+柱状图 |
| 8 | test_intro | 测试二：记忆干扰（相似内容的"覆盖"效应） | 青色 |
| 9 | comparison | AI的记忆覆盖逻辑完全不同于人类 | 青色天平 |
| 10 | test_intro | 测试三：交错事件（时间线的"拼图"能力） | 品红 |
| 11 | chart_result | 意外发现：重复播放竟能强化AI记忆 | 绿色+分组柱状图 |
| 12 | test_intro | 测试四：N-Back（符号化与工作记忆容量极限） | 橙色 |
| 13 | chart_result | 鸿沟再现：大模型缺乏人类级的"符号记忆力" | 橙色+折线图 |
| 14 | problem_deep | 为什么AI的记忆力会在这里崩盘？ | 红色 |
| 15 | summary_table | M³Eval评估结论矩阵：智能的岔路口 | 多色 |
| 16 | ranking | 现役大模型多模态记忆力摸底排行 | 青色+排名条 |
| 17 | future | 进化的方向：给AI装上真正的"海马体" | 紫色 |
| 18 | takeaway | 我们学到了什么？(Key Takeaways) | 三卡片 |
| 19 | ending | 真实的智能，藏在对记忆的重塑之中。 | 脑/电路 |

### 图表类型
1. **柱状图** - 带发光效果，值标签带彩色背景
2. **分组柱状图** - 多系列对比
3. **折线图** - 填充区域，多条线
4. **水平排名条** - 金银铜色

## 实施方案

### Step 1: 创建手动脚本 `dast_manual_script.json`
基于参考视频逐帧提取的文本内容，创建精确的22段脚本。每段包含：
- `id`, `type`, `label`, `text`（旁白）, `on_screen`（屏幕文字）, `duration_sec`
- `chart_data`（图表数据）, `accent_color`（主题色）
- `sub_type`（子类型：如 bar_chart, line_chart, grouped_bar, ranking 等）

### Step 2: 重构 `slide_html.py` - 新建 `slide_templates.py`
创建12种 HTML/CSS 幻灯片模板，每种匹配参考视频的一种布局：

```
templates/
├── title_slide.html          # 封面：机构名+大标题+副标题+英文
├── question_slide.html       # 问题引入：大标题+图标对比
├── problem_slide.html        # 问题揭示：标题+示意图+底部字幕
├── method_slide.html         # 方法介绍：标题+流程图+底部字幕
├── overview_slide.html       # 概览四象限：中心标题+四个区域
├── test_intro_slide.html     # 测试介绍：标题+示意图+底部字幕
├── data_result_slide.html    # 数据结果：标题+图表+结论框
├── comparison_slide.html     # 对比：标题+A vs B+底部洞察
├── chart_result_slide.html   # 图表结果：标题+图表+右侧分析框
├── ranking_slide.html        # 排名：标题+水平条+分梯队
├── future_slide.html         # 未来方向：标题+芯片图+三个方向
├── takeaway_slide.html       # 收获：三张卡片
└── ending_slide.html         # 结尾：大字+小字
```

CSS 设计要点：
- 1920x1080 viewport，Noto Sans SC 字体
- 深色背景 + CSS 渐变模拟电路纹理
- 发光边框/文字用 `box-shadow` 和 `text-shadow`
- 图表区域用 CSS 网格/弹性布局
- 底部字幕栏：半透明深色背景 + 白色文字

### Step 3: 重构 `chart_generator.py`
适配参考视频的图表风格：
- 暗色主题（背景透明/深色）
- 发光效果（glow shadow）
- 值标签带彩色圆角背景
- 特定颜色映射：青/绿/品红/橙/紫
- 折线图带渐变填充
- 排名图：金(#FFD700)/银(#C0C0C0)/铜(#CD7F32)

### Step 4: 创建 `dast_pipeline.py` - 主流程
```
输入: paper_url.txt → 读取论文 → 加载 dast_manual_script.json
流程:
  1. 生成 TTS 旁白（edge-tts, zh-CN-YunxiNeural）
  2. 生成字幕 SRT（按句分割）
  3. 为每个 slide 生成图表 PNG（如有）
  4. 用 Playwright 渲染 HTML → PNG（1920x1080）
  5. Ken Burns 动效渲染（ffmpeg zoompan）
  6. 混合旁白+字幕+背景音乐
输出: final.mp4
```

### Step 5: 迭代优化
- 生成视频后，提取帧与参考视频逐帧对比
- 对比维度：布局、配色、文字、图表数据、时间节奏
- 差异大的部分调整模板参数重新渲染

## 关键文件变更

| 文件 | 操作 | 说明 |
|------|------|------|
| `dast_manual_script.json` | 新建 | 22段精确脚本 |
| `slide_templates.py` | 新建 | 12种 HTML/CSS 模板 |
| `chart_generator_v2.py` | 新建 | 暗色发光风格图表 |
| `dast_pipeline.py` | 新建 | 主流程编排 |
| `dast_compare.py` | 新建 | 帧对比工具 |

保留旧文件不动，新文件独立运行。

## 验证
1. 运行 `python dast_pipeline.py` 生成视频
2. 运行 `python dast_compare.py` 逐帧对比
3. 调整模板/配色/布局直到匹配度 > 80%
4. 提交 git
