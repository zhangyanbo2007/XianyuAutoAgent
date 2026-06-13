"""Tests for video generator subtitle styling."""

import tempfile
import unittest
from pathlib import Path

from video_generator import _srt_to_styled_ass


class VideoGeneratorTest(unittest.TestCase):
    def test_ass_style_uses_reference_bottom_bar_resolution(self):
        with tempfile.TemporaryDirectory() as tmp:
            srt = Path(tmp) / "narration.srt"
            srt.write_text("1\n00:00:00,000 --> 00:00:02,000\n测试字幕\n\n", encoding="utf-8")

            ass = Path(_srt_to_styled_ass(str(srt), tmp))
            content = ass.read_text(encoding="utf-8")

            self.assertIn("PlayResX: 1920", content)
            self.assertIn("PlayResY: 1080", content)
            self.assertIn("MarginV", content)
            self.assertIn("测试字幕", content)


if __name__ == "__main__":
    unittest.main()
