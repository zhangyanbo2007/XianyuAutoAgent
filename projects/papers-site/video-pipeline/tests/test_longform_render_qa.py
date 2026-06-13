from pathlib import Path
import sys
import json
import tempfile
import unittest
from unittest.mock import patch

PIPELINE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPELINE_DIR))

from longform.fact_pack import build_fact_pack
from longform.storyboard import build_storyboard
from longform.visual_plan import build_visual_plan
from longform.render import render_visual_plan
from longform.qa import build_qa_report
from longform.timeline import build_timeline, write_srt


class LongformRenderQaTests(unittest.TestCase):
    def test_render_outputs_html_png_and_qa_report(self):
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
            timeline = build_timeline(visual_scenes)
            srt_path = write_srt(timeline, out_dir / "narration.srt")
            report = build_qa_report(visual_scenes, result, out_dir, timeline=timeline, srt_path=srt_path)

            self.assertEqual(len(result.html_files), 25)
            self.assertEqual(len(result.png_files), 25)
            self.assertTrue(result.contact_sheet.exists())
            self.assertEqual(report["scene_count"], 25)
            self.assertEqual(report["paper_anchor_coverage"], 1.0)
            self.assertGreaterEqual(report["template_count"], 8)
            self.assertEqual(report["timeline_entry_count"], 25)
            self.assertGreaterEqual(report["total_duration_sec"], 8 * 60)
            self.assertLessEqual(report["total_duration_sec"], 12 * 60)
            self.assertTrue(report["srt_exists"])
            self.assertGreater(report["srt_block_count"], report["scene_count"])
            self.assertLessEqual(report["max_subtitle_duration_sec"], 7.1)
            self.assertTrue((out_dir / "qa_report.json").exists())
            saved = json.loads((out_dir / "qa_report.json").read_text())
            self.assertEqual(saved["scene_count"], 25)
            self.assertEqual(saved["timeline_entry_count"], 25)


    def test_hero_template_uses_brain_circuit_visual_instead_of_placeholder(self):
        from longform.models import VisualScene
        from longform.templates import render_slide_html

        scene = VisualScene(
            index=0,
            kind="title",
            title="AI 看视频真的能过目不忘吗？",
            narration="开场",
            paper_anchor="paper: M3Eval",
            template="hero_title",
            duration_sec=18,
            visual_prompt="brain circuit",
            accent="cyan",
        )
        html = render_slide_html(scene, total=25)

        self.assertIn("hero-brain", html)
        self.assertIn("circuit", html)
        self.assertNotIn("<div class='orb'>?</div>", html)

    def test_non_memory_templates_do_not_render_memory_specific_labels(self):
        from longform.models import VisualScene
        from longform.templates import render_slide_html

        scene = VisualScene(
            index=0,
            kind="title",
            title="智能体搜索的证据链",
            narration="开场",
            paper_anchor="finding: direct corpus retrieval trace quality",
            template="hero_title",
            duration_sec=18,
            visual_prompt="agentic search direct corpus retrieval trace map, cinematic dark background neon HUD, no readable text",
            accent="cyan",
        )
        html = render_slide_html(scene, total=8)

        self.assertNotIn("MEMORY", html)
        self.assertNotIn("CIRCUIT", html)
        self.assertIn("CORPUS", html)

        method_scene = VisualScene(
            index=3,
            kind="method",
            title="直接语料库交互方法",
            narration="方法",
            paper_anchor="method: direct corpus interaction with retrieval trace inspection",
            template="method_transfer",
            duration_sec=22,
            visual_prompt="direct corpus interaction retrieval trace inspection, cinematic dark background neon HUD, no readable text",
            accent="green",
        )
        method_html = render_slide_html(method_scene, total=8)
        self.assertNotIn("认知心理学", method_html)
        self.assertNotIn("多模态记忆", method_html)
        self.assertIn("CORPUS", method_html)

        future_scene = VisualScene(
            index=7,
            kind="future",
            title="未来方向与总结",
            narration="总结",
            paper_anchor="future: retrieval trace auditing and stopping decision calibration",
            template="future_direction",
            duration_sec=22,
            visual_prompt="retrieval trace auditing stopping decision calibration, cinematic dark background neon HUD, no readable text",
            accent="cyan",
        )
        future_html = render_slide_html(future_scene, total=8)
        self.assertNotIn("Temporal Grounding", future_html)
        self.assertNotIn("Strategic Forgetting", future_html)
        self.assertIn("RETRIEVAL", future_html)

    def test_content_labels_prioritize_paper_terms_over_style_words(self):
        from longform.content_spec import content_labels
        from longform.models import VisualScene

        scene = VisualScene(
            index=0,
            kind="title",
            title="超越语义相似性：智能体搜索的检索范式革新",
            narration="开场",
            paper_anchor="固定 top-k 检索会提前过滤证据，direct corpus interaction 让智能体直接操作原始语料。",
            template="hero_title",
            duration_sec=18,
            data={"title": "Beyond Semantic Similarity: Rethinking Retrieval for Agentic Search via Direct Corpus Interaction"},
            visual_prompt="cinematic high-tech dark background neon HUD holographic interface, no readable text",
            accent="cyan",
        )

        labels = content_labels(scene, count=4)

        self.assertIn("TOP-K", labels)
        self.assertIn("DIRECT CORPUS", labels)
        self.assertNotIn("HIGH-TECH", labels)
        self.assertNotIn("HUD", labels)

    def test_content_labels_can_fill_sparse_scenes_without_hanging(self):
        from longform.content_spec import content_labels
        from longform.models import VisualScene

        scene = VisualScene(
            index=0,
            kind="title",
            title="短标题",
            narration="开场",
            paper_anchor="paper: minimal",
            template="hero_title",
            duration_sec=18,
            visual_prompt="brain circuit",
            accent="cyan",
        )

        labels = content_labels(scene, count=10)

        self.assertEqual(len(labels), 10)
        self.assertEqual(len(set(labels)), 10)

    def test_html_hero_visual_uses_paper_content_not_style_labels(self):
        from longform.models import VisualScene
        from longform.templates import render_slide_html

        scene = VisualScene(
            index=0,
            kind="title",
            title="超越语义相似性：智能体搜索的检索范式革新",
            narration="开场",
            paper_anchor="固定 top-k 检索会提前过滤证据，direct corpus interaction 让智能体直接操作原始语料。",
            template="hero_title",
            duration_sec=18,
            data={"title": "Beyond Semantic Similarity: Rethinking Retrieval for Agentic Search via Direct Corpus Interaction"},
            visual_prompt="cinematic high-tech dark background neon HUD holographic interface, no readable text",
            accent="cyan",
        )

        html = render_slide_html(scene, total=8)

        self.assertIn("TOP-K", html)
        self.assertIn("DIRECT CORPUS", html)
        self.assertNotIn("HIGH-TECH", html)

    def test_hero_pairs_topk_problem_with_direct_corpus_method_across_fields(self):
        from longform.models import VisualScene
        from longform.templates import render_slide_html

        scene = VisualScene(
            index=0,
            kind="title",
            title="超越语义相似性：智能体搜索的检索范式革新",
            narration="开场",
            paper_anchor="现代检索系统通过固定的相似性接口暴露语料库，将访问压缩为单个top-k检索步骤。这种抽象对智能体搜索成为瓶颈。",
            template="hero_title",
            duration_sec=18,
            data={"title": "Beyond Semantic Similarity: Rethinking Retrieval for Agentic Search via Direct Corpus Interaction"},
            visual_prompt="cinematic high-tech dark background neon HUD holographic interface, no readable text",
            accent="cyan",
        )

        html = render_slide_html(scene, total=8)

        self.assertIn("TOP-K", html)
        self.assertIn("DIRECT CORPUS", html)

    def test_task_matrix_uses_scene_content_instead_of_generic_section_labels(self):
        from longform.models import VisualScene
        from longform.templates import render_slide_html

        scene = VisualScene(
            index=4,
            kind="overview",
            title="DCI如何工作：智能体与语料的直接对话",
            narration="概览",
            paper_anchor="这种方法不需要离线索引，并且自然地适应不断演变的本地语料库。",
            template="task_matrix",
            duration_sec=20,
            data={
                "interaction": "command-based exploration",
                "adaptability": "适应动态语料库",
                "indexing": "无需离线索引",
            },
            visual_prompt="cinematic high-tech dark background neon HUD, no readable text",
            accent="gold",
        )

        html = render_slide_html(scene, total=8)

        self.assertIn("COMMAND", html)
        self.assertIn("NO INDEX", html)
        self.assertNotIn(">Problem<", html)
        self.assertNotIn(">Method<", html)
        self.assertNotIn(">Takeaway<", html)

    def test_png_renderer_draws_template_specific_visual_shapes(self):
        from PIL import Image
        from longform.models import VisualScene
        from longform.render import _render_png

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            bar_scene = VisualScene(
                index=8,
                kind="finding",
                title="柱状图发现",
                narration="测试旁白",
                paper_anchor="paper finding: Memory Interference",
                template="bar_finding",
                duration_sec=24,
                visual_prompt="bar chart",
                accent="cyan",
            )
            hero_scene = VisualScene(
                index=0,
                kind="title",
                title="AI 看视频真的能过目不忘吗？",
                narration="测试旁白",
                paper_anchor="paper: M3Eval",
                template="hero_title",
                duration_sec=18,
                visual_prompt="brain circuit",
                accent="gold",
            )
            bar_path = tmp_path / "bar.png"
            hero_path = tmp_path / "hero.png"
            _render_png(bar_scene, bar_path)
            _render_png(hero_scene, hero_path)
            bar = Image.open(bar_path).convert("RGB")
            hero = Image.open(hero_path).convert("RGB")

        self.assertGreater(bar.getpixel((520, 620))[1], 120)
        self.assertGreater(bar.getpixel((780, 520))[2], 120)
        self.assertGreater(hero.getpixel((780, 500))[0], 90)
        self.assertGreater(hero.getpixel((1120, 500))[2], 90)

    def test_png_renderer_uses_cinematic_background_when_available(self):
        from PIL import Image
        from longform.models import VisualScene
        from longform.render import _render_png

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            bg_path = tmp_path / "background.png"
            Image.new("RGB", (1024, 576), "#9b1c1c").save(bg_path)
            scene = VisualScene(
                index=2,
                kind="finding",
                title="检索路径决定答案可信度",
                narration="测试旁白",
                paper_anchor="finding: retrieval trace quality",
                template="task_matrix",
                duration_sec=22,
                visual_prompt="agentic search corpus map",
                accent="cyan",
            )
            png_path = tmp_path / "slide.png"
            _render_png(scene, png_path, background_path=bg_path)
            img = Image.open(png_path).convert("RGB")

        self.assertGreater(img.getpixel((1700, 500))[0], 40)
        self.assertLess(img.getpixel((1700, 500))[1], 45)

    def test_png_renderer_keeps_content_overlay_when_background_exists(self):
        from PIL import Image
        from longform.models import VisualScene
        from longform.render import _render_png

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            bg_path = tmp_path / "background.png"
            Image.new("RGB", (1024, 576), "#000000").save(bg_path)
            scene = VisualScene(
                index=0,
                kind="title",
                title="超越语义相似性：智能体搜索的检索范式革新",
                narration="开场",
                paper_anchor="固定 top-k 检索会提前过滤证据，direct corpus interaction 让智能体直接操作原始语料。",
                template="hero_title",
                duration_sec=18,
                data={"title": "Beyond Semantic Similarity: Rethinking Retrieval for Agentic Search via Direct Corpus Interaction"},
                visual_prompt="cinematic high-tech dark background neon HUD holographic interface, no readable text",
                accent="cyan",
            )
            png_path = tmp_path / "slide.png"
            _render_png(scene, png_path, background_path=bg_path)
            img = Image.open(png_path).convert("RGB")

        self.assertGreater(sum(img.getpixel((700, 520))), 140)

    def test_slide_artifacts_reserve_bottom_band_for_burned_subtitles(self):
        from PIL import Image
        from longform.models import VisualScene
        from longform.render import _render_png
        from longform.templates import render_slide_html

        narration = "这是一段很长的旁白，最终视频会通过 SRT 动态烧录字幕，因此幻灯片本身不能再把这整段文字画在底部。"
        scene = VisualScene(
            index=0,
            kind="title",
            title="AI 看视频真的能过目不忘吗？",
            narration=narration,
            paper_anchor="paper: M3Eval",
            template="hero_title",
            duration_sec=18,
            visual_prompt="brain circuit",
            accent="cyan",
        )
        with tempfile.TemporaryDirectory() as tmp:
            png_path = Path(tmp) / "slide.png"
            _render_png(scene, png_path)
            img = Image.open(png_path).convert("RGB")

        html = render_slide_html(scene, total=25)
        self.assertNotIn(narration, html)
        bottom_band = img.crop((90, 820, 1830, 1010))
        pixels = bottom_band.load()
        bright_pixels = 0
        for y in range(bottom_band.height):
            for x in range(bottom_band.width):
                r, g, b = pixels[x, y]
                if r + g + b > 420:
                    bright_pixels += 1
        self.assertLess(bright_pixels / (bottom_band.width * bottom_band.height), 0.012)

    def test_png_text_wrapping_keeps_english_words_intact(self):
        from longform.render import _wrap_text

        self.assertEqual(_wrap_text("ending: grounded conclusion", 24), ["ending: grounded", "conclusion"])

    def test_motion_renderer_keeps_slide_motion_centered_to_avoid_edge_cropping(self):
        import motion_renderer

        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            class Result:
                returncode = 0
                stderr = ""
            return Result()

        with patch("motion_renderer.subprocess.run", side_effect=fake_run):
            for index in range(3):
                motion_renderer._create_animated_segment(
                    "ffmpeg",
                    "slide.png",
                    f"segment_{index}.mp4",
                    duration=8,
                    fps=30,
                    index=index,
                )

        for call in calls:
            filter_arg = call[call.index("-vf") + 1]
            self.assertIn("scale=3840:-1", filter_arg)
            self.assertNotIn("scale=8000:-1", filter_arg)
            self.assertIn("x='iw/2-(iw/zoom/2)'", filter_arg)
            self.assertNotIn("x='(iw-iw/zoom)*on", filter_arg)
            self.assertNotIn("1.08", filter_arg)


if __name__ == "__main__":
    unittest.main()
