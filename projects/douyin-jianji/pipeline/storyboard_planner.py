"""Reference-style storyboard planner for Douyin demand scripts."""

import re


DATA_PATTERN = re.compile(r"\d+(?:\.\d+)?\s*(?:GW|%|个工作日)", re.I)
VISUAL_DIRECTION_WORDS = (
    "动画",
    "画面",
    "轮播",
    "镜头",
    "配图",
    "素材",
    "发布现场",
    "政策要点",
    "项目解冻",
)


def plan_storyboard(script: dict) -> dict:
    """Build reference-style storyboard shots from a parsed script."""
    title = _display_title(script)
    headline = script.get("headline") or script.get("program_title") or title
    cover_sub = _cover_subtitle(script, headline)
    shots = [_make_shot(
        template="cover_dark",
        title=title,
        subtitle=cover_sub,
        duration=2.6,
        data={"headline": cover_sub, "kicker": title},
        section_id=-1,
        bg_role="hero",
    )]

    for index, section in enumerate(script.get("sections", [])):
        shots.extend(_shots_for_section(section, title, index))

    return {
        "title": title,
        "headline": headline,
        "hero_prompt": _hero_prompt(title, headline),
        "dark_prompt": _dark_prompt(),
        "shots": shots,
    }


def _shots_for_section(section: dict, title: str, section_id: int) -> list[dict]:
    templates = _templates_for_section(section)
    chunks = _split_section_text(section, max(1, len(templates)))

    shots = []
    for index, template in enumerate(templates):
        subtitle = chunks[min(index, len(chunks) - 1)]
        duration = _bounded_duration(section.get("duration_sec", 4.0) / len(templates))
        shots.append(_make_shot(
            template=template,
            title=title,
            subtitle=subtitle,
            duration=duration,
            data=_data_for_template(template, section),
            section_id=section_id,
            bg_role="dark",
        ))
    return shots


def _cover_subtitle(script: dict, headline: str) -> str:
    """Pick a punchy cover line: prefer cover_text, then the first headline clause."""
    cover = (script.get("execution_tips", {}) or {}).get("cover_text", "")
    if cover:
        return cover.strip()
    return re.split(r"[/／]", headline, maxsplit=1)[0].strip()


def _hero_prompt(title: str, headline: str) -> str:
    return (
        "Cinematic wide shot of a large rooftop and ground solar photovoltaic farm "
        "at golden hour, glowing green energy light streaks flowing across the panels, "
        "deep navy blue sky, high-tech clean-energy mood, dramatic professional "
        "lighting, ultra detailed, 16:9"
    )


def _dark_prompt() -> str:
    return (
        "Minimal dark navy blue technology background, subtle abstract solar panel "
        "grid texture and faint green energy waves in the lower corner, lots of empty "
        "dark space for text overlay, cinematic soft gradient, professional infographic "
        "backdrop, 16:9"
    )


def _templates_for_section(section: dict) -> list[str]:
    label = section.get("label", "")
    text = f"{section.get('visual', '')} {section.get('text', '')}"
    templates = []

    if "结尾" in label or "引导" in label or any(k in text for k in ["评论", "下期", "关注", "问我"]):
        return ["cta_summary"]
    if "痛点" in label or "悬念" in label or "坑" in text:
        return ["headline_warning"]
    if "->" in text or any(k in text for k in ["流程", "顺序", "步骤"]):
        templates.append("process_flow")
    if any(k in text for k in ["资料", "身份证", "权属", "承重", "清单", "必备"]):
        templates.append("material_grid")
    if any(k in text for k in ["APP", "营业厅", "提交申请", "办理渠道"]):
        templates.append("channel_steps")
    if DATA_PATTERN.search(text):
        templates.append("data_release")
    if "绿" in text and "黄" in text and "红" in text:
        templates.append("zone_cards")

    duration = float(section.get("duration_sec") or 0)
    if duration > 8 and len(templates) < 3:
        templates.append("policy_explain")
    if duration > 12 and len(templates) < 3:
        templates.append("policy_explain")

    return templates or [section.get("template") or "policy_explain"]


def _split_section_text(section: dict, count: int) -> list[str]:
    text = section.get("text") or section.get("visual") or section.get("label") or ""
    parts = [p.strip() for p in re.split(r"(?<=[。！？；])", text) if p.strip()]
    if not parts:
        parts = [text.strip()]

    if len(parts) >= count:
        return parts[:count]

    while len(parts) < count:
        parts.append(parts[-1])
    return parts


