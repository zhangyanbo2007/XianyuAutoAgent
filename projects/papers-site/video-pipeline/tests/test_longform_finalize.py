from pathlib import Path
import json
import sys
import tempfile
import unittest

PIPELINE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPELINE_DIR))

from longform.assembly import build_render_manifest
from longform.fact_pack import build_fact_pack
from longform.finalize import build_production_readiness, generate_audio_from_manifest, render_video_from_manifest, retime_manifest_to_audio_segments
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


def _manifest(out_dir: Path) -> Path:
    visual_scenes = build_visual_plan(build_storyboard(build_fact_pack(_paper()), target_scene_count=25))
    render_result = render_visual_plan(visual_scenes, out_dir)
    timeline = build_timeline(visual_scenes)
    srt_path = write_srt(timeline, out_dir / "narration.srt")
    return build_render_manifest(visual_scenes, render_result, timeline, srt_path, out_dir)


class LongformFinalizeTests(unittest.TestCase):
    def test_production_readiness_reports_inputs_dependencies_and_next_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            manifest_path = _manifest(out_dir)
            readiness_path = build_production_readiness(
                manifest_path,
                dependency_overrides={"ffmpeg": True, "edge_tts": True},
            )
            report = json.loads(readiness_path.read_text(encoding="utf-8"))

        self.assertEqual(report["scene_count"], 25)
        self.assertTrue(report["slides_ready"])
        self.assertTrue(report["subtitle_ready"])
        self.assertTrue(report["ffmpeg_ready"])
        self.assertTrue(report["tts_ready"])
        self.assertFalse(report["audio_ready"])
        self.assertFalse(report["can_render_final_video"])
        self.assertEqual(report["next_action"], "generate_audio")

    def test_generate_audio_from_manifest_uses_per_scene_tts_and_concat(self):
        tts_calls = []
        join_calls = {}

        def fake_tts(text, output_path, voice):
            tts_calls.append({"text": text, "output_path": str(output_path), "voice": voice})
            Path(output_path).write_bytes(b"fake mp3 segment")
            return Path(output_path)

        def fake_joiner(segment_paths, output_path):
            join_calls["segment_count"] = len(segment_paths)
            join_calls["output_path"] = str(output_path)
            Path(output_path).write_bytes(b"fake joined mp3")
            return Path(output_path)

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            manifest_path = _manifest(out_dir)
            audio_path = generate_audio_from_manifest(
                manifest_path,
                tts_writer=fake_tts,
                audio_joiner=fake_joiner,
                voice="zh-CN-YunxiNeural",
            )
            self.assertTrue(audio_path.exists())

        self.assertEqual(len(tts_calls), 25)
        self.assertTrue(any("最后回到这篇论文" in call["text"] for call in tts_calls))
        self.assertTrue(all("audio_segments" in call["output_path"] for call in tts_calls))
        self.assertEqual(join_calls["segment_count"], 25)
        self.assertTrue(join_calls["output_path"].endswith("narration.mp3"))
        self.assertEqual(tts_calls[0]["voice"], "zh-CN-YunxiNeural")

    def test_retime_manifest_to_audio_segments_updates_slide_durations_and_srt(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            manifest_path = _manifest(out_dir)
            segment_dir = out_dir / "audio_segments"
            segment_dir.mkdir()
            for i in range(25):
                (segment_dir / f"section_{i:02d}.mp3").write_bytes(b"fake segment")

            retimed_path = retime_manifest_to_audio_segments(
                manifest_path,
                duration_probe=lambda path: 10.0 + int(Path(path).stem.split("_")[-1]) * 0.1,
            )
            manifest = json.loads(retimed_path.read_text(encoding="utf-8"))
            srt_text = Path(manifest["subtitle_path"]).read_text(encoding="utf-8")

        self.assertAlmostEqual(manifest["slides"][0]["duration_sec"], 10.0, places=3)
        self.assertAlmostEqual(manifest["slides"][1]["duration_sec"], 10.1, places=3)
        self.assertAlmostEqual(manifest["total_duration_sec"], sum(10.0 + i * 0.1 for i in range(25)), places=3)
        self.assertGreater(srt_text.count("-->"), 25)
        self.assertIn("最后回到这篇论文", srt_text)

    def test_render_video_from_manifest_consumes_manifest_with_injected_renderer(self):
        calls = {}

        def fake_renderer(slides, audio_path, output_path, srt_path, fps):
            calls["slide_count"] = len(slides)
            calls["audio_path"] = audio_path
            calls["output_path"] = output_path
            calls["srt_path"] = srt_path
            calls["fps"] = fps
            Path(output_path).write_bytes(b"fake mp4")
            return output_path

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            manifest_path = _manifest(out_dir)
            audio_path = out_dir / "narration.mp3"
            audio_path.write_bytes(b"fake audio")
            output = render_video_from_manifest(
                manifest_path,
                audio_path=audio_path,
                renderer=fake_renderer,
                dependency_overrides={"ffmpeg": True, "edge_tts": True},
            )
            self.assertTrue(output.exists())

        self.assertEqual(calls["slide_count"], 25)
        self.assertTrue(calls["audio_path"].endswith("narration.mp3"))
        self.assertTrue(calls["srt_path"].endswith("narration.srt"))
        self.assertEqual(calls["fps"], 30)


if __name__ == "__main__":
    unittest.main()
