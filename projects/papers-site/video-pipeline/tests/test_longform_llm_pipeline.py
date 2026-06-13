from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

PIPELINE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPELINE_DIR))

from longform.llm_planner import LLMPlanValidationError, build_planning_messages, plan_longform_with_llm
from longform.llm_client import OpenAICompatibleJsonClient
from longform.visual_assets import generate_visual_assets


def _agentic_search_paper():
    return {
        "slug": "a262-agentic-search-direct-corpus",
        "title": "Agentic Search over a Direct Corpus",
        "summary": "The paper studies agentic search over a direct corpus, where agents inspect retrieval traces, cite evidence, and decide when to stop searching.",
        "abstract": "We introduce an evaluation for agentic search systems that navigate a direct document corpus. The benchmark measures retrieval trace quality, evidence grounding, citation faithfulness, and stopping decisions.",
        "paper_urls": ["https://example.test/agentic-search"],
    }


def _llm_payload(scene_count=6):
    scenes = []
    visuals = []
    concepts = [
        ("title", "Agentic search is not keyword search", "paper: agentic search over a direct corpus", "agentic search control room with corpus map"),
        ("problem", "The direct corpus changes the search problem", "problem: agents inspect retrieval traces", "direct corpus maze with retrieval trace paths"),
        ("method", "Trace quality becomes measurable", "method: cite evidence and decide when to stop", "evidence citation graph with stopping decision gate"),
        ("finding", "Faithfulness depends on the path", "finding: citation faithfulness and grounding", "grounded citation chain linked to source documents"),
        ("limitation", "Search agents can stop too early", "limitation: stopping decisions", "premature stop signal cutting off relevant documents"),
        ("ending", "Better agents leave better trails", "takeaway: retrieval trace quality", "agent trail through document corpus with verified evidence"),
    ]
    for i, (kind, title, anchor, concept) in enumerate(concepts[:scene_count]):
        scenes.append(
            {
                "kind": kind,
                "title": title,
                "narration": f"这一段解释 {title}，并把它绑定到论文中的 {anchor}，强调检索轨迹、证据引用和停止决策。",
                "paper_anchor": anchor,
                "template_hint": "method_transfer" if kind == "method" else "task_matrix",
                "duration_sec": 22,
                "data": {"concept": concept},
            }
        )
        visuals.append(
            {
                "template": "method_transfer" if kind == "method" else "task_matrix",
                "visual_prompt": f"{concept}, cinematic high-tech sci-fi illustration, dark background, neon HUD overlays, no readable text, no watermark",
                "accent": "cyan",
                "data": {"concept": concept},
            }
        )
    return {
        "fact_pack": {
            "slug": "a262-agentic-search-direct-corpus",
            "title": "Agentic Search over a Direct Corpus",
            "summary": "Agentic search over a direct corpus with retrieval traces and evidence grounding.",
            "abstract": "Agents navigate documents, cite evidence, and stop searching.",
            "urls": ["https://example.test/agentic-search"],
            "problem": "Keyword-style evaluation misses retrieval trace quality.",
            "method": "Evaluate corpus navigation, citation grounding, and stopping decisions.",
            "findings": ["Faithful answers depend on the retrieval path."],
            "limitations": ["Agents may stop early."],
            "key_terms": ["agentic search", "direct corpus", "retrieval trace", "citation faithfulness"],
            "anchors": [
                {"kind": "problem", "text": "direct corpus changes search", "evidence": "abstract"},
                {"kind": "method", "text": "retrieval trace quality", "evidence": "summary"},
            ],
        },
        "scenes": scenes,
        "visual_scenes": visuals,
    }


class FakeLLM:
    def __init__(self, payload):
        self.payload = payload
        self.messages = None

    def complete_json(self, messages):
        self.messages = messages
        return self.payload


