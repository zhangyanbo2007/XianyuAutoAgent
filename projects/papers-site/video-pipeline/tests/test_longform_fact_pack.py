from pathlib import Path
import sys
import unittest

PIPELINE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPELINE_DIR))

from longform.fact_pack import build_fact_pack


class LongformFactPackTests(unittest.TestCase):
    def test_build_fact_pack_extracts_m3eval_memory_anchors(self):
        paper = {
            "slug": "mm80-m3eval-multimodal-memory",
            "title": "M^3Eval: Multi-Modal Memory Evaluation through Cognitively-Grounded Video Tasks",
            "summary": "M3Eval 基于认知心理学设计视频任务，分别测试记忆保持、干扰下的稳健性、空间/时间 source grounding、并行视频流中的解缠，以及符号记忆。",
            "abstract": "We introduce M3Eval, a benchmark for memory in multi-modal models. Models struggle with parallel video streams, interference patterns, spatial versus temporal source grounding, and symbolic memory.",
            "paper_urls": ["https://arxiv.org/abs/2606.05008"],
            "project_urls": ["https://pku-value-lab.github.io/m3eval-homepage"],
        }

        fact_pack = build_fact_pack(paper)

        self.assertEqual(fact_pack.slug, "mm80-m3eval-multimodal-memory")
        self.assertTrue(fact_pack.problem)
        self.assertIn("memory", fact_pack.key_terms)
        self.assertGreaterEqual(len(fact_pack.anchors), 4)
        self.assertTrue(any(anchor["kind"] == "task" and "interference" in anchor["text"].lower() for anchor in fact_pack.anchors))


if __name__ == "__main__":
    unittest.main()
