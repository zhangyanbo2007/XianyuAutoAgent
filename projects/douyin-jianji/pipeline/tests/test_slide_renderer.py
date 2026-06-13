"""Tests for reference-style slide rendering."""

import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

import config
from slide_renderer import _font, _wrap, render_slide


class SlideRendererTest(unittest.TestCase):
    def test_wrap_limits_lines_and_adds_ellipsis(self):
        img = Image.new("RGB", (config.VIDEO_WIDTH, config.VIDEO_HEIGHT))
        draw = ImageDraw.Draw(img)
        font = _font("subtitle")

        lines = _wrap(
            draw,
            "这是一个特别长的政策解读标题，需要在参考视频标题栏里保持完整可读而不是横向溢出画面",
            font,
            520,
            max_lines=2,
        )

        self.assertLessEqual(len(lines), 2)
        self.assertTrue(lines[-1].endswith("..."))
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            self.assertLessEqual(bbox[2] - bbox[0], 520)

    def test_wrap_avoids_orphan_punctuation_line(self):
        img = Image.new("RGB", (config.VIDEO_WIDTH, config.VIDEO_HEIGHT))
        draw = ImageDraw.Draw(img)

        lines = _wrap(
            draw,
            "绿区负载低于60%，承载力充足，直接备案接入，无需配储能，流程相当简单；",
            _font("subtitle_bar"),
            config.VIDEO_WIDTH - 180,
            max_lines=2,
        )

        self.assertLessEqual(len(lines), 2)
        self.assertNotIn(lines[-1], {"单；", "；"})
        self.assertTrue(lines[-1].endswith("..."))

    def test_rendered_slide_has_reference_bars_and_non_empty_center(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "slide.png"
            render_slide(
                {
                    "template": "data_release",
                    "title": "618光伏新政解析",
                    "subtitle": "沿用多年的80%硬性红线正式废止",
                    "data": {
                        "headline": "80%红线废止",
                        "stats": [{"value": "50GW", "label": "存量项目释放", "color": "accent_gold"}],
                    },
                },
                None,
                str(output),
                "618光伏新政解析",
            )

            img = Image.open(output).convert("RGB")
            self.assertEqual(img.size, (config.VIDEO_WIDTH, config.VIDEO_HEIGHT))
            top_pixel = img.getpixel((config.VIDEO_WIDTH // 2, 30))
            bottom_pixel = img.getpixel((config.VIDEO_WIDTH // 2, config.VIDEO_HEIGHT - 40))
            center_pixel = img.getpixel((config.VIDEO_WIDTH // 2, config.VIDEO_HEIGHT // 2))
            self.assertNotEqual(top_pixel, center_pixel)
            self.assertNotEqual(bottom_pixel, center_pixel)
            self.assertGreater(sum(bottom_pixel), 180)


if __name__ == "__main__":
    unittest.main()
