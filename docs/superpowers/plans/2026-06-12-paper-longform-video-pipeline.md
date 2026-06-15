# Paper Longform Video Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dedicated longform paper-video pipeline that produces paper-grounded storyboard, visual plan, HTML/PNG slide artifacts, timeline/SRT subtitles, render manifests, and QA contact sheets matching the M3Eval-style reference standard.

**Architecture:** Add a new `projects/papers-site/video-pipeline/longform/` package with dataclass models, deterministic fact-pack/storyboard/visual planners, HTML template rendering, lightweight PNG fallback rendering, timeline/SRT generation, render manifest assembly, final-render readiness checks, QA reporting, and a CLI dry-run path. Historical pipelines remain untouched.

**Tech Stack:** Python 3 standard library, dataclasses, json, argparse, pathlib, optional Pillow for PNG/contact sheet rendering.

---

### Task 1: Datamodel and Fact Pack

**Files:**
- Create: `projects/papers-site/video-pipeline/longform/__init__.py`
- Create: `projects/papers-site/video-pipeline/longform/models.py`
- Create: `projects/papers-site/video-pipeline/longform/fact_pack.py`
- Test: `projects/papers-site/video-pipeline/tests/test_longform_fact_pack.py`

- [ ] **Step 1: Write failing tests**

```python
from pathlib import Path
import sys

PIPELINE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPELINE_DIR))

from longform.fact_pack import build_fact_pack


def test_build_fact_pack_extracts_m3eval_memory_anchors():
    paper = {
        "slug": "mm80-m3eval-multimodal-memory",
        "title": "M^3Eval: Multi-Modal Memory Evaluation through Cognitively-Grounded Video Tasks",
        "summary": "M3Eval 基于认知心理学设计视频任务，分别测试记忆保持、干扰下的稳健性、空间/时间 source grounding、并行视频流中的解缠，以及符号记忆。",
        "abstract": "We introduce M3Eval, a benchmark for memory in multi-modal models. Models struggle with parallel video streams, interference patterns, spatial versus temporal source grounding, and symbolic memory.",
        "paper_urls": ["https://arxiv.org/abs/2606.05008"],
        "project_urls": ["https://pku-value-lab.github.io/m3eval-homepage"],
    }

    fact_pack = build_fact_pack(paper)

    assert fact_pack.slug == "mm80-m3eval-multimodal-memory"
    assert fact_pack.problem
    assert "memory" in fact_pack.key_terms
    assert len(fact_pack.anchors) >= 4
    assert any(anchor["kind"] == "task" and "interference" in anchor["text"].lower() for anchor in fact_pack.anchors)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest discover -s projects/papers-site/video-pipeline/tests -p 'test_longform_fact_pack.py' -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'longform'`.

- [ ] **Step 3: Implement datamodel and fact pack**

Create dataclasses for `PaperFactPack` and extraction helpers. Implement deterministic keyword anchors for M3Eval-style memory papers.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest discover -s projects/papers-site/video-pipeline/tests -p 'test_longform_fact_pack.py' -v`
Expected: PASS.

### Task 2: Storyboard and Visual Planner

**Files:**
- Create: `projects/papers-site/video-pipeline/longform/storyboard.py`
- Create: `projects/papers-site/video-pipeline/longform/visual_plan.py`
- Test: `projects/papers-site/video-pipeline/tests/test_longform_storyboard.py`

- [ ] **Step 1: Write failing tests**

```python
from pathlib import Path
import sys

PIPELINE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPELINE_DIR))

from longform.fact_pack import build_fact_pack
from longform.storyboard import build_storyboard
from longform.visual_plan import build_visual_plan


def _paper():
    return {
        "slug": "mm80-m3eval-multimodal-memory",
        "title": "M^3Eval: Multi-Modal Memory Evaluation through Cognitively-Grounded Video Tasks",
        "summary": "M3Eval 基于认知心理学设计视频任务，分别测试记忆保持、干扰下的稳健性、空间/时间 source grounding、并行视频流中的解缠，以及符号记忆。",
        "abstract": "We introduce M3Eval. Models struggle with parallel video streams, interference patterns, spatial versus temporal source grounding, and symbolic memory.",
        "paper_urls": ["https://arxiv.org/abs/2606.05008"],
    }


def test_storyboard_has_longform_structure_and_paper_anchors():
    scenes = build_storyboard(build_fact_pack(_paper()), target_scene_count=28)

    assert len(scenes) == 28
    assert scenes[0].template_hint == "hero_title"
    assert scenes[-1].kind == "ending"
    assert all(scene.paper_anchor for scene in scenes)
    assert any("Interference" in scene.title or "干扰" in scene.title for scene in scenes)


