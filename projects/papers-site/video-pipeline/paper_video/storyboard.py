"""LLM-driven, paper-grounded audio-visual storyboard (精细音画分镜脚本).

Produces a list of ``section`` dicts whose schema is exactly what the
high-quality renderer (``slide_templates.render_slide`` +
``chart_generator_v2``) consumes, plus a spoken ``text`` narration and a
textless ``visual_prompt`` per scene for the cinematic AI backdrop.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Optional

from .paper_source import paper_context

# ── template contracts ──────────────────────────────────────────────
# Each entry: human note used in the prompt. The renderer reads the
# ``on_screen`` fields listed here, so the LLM must populate them.
_TYPE_CONTRACT = {
    "title":      "封面。on_screen: {top_label(机构), title(主标题), subtitle, description, english(英文标题)}",
    "question":   "核心问题。on_screen: {title(一句反差提问)}",
    "problem":    "研究缺口。on_screen: {title, labels_top:[2项已被研究], labels_bottom:[3-4项被忽略]}",
    "method":     "方法。on_screen: {title, flow:[3步,如 来源→迁移→落点]}",
    "overview":   "总览/四象限。on_screen: {title, center(核心词), quadrants:[4×{id,title,en,desc}]}",
    "test_intro": "实验介绍。on_screen.sub_type 取 divided_attention{left_label,right_label} | memory_interference{retroactive,proactive} | interleaved_events | nback_test{sequence:[3-4符号]}; 都需 {title}",
    "data_result":"数据结论(柱状图)。on_screen: {title, conclusion, root_cause}; 需 chart(type=bar)",
    "comparison": "对比(天平)。on_screen: {title, human_side:{label,left,right,balance}, ai_side:{label,left,right,balance}, insight}",
    "chart_result":"图表发现。on_screen: {title, insight, findings:[2-3条]}; 需 chart(type=line|grouped_bar)",
    "summary":    "结论矩阵。on_screen: {title, rows:[{dim,human,ai}]}",
    "ranking":    "模型排行。on_screen: {title, baseline, tiers:[{tier,models:[{name,score(0-100),color}]}]}",
    "future":     "未来方向。on_screen: {title, directions:[3×{title,en,desc,color}]}",
    "takeaway":   "关键收获。on_screen: {title, cards:[3×{title,desc,color}]}",
    "ending":     "结尾。on_screen: {title(金句), subtitle}",
}

_CHART_CONTRACT = (
    'chart 规范: '
    '{"type":"bar","title":..,"y_label":..,"data":[{"label":..,"value":0-100,"color":"#hex"}]} | '
    '{"type":"line","title":..,"x_label":..,"y_label":..,"baseline_value":num,"baseline":str,'
    '"lines":[{"label":..,"color":"#hex","data":[num,..]}]} | '
    '{"type":"grouped_bar","title":..,"y_label":..,"groups":[{"label":..}],'
    '"series":[{"label":..,"color":"#hex","values":[num,..]}]} | '
    '{"type":"ranking","title":..,"max_score":100,"data":[{"name":..,"score":num,"color":"#hex"}]}'
)

_ACCENT_BY_TYPE = {
    "title": "#00d4ff", "question": "#00ff88", "problem": "#00d4ff",
    "method": "#00d4ff", "overview": "#00d4ff", "test_intro": "#00ff88",
    "data_result": "#00ff88", "comparison": "#00d4ff", "chart_result": "#00ff88",
    "summary": "#a855f7", "ranking": "#00d4ff", "future": "#a855f7",
    "takeaway": "#00d4ff", "ending": "#00d4ff",
}
_PALETTE = ["#00d4ff", "#00ff88", "#ff00ff", "#ff8800", "#a855f7", "#ff4444"]
_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
_VISUAL_SUFFIX = (
    "cinematic high-tech dark background, neon HUD, holographic interface, "
    "volumetric light, depth of field, no readable text, no letters, no numbers, no watermark"
)
SUPPORTED_TYPES = set(_TYPE_CONTRACT)


# ── prompt construction ─────────────────────────────────────────────


def build_messages(doc: dict[str, Any], scene_count: int) -> list[dict[str, str]]:
    contract = "\n".join(f"- {name}: {note}" for name, note in _TYPE_CONTRACT.items())
    schema = {
        "title": "中文短标题",
        "sections": [
            {
                "id": "s01_xxx",
                "type": "上面允许的一种",
                "label": "该镜头中文标签",
                "text": "口播旁白(中文, 60-140字, 口语化、有信息密度)",
                "duration_sec": 24,
                "accent_color": "#00d4ff",
                "on_screen": {"按该 type 的字段契约填写": "..."},
                "visual_prompt": "English textless cinematic image prompt grounded in this scene",
                "chart": "仅 data_result/chart_result 需要, 见 chart 规范",
            }
        ],
    }
    system = (
        "你是顶尖的论文讲解视频导演。只输出 JSON。"
        "你必须完全基于提供的论文内容来设计每一个镜头，所有数据、结论、术语都要忠于论文，"
        "不得编造论文未提及的具体数字或专有名词。"
        "所有屏幕文字和旁白用中文；visual_prompt 用英文且只描述画面、绝不含任何可读文字/数字/标签。"
    )
    user = (
        f"为这篇论文制作一支 {scene_count} 个镜头的精细『音画分镜脚本』。\n\n"
        "整体要求:\n"
        f"- 镜头数量 = {scene_count}，总时长约 8-11 分钟。\n"
        "- 叙事弧线: 封面 → 反差提问 → 研究缺口 → 方法 → 总览 → 逐个实验(介绍+结果) → 对比 → 结论矩阵 → 模型排行 → 未来方向 → 关键收获 → 结尾。\n"
        "- 第一个镜头必须是 title，最后一个必须是 ending。\n"
        "- 每个镜头的 text 是口播旁白(中文, 60-140字)；on_screen 是屏幕上显示的精炼要点(短词短句)。\n"
        "- 凡涉及数据/分数的镜头(data_result/chart_result/ranking)必须给出 chart，并让数值忠于论文(论文没有的就给出合理的相对示意并在 root_cause/insight 中说明是示意)。\n"
        "- accent_color 用 16 进制；visual_prompt 必须以画面意象为主、贴合该镜头的论文内容、并自带高科技暗色霓虹氛围。\n"
        "- 不要让同一个 type 连续重复超过两次。\n\n"
        f"镜头类型字段契约:\n{contract}\n\n{_CHART_CONTRACT}\n\n"
        f"严格返回此 JSON 形状: {json.dumps(schema, ensure_ascii=False)}\n\n"
        f"论文内容:\n{paper_context(doc)}"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


# ── LLM call ────────────────────────────────────────────────────────


def _default_llm() -> Callable[[list[dict[str, str]]], dict[str, Any]]:
    import requests  # noqa: F401  (import here so tests can inject a fake llm)
    import config

    def call(messages: list[dict[str, str]]) -> dict[str, Any]:
        import requests

        endpoint = config.API_BASE_URL.rstrip("/") + "/chat/completions"
        resp = requests.post(
            endpoint,
            headers={"Authorization": f"Bearer {config.API_KEY}", "Content-Type": "application/json"},
            json={
                "model": config.LLM_MODEL,
                "messages": messages,
                "temperature": 0.5,
                "response_format": {"type": "json_object"},
            },
            timeout=240,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return _extract_json(content)

    return call


def _extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped[:4].lower() == "json":
            stripped = stripped[4:]
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        start, end = stripped.find("{"), stripped.rfind("}")
        if start >= 0 and end > start:
            return json.loads(stripped[start : end + 1])
        raise


# ── normalization / repair ──────────────────────────────────────────


def _clean_hex(value: Any, fallback: str) -> str:
    text = str(value or "").strip()
    return text if _HEX_RE.match(text) else fallback


def _normalize_visual_prompt(prompt: str) -> str:
    text = " ".join(str(prompt or "").split())
    text = re.sub(r"(['\"])[^'\"]{0,40}\1", "abstract glyph", text)  # drop quoted literals
    lower = text.lower()
    if "no readable text" not in lower or "no letters" not in lower:
        text = f"{text}, {_VISUAL_SUFFIX}" if text else _VISUAL_SUFFIX
    return text


def normalize_sections(raw_sections: list[Any], scene_count: Optional[int] = None) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    for i, item in enumerate(raw_sections):
        if not isinstance(item, dict):
            continue
        stype = str(item.get("type", "")).strip()
        if stype not in SUPPORTED_TYPES:
            stype = "takeaway"
        on_screen = item.get("on_screen")
        if not isinstance(on_screen, dict):
            on_screen = {}
        try:
            duration = float(item.get("duration_sec", 24))
        except (TypeError, ValueError):
            duration = 24.0
        duration = max(8.0, min(45.0, duration))
        section = {
            "id": str(item.get("id") or f"s{i + 1:02d}_{stype}"),
            "type": stype,
            "label": str(item.get("label") or on_screen.get("title") or stype),
            "text": str(item.get("text") or "").strip(),
            "duration_sec": duration,
            "accent_color": _clean_hex(item.get("accent_color"), _ACCENT_BY_TYPE.get(stype, _PALETTE[i % len(_PALETTE)])),
            "on_screen": on_screen,
            "visual_prompt": _normalize_visual_prompt(item.get("visual_prompt", "")),
        }
        chart = item.get("chart")
        if isinstance(chart, dict) and chart.get("type"):
            section["chart"] = chart
        sections.append(section)
    return sections


def generate_storyboard(
    doc: dict[str, Any],
    scene_count: int = 18,
    llm: Optional[Callable[[list[dict[str, str]]], dict[str, Any]]] = None,
) -> dict[str, Any]:
    """Call the LLM and return a normalized storyboard dict."""
    call = llm or _default_llm()
    payload = call(build_messages(doc, scene_count))
    if not isinstance(payload, dict):
        raise ValueError("LLM did not return a JSON object")
    raw_sections = payload.get("sections")
    if not isinstance(raw_sections, list) or not raw_sections:
        raise ValueError(f"LLM returned no sections; keys={list(payload.keys())}")
    sections = normalize_sections(raw_sections, scene_count)
    if not sections:
        raise ValueError("no valid sections after normalization")
    return {
        "title": str(payload.get("title") or doc.get("title") or "论文解读"),
        "paper_arxiv_id": doc.get("arxiv_id", ""),
        "paper_urls": doc.get("urls", []),
        "sources": doc.get("sources", []),
        "total_duration_sec": round(sum(s["duration_sec"] for s in sections), 1),
        "sections": sections,
    }


# ── human-readable markdown ─────────────────────────────────────────


def _on_screen_brief(on_screen: dict[str, Any]) -> str:
    parts = []
    for key, value in on_screen.items():
        if isinstance(value, (list, dict)):
            value = json.dumps(value, ensure_ascii=False)
        text = str(value)
        if len(text) > 120:
            text = text[:117] + "…"
        parts.append(f"  - **{key}**: {text}")
    return "\n".join(parts)


def storyboard_to_markdown(storyboard: dict[str, Any]) -> str:
    lines = [
        f"# 音画分镜脚本 · {storyboard.get('title', '')}",
        "",
        f"- arxiv: {storyboard.get('paper_arxiv_id', '')}",
        f"- 镜头数: {len(storyboard.get('sections', []))}",
        f"- 预计时长: {storyboard.get('total_duration_sec', 0)} 秒",
        f"- 数据来源: {', '.join(storyboard.get('sources', [])) or 'n/a'}",
        "",
        "---",
        "",
    ]
    for i, sec in enumerate(storyboard.get("sections", [])):
        lines.append(f"## 镜头 {i + 1:02d} · {sec.get('label', '')}  `[{sec.get('type')}]`")
        lines.append(f"_时长 ≈ {sec.get('duration_sec')}s · accent {sec.get('accent_color')}_")
        lines.append("")
        lines.append("**🎙 旁白**")
        lines.append(f"> {sec.get('text', '')}")
        lines.append("")
        lines.append("**🖼 画面**")
        brief = _on_screen_brief(sec.get("on_screen", {}))
        lines.append(brief if brief else "  - (无)")
        if sec.get("chart"):
            lines.append(f"  - **chart**: {json.dumps(sec['chart'], ensure_ascii=False)}")
        lines.append("")
        lines.append(f"**🎨 配图提示**: {sec.get('visual_prompt', '')}")
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)
