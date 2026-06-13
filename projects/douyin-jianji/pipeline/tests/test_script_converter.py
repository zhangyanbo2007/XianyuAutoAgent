"""Tests for demand Excel parsing and visual text cleanup."""

import unittest
from pathlib import Path

from script_converter import (
    clean_visual_text,
    convert_excel_to_script,
    parse_excel_scripts,
)


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent


class ScriptConverterTest(unittest.TestCase):
    def test_618_workbook_has_three_script_blocks(self):
        scripts = parse_excel_scripts(PROJECT / "demand" / "618.xlsx")

        self.assertEqual(len(scripts), 3)
        self.assertEqual([s["block_index"] for s in scripts], [0, 1, 2])
        self.assertIn("618光伏新政1", scripts[0]["program_title"])
        self.assertIn("618光伏新政2", scripts[1]["program_title"])
        self.assertIn("618光伏新政3", scripts[2]["program_title"])

    def test_douyin_workbook_has_one_script_block(self):
        scripts = parse_excel_scripts(PROJECT / "demand" / "douyinwenanjiaoben.xlsx")

        self.assertEqual(len(scripts), 1)
        self.assertIn("光伏前期手续", scripts[0]["program_title"])
        self.assertEqual(len(scripts[0]["sections"]), 5)

    def test_visual_text_is_cleaned_before_structuring(self):
        raw = "【画面】\n【字幕】✅ 正确顺序：备案 → 施工 → 并网"

        self.assertEqual(clean_visual_text(raw), "正确顺序：备案 -> 施工 -> 并网")

    def test_legacy_converter_returns_first_script_for_single_output_callers(self):
        script = convert_excel_to_script(PROJECT / "demand" / "618.xlsx")

        self.assertIn("618光伏新政1", script["program_title"])
        self.assertGreaterEqual(len(script["sections"]), 4)


if __name__ == "__main__":
    unittest.main()
