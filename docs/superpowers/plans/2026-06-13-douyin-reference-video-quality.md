# Douyin Reference Video Quality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade `projects/douyin-jianji` so every script block in `demand/` generates a horizontal reference-style infographic video with storyboard, subtitles, audio, and quality reports.

**Architecture:** Keep the existing Python pipeline, but split responsibilities into parser, storyboard planner, infographic renderer, media composer, and quality reporter. The pipeline must work offline for visual generation and report clearly when TTS, BGM, or external image APIs degrade.

**Tech Stack:** Python 3.10+, openpyxl, Pillow, imageio-ffmpeg/FFmpeg, unittest, optional MiMo TTS, optional edge-tts.

---

## File Structure

- Modify: `projects/douyin-jianji/pipeline/script_converter.py`
  - Parse multiple script blocks from one workbook.
  - Clean visual text.
  - Infer semantic templates from content.
  - Keep `convert_excel_to_script()` as a backward-compatible wrapper.
- Create: `projects/douyin-jianji/pipeline/storyboard_planner.py`
  - Convert parsed script sections into 6-9 reference-style shots per short video.
  - Extract data stats, process steps, material items, channel steps, and zone cards.
- Create: `projects/douyin-jianji/pipeline/quality_report.py`
  - Probe output media.
  - Check storyboard coverage, parse residue, empty placeholders, subtitles, and audio.
  - Write JSON and Markdown reports.
- Modify: `projects/douyin-jianji/pipeline/slide_renderer.py`
  - Add reference-video templates: `cover_dark`, `headline_warning`, `data_release`, `process_flow`, `zone_cards`, `policy_explain`, `material_grid`, `channel_steps`, `cta_summary`.
  - Always draw top title bar and bottom subtitle bar.
- Modify: `projects/douyin-jianji/pipeline/video_generator.py`
  - Add pan/zoom to static slides.
  - Output 44.1kHz AAC.
  - Preserve styled ASS subtitles and report libass failures.
- Modify: `projects/douyin-jianji/pipeline/tts_generator.py`
  - Keep existing MiMo/edge flow.
  - Add cached/no-audio fallback metadata.
  - Generate short subtitle chunks.
- Modify: `projects/douyin-jianji/pipeline/pipeline.py`
  - Batch all `demand/*.xlsx` script blocks.
  - Write `script.json`, `storyboard.json`, `quality_report.json`, `quality_report.md`, key frames, and final MP4.
- Create: `projects/douyin-jianji/pipeline/tests/test_script_converter.py`
- Create: `projects/douyin-jianji/pipeline/tests/test_storyboard_planner.py`
- Create: `projects/douyin-jianji/pipeline/tests/test_quality_report.py`
- Create: `projects/douyin-jianji/pipeline/tests/test_slide_renderer.py`
- Modify: `projects/douyin-jianji/pipeline/tests/test_config.py`

## Task 1: Parser Tests For Multi-Block Excel And Text Cleaning

**Files:**
- Create: `projects/douyin-jianji/pipeline/tests/test_script_converter.py`
- Modify: `projects/douyin-jianji/pipeline/script_converter.py`

- [ ] **Step 1: Write failing parser tests**

Create `projects/douyin-jianji/pipeline/tests/test_script_converter.py`:

