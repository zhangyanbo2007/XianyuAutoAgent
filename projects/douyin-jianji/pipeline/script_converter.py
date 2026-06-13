"""将Excel脚本转换为pipeline可用的JSON格式"""

import json
import re
from typing import Dict

import openpyxl


SCRIPT_START = "抖音短视频脚本"
METADATA_KEYS = {
    "时长": "duration_text",
    "风格": "style",
    "BGM": "bgm",
    "标题": "headline",
    "话题": "hashtags",
    "出镜": "camera",
}
TIP_KEYS = {
    "评论区预埋": "comments",
    "字幕细节": "subtitle_tips",
    "封面文案": "cover_text",
}
EMOJI_PATTERN = re.compile(r"[✅📋⚠🚫💡✨]")
TIME_RANGE_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*s", re.I)


def parse_excel_scripts(excel_path) -> list[dict]:
    """Return every script block from an Excel workbook."""
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    scripts = []

    for ws in wb.worksheets:
        rows = [_row_values(row) for row in ws.iter_rows(values_only=True)]
        starts = [
            index for index, row in enumerate(rows)
            if _cell_text(row, 0) == SCRIPT_START
        ]

        for local_index, start in enumerate(starts):
            end = starts[local_index + 1] if local_index + 1 < len(starts) else len(rows)
            script = _parse_script_block(
                rows[start:end],
                excel_path=str(excel_path),
                sheet_name=ws.title,
                block_index=len(scripts),
            )
            if script["sections"]:
                scripts.append(script)

    return scripts


