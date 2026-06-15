# 论文长视频 Pipeline 重构设计

## 目标

重构 `projects/papers-site/video-pipeline`，新增一条专门面向论文解读长视频的 `longform` 主线。目标标准参考 M3Eval 原视频的完成度：内容紧贴论文、叙事连续、信息图密度高、画面切换顺滑、语音和字幕节奏稳定；但实现必须面向任意论文，不能写死某一篇论文的场景或视觉 prompt。

## 非目标

- 不在第一阶段重做短视频 Excel pipeline。
- 不要求每次 dry-run 都调用真实在线 AI 图片生成和 TTS；真实图像生成可通过 `--generate-images` 显式启用。
- 不删除历史 `pipeline.py`、`pipeline_v2.py`、`pipeline_v8.py`，避免破坏已有产物。

## 核心原则

1. 先生成论文事实包，再生成脚本，减少泛泛科普和幻觉。
2. 每个 scene 都要绑定 `paper_anchor`，说明对应论文摘要、方法、任务、结果或局限。
3. AI 只生成背景/主体视觉，不生成中文标题、数字、模型名和关键图表。
4. 所有中文、图表、排行榜、矩阵和解释框由代码渲染。
5. 输出中间产物必须可审查：`fact_pack.json`、`storyboard.json`、`visual_plan.json`、`timeline.json`、`narration.srt`、`slides_html/`、`slides_png/`、`contact_sheet.jpg`、`render_manifest.json`、`production_readiness.json`、`qa_report.json`。

## 架构

新增目录：

```text
projects/papers-site/video-pipeline/longform/
  __init__.py
  models.py
  llm_client.py
  llm_planner.py
  fact_pack.py
  storyboard.py
  visual_plan.py
  visual_assets.py
  timeline.py
  templates.py
  render.py
  assembly.py
  finalize.py
  qa.py
  cli.py
```

### `models.py`

定义核心数据模型：

- `PaperFactPack`：论文事实包。
- `Scene`：长视频分镜。
- `VisualScene`：带模板和渲染参数的视觉分镜。
- `TimelineEntry` / `Timeline`：scene 起止时间、转场和旁白时间轴。
- `RenderResult`：渲染产物路径。

使用 dataclass 和标准库，避免第一阶段引入 pydantic 等额外依赖。

### `llm_client.py` / `llm_planner.py`

提供通用 LLM 规划入口，不写死任何论文或 scene：

- `llm_client.py` 通过 OpenAI-compatible `/chat/completions` 直连返回 JSON，避免受本地 SDK/httpx 版本耦合影响。
- `llm_planner.py` 要求 LLM 基于输入论文生成 `fact_pack`、`scenes` 和 `visual_scenes`。
- prompt 明确要求：每个 scene 必须来自论文内容，不能复用固定论文专用场景列表。
- 校验器会拒绝空泛或重复的视觉 prompt，并检查 prompt 是否引用 scene/paper 中的术语。
- 测试使用 fake LLM，不依赖真实网络；真实运行通过 `--llm-plan` 启用。

### `fact_pack.py`

从 paper dict 构建事实包：

- title、slug、abstract、summary、urls。
- problem、method、findings、limitations。
- 从 title/summary/abstract 动态抽取句子、枚举片段和关键词作为 anchors。
- 如果摘要提到 benchmark/task/evaluation/findings，按上下文分类为 task、method、finding、limitation 等锚点。
- 不维护论文专属任务列表；M3Eval、A262 或其他论文都走同一套抽取逻辑。

### `storyboard.py`

从事实包生成 25-35 个 scene 的长视频结构。默认 deterministic planner 不调用 LLM，保证测试可重复；启用 `--llm-plan` 后由 LLM 直接生成事实包、分镜和视觉分镜。

通用结构：

1. Hero title
2. Core question
3. Evaluation gap
4. Method transfer
5. Task matrix
6. Metric/data setup
7. Paper-grounded evidence sections
8. Findings / limitations / future directions
9. Ranking/summary when the paper supports it
10. Final paper takeaway

### `visual_plan.py`

把 scene 映射到视觉模板，并根据 scene title、paper anchor 和 data 生成论文专属视觉 prompt。所有默认 prompt 统一走科技风：dark background、cinematic high-tech、neon HUD、holographic interface、technical data flow、no readable text/no labels。模板只提供构图方向，不再提供 M3Eval/记忆论文专属图像。

- `hero_title`
- `core_question`
- `paper_gap_iceberg`
- `method_transfer`
- `task_matrix`
- `metric_cards`
- `split_comparison`
- `bar_finding`
- `ranking_board`
- `takeaway_cards`
- `future_direction`

### `visual_assets.py`

把 `visual_plan.json` 中的 `visual_prompt` 交给图像生成器，生成每个 scene 的电影化主视觉：

- 默认调用现有 DashScope 图像生成入口。
- 生成 `cinematic_assets/` 和 `visual_assets.json`。
- 可注入 fake image generator 做测试，不把测试绑定到真实外部服务。
- 当图像生成失败时，流水线仍可退回代码渲染的信息图，不伪造已生成图片。

### `timeline.py`

生成长视频时间轴和字幕：

- scene 时间轴连续，默认首帧 `cut`，后续 `crossfade`。
- 总时长控制在 8-12 分钟区间。
- `narration.srt` 按短字幕块输出，单条字幕约 7 秒以内，避免整段字幕长时间停留。

### `templates.py`

生成 1920x1080 HTML 信息图。风格：黑底、青绿/品红/金色霓虹、HUD 边框、底部解释框、清晰中文。

