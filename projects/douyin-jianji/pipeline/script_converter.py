"""将Excel脚本转换为pipeline可用的JSON格式"""

import json
import openpyxl
from typing import List, Dict


def convert_excel_to_script(excel_path: str) -> Dict:
    """
    将Excel脚本转换为pipeline格式的JSON

    Args:
        excel_path: Excel文件路径

    Returns:
        pipeline格式的脚本字典
    """
    wb = openpyxl.load_workbook(excel_path)
    ws = wb.active

    # 提取基本信息
    script = {
        "video_title": "",
        "duration": "",
        "style": "",
        "bgm": "",
        "headline": "",
        "hashtags": "",
        "camera": "",
        "sections": [],
        "execution_tips": {}
    }

    # 遍历所有行
    for row in ws.iter_rows(min_row=1, max_row=ws.max_row, values_only=False):
        row_data = [cell.value for cell in row]

        # 提取标题
        if row_data[0] and "抖音短视频脚本" in str(row_data[0]):
            script["video_title"] = str(row_data[0]).strip()

        # 提取基本信息
        if row_data[0] and "时长" in str(row_data[0]):
            script["duration"] = str(row_data[1]).strip() if row_data[1] else ""
        elif row_data[0] and "风格" in str(row_data[0]):
            script["style"] = str(row_data[1]).strip() if row_data[1] else ""
        elif row_data[0] and "BGM" in str(row_data[0]):
            script["bgm"] = str(row_data[1]).strip() if row_data[1] else ""
        elif row_data[0] and "标题" in str(row_data[0]):
            script["headline"] = str(row_data[1]).strip() if row_data[1] else ""
        elif row_data[0] and "话题" in str(row_data[0]):
            script["hashtags"] = str(row_data[1]).strip() if row_data[1] else ""
        elif row_data[0] and "出镜" in str(row_data[0]):
            script["camera"] = str(row_data[1]).strip() if row_data[1] else ""

        # 提取脚本段落
        if row_data[0] and "-" in str(row_data[0]) and "s" in str(row_data[0]):
            # 解析时间段
            time_str = str(row_data[0]).strip()
            duration_sec = _parse_time_range(time_str)

            # 推断模板类型
            template_type = _infer_template_type(time_str, str(row_data[1] if row_data[1] else ""))

            # 生成AI图片提示词
            bg_prompt = _generate_bg_prompt(template_type, script.get("headline", ""))

            section = {
                "id": len(script["sections"]),
                "type": template_type,
                "duration_sec": duration_sec,
                "label": _extract_label(time_str),
                "text": str(row_data[2]).strip() if row_data[2] else "",
                "visual": str(row_data[1]).strip() if row_data[1] else "",
                "素材建议": str(row_data[4]).strip() if len(row_data) > 4 and row_data[4] else "",
                "slide": {
                    "template": template_type,
                    "data": {
                        "headline": _extract_headline(time_str, str(row_data[1] if row_data[1] else "")),
                        "bg_prompt": bg_prompt,
                    }
                }
            }

            # 根据模板类型添加特定数据
            if template_type == "step_list":
                section["slide"]["data"]["steps"] = _extract_steps(str(row_data[1] if row_data[1] else ""))
            elif template_type == "grid_2x2":
                section["slide"]["data"]["items"] = _extract_grid_items(str(row_data[1] if row_data[1] else ""))

            script["sections"].append(section)

        # 提取执行建议
        if row_data[0] and "评论区预埋" in str(row_data[0]):
            script["execution_tips"]["comments"] = str(row_data[1]).strip() if row_data[1] else ""
        elif row_data[0] and "字幕细节" in str(row_data[0]):
            script["execution_tips"]["subtitle_tips"] = str(row_data[1]).strip() if row_data[1] else ""
        elif row_data[0] and "封面文案" in str(row_data[0]):
            script["execution_tips"]["cover_text"] = str(row_data[1]).strip() if row_data[1] else ""

    return script


def _parse_time_range(time_str: str) -> float:
    """解析时间段，返回时长（秒）"""
    try:
        time_str = time_str.replace("s", "").strip()
        if "-" in time_str:
            parts = time_str.split("-")
            start = float(parts[0].strip())
            end = float(parts[1].strip())
            return end - start
        return 5.0
    except:
        return 5.0


