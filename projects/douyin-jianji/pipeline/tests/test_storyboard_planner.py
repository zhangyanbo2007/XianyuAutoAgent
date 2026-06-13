"""Tests for reference-style storyboard planning."""

import unittest

from storyboard_planner import plan_storyboard


class StoryboardPlannerTest(unittest.TestCase):
    def test_long_core_section_splits_into_multiple_shots(self):
        script = {
            "headline": "卡了6年的光伏80%红线，正式作废！",
            "program_title": "《618光伏新政1》 - 文件解读",
            "sections": [
                {
                    "label": "痛点/悬念",
                    "duration_sec": 3,
                    "visual": "80%并网红线，彻底取消！",
                    "text": "多少光伏项目，倒在变压器80%负载率这条线上？",
                    "template": "headline_warning",
                },
                {
                    "label": "核心干货输出",
                    "duration_sec": 15,
                    "visual": "废止80%红线｜释放50GW存量项目｜三色分区柔性管控",
                    "text": "沿用多年的光伏并网80%硬性红线，在新政里直接被废止！再也不是一刀切禁止并网。行业统计显示，这一次直接盘活50GW被积压的存量光伏项目。新政换成更科学的绿、黄、红三色分区柔性管控。",
                    "template": "data_release",
                },
                {
                    "label": "结尾引导",
                    "duration_sec": 4,
                    "visual": "",
                    "text": "三色分区到底怎么划分？下期视频一次性讲透",
                    "template": "cta_summary",
                },
            ],
        }

        storyboard = plan_storyboard(script)

        self.assertGreaterEqual(len(storyboard["shots"]), 6)
        templates = {shot["template"] for shot in storyboard["shots"]}
        self.assertIn("cover_dark", templates)
        self.assertIn("data_release", templates)
        self.assertIn("zone_cards", templates)
        self.assertIn("cta_summary", templates)

    def test_process_and_material_content_get_specific_templates(self):
        script = {
            "headline": "家用光伏前期手续完整版，新手直接照做",
            "program_title": "《光伏前期手续》 - 科普知识",
            "sections": [
                {
                    "label": "核心新规科普",
                    "duration_sec": 7,
                    "visual": "正确顺序：备案 -> 施工 -> 并网",
                    "text": "家用光伏必须先办手续、再施工。",
                    "template": "process_flow",
                },
                {
                    "label": "必备材料清单",
                    "duration_sec": 8,
                    "visual": "必备资料：身份证 + 房屋权属证明 + 承重报告（老房）",
                    "text": "前期只需要准备三样东西。",
                    "template": "material_grid",
                },
            ],
        }

        storyboard = plan_storyboard(script)
        templates = [shot["template"] for shot in storyboard["shots"]]

        self.assertIn("process_flow", templates)
        self.assertIn("material_grid", templates)
        self.assertNotIn("grid_2x2", templates)


if __name__ == "__main__":
    unittest.main()
