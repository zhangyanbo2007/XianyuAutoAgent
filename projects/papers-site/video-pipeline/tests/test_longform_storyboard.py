from pathlib import Path
import sys
import unittest

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


def _agentic_search_paper():
    return {
        "slug": "a262-agentic-search-direct-corpus",
        "title": "Beyond Semantic Similarity: Rethinking Retrieval for Agentic Search via Direct Corpus Interaction",
        "summary": "The paper studies agentic search over a direct corpus, where agents inspect retrieval traces, cite evidence, and decide when to stop searching.",
        "abstract": "The benchmark measures retrieval trace quality, evidence grounding, citation faithfulness, and stopping decisions for agents that navigate a direct document corpus.",
        "paper_urls": ["https://example.test/agentic-search"],
    }


class LongformStoryboardTests(unittest.TestCase):
    def test_storyboard_has_longform_structure_and_paper_anchors(self):
        scenes = build_storyboard(build_fact_pack(_paper()), target_scene_count=28)

        self.assertEqual(len(scenes), 28)
        self.assertEqual(scenes[0].template_hint, "hero_title")
        self.assertEqual(scenes[-1].kind, "ending")
        self.assertTrue(all(scene.paper_anchor for scene in scenes))
        self.assertTrue(any("Interference" in scene.title or "干扰" in scene.title for scene in scenes))

    def test_storyboard_narration_has_longform_audio_density(self):
        scenes = build_storyboard(build_fact_pack(_paper()), target_scene_count=25)
        total_chars = sum(len(scene.narration) for scene in scenes)

        self.assertGreaterEqual(total_chars, 3000)
        self.assertLessEqual(total_chars, 3800)
        self.assertGreaterEqual(min(len(scene.narration) for scene in scenes), 80)
        self.assertIn("论文", scenes[-1].narration)

    def test_visual_plan_uses_at_least_eight_templates(self):
        scenes = build_storyboard(build_fact_pack(_paper()), target_scene_count=28)
        visual_scenes = build_visual_plan(scenes)

        templates = {scene.template for scene in visual_scenes}
        self.assertGreaterEqual(len(templates), 8)
        self.assertIn("task_matrix", templates)
        self.assertIn("takeaway_cards", templates)

    def test_default_storyboard_is_grounded_in_non_memory_paper(self):
        scenes = build_storyboard(build_fact_pack(_agentic_search_paper()), target_scene_count=14)
        text = "\n".join([scene.title + "\n" + scene.narration + "\n" + scene.paper_anchor for scene in scenes])

        self.assertIn("direct corpus", text.lower())
        self.assertIn("retrieval", text.lower())
        self.assertIn("citation", text.lower())
        self.assertNotIn("M3Eval", text)
        self.assertNotIn("N-Back", text)
        self.assertNotIn("认知心理学", text)
        self.assertNotIn("记忆干扰", text)

    def test_default_visual_prompts_are_paper_grounded_tech_style(self):
        scenes = build_storyboard(build_fact_pack(_agentic_search_paper()), target_scene_count=14)
        visual_scenes = build_visual_plan(scenes)
        prompts = "\n".join(scene.visual_prompt for scene in visual_scenes)

        self.assertIn("high-tech", prompts)
        self.assertIn("neon HUD", prompts)
        self.assertIn("direct corpus", prompts.lower())
        self.assertIn("retrieval", prompts.lower())
        self.assertNotIn("psychology", prompts.lower())
        self.assertNotIn("memory architecture", prompts.lower())
        self.assertNotIn("brain versus AI", prompts.lower())


if __name__ == "__main__":
    unittest.main()
