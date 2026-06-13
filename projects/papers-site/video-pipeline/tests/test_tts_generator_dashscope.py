"""Regression tests for DashScope TTS generation."""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch

import tts_generator_dashscope as tts


class DashScopeTtsTest(unittest.TestCase):
    def test_requests_uses_current_speech_synthesizer_api(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "speech.mp3")
            srt_path = os.path.join(tmpdir, "speech.srt")

            post_response = Mock()
            post_response.json.return_value = {
                "output": {
                    "audio": {
                        "url": "https://example.test/speech.mp3",
                    },
                },
            }
            get_response = Mock(content=b"mp3-data")

            with (
                patch("requests.post", return_value=post_response) as post,
                patch("requests.get", return_value=get_response) as get,
                patch.object(tts, "_get_audio_duration", return_value=1.5),
                patch.object(tts, "_generate_srt_from_text"),
            ):
                result = tts._generate_with_requests("测试。", output_path, srt_path, "longxiaochun_v3")

            self.assertEqual(result["audio_path"], output_path)
            self.assertEqual(get.call_args.args[0], "https://example.test/speech.mp3")

            post_url = post.call_args.args[0]
            post_payload = post.call_args.kwargs["json"]
            self.assertEqual(
                post_url,
                "https://dashscope.aliyuncs.com/api/v1/services/audio/tts/SpeechSynthesizer",
            )
            self.assertEqual(post_payload["model"], "cosyvoice-v3-flash")
            self.assertEqual(
                post_payload["input"],
                {
                    "text": "测试。",
                    "voice": "longxiaochun_v3",
                    "format": "mp3",
                    "sample_rate": 24000,
                },
            )


if __name__ == "__main__":
    unittest.main()