def _data_for_template(template: str, section: dict) -> dict:
    visual = section.get("visual", "")
    text = section.get("text", "")
    headline = _headline_from_visual(visual, section.get("label", ""))
    if _looks_like_visual_direction(headline):
        headline = _headline_from_text(text, section.get("label", ""))

    if template == "data_release":
        return {"headline": headline, "stats": _extract_stats(f"{visual} {text}")}
    if template == "zone_cards":
        return {"headline": headline, "items": _zone_items(f"{visual} {text}")}
    if template == "process_flow":
        return {"headline": headline, "steps": _extract_steps(visual)}
    if template in {"material_grid", "channel_steps"}:
        return {"headline": headline, "items": _extract_items(visual)}
    if template == "cta_summary":
        return {"headline": headline or "评论区答疑", "subtitle": text}
    return {"headline": headline}


def _make_shot(template: str, title: str, subtitle: str,
               duration: float, data: dict,
               section_id: int = 0, bg_role: str = "dark") -> dict:
    return {
        "template": template,
        "title": title,
        "subtitle": subtitle,
        "duration_sec": _bounded_duration(duration),
        "data": data,
        "section_id": section_id,
        "bg_role": bg_role,
    }


def _display_title(script: dict) -> str:
    title = script.get("program_title") or script.get("headline") or "光伏政策解读"
    if "618" in title:
        return "618光伏新政解析"
    if "山东" in title:
        return "山东光伏新政策解读"
    return "光伏并网流程解读"


def _bounded_duration(value: float) -> float:
    return round(min(6.0, max(2.5, float(value or 3.0))), 2)


def _headline_from_visual(visual: str, fallback: str) -> str:
    if not visual:
        return _shorten_headline(fallback)
    text = visual.replace("→", "->").strip()
    if "：" in text:
        prefix, rest = text.split("：", 1)
        if _looks_like_visual_direction(prefix) or len(prefix) <= 6:
            text = rest
    text = re.sub(r"^(配)?(大字提示|大字|提示)[:：]?", "", text).strip()
    headline = re.split(r"\s*->\s*|[|｜\n，。；,;]", text, maxsplit=1)[0].strip()
    return _shorten_headline(headline or fallback)


def _headline_from_text(text: str, fallback: str) -> str:
    if not text:
        return _shorten_headline(fallback)
    sentence = re.split(r"[。！？；，,]", text, maxsplit=1)[0].strip()
    sentence = re.sub(r"^(沿用多年的|这一次|直接|行业统计显示)", "", sentence).strip()
    return _shorten_headline(sentence or fallback)


def _shorten_headline(text: str, max_chars: int = 18) -> str:
    text = str(text or "").replace("→", "->").strip()
    text = re.sub(r"\s+", "", text)
    if len(text) <= max_chars:
        return text
    return text[:max_chars - 3] + "..."


def _looks_like_visual_direction(text: str) -> bool:
    value = str(text or "")
    return any(word in value for word in VISUAL_DIRECTION_WORDS)


def _extract_stats(text: str) -> list[dict]:
    values = DATA_PATTERN.findall(text)
    if not values:
        return []
    stats = []
    seen = set()
    for value in values:
        normalized = value.replace(" ", "")
        if normalized in seen:
            continue
        seen.add(normalized)
        label = "关键数据"
        if "GW" in normalized.upper():
            label = "存量项目释放"
        elif "%" in normalized:
            label = "政策红线"
        elif "工作日" in normalized:
            label = "审批时长"
        stats.append({"value": normalized, "label": label, "color": "accent_gold"})
        if len(stats) == 3:
            break
    return stats


def _zone_items(text: str) -> list[dict]:
    return [
        {"title": "绿区", "desc": "承载力充足，优先接入", "color": "success"},
        {"title": "黄区", "desc": "承载力偏紧，配储或安控", "color": "warning"},
        {"title": "红区", "desc": "电网改造后有序接入", "color": "danger"},
    ]


def _extract_steps(visual: str) -> list[str]:
    content = visual.split("：", 1)[-1] if "：" in visual else visual
    if "->" in content:
        return [part.strip() for part in content.split("->") if part.strip()]
    return [part.strip() for part in re.split(r"[、/｜|]", content) if part.strip()]


def _extract_items(visual: str) -> list[dict]:
    content = visual.split("：", 1)[-1] if "：" in visual else visual
    parts = [part.strip() for part in re.split(r"\s*\+\s*|\s*/\s*|[、｜|]", content) if part.strip()]
    return [{"title": part, "desc": ""} for part in parts]
