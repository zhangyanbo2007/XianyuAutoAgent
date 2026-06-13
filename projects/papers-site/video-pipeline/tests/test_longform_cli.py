from pathlib import Path
import json
import sys
import tempfile
import unittest

PIPELINE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPELINE_DIR))

from longform.cli import run_longform_dry_run
from longform.models import PaperFactPack, Scene, VisualScene


class LongformCliTests(unittest.TestCase):
    def test_cli_dry_run_writes_reviewable_artifacts(self):
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

            self.assertTrue(paths["fact_pack"].exists())
            self.assertTrue(paths["storyboard"].exists())
            self.assertTrue(paths["visual_plan"].exists())
            self.assertTrue(paths["timeline"].exists())
            self.assertTrue(paths["narration_srt"].exists())
            self.assertTrue(paths["render_manifest"].exists())
            self.assertTrue(paths["production_readiness"].exists())
            self.assertTrue(paths["qa_report"].exists())
            self.assertTrue(paths["contact_sheet"].exists())

            manifest = json.loads(paths["render_manifest"].read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["slides"]), 25)
            readiness = json.loads(paths["production_readiness"].read_text(encoding="utf-8"))
            self.assertEqual(readiness["scene_count"], 25)
            self.assertTrue(readiness["slides_ready"])
            self.assertTrue(readiness["subtitle_ready"])
            qa = json.loads(paths["qa_report"].read_text(encoding="utf-8"))
            self.assertEqual(qa["timeline_entry_count"], 25)
            self.assertTrue(qa["srt_exists"])

    def test_cli_dry_run_can_use_llm_plan_and_generated_visual_assets(self):
        paper = {
            "slug": "agentic-search",
            "title": "Agentic Search over a Direct Corpus",
            "summary": "Agents inspect retrieval traces and cite evidence.",
            "abstract": "The paper evaluates retrieval trace quality and stopping decisions.",
        }

        def fake_planner(input_paper, scene_count):
            fact_pack = PaperFactPack(
                slug=input_paper["slug"],
                title=input_paper["title"],
                summary=input_paper["summary"],
                abstract=input_paper["abstract"],
                problem="Search evaluation misses trace quality.",
                method="Measure retrieval traces and citation grounding.",
                findings=["Trace quality changes answer faithfulness."],
                limitations=["Agents can stop too early."],
                key_terms=["agentic search", "direct corpus", "retrieval trace"],
                anchors=[{"kind": "finding", "text": "retrieval trace quality", "evidence": "abstract"}],
            )
            scenes = [
                Scene(
                    index=i,
                    kind="finding",
                    title=f"检索证据链 {i + 1}",
                    narration=f"这一页解释 direct corpus 中的 retrieval trace 如何影响答案可信度，并绑定论文证据 {i + 1}。",
                    paper_anchor="finding: retrieval trace quality",
                    template_hint="task_matrix",
                    duration_sec=22,
                    data={"term": "retrieval trace"},
                )
                for i in range(scene_count)
            ]
            visuals = [
                VisualScene(
                    index=i,
                    kind=scenes[i].kind,
                    title=scenes[i].title,
                    narration=scenes[i].narration,
                    paper_anchor=scenes[i].paper_anchor,
                    template="task_matrix",
                    duration_sec=scenes[i].duration_sec,
                    data=scenes[i].data,
                    visual_prompt=f"agentic search retrieval trace corpus map {i}, cinematic dark background neon HUD, no readable text",
                    accent="cyan",
                )
                for i in range(scene_count)
            ]
            return fact_pack, scenes, visuals

        def fake_image_generator(prompt, cache_dir, index):
            from PIL import Image

            path = Path(cache_dir) / f"asset_{index:02d}.png"
            Image.new("RGB", (1024, 576), "#123456").save(path)
            return path

        with tempfile.TemporaryDirectory() as tmp:
            paths = run_longform_dry_run(
                paper,
                Path(tmp),
                scene_count=6,
                planner=fake_planner,
                generate_images=True,
                image_generator=fake_image_generator,
            )

            self.assertTrue(paths["visual_assets"].exists())
            assets = json.loads(paths["visual_assets"].read_text(encoding="utf-8"))
            manifest = json.loads(paths["render_manifest"].read_text(encoding="utf-8"))

        self.assertEqual(assets["asset_count"], 6)
        self.assertEqual(len(manifest["slides"]), 6)


if __name__ == "__main__":
    unittest.main()