### `render.py`

第一阶段提供 dry-run renderer：

- 写出 HTML。
- 如可用 Pillow，则渲染 PNG。
- 如果存在 `visual_assets` 主视觉，则以主视觉为背景，代码叠加标题、论文 anchor、HUD 边框和字幕安全区。
- 如果没有主视觉，则退回代码信息图 fallback。
- 不依赖 Playwright 和网络。

后续阶段再接 HTML screenshot/ffmpeg motion/TTS。

### `assembly.py`

把前面产物整理成视频合成清单：

- `slides`：PNG 路径、时长、转场、模板和 scene 类型。
- `narration_sections`：后续 TTS 可消费的分段文本。
- `subtitle_path`、`audio_output_path`、`video_output_path`。
- 标明后续可由 `motion_renderer.render_video_v2` 合成。

### `finalize.py`

把 `render_manifest.json` 推进到最终成片阶段：

- `production_readiness.json` 检查 slides、字幕、音频、FFmpeg、TTS 是否就绪。
- `render_video_from_manifest()` 在音频和 FFmpeg 可用时调用 `motion_renderer.render_video_v2` 输出 MP4。
- 不伪造成片：依赖缺失时报告 `next_action`，例如 `install_or_configure_tts` 或 `install_ffmpeg`。

### `qa.py`

输出 QA 报告和 contact sheet：

- scene 数量。
- 模板分布。
- 是否所有 scene 有 paper anchor。
- 是否有 HTML/PNG。
- timeline 是否和 scene 对齐、是否连续、总时长是否在长视频区间。
- SRT 是否存在、字幕块数量、最长字幕停留时间。
- 生成 contact sheet 方便肉眼验片。

### `cli.py`

命令：

```bash
python -m longform.cli --paper-slug mm80-m3eval-multimodal-memory --dry-run
python -m longform.cli --paper-slug a262-agentic-search-direct-corpus --scene-count 8 --llm-plan
python -m longform.cli --paper-slug a262-agentic-search-direct-corpus --llm-plan --generate-images
```

输出到：

```text
projects/papers-site/video-pipeline/output/<slug>/longform/
```

关键产物包括 `timeline.json`、`narration.srt`、`visual_assets.json`、`render_manifest.json` 和 `production_readiness.json`。当 `production_readiness.json` 显示 `audio_ready=true` 且 `ffmpeg_ready=true` 时，可用 `render_video_from_manifest()` 接 `motion_renderer.render_video_v2` 生成 MP4。

## 验收标准

- 可基于 `data/papers.json` 中 M3Eval 生成 longform 中间产物。
- storyboard 至少 25 个 scene。
- 每个 scene 都有 `paper_anchor`。
- 至少 8 类视觉模板。
- 生成 `fact_pack.json`、`storyboard.json`、`visual_plan.json`、`timeline.json`、`narration.srt`、`slides_html/`、`slides_png/`、`contact_sheet.jpg`、`render_manifest.json`、`production_readiness.json`、`qa_report.json`。
- `timeline.json` 有连续 scene 时间轴，总时长在 8-12 分钟。
- `narration.srt` 为短字幕块，最长字幕停留时间约 7 秒以内。
- QA 报告能证明模板分布、scene 完整性和论文 anchor 覆盖率。
- 不破坏历史 pipeline 文件。
- `--llm-plan` 能基于非 M3Eval 论文生成通用事实包、分镜和论文专属视觉 prompt。
- LLM prompt 校验必须拒绝空泛重复 prompt，避免把某篇论文的固定场景写死到通用流水线里。
- 默认 deterministic 路径也必须对非 M3Eval 论文保持论文粘结度，不能出现 M3Eval/N-Back/认知心理学等无关固定内容。
- LLM 视觉 prompt 会被规范化：补齐 high-tech/no readable text/no labels 等约束，并把 label/引号文字改为抽象视觉标记，避免图像模型直接生成可读文字。

## 当前生产化状态

- 当前环境已安装可用 FFmpeg 和 `edge-tts`，M3Eval golden sample 已生成真实分段 TTS、合并后的 `narration.mp3` 和最终 `longform.mp4`。
- 最终样片路径：`projects/papers-site/video-pipeline/output/mm80-m3eval-multimodal-memory/longform/longform.mp4`。
- 当前验证结果：25 个 scene、11 类视觉模板、paper anchor 覆盖率 `1.0`、最长字幕停留 `6.0` 秒、视频/音频/manifest 总时长分别约 `614.67` / `614.69` / `614.68` 秒。
- `a262-agentic-search-direct-corpus` 已通过默认 deterministic dry-run：14 个 scene、8 类模板、paper anchor 覆盖率 `1.0`，未混入 M3Eval/N-Back/psychology，并包含 direct corpus、retrieval、high-tech。
- `a262-agentic-search-direct-corpus` 已通过真实 LLM dry-run：8 个 scene、8 类模板、8 个唯一视觉 prompt、paper anchor 覆盖率 `1.0`，未混入 M3Eval/N-Back/psychology，并补齐 high-tech/no readable text/no labels。
- 已基于 A262 LLM visual plan 生成 8 张 DashScope 科技背景图并重渲染 contact sheet：`projects/papers-site/video-pipeline/output/a262-llm-dry-run/contact_sheet.jpg`。
- 流水线仍保留 production readiness gate：当未来环境缺少 slides/SRT/audio/FFmpeg/TTS 时，会在 `production_readiness.json` 中明确报告，不会伪造最终成片。