```python
"""Tests for demand Excel parsing and visual text cleanup."""

import unittest
from pathlib import Path

from script_converter import (
    clean_visual_text,
    convert_excel_to_script,
    parse_excel_scripts,
)


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent


class ScriptConverterTest(unittest.TestCase):
    def test_618_workbook_has_three_script_blocks(self):
        scripts = parse_excel_scripts(PROJECT / "demand" / "618.xlsx")

        self.assertEqual(len(scripts), 3)
        self.assertEqual([s["block_index"] for s in scripts], [0, 1, 2])
        self.assertIn("618光伏新政1", scripts[0]["program_title"])
        self.assertIn("618光伏新政2", scripts[1]["program_title"])
        self.assertIn("618光伏新政3", scripts[2]["program_title"])

    def test_douyin_workbook_has_one_script_block(self):
        scripts = parse_excel_scripts(PROJECT / "demand" / "douyinwenanjiaoben.xlsx")

        self.assertEqual(len(scripts), 1)
        self.assertIn("光伏前期手续", scripts[0]["program_title"])
        self.assertEqual(len(scripts[0]["sections"]), 5)

    def test_visual_text_is_cleaned_before_structuring(self):
        raw = "【画面】\n【字幕】✅ 正确顺序：备案 → 施工 → 并网"

        self.assertEqual(clean_visual_text(raw), "正确顺序：备案 -> 施工 -> 并网")

    def test_legacy_converter_returns_first_script_for_single_output_callers(self):
        script = convert_excel_to_script(PROJECT / "demand" / "618.xlsx")

        self.assertIn("618光伏新政1", script["program_title"])
        self.assertGreaterEqual(len(script["sections"]), 4)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run parser tests and verify RED**

Run:

```bash
cd /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/projects/douyin-jianji/pipeline
python -m unittest tests.test_script_converter -v
```

Expected: fail because `parse_excel_scripts` and `clean_visual_text` are not implemented.

- [ ] **Step 3: Implement parser functions**

In `projects/douyin-jianji/pipeline/script_converter.py`, implement these public functions:

```python
def parse_excel_scripts(excel_path) -> list[dict]:
    """Return every script block from an Excel workbook."""

def clean_visual_text(value: str) -> str:
    """Remove visual labels and rendering-hostile symbols from a visual cell."""

def convert_excel_to_script(excel_path: str) -> dict:
    """Backward-compatible wrapper returning the first parsed script."""
```

Implementation rules:

- Use `openpyxl.load_workbook(excel_path, data_only=True)`.
- Start a new script block when column A equals `抖音短视频脚本`.
- Stop a block at the next `抖音短视频脚本` row or the end of the sheet.
- Read metadata rows by column A keys: `时长`, `风格`, `BGM`, `标题`, `话题`, `出镜`, `评论区预埋`, `字幕细节`, `封面文案`.
- Read section rows when column A contains a time range like `3-18s`.
- Clean visual text before storing it.
- Use keys from the spec: `source_file`, `sheet_name`, `block_index`, `program_title`, `headline`, `hashtags`, `style`, `duration_text`, `sections`, `execution_tips`.
- Each section has `id`, `time_range`, `duration_sec`, `label`, `visual`, `text`, `asset_hint`, `template`.
- Keep ASCII arrows `->` in structured output.

- [ ] **Step 4: Run parser tests and verify GREEN**

Run:

```bash
cd /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/projects/douyin-jianji/pipeline
python -m unittest tests.test_script_converter -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit parser work**

Run:

```bash
cd /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering
git add projects/douyin-jianji/pipeline/script_converter.py projects/douyin-jianji/pipeline/tests/test_script_converter.py
git commit -m "feat: parse douyin demand script blocks"
```

## Task 2: Storyboard Planner

**Files:**
- Create: `projects/douyin-jianji/pipeline/storyboard_planner.py`
- Create: `projects/douyin-jianji/pipeline/tests/test_storyboard_planner.py`

- [ ] **Step 1: Write failing storyboard tests**

Create `projects/douyin-jianji/pipeline/tests/test_storyboard_planner.py`:

