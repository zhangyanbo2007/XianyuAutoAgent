from pathlib import Path
import json
import sys
import tempfile
import unittest

PIPELINE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPELINE_DIR))

from longform.assembly import build_render_manifest
from longform.fact_pack import build_fact_pack
from longform.render import render_visual_plan
from longform.storyboard import build_storyboard
from longform.timeline import build_timeline, write_srt
from longform.visual_plan import build_visual_plan


def _paper():
    return {
        "slug": "mm80-m3eval-multimodal-memory",
        "title": "M^3Eval: Multi-Modal Memory Evaluation through Cognitively-Grounded Video Tasks",
        "summary": "M3Eval 测试记忆保持、干扰、空间/时间定位、并行视频流解缠和符号记忆。",
        "abstract": "Models struggle with parallel video streams, interference, temporal source grounding, and symbolic memory.",
        "paper_urls": ["https://arxiv.org/abs/2606.05008"],
    }


class LongformAssemblyTests(unittest.TestCase):
    def test_render_manifest_connects_slides_timeline_and_subtitles(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            visual_scenes = build_visual_plan(build_storyboard(build_fact_pack(_paper()), target_scene_count=25))
            render_result = render_visual_plan(visual_scenes, out_dir)
            timeline = build_timeline(visual_scenes)
            srt_path = write_srt(timeline, out_dir / "narration.srt")

            manifest_path = build_render_manifest(visual_scenes, render_result, timeline, srt_path, out_dir)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(manifest["renderer"], "motion_renderer.render_video_v2")
        self.assertEqual(manifest["resolution"], [1920, 1080])
        self.assertEqual(len(manifest["slides"]), 25)
        self.assertTrue(all(slide["path"].endswith(".png") for slide in manifest["slides"]))
        self.assertEqual(manifest["slides"][0]["transition"], "cut")
        self.assertEqual(manifest["slides"][1]["transition"], "crossfade")
        self.assertTrue(manifest["subtitle_path"].endswith("narration.srt"))
        self.assertIn("最后回到这篇论文", manifest["narration_text"])


if __name__ == "__main__":
    unittest.main()
