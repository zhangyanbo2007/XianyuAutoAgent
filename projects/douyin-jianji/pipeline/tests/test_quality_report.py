"""Tests for video quality report checks."""

import tempfile
import unittest
from pathlib import Path

from quality_report import build_quality_report, find_parse_residue


class QualityReportTest(unittest.TestCase):
    def test_find_parse_residue_detects_bad_tokens(self):
        payload = {
            "shots": [
                {"title": "【字幕】错误", "items": [{"title": "项目1"}]},
                {"subtitle": "正常字幕"},
            ]
        }

        residue = find_parse_residue(payload)

        self.assertIn("【字幕】", residue)
        self.assertIn("项目1", residue)

    def test_build_quality_report_marks_reference_style_requirements(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            storyboard = {
                "shots": [
                    {"template": "cover_dark", "subtitle": "开场"},
                    {"template": "data_release", "subtitle": "50GW项目释放"},
                    {"template": "process_flow", "subtitle": "备案施工并网"},
                    {"template": "cta_summary", "subtitle": "评论区问我"},
                ]
            }
            report = build_quality_report(
                output_dir=out,
                script={"source_file": "demand/618.xlsx", "sheet_name": "618新政", "block_index": 0},
                storyboard=storyboard,
                video_path=out / "missing.mp4",
                audio_path=out / "missing.mp3",
                subtitle_path=out / "missing.srt",
                tts_status="missing",
            )

            self.assertFalse(report["checks"]["has_audio"])
            self.assertTrue(report["checks"]["has_top_title_bar"])
            self.assertTrue(report["checks"]["has_bottom_subtitle_bar"])
            self.assertTrue(report["checks"]["has_infographic_body"])
            self.assertTrue(report["checks"]["has_data_or_process"])
            self.assertTrue((out / "quality_report.json").exists())
            self.assertTrue((out / "quality_report.md").exists())


if __name__ == "__main__":
    unittest.main()