```python
"""Tests for reference-style storyboard planning."""

import unittest

from storyboard_planner import plan_storyboard


class StoryboardPlannerTest(unittest.TestCase):
    def test_long_core_section_splits_into_multiple_shots(self):
        script = {
            "headline": "卡了6年的光伏80%红线，正式作废！",
            "program_title": "《618光伏新政1》 - 文件解读",
            "sections": [
                {
                    "label": "痛点/悬念",
                    "duration_sec": 3,
                    "visual": "80%并网红线，彻底取消！",
                    "text": "多少光伏项目，倒在变压器80%负载率这条线上？",
                    "template": "headline_warning",
                },
                {
                    "label": "核心干货输出",
                    "duration_sec": 15,
                    "visual": "废止80%红线｜释放50GW存量项目｜三色分区柔性管控",
                    "text": "沿用多年的光伏并网80%硬性红线，在新政里直接被废止！再也不是一刀切禁止并网。行业统计显示，这一次直接盘活50GW被积压的存量光伏项目。新政换成更科学的绿、黄、红三色分区柔性管控。",
                    "template": "data_release",
                },
                {
                    "label": "结尾引导",
                    "duration_sec": 4,
                    "visual": "",
                    "text": "三色分区到底怎么划分？下期视频一次性讲透",
                    "template": "cta_summary",
                },
            ],
        }

        storyboard = plan_storyboard(script)

        self.assertGreaterEqual(len(storyboard["shots"]), 6)
        templates = {shot["template"] for shot in storyboard["shots"]}
        self.assertIn("cover_dark", templates)
        self.assertIn("data_release", templates)
        self.assertIn("zone_cards", templates)
        self.assertIn("cta_summary", templates)

    def test_process_and_material_content_get_specific_templates(self):
        script = {
            "headline": "家用光伏前期手续完整版，新手直接照做",
            "program_title": "《光伏前期手续》 - 科普知识",
            "sections": [
                {
                    "label": "核心新规科普",
                    "duration_sec": 7,
                    "visual": "正确顺序：备案 -> 施工 -> 并网",
                    "text": "家用光伏必须先办手续、再施工。",
                    "template": "process_flow",
                },
                {
                    "label": "必备材料清单",
                    "duration_sec": 8,
                    "visual": "必备资料：身份证 + 房屋权属证明 + 承重报告（老房）",
                    "text": "前期只需要准备三样东西。",
                    "template": "material_grid",
                },
            ],
        }

        storyboard = plan_storyboard(script)
        templates = [shot["template"] for shot in storyboard["shots"]]

        self.assertIn("process_flow", templates)
        self.assertIn("material_grid", templates)
        self.assertNotIn("grid_2x2", templates)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run storyboard tests and verify RED**

Run:

```bash
cd /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/projects/douyin-jianji/pipeline
python -m unittest tests.test_storyboard_planner -v
```

Expected: fail because `storyboard_planner.py` does not exist.

- [ ] **Step 3: Implement storyboard planner**

Create `projects/douyin-jianji/pipeline/storyboard_planner.py` with:

```python
def plan_storyboard(script: dict) -> dict:
    """Build reference-style storyboard shots from a parsed script."""
```

Implementation rules:

- Return `{"title": "视频栏目标题", "headline": "视频标题", "shots": [{"template": "cover_dark", "title": "视频栏目标题", "subtitle": "开场字幕", "duration_sec": 3.0, "data": {}}]}`.
- Add a `cover_dark` shot first for every video.
- Split any section longer than 8 seconds by Chinese punctuation into 2 or 3 shots.
- If text or visual contains `绿`, `黄`, and `红`, add a `zone_cards` shot.
- If text or visual contains a number plus `GW`, `%`, or `个工作日`, add a `data_release` shot with `stats`.
- If visual contains `->`, add `process_flow` with `steps`.
- If visual contains `资料`, `身份证`, `权属`, or `承重`, add `material_grid` with `items`.
- If visual contains `APP`, `营业厅`, or text contains `提交申请`, add `channel_steps`.
- If label or text contains `评论`, `下期`, `关注`, or `问我`, add `cta_summary`.
- Keep individual shot durations between 2.5 and 6.0 seconds.
- Include `subtitle` on every shot from the relevant narration text.

- [ ] **Step 4: Run storyboard tests and verify GREEN**

Run:

```bash
cd /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/projects/douyin-jianji/pipeline
python -m unittest tests.test_storyboard_planner -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit storyboard work**

Run:

```bash
cd /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering
git add projects/douyin-jianji/pipeline/storyboard_planner.py projects/douyin-jianji/pipeline/tests/test_storyboard_planner.py
git commit -m "feat: plan reference style storyboards"
```

## Task 3: Quality Report

**Files:**
- Create: `projects/douyin-jianji/pipeline/quality_report.py`
- Create: `projects/douyin-jianji/pipeline/tests/test_quality_report.py`

- [ ] **Step 1: Write failing quality report tests**

Create `projects/douyin-jianji/pipeline/tests/test_quality_report.py`:

```python
"""Tests for video quality report checks."""

import tempfile
import unittest
from pathlib import Path

from quality_report import build_quality_report, find_parse_residue


class QualityReportTest(unittest.TestCase):
    def test_find_parse_residue_detects_bad_tokens(self):
        payload = {
            "shots": [
                {"title": "【字幕】错误", "items": [{"title": "项目1"}]},
                {"subtitle": "正常字幕"},
            ]
        }

        residue = find_parse_residue(payload)

        self.assertIn("【字幕】", residue)
        self.assertIn("项目1", residue)

    def test_build_quality_report_marks_reference_style_requirements(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            storyboard = {
                "shots": [
                    {"template": "cover_dark", "subtitle": "开场"},
                    {"template": "data_release", "subtitle": "50GW项目释放"},
                    {"template": "process_flow", "subtitle": "备案施工并网"},
                    {"template": "cta_summary", "subtitle": "评论区问我"},
                ]
            }
            report = build_quality_report(
                output_dir=out,
                script={"source_file": "demand/618.xlsx", "sheet_name": "618新政", "block_index": 0},
                storyboard=storyboard,
                video_path=out / "missing.mp4",
                audio_path=out / "missing.mp3",
                subtitle_path=out / "missing.srt",
                tts_status="missing",
            )

            self.assertFalse(report["checks"]["has_audio"])
            self.assertTrue(report["checks"]["has_top_title_bar"])
            self.assertTrue(report["checks"]["has_bottom_subtitle_bar"])
            self.assertTrue(report["checks"]["has_infographic_body"])
            self.assertTrue(report["checks"]["has_data_or_process"])
            self.assertTrue((out / "quality_report.json").exists())
            self.assertTrue((out / "quality_report.md").exists())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run quality tests and verify RED**

Run:

```bash
cd /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/projects/douyin-jianji/pipeline
python -m unittest tests.test_quality_report -v
```

Expected: fail because `quality_report.py` does not exist.

- [ ] **Step 3: Implement quality report module**

Create `projects/douyin-jianji/pipeline/quality_report.py` with:

```python
def find_parse_residue(payload) -> list[str]:
    """Return bad text markers found in nested dictionaries and lists."""

def build_quality_report(
    output_dir,
    script: dict,
    storyboard: dict,
    video_path,
    audio_path,
    subtitle_path,
    tts_status: str,
) -> dict:
    """Write quality_report.json and quality_report.md, then return the report."""
```

Implementation rules:

- Bad markers are `【画面】`, `【字幕】`, `项目1`, `项目2`, `步骤1`, `步骤2`, `步骤3`.
- Recursively scan dict/list/string values.
- `has_top_title_bar` is true when at least one shot exists because the renderer will always draw it.
- `has_bottom_subtitle_bar` is true when every shot has `subtitle`.
- `has_infographic_body` is true when a shot template is not `cover_dark` or `headline_warning`.
- `has_data_or_process` is true when template is `data_release`, `process_flow`, `zone_cards`, `material_grid`, or `channel_steps`.
- Write stable JSON with `ensure_ascii=False, indent=2`.
- Write Markdown with a short summary table and a checks table.

- [ ] **Step 4: Run quality tests and verify GREEN**

Run:

```bash
cd /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/projects/douyin-jianji/pipeline
python -m unittest tests.test_quality_report -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit quality report work**

Run:

```bash
cd /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering
git add projects/douyin-jianji/pipeline/quality_report.py projects/douyin-jianji/pipeline/tests/test_quality_report.py
git commit -m "feat: report douyin video quality checks"
```

## Task 4: Reference-Style Slide Renderer

**Files:**
- Modify: `projects/douyin-jianji/pipeline/slide_renderer.py`
- Create: `projects/douyin-jianji/pipeline/tests/test_slide_renderer.py`

- [ ] **Step 1: Write failing renderer tests**

Create `projects/douyin-jianji/pipeline/tests/test_slide_renderer.py`:

```python
"""Tests for reference-style slide rendering."""

import tempfile
import unittest
from pathlib import Path

from PIL import Image

import config
from slide_renderer import render_slide


class SlideRendererTest(unittest.TestCase):
    def test_rendered_slide_has_reference_bars_and_non_empty_center(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "slide.png"
            render_slide(
                {
                    "template": "data_release",
                    "title": "618光伏新政解析",
                    "subtitle": "沿用多年的80%硬性红线正式废止",
                    "data": {
                        "headline": "80%红线废止",
                        "stats": [{"value": "50GW", "label": "存量项目释放", "color": "accent_gold"}],
                    },
                },
                None,
                str(output),
                "618光伏新政解析",
            )

            img = Image.open(output).convert("RGB")
            self.assertEqual(img.size, (config.VIDEO_WIDTH, config.VIDEO_HEIGHT))
            top_pixel = img.getpixel((config.VIDEO_WIDTH // 2, 30))
            bottom_pixel = img.getpixel((config.VIDEO_WIDTH // 2, config.VIDEO_HEIGHT - 40))
            center_pixel = img.getpixel((config.VIDEO_WIDTH // 2, config.VIDEO_HEIGHT // 2))
            self.assertNotEqual(top_pixel, center_pixel)
            self.assertNotEqual(bottom_pixel, center_pixel)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run renderer tests and verify RED or behavior gap**

Run:

```bash
cd /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/projects/douyin-jianji/pipeline
python -m unittest tests.test_slide_renderer -v
```

Expected: fail because the current renderer does not draw the reference-style bottom subtitle bar and does not know `data_release`.

- [ ] **Step 3: Extend renderer templates**

Modify `projects/douyin-jianji/pipeline/slide_renderer.py`:

- Map template aliases:
  - `cover_dark` and `headline_warning` to strong title rendering.
  - `data_release` to data card rendering.
  - `process_flow` to flow rendering.
  - `zone_cards` to green/yellow/red cards.
  - `material_grid` to material cards.
  - `channel_steps` to channel cards.
  - `cta_summary` to CTA rendering.
- Always draw a top title bar.
- Always draw a bottom subtitle bar when `subtitle` exists.
- Add `_draw_bottom_subtitle_bar(draw, subtitle)`.
- Add `_wrap_text(draw, text, font, max_width)`.
- Make fallback backgrounds include subtle grid lines and accent waves, not a plain blank rectangle.

- [ ] **Step 4: Run renderer tests and verify GREEN**

Run:

```bash
cd /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/projects/douyin-jianji/pipeline
python -m unittest tests.test_slide_renderer -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit renderer work**

Run:

```bash
cd /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering
git add projects/douyin-jianji/pipeline/slide_renderer.py projects/douyin-jianji/pipeline/tests/test_slide_renderer.py
git commit -m "feat: render reference style infographic slides"
```

## Task 5: TTS Metadata And Subtitle Chunking

**Files:**
- Modify: `projects/douyin-jianji/pipeline/tts_generator.py`
- Create: `projects/douyin-jianji/pipeline/tests/test_tts_generator.py`

- [ ] **Step 1: Write failing subtitle chunk tests**

Create `projects/douyin-jianji/pipeline/tests/test_tts_generator.py`:

```python
"""Tests for subtitle chunking helpers."""

import unittest

from tts_generator import split_subtitle_text


class TtsGeneratorTest(unittest.TestCase):
    def test_split_subtitle_text_keeps_lines_short(self):
        chunks = split_subtitle_text("沿用多年的光伏并网80%硬性红线，在新政里直接被废止！再也不是一刀切禁止并网。", max_chars=22)

        self.assertGreaterEqual(len(chunks), 3)
        self.assertTrue(all(len(chunk) <= 22 for chunk in chunks))
        self.assertIn("80%", "".join(chunks))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run TTS tests and verify RED**

Run:

```bash
cd /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/projects/douyin-jianji/pipeline
python -m unittest tests.test_tts_generator -v
```

Expected: fail because `split_subtitle_text` does not exist.

- [ ] **Step 3: Implement subtitle helper and metadata**

Modify `projects/douyin-jianji/pipeline/tts_generator.py`:

```python
def split_subtitle_text(text: str, max_chars: int = 24) -> list[str]:
    """Split narration into short subtitle chunks."""