def _extract_label(time_str: str) -> str:
    """从时间段提取标签"""
    try:
        if "(" in time_str and ")" in time_str:
            start = time_str.index("(") + 1
            end = time_str.index(")")
            return time_str[start:end]
        return time_str.replace("s", "").strip()
    except:
        return time_str


def _extract_headline(time_str: str, visual: str) -> str:
    """提取标题文字"""
    label = _extract_label(time_str)

    # 从视觉描述中提取标题
    if "字幕】" in visual:
        # 提取字幕内容
        parts = visual.split("字幕】")
        if len(parts) > 1:
            text = parts[1].strip()
            # 移除emoji和特殊字符
            import re
            text = re.sub(r'[✅📋⚠️🚫💡✨]', '', text)
            return text.strip()[:20]  # 限制长度

    return label


def _infer_template_type(time_str: str, visual: str) -> str:
    """根据时间段和视觉描述推断模板类型"""
    label = _extract_label(time_str).lower()
    visual_lower = visual.lower() if visual else ""

    if "痛点" in label or "悬念" in label or "坑" in visual_lower:
        return "title"
    elif "顺序" in visual_lower or "流程" in visual_lower or "步骤" in visual_lower:
        return "step_list"
    elif "材料" in visual_lower or "清单" in visual_lower or "必备" in visual_lower:
        return "grid_2x2"
    elif "渠道" in visual_lower or "办理" in visual_lower or "申请" in visual_lower:
        return "grid_2x2"
    elif "引导" in label or "评论" in visual_lower or "关注" in visual_lower:
        return "cta"
    else:
        return "data_big"


def _generate_bg_prompt(template_type: str, topic: str) -> str:
    """根据模板类型生成AI图片提示词"""
    prompts = {
        "title": (
            f"Professional dark tech background with {topic} theme, "
            "subtle green energy waves, cinematic lighting, "
            "modern corporate style, 16:9 aspect ratio"
        ),
        "data_big": (
            f"Industrial {topic} scene, aerial view, "
            "professional photography, dark blue tone, "
            "subtle light effects, 16:9 aspect ratio"
        ),
        "grid_2x2": (
            f"Modern {topic} infrastructure, "
            "clean professional background, "
            "dark gradient with accent lighting, 16:9 aspect ratio"
        ),
        "grid_3x1": (
            f"Power grid {topic} system, "
            "professional infographic style, "
            "dark background with highlights, 16:9 aspect ratio"
        ),
        "step_list": (
            f"Step-by-step {topic} process, "
            "professional infographic style, "
            "dark background with highlights, 16:9 aspect ratio"
        ),
        "cta": (
            f"Professional {topic} consultation scene, "
            "trustworthy and reliable mood, "
            "warm accent lighting, 16:9 aspect ratio"
        ),
    }
    return prompts.get(template_type, prompts["data_big"])


def _extract_steps(visual: str) -> list:
    """从视觉描述中提取步骤"""
    import re

    # 尝试匹配 "A → B → C" 格式
    if "→" in visual:
        parts = visual.split("→")
        return [p.strip() for p in parts if p.strip()]

    # 尝试匹配 "A、B、C" 格式
    if "、" in visual:
        parts = visual.split("、")
        return [p.strip() for p in parts if p.strip()]

    # 默认步骤
    return ["步骤1", "步骤2", "步骤3"]


def _extract_grid_items(visual: str) -> list:
    """从视觉描述中提取网格项目"""
    items = []

    # 尝试匹配 "A + B + C" 格式
    if "+" in visual:
        parts = visual.split("+")
        for p in parts:
            p = p.strip()
            if p:
                items.append({"title": p, "desc": ""})

    # 尝试匹配 "A、B、C" 格式
    elif "、" in visual:
        parts = visual.split("、")
        for p in parts:
            p = p.strip()
            if p:
                items.append({"title": p, "desc": ""})

    # 默认项目
    if not items:
        items = [
            {"title": "项目1", "desc": ""},
            {"title": "项目2", "desc": ""},
        ]

    return items


def save_script_to_json(script: Dict, output_path: str):
    """将脚本保存为JSON文件"""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)
    print(f"脚本已保存到: {output_path}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python script_converter.py <excel文件路径> [输出JSON路径]")
        sys.exit(1)

    excel_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "script.json"

    script = convert_excel_to_script(excel_path)
    save_script_to_json(script, output_path)