def test_visual_plan_uses_at_least_eight_templates():
    scenes = build_storyboard(build_fact_pack(_paper()), target_scene_count=28)
    visual_scenes = build_visual_plan(scenes)

    templates = {scene.template for scene in visual_scenes}
    assert len(templates) >= 8
    assert "task_matrix" in templates
    assert "takeaway_cards" in templates
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest discover -s projects/papers-site/video-pipeline/tests -p 'test_longform_storyboard.py' -v`
Expected: FAIL because storyboard modules do not exist.

- [ ] **Step 3: Implement storyboard and visual planner**

Create deterministic longform section scaffolding with task/finding scenes. Map templates from `template_hint` and scene kind.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest discover -s projects/papers-site/video-pipeline/tests -p 'test_longform_storyboard.py' -v`
Expected: PASS.

### Task 3: Rendering and QA Artifacts

**Files:**
- Create: `projects/papers-site/video-pipeline/longform/templates.py`
- Create: `projects/papers-site/video-pipeline/longform/render.py`
- Create: `projects/papers-site/video-pipeline/longform/qa.py`
- Test: `projects/papers-site/video-pipeline/tests/test_longform_render_qa.py`

- [ ] **Step 1: Write failing tests**

```python
from pathlib import Path
import sys
import json
import tempfile

PIPELINE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPELINE_DIR))

from longform.fact_pack import build_fact_pack
from longform.storyboard import build_storyboard
from longform.visual_plan import build_visual_plan
from longform.render import render_visual_plan
from longform.qa import build_qa_report


def test_render_outputs_html_png_and_qa_report():
    paper = {
        "slug": "mm80-m3eval-multimodal-memory",
        "title": "M^3Eval: Multi-Modal Memory Evaluation through Cognitively-Grounded Video Tasks",
        "summary": "M3Eval 测试记忆保持、干扰、空间/时间定位、并行视频流解缠和符号记忆。",
        "abstract": "Models struggle with parallel video streams, interference, temporal source grounding, and symbolic memory.",
        "paper_urls": ["https://arxiv.org/abs/2606.05008"],
    }
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp)
        scenes = build_storyboard(build_fact_pack(paper), target_scene_count=25)
        visual_scenes = build_visual_plan(scenes)
        result = render_visual_plan(visual_scenes, out_dir)
        report = build_qa_report(visual_scenes, result, out_dir)

        assert len(result.html_files) == 25
        assert len(result.png_files) == 25
        assert result.contact_sheet.exists()
        assert report["scene_count"] == 25
        assert report["paper_anchor_coverage"] == 1.0
        assert report["template_count"] >= 8
        assert (out_dir / "qa_report.json").exists()
        assert json.loads((out_dir / "qa_report.json").read_text())["scene_count"] == 25
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest discover -s projects/papers-site/video-pipeline/tests -p 'test_longform_render_qa.py' -v`
Expected: FAIL because render modules do not exist.

- [ ] **Step 3: Implement HTML, PNG fallback, contact sheet, and QA**

Use standard library HTML writing and Pillow if available. If Pillow is missing, create placeholder `.png` files with a clear text marker and still write QA JSON.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest discover -s projects/papers-site/video-pipeline/tests -p 'test_longform_render_qa.py' -v`
Expected: PASS.

### Task 4: CLI Dry Run for Golden Sample

**Files:**
- Create: `projects/papers-site/video-pipeline/longform/cli.py`
- Test: `projects/papers-site/video-pipeline/tests/test_longform_cli.py`

- [ ] **Step 1: Write failing test**

```python
from pathlib import Path
import sys
import tempfile

PIPELINE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPELINE_DIR))

from longform.cli import run_longform_dry_run