def clean_visual_text(value: str) -> str:
    """Remove visual labels and rendering-hostile symbols from a visual cell."""
    text = "" if value is None else str(value)
    text = text.replace("→", " -> ")
    text = re.sub(r"【\s*画面\s*】", "", text)
    text = re.sub(r"【\s*字幕\s*】", "", text)
    text = EMOJI_PATTERN.sub("", text).replace("\ufe0f", "")
    text = text.replace("\u200b", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s*\n\s*", " ", text)
    text = re.sub(r"\s*->\s*", " -> ", text)
    return text.strip()


def convert_excel_to_script(excel_path: str) -> Dict:
    """Backward-compatible wrapper returning the first parsed script."""
    scripts = parse_excel_scripts(excel_path)
    if not scripts:
        raise ValueError(f"未在Excel中找到脚本段落: {excel_path}")
    return scripts[0]


def _parse_script_block(rows: list[list], excel_path: str,
                        sheet_name: str, block_index: int) -> dict:
    """Parse one contiguous script block from worksheet rows."""
    script = {
        "source_file": excel_path,
        "sheet_name": sheet_name,
        "block_index": block_index,
        "video_title": SCRIPT_START,
        "program_title": "",
        "duration_text": "",
        "duration": "",
        "style": "",
        "bgm": "",
        "headline": "",
        "hashtags": "",
        "camera": "",
        "sections": [],
        "execution_tips": {},
    }

    for row in rows:
        key = _cell_text(row, 0)
        value = _cell_text(row, 1)

        if not key:
            continue

        if key != SCRIPT_START and not script["program_title"] and not _is_known_label(key):
            script["program_title"] = key
            script["video_title"] = key
            continue

        if key in METADATA_KEYS:
            target = METADATA_KEYS[key]
            script[target] = value
            if target == "duration_text":
                script["duration"] = value
            continue

        if key in TIP_KEYS:
            script["execution_tips"][TIP_KEYS[key]] = value
            continue

        if _is_section_row(key):
            script["sections"].append(_parse_section(row, len(script["sections"])))

    if not script["program_title"]:
        script["program_title"] = script.get("headline") or f"脚本{block_index + 1}"
        script["video_title"] = script["program_title"]

    return script


def _parse_section(row: list, section_id: int) -> dict:
    time_cell = _cell_text(row, 0)
    visual = clean_visual_text(_cell_text(row, 1))
    text = _cell_text(row, 2)
    asset_hint = _cell_text(row, 4)
    template_type = _infer_template_type(time_cell, f"{visual} {text}")
    headline = _extract_headline(time_cell, visual)

    section = {
        "id": section_id,
        "time_range": _extract_time_range(time_cell),
        "type": template_type,
        "template": template_type,
        "duration_sec": _parse_time_range(time_cell),
        "label": _extract_label(time_cell),
        "text": text,
        "visual": visual,
        "asset_hint": asset_hint,
        "素材建议": asset_hint,
        "slide": {
            "template": template_type,
            "data": {
                "headline": headline,
                "bg_prompt": _generate_bg_prompt(template_type, headline),
            },
        },
    }

    if template_type == "process_flow":
        section["slide"]["data"]["steps"] = _extract_steps(visual)
    elif template_type in {"material_grid", "channel_steps"}:
        section["slide"]["data"]["items"] = _extract_grid_items(visual)

    return section


def _row_values(row) -> list:
    return [cell for cell in row]


def _cell_text(row: list, index: int) -> str:
    if index >= len(row) or row[index] is None:
        return ""
    return str(row[index]).strip()


def _is_known_label(value: str) -> bool:
    return (
        value == SCRIPT_START or
        value in METADATA_KEYS or
        value in TIP_KEYS or
        value in {"时间", "执行建议"} or
        _is_section_row(value)
    )


def _is_section_row(value: str) -> bool:
    return bool(TIME_RANGE_PATTERN.search(value or ""))


def _extract_time_range(time_str: str) -> str:
    match = TIME_RANGE_PATTERN.search(time_str or "")
    if not match:
        return ""
    start, end = match.group(1), match.group(2)
    return f"{start}-{end}s"


def _parse_time_range(time_str: str) -> float:
    """解析时间段，返回时长（秒）"""
    match = TIME_RANGE_PATTERN.search(time_str or "")
    if not match:
        return 5.0
    return float(match.group(2)) - float(match.group(1))


def _extract_label(time_str: str) -> str:
    """从时间段提取标签"""
    try:
        if "(" in time_str and ")" in time_str:
            start = time_str.index("(") + 1
            end = time_str.index(")")
            return time_str[start:end]
        return _extract_time_range(time_str)
    except Exception:
        return time_str


def _extract_headline(time_str: str, visual: str) -> str:
    """提取标题文字"""
    if visual:
        return visual[:34]
    return _extract_label(time_str)


def _infer_template_type(time_str: str, visual: str) -> str:
    """根据时间段和视觉描述推断模板类型"""
    label = _extract_label(time_str)
    text = visual or ""

    if any(keyword in label for keyword in ["结尾", "引导"]) or any(
        keyword in text for keyword in ["评论", "关注", "下期", "问我"]
    ):
        return "cta_summary"
    if "痛点" in label or "悬念" in label or "坑" in text:
        return "headline_warning"
    if "绿" in text and "黄" in text and "红" in text:
        return "zone_cards"
    if re.search(r"\d+(?:\.\d+)?\s*(?:GW|%|个工作日)", text, re.I):
        return "data_release"
    if any(keyword in text for keyword in ["顺序", "流程", "步骤", "备案", "并网"]):
        return "process_flow"
    if any(keyword in text for keyword in ["材料", "清单", "必备", "身份证", "权属", "承重"]):
        return "material_grid"
    if any(keyword in text for keyword in ["渠道", "办理", "申请", "营业厅", "APP"]):
        return "channel_steps"
    return "policy_explain"


def _generate_bg_prompt(template_type: str, topic: str) -> str:
    """根据模板类型生成AI图片提示词"""
    prompts = {
        "cover_dark": (
            "Professional dark tech background with solar panels theme, "
            "green energy waves, cinematic lighting, modern corporate style, "
            "16:9 aspect ratio"
        ),
        "headline_warning": (
            "Solar policy warning scene, dark blue background, gold headline, "
            "professional infographic aesthetic, 16:9 aspect ratio"
        ),
        "data_release": (
            "Solar energy policy data visualization, dark blue tone, "
            "large numeric infographic, green accent lighting, 16:9 aspect ratio"
        ),
        "zone_cards": (
            "Power grid green yellow red zone management infographic, "
            "professional policy explainer style, 16:9 aspect ratio"
        ),
        "policy_explain": (
            "Modern solar infrastructure and power grid control room, "
            "clean professional explainer background, 16:9 aspect ratio"
        ),
        "process_flow": (
            "Solar installation permit process flow, professional infographic, "
            "dark background with green highlights, 16:9 aspect ratio"
        ),
        "material_grid": (
            "Solar permit documents and rooftop panels, clean professional "
            "background, 16:9 aspect ratio"
        ),
        "channel_steps": (
            "State Grid service app and power supply office workflow, "
            "professional infographic background, 16:9 aspect ratio"
        ),
        "cta_summary": (
            "Professional solar consultation scene, trustworthy mood, "
            "warm accent lighting, 16:9 aspect ratio"
        ),
    }
    return prompts.get(template_type, prompts["policy_explain"])


def _extract_steps(visual: str) -> list:
    """从视觉描述中提取步骤"""
    content = visual.split("：", 1)[-1] if "：" in visual else visual
    if "->" in content:
        return [part.strip() for part in content.split("->") if part.strip()]
    if "、" in content:
        return [part.strip() for part in content.split("、") if part.strip()]
    if "备案" in visual or "施工" in visual or "并网" in visual:
        return ["备案申请", "施工安装", "并网验收"]
    return []


def _extract_grid_items(visual: str) -> list:
    """从视觉描述中提取网格项目"""
    content = visual.split("：", 1)[-1] if "：" in visual else visual
    separators = ["+", " / ", "、", "|", "｜"]
    parts = [content]
    for sep in separators:
        if sep in content:
            parts = content.split(sep)
            break

    items = []
    for part in parts:
        title = part.strip()
        if title:
            items.append({"title": title, "desc": ""})

    if items:
        return items

    if "身份证" in visual or "房屋" in visual:
        return [
            {"title": "身份证", "desc": "本人有效身份证件"},
            {"title": "房屋权属证明", "desc": "房产证或宅基地证明"},
            {"title": "承重报告", "desc": "老房子需提供"},
        ]
    if "网上国网" in visual or "营业厅" in visual:
        return [
            {"title": "网上国网APP", "desc": "在线提交申请"},
            {"title": "供电营业厅", "desc": "线下提交申请"},
        ]
    return []


def save_script_to_json(script: Dict, output_path: str):
    """将脚本保存为JSON文件"""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)
    print(f"脚本已保存到: {output_path}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python script_converter.py <Excel文件路径> [输出JSON路径]")
        sys.exit(1)

    excel_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "script.json"

    script = convert_excel_to_script(excel_path)
    save_script_to_json(script, output_path)
