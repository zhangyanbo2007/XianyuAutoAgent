from pathlib import Path
import sys
import tempfile
import unittest

PIPELINE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPELINE_DIR))

from longform.fact_pack import build_fact_pack
from longform.storyboard import build_storyboard
from longform.visual_plan import build_visual_plan
from longform.timeline import build_timeline, write_srt


def _paper():
    return {
        "slug": "mm80-m3eval-multimodal-memory",
        "title": "M^3Eval: Multi-Modal Memory Evaluation through Cognitively-Grounded Video Tasks",
        "summary": "M3Eval 测试记忆保持、干扰、空间/时间定位、并行视频流解缠和符号记忆。",
        "abstract": "Models struggle with parallel video streams, interference, temporal source grounding, and symbolic memory.",
        "paper_urls": ["https://arxiv.org/abs/2606.05008"],
    }


def _srt_seconds(value):
    hms, millis = value.split(",")
    h, m, s = hms.split(":")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(millis) / 1000


class LongformTimelineTests(unittest.TestCase):
    def test_timeline_is_contiguous_and_longform_duration(self):
        scenes = build_visual_plan(build_storyboard(build_fact_pack(_paper()), target_scene_count=25))
        timeline = build_timeline(scenes)

        self.assertEqual(len(timeline.entries), 25)
        self.assertEqual(timeline.entries[0].start_sec, 0.0)
        for previous, current in zip(timeline.entries, timeline.entries[1:]):
            self.assertAlmostEqual(previous.end_sec, current.start_sec, places=3)
            self.assertEqual(current.transition, "crossfade")
        self.assertGreaterEqual(timeline.total_duration_sec, 8 * 60)
        self.assertLessEqual(timeline.total_duration_sec, 12 * 60)

    def test_write_srt_outputs_one_block_per_scene(self):
        scenes = build_visual_plan(build_storyboard(build_fact_pack(_paper()), target_scene_count=25))
        timeline = build_timeline(scenes)
        with tempfile.TemporaryDirectory() as tmp:
            srt_path = write_srt(timeline, Path(tmp) / "narration.srt")
            text = srt_path.read_text(encoding="utf-8")

        self.assertIn("1\n00:00:00,000 -->", text)
        self.assertGreater(text.count("-->"), 25)
        self.assertIn("最后回到这篇论文", text)

        durations = []
        captions = []
        for block in text.strip().split("\n\n"):
            lines = block.splitlines()
            if len(lines) < 3 or "-->" not in lines[1]:
                continue
            start, end = [part.strip() for part in lines[1].split("-->")]
            durations.append(_srt_seconds(end) - _srt_seconds(start))
            captions.append(" ".join(lines[2:]).strip())
        self.assertLessEqual(max(durations), 7.1)
        self.assertFalse(any(caption in "，。、；：,.!?;" for caption in captions))
        self.assertFalse(any(caption.startswith(("emory", "erception", "itively")) for caption in captions))
        self.assertFalse(any("findings变成" in caption or "grounding和" in caption for caption in captions))
        self.assertFalse(any(" :" in caption or ":Multi" in caption for caption in captions))
        self.assertFalse(any(caption.startswith("量的") for caption in captions))


if __name__ == "__main__":
    unittest.main()