class LongformLlmPipelineTests(unittest.TestCase):
    def test_openai_compatible_client_posts_directly_to_chat_completions(self):
        class Response:
            def raise_for_status(self):
                return None

            def json(self):
                return {"choices": [{"message": {"content": '{"ok": true}'}}]}

        with patch("requests.post", return_value=Response()) as post:
            client = OpenAICompatibleJsonClient(api_key="test-key", base_url="https://example.test/v1", model="test-model")
            result = client.complete_json([{"role": "user", "content": "json"}])

        self.assertEqual(result, {"ok": True})
        self.assertEqual(post.call_args.args[0], "https://example.test/v1/chat/completions")
        self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer test-key")
        self.assertEqual(post.call_args.kwargs["json"]["model"], "test-model")

    def test_llm_planner_uses_paper_content_for_non_memory_video_prompts(self):
        fake = FakeLLM(_llm_payload())
        fact_pack, scenes, visual_scenes = plan_longform_with_llm(_agentic_search_paper(), scene_count=6, llm=fake)
        message_text = json.dumps(fake.messages, ensure_ascii=False)

        self.assertEqual(fact_pack.slug, "a262-agentic-search-direct-corpus")
        self.assertEqual(len(scenes), 6)
        self.assertEqual(len(visual_scenes), 6)
        self.assertIn("Agentic Search over a Direct Corpus", message_text)
        self.assertIn("derive every scene from the supplied paper", message_text)
        self.assertIn("Do not reuse a fixed paper-specific scene list", message_text)
        self.assertIn("high-tech", message_text)

        prompts = "\n".join(scene.visual_prompt for scene in visual_scenes)
        self.assertIn("agentic search", prompts)
        self.assertIn("direct corpus", prompts)
        self.assertIn("retrieval trace", prompts)
        self.assertIn("citation", prompts)
        self.assertNotIn("M3Eval", prompts)
        self.assertNotIn("N-Back", prompts)
        self.assertGreaterEqual(len({scene.visual_prompt for scene in visual_scenes}), 6)

    def test_llm_planner_rejects_generic_or_repeated_visual_prompts(self):
        payload = _llm_payload()
        for visual in payload["visual_scenes"]:
            visual["visual_prompt"] = "cinematic high-tech dark background neon HUD dashboard, no readable text"

        with self.assertRaises(LLMPlanValidationError):
            plan_longform_with_llm(_agentic_search_paper(), scene_count=6, llm=FakeLLM(payload))

    def test_llm_planner_normalizes_visual_prompts_for_text_free_tech_style(self):
        payload = _llm_payload()
        payload["visual_scenes"][0]["visual_prompt"] = "agentic search direct corpus title card labeled 'DCI'"

        _fact_pack, _scenes, visual_scenes = plan_longform_with_llm(_agentic_search_paper(), scene_count=6, llm=FakeLLM(payload))
        prompt = visual_scenes[0].visual_prompt

        self.assertIn("high-tech", prompt)
        self.assertIn("neon HUD", prompt)
        self.assertIn("no readable text", prompt)
        self.assertIn("no labels", prompt)
        self.assertNotIn("'DCI'", prompt)
        self.assertNotIn("labeled", prompt.lower())

    def test_llm_planner_preserves_scene_data_when_visual_data_overlaps(self):
        payload = _llm_payload()
        payload["scenes"][0]["data"]["title"] = "Beyond Semantic Similarity: Direct Corpus Interaction"
        payload["visual_scenes"][0]["data"]["title"] = "Short decorative title"

        _fact_pack, _scenes, visual_scenes = plan_longform_with_llm(_agentic_search_paper(), scene_count=6, llm=FakeLLM(payload))

        self.assertEqual(
            visual_scenes[0].data["title"],
            "Beyond Semantic Similarity: Direct Corpus Interaction",
        )

    def test_visual_assets_generate_images_from_llm_visual_prompts(self):
        _fact_pack, _scenes, visual_scenes = plan_longform_with_llm(_agentic_search_paper(), scene_count=6, llm=FakeLLM(_llm_payload()))
        calls = []

        def fake_image_generator(prompt, cache_dir, index):
            calls.append((prompt, Path(cache_dir), index))
            path = Path(cache_dir) / f"frame_{index:02d}.png"
            path.write_bytes(b"fake image")
            return path

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            assets = generate_visual_assets(visual_scenes, out_dir, image_generator=fake_image_generator)
            manifest = json.loads((out_dir / "visual_assets.json").read_text(encoding="utf-8"))

        self.assertEqual(len(assets), 6)
        self.assertEqual(len(calls), 6)
        self.assertIn("retrieval trace", "\n".join(call[0] for call in calls))
        self.assertEqual(manifest["scene_count"], 6)
        self.assertTrue(all(str(index) in manifest["assets"] for index in range(6)))


if __name__ == "__main__":
    unittest.main()
