"""Tests for reference-style slide rendering."""

import tempfile
import unittest
from pathlib import Path

from PIL import Image

import config
from slide_renderer import render_slide


class SlideRendererTest(unittest.TestCase):
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