def test_cli_dry_run_writes_reviewable_artifacts():
    paper = {
        "slug": "mm80-m3eval-multimodal-memory",
        "title": "M^3Eval: Multi-Modal Memory Evaluation through Cognitively-Grounded Video Tasks",
        "summary": "M3Eval 测试记忆保持、干扰、空间/时间定位、并行视频流解缠和符号记忆。",
        "abstract": "Models struggle with parallel video streams, interference, temporal source grounding, and symbolic memory.",
        "paper_urls": ["https://arxiv.org/abs/2606.05008"],
    }
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp)
        paths = run_longform_dry_run(paper, out_dir, scene_count=25)

        assert paths["fact_pack"].exists()
        assert paths["storyboard"].exists()
        assert paths["visual_plan"].exists()
        assert paths["qa_report"].exists()
        assert paths["contact_sheet"].exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest discover -s projects/papers-site/video-pipeline/tests -p 'test_longform_cli.py' -v`
Expected: FAIL because CLI module does not exist.

- [ ] **Step 3: Implement CLI dry-run orchestration**

Load paper by slug from `../data/papers.json`, write JSON intermediate artifacts, render slides, and return artifact paths.

- [ ] **Step 4: Run all longform tests**

Run: `python3 -m unittest discover -s projects/papers-site/video-pipeline/tests -p 'test_longform_*.py' -v`
Expected: PASS.

### Task 4.5: Timeline, Subtitles, and Render Manifest

**Files:**
- Create: `projects/papers-site/video-pipeline/longform/timeline.py`
- Create: `projects/papers-site/video-pipeline/longform/assembly.py`
- Update: `projects/papers-site/video-pipeline/longform/models.py`
- Update: `projects/papers-site/video-pipeline/longform/qa.py`
- Update: `projects/papers-site/video-pipeline/longform/cli.py`
- Test: `projects/papers-site/video-pipeline/tests/test_longform_timeline.py`
- Test: `projects/papers-site/video-pipeline/tests/test_longform_assembly.py`

- [x] **Step 1: Write failing tests for timeline continuity and SRT subtitle pacing**

Expected: FAIL until `timeline.py` exists and SRT uses short caption blocks.

- [x] **Step 2: Implement timeline and SRT generation**

Create contiguous scene timing, crossfade metadata, and short SRT caption blocks with max subtitle duration around 7 seconds.

- [x] **Step 3: Write failing tests for render manifest output**

Expected: FAIL until `assembly.py` exists and CLI returns `render_manifest`.

- [x] **Step 4: Implement render manifest and QA metrics**

Write `render_manifest.json` with slide paths, durations, transitions, narration sections, subtitle path, and downstream renderer. Add QA fields for timeline count, continuity, total duration, SRT block count, and max subtitle duration.

### Task 4.6: Final Render Readiness

**Files:**
- Create: `projects/papers-site/video-pipeline/longform/finalize.py`
- Update: `projects/papers-site/video-pipeline/longform/cli.py`
- Test: `projects/papers-site/video-pipeline/tests/test_longform_finalize.py`
- Test: `projects/papers-site/video-pipeline/tests/test_longform_cli.py`

- [x] **Step 1: Write failing tests for production readiness and manifest rendering handoff**

Expected: FAIL until `longform.finalize` exists and CLI returns `production_readiness`.

- [x] **Step 2: Implement production readiness report**

Write `production_readiness.json` with slide/subtitle/audio/dependency status, missing dependencies, output path, and next action.

- [x] **Step 3: Implement render handoff from manifest**

Expose `render_video_from_manifest()` so a ready manifest plus audio path can call `motion_renderer.render_video_v2`. Tests use an injected renderer to verify handoff without requiring FFmpeg.

- [x] **Step 4: Generate final MP4 sample**

Generated the M3Eval golden sample with per-scene `edge-tts` audio, audio-aligned timeline/SRT, centered micro-zoom motion, burned subtitles, and final MP4 output at `projects/papers-site/video-pipeline/output/mm80-m3eval-multimodal-memory/longform/longform.mp4`.

### Task 5: Manual Golden Sample Verification

**Files:**
- Generated only under `projects/papers-site/video-pipeline/output/mm80-m3eval-multimodal-memory/longform/`

- [x] **Step 1: Run dry-run CLI**

Run: `cd projects/papers-site/video-pipeline && python3 -m longform.cli --paper-slug mm80-m3eval-multimodal-memory --scene-count 25 --dry-run`
Expected: outputs paths for fact pack, storyboard, visual plan, timeline, narration SRT, render manifest, production readiness, contact sheet, and QA report.

- [x] **Step 2: Inspect QA report**

Run: `sed -n '1,220p' projects/papers-site/video-pipeline/output/mm80-m3eval-multimodal-memory/longform/qa_report.json`
Verified: `paper_anchor_coverage` is `1.0`, `template_count` is `11`, `scene_count` is `25`, `timeline_entry_count` is `25`, and `max_subtitle_duration_sec` is `6.0`. `production_readiness.json` shows `slides_ready=true`, `subtitle_ready=true`, `audio_ready=true`, `ffmpeg_ready=true`, `tts_ready=true`, and `missing_dependencies=[]`.

- [ ] **Step 3: Commit**

Run: `git add docs/superpowers/specs/2026-06-12-paper-longform-video-pipeline-design.md docs/superpowers/plans/2026-06-12-paper-longform-video-pipeline.md projects/papers-site/video-pipeline/longform projects/papers-site/video-pipeline/tests`
Run: `git commit -m "feat: add paper longform video pipeline"`