```

Rules:

- Split first by Chinese punctuation `。！？；，、`.
- Preserve numeric tokens such as `80%` and `50GW`.
- If a chunk remains longer than `max_chars`, split by character width.
- Return non-empty stripped chunks.
- Add `tts_status` to section result: `mimo`, `edge`, `cached`, or `missing`.
- If external TTS fails and cached audio exists, reuse it and mark `cached`.
- If no audio can be generated, return metadata with empty `audio_path`, generated subtitle path, and `tts_status="missing"`.

- [ ] **Step 4: Run TTS tests and verify GREEN**

Run:

```bash
cd /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/projects/douyin-jianji/pipeline
python -m unittest tests.test_tts_generator -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit TTS work**

Run:

```bash
cd /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering
git add projects/douyin-jianji/pipeline/tts_generator.py projects/douyin-jianji/pipeline/tests/test_tts_generator.py
git commit -m "feat: chunk subtitles and report tts status"
```

## Task 6: Video Generator Media Settings

**Files:**
- Modify: `projects/douyin-jianji/pipeline/video_generator.py`
- Create: `projects/douyin-jianji/pipeline/tests/test_video_generator.py`

- [ ] **Step 1: Write failing ASS style test**

Create `projects/douyin-jianji/pipeline/tests/test_video_generator.py`:

```python
"""Tests for video generator subtitle styling."""

import tempfile
import unittest
from pathlib import Path

from video_generator import _srt_to_styled_ass


class VideoGeneratorTest(unittest.TestCase):
    def test_ass_style_uses_reference_bottom_bar_resolution(self):
        with tempfile.TemporaryDirectory() as tmp:
            srt = Path(tmp) / "narration.srt"
            srt.write_text("1\n00:00:00,000 --> 00:00:02,000\n测试字幕\n\n", encoding="utf-8")

            ass = Path(_srt_to_styled_ass(str(srt), tmp))
            content = ass.read_text(encoding="utf-8")

            self.assertIn("PlayResX: 1920", content)
            self.assertIn("PlayResY: 1080", content)
            self.assertIn("MarginV", content)
            self.assertIn("测试字幕", content)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run video tests and verify current behavior**

Run:

```bash
cd /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/projects/douyin-jianji/pipeline
python -m unittest tests.test_video_generator -v
```

Expected: pass or fail. If it passes, keep it as a regression test before changing ffmpeg commands.

- [ ] **Step 3: Update ffmpeg commands**

Modify `projects/douyin-jianji/pipeline/video_generator.py`:

- Add a slight zoompan filter in `_create_segment`.
- Force audio output to `-ar 44100`.
- Use `-b:a 192k` for final audio.
- Capture stderr when subtitle burn-in fails and write it to `subtitle_burn_error.log` in the output directory.
- Keep output MP4 at 30fps and yuv420p.

- [ ] **Step 4: Run video tests and existing config tests**

Run:

```bash
cd /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/projects/douyin-jianji/pipeline
python -m unittest tests.test_video_generator tests.test_config -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit video generator work**

Run:

```bash
cd /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering
git add projects/douyin-jianji/pipeline/video_generator.py projects/douyin-jianji/pipeline/tests/test_video_generator.py
git commit -m "feat: improve video composition settings"
```

## Task 7: Pipeline Batch Integration

**Files:**
- Modify: `projects/douyin-jianji/pipeline/pipeline.py`
- Modify: `projects/douyin-jianji/pipeline/README.md`

- [ ] **Step 1: Add integration behavior**

Modify `projects/douyin-jianji/pipeline/pipeline.py` so it:

- Uses `parse_excel_scripts()` when an input path is an Excel file.
- Uses `plan_storyboard()` for every parsed script.
- Writes `script.json` and `storyboard.json`.
- Renders one slide per storyboard shot.
- Uses the shot subtitle as slide bottom subtitle.
- Calls TTS per original script section.
- Calls `render_video()`.
- Calls `build_quality_report()`.
- Adds `run_demand_directory(demand_dir)` for `../demand`.
- Produces unique output slugs from `program_title` or `headline`.

- [ ] **Step 2: Add a no-network smoke mode**

Add CLI flag:

```text
--no-tts
```

Behavior:

- Skip external TTS.
- Generate storyboard, slides, subtitles, silent placeholder audio, video, and report.
- Mark `tts_status="missing"` or `tts_status="silent_smoke"` in the report.

