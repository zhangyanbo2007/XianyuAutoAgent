# Content-First Paper Video Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the longform paper-video pipeline render paper mechanisms as the visual subject, with high-tech styling only as supporting treatment.

**Architecture:** Add a shared content extraction layer that derives display labels from scene data, paper anchors, and titles while filtering style words. Use that layer in both HTML and PNG renderers. Preserve scene data over visual-only data when LLM payloads conflict, so content is not lost before rendering.

**Tech Stack:** Python dataclasses, stdlib, Pillow renderer, unittest.

---

### Task 1: Content Labels

**Files:**
- Create: `projects/papers-site/video-pipeline/longform/content_spec.py`
- Test: `projects/papers-site/video-pipeline/tests/test_longform_render_qa.py`

- [ ] Write a failing test that a scene containing `top-k`, `direct corpus`, and `high-tech` returns content labels including `TOP-K` and `DIRECT CORPUS`, but not `HIGH-TECH`.
- [ ] Run `python3 -B -m unittest projects/papers-site/video-pipeline/tests/test_longform_render_qa.py -v` and verify the test fails.
- [ ] Implement `content_labels(scene, count)` and `content_pair(scene)` using scene data first, then title/anchor, then visual prompt as a filtered fallback.
- [ ] Run the render QA tests and verify they pass.

### Task 2: Content-Driven Renderers

**Files:**
- Modify: `projects/papers-site/video-pipeline/longform/templates.py`
- Modify: `projects/papers-site/video-pipeline/longform/render.py`
- Test: `projects/papers-site/video-pipeline/tests/test_longform_render_qa.py`

- [ ] Write a failing HTML test for the A262 title scene: the hero visual must show `TOP-K` and `DIRECT CORPUS`, and must not show `HIGH-TECH`.
- [ ] Write a failing PNG test proving content overlays still render when an AI background image exists.
- [ ] Replace local concept extraction in templates and PNG renderer with the shared content extraction layer.
- [ ] In PNG rendering, draw content diagrams even when a background image exists; remove the dense overlay grid for background-backed slides.
- [ ] Run the render QA tests and verify they pass.

### Task 3: LLM Data Preservation

**Files:**
- Modify: `projects/papers-site/video-pipeline/longform/llm_planner.py`
- Test: `projects/papers-site/video-pipeline/tests/test_longform_llm_pipeline.py`

- [ ] Write a failing test where `visual_scenes[].data.title` conflicts with `scenes[].data.title`; scene data must win.
- [ ] Change `_visual_from_payload()` merge order so visual-only data fills gaps but never overwrites scene data.
- [ ] Run LLM pipeline tests and verify they pass.

### Task 4: Verification

**Files:**
- Generated output under `projects/papers-site/video-pipeline/output/a262-llm-dry-run/`

- [ ] Run `python3 -B -m unittest discover -s projects/papers-site/video-pipeline/tests -p 'test_longform_*.py' -v`.
- [ ] Re-render the A262 LLM dry-run from existing JSON and generated assets.
- [ ] Inspect `contact_sheet.jpg` and verify the main visual carries paper mechanisms, not style labels.
