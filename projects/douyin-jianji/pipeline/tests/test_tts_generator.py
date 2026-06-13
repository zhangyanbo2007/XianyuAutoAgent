"""Tests for subtitle chunking helpers."""

import unittest

from tts_generator import split_subtitle_text


class TtsGeneratorTest(unittest.TestCase):
    def test_split_subtitle_text_keeps_lines_short(self):
        chunks = split_subtitle_text("沿用多年的光伏并网80%硬性红线，在新政里直接被废止！再也不是一刀切禁止并网。", max_chars=22)

        self.assertGreaterEqual(len(chunks), 3)
        self.assertTrue(all(len(chunk) <= 22 for chunk in chunks))
        self.assertIn("80%", "".join(chunks))


if __name__ == "__main__":
    unittest.main()