- [ ] **Step 3: Update README usage**

In `projects/douyin-jianji/pipeline/README.md`, document:

```bash
cd pipeline
python pipeline.py ../demand --batch --no-tts
python pipeline.py ../demand/618.xlsx --batch
```

Explain expected outputs:

- `script.json`
- `storyboard.json`
- `quality_report.md`
- final MP4

- [ ] **Step 4: Run all unit tests**

Run:

```bash
cd /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/projects/douyin-jianji/pipeline
python -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit pipeline integration**

Run:

```bash
cd /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering
git add projects/douyin-jianji/pipeline/pipeline.py projects/douyin-jianji/pipeline/README.md
git commit -m "feat: batch generate reference style douyin videos"
```

## Task 8: End-To-End Generation And Verification

**Files:**
- Generated under: `projects/douyin-jianji/output/`
- Create or update: `projects/douyin-jianji/执行结果.md`
- Create or update: `projects/douyin-jianji/质量对比分析.md`

- [ ] **Step 1: Run no-network batch generation**

Run:

```bash
cd /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/projects/douyin-jianji/pipeline
python pipeline.py ../demand --batch --no-tts
```

Expected:

- 4 output directories are created or updated.
- Each output directory has `script.json`, `storyboard.json`, `slides/`, `quality_report.md`, and MP4.
- Quality reports mark visual checks as passing.
- TTS status is clearly marked as smoke/silent when no external audio is used.

- [ ] **Step 2: Run media probes**

Run:

```bash
cd /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/projects/douyin-jianji
python - <<'PY'
import json
from pathlib import Path
reports = sorted(Path("output").glob("*/quality_report.json"))
print("reports", len(reports))
for path in reports:
    data = json.loads(path.read_text(encoding="utf-8"))
    print(path.parent.name, data["checks"])
PY
```

Expected:

- `reports 4` or more if older reports remain.
- No report contains parse residue.
- Every new report has top title bar, bottom subtitle bar, infographic body, and data/process coverage.

- [ ] **Step 3: Inspect generated key frames**

Run:

```bash
cd /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/projects/douyin-jianji
find output -path "*/frames/*.jpg" -o -path "*/slides/*.png" | head -20
```

Expected:

- Generated frame or slide files exist.
- Manual visual inspection shows top title bar, bottom subtitle bar, and populated infographic center.

- [ ] **Step 4: Update result documents**

Update `projects/douyin-jianji/执行结果.md` with:

- Exact command used.
- Number of parsed scripts.
- Number of generated videos.
- TTS status.
- Paths to generated MP4 files.

Update `projects/douyin-jianji/质量对比分析.md` with:

- Before/after differences.
- Reference-style checks.
- Known remaining gaps if external TTS or BGM is unavailable.

- [ ] **Step 5: Run final verification**

Run:

```bash
cd /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/projects/douyin-jianji/pipeline
python -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit verification artifacts**

Run:

```bash
cd /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering
git add projects/douyin-jianji/pipeline projects/douyin-jianji/执行结果.md projects/douyin-jianji/质量对比分析.md
git commit -m "test: verify douyin reference video generation"
```

## Self-Review

- Spec coverage:
  - Multi-block demand parsing: Task 1 and Task 7.
  - 4 demand videos: Task 1 and Task 8.
  - Reference-style storyboard density: Task 2.
  - Top title bar, bottom subtitle bar, infographic body: Task 4 and Task 8.
  - TTS status and subtitle chunking: Task 5.
  - 44.1kHz AAC and ASS subtitles: Task 6.
  - Quality reports: Task 3 and Task 8.
  - Tests before implementation: Tasks 1 through 6.
- Placeholder scan:
  - No open-ended task uses undefined future work.
  - No task asks for generic handling without exact behavior.
- Type consistency:
  - `parse_excel_scripts`, `clean_visual_text`, `plan_storyboard`, `build_quality_report`, and `split_subtitle_text` are defined before use.
  - Template names match the design spec.

## Execution Decision

The user has approved continuing until the goal is complete. Execute inline with `superpowers:executing-plans`, using TDD and committing after each completed task.
