"""Deterministic longform storyboard planning."""

from __future__ import annotations

from .models import PaperFactPack, Scene


_TEMPLATES_BY_KIND = {
    "problem": ["paper_gap_iceberg", "core_question"],
    "method": ["method_transfer", "task_matrix"],
    "task": ["split_comparison", "task_matrix"],
    "finding": ["bar_finding", "ranking_board", "split_comparison"],
    "limitation": ["paper_gap_iceberg", "takeaway_cards"],
    "future": ["future_direction", "takeaway_cards"],
}
_FALLBACK_TEMPLATES = ["bar_finding", "split_comparison", "ranking_board", "takeaway_cards", "future_direction"]


def _anchor_item(fact_pack: PaperFactPack, index: int = 0) -> dict[str, str]:
    if not fact_pack.anchors:
        return {"kind": "problem", "text": fact_pack.problem or "summary/abstract", "evidence": "summary/abstract"}
    return fact_pack.anchors[index % len(fact_pack.anchors)]


def _anchor(fact_pack: PaperFactPack, index: int = 0) -> str:
    item = _anchor_item(fact_pack, index)
    return f"{item.get('kind', 'evidence')}: {item.get('text', 'summary/abstract')}"


def _term(fact_pack: PaperFactPack, index: int = 0, fallback: str = "论文证据") -> str:
    if fact_pack.key_terms:
        return fact_pack.key_terms[index % len(fact_pack.key_terms)]
    return fallback


def _headline(text: str, max_chars: int = 28) -> str:
    value = " ".join(text.split())
    if len(value) > max_chars:
        value = value[: max_chars - 1].rstrip() + "…"
    if value and value[0].isascii():
        value = value[:1].upper() + value[1:]
    return value or "论文证据"


def _narration_expansion(kind: str, anchor: str) -> str:
    expansions = {
        "title": "这一页的任务是先立住论文问题，而不是先堆结论；观众需要马上知道这篇论文为什么值得被拆解。",
        "question": "这里把标题里的概念翻译成一个可追问的问题，让后面的实验、指标或案例都围绕同一个判断展开。",
        "gap": "这一页说明论文补上的空白：过去的做法哪里不够，作者为什么要换一种观察方式。",
        "method": "方法页要把抽象贡献落到流程上：输入是什么，系统如何处理，最后用什么证据证明它有效。",
        "overview": "路线图页负责给观众定位，后面的每个画面都会回到这些核心概念、证据链和结论节点。",
        "data": "证据页先建立可信度：不是孤立观点，而是来自论文里的任务、指标、实验设置或可复查材料。",
        "task": "这一页只展开一个论文锚点，先解释它测什么，再解释它为什么能支撑全片主线。",
        "finding": "讲发现时不只读结果，而是把结果翻译成一句诊断：它改变了我们对这个问题的哪一层理解。",
        "limitation": "限制页要讲清边界：哪些结论来自论文证据，哪些只是面向系统设计的合理延伸。",
        "future": "未来方向页从论文证据自然推出下一步，而不是突然跳到泛泛建议。",
        "evidence": "这一页继续压实论文粘结度：画面和旁白都围绕同一个可追溯锚点组织。",
        "ending": "结尾回扣开头问题，把论文的核心判断收束成观众能记住的一句话，并保留继续追问的入口。",
    }
    suffix = expansions.get(kind, expansions["evidence"])
    return f"{suffix} 本页绑定对应论文锚点。"


def _expand_narration(kind: str, narration: str, anchor: str) -> str:
    clean = narration.strip()
    if clean.endswith("。"):
        return f"{clean}{_narration_expansion(kind, anchor)}"
    return f"{clean}。{_narration_expansion(kind, anchor)}"


def _scene(
    index: int,
    kind: str,
    title: str,
    narration: str,
    anchor: str,
    template: str,
    duration: float = 24.0,
    data: dict | None = None,
) -> Scene:
    return Scene(
        index=index,
        kind=kind,
        title=title,
        narration=_expand_narration(kind, narration, anchor),
        paper_anchor=anchor,
        template_hint=template,
        duration_sec=duration,
        data=data or {},
    )


def _base_scenes(fact_pack: PaperFactPack) -> list[Scene]:
    title = fact_pack.title or "论文解读"
    term0 = _term(fact_pack, 0)
    term1 = _term(fact_pack, 1, "证据链")
    terms = fact_pack.key_terms[:4] or ["Problem", "Method", "Evidence", "Takeaway"]
    metrics = [
        {"label": "论文锚点", "value": str(max(len(fact_pack.anchors), 1))},
        {"label": "核心概念", "value": str(max(len(fact_pack.key_terms), 1))},
    ]
    return [
        _scene(0, "title", "这篇论文真正要解决什么？", f"这期视频拆解《{title}》，先抓住 {term0} 这条主线，再沿着论文证据一步步还原它的贡献。", _anchor(fact_pack, 0), "hero_title", 18.0),
        _scene(1, "question", f"{_headline(term0, 18)} 的关键问题", f"不要把这篇论文看成几个术语的组合，它真正要回答的是：{term0} 和 {term1} 之间到底缺了哪种可验证的连接。", _anchor(fact_pack, 0), "core_question"),
        _scene(2, "gap", "论文要补上的缺口", fact_pack.problem or "这篇论文指出，现有方法还不能完整解释关键能力从哪里来、又在哪里失效。", _anchor(fact_pack, 1), "paper_gap_iceberg"),
        _scene(3, "method", "方法：把问题变成证据链", fact_pack.method or "作者把研究问题拆成可检查的流程、指标和证据，让结论能被追溯。", _anchor(fact_pack, 2), "method_transfer"),
        _scene(4, "overview", "全片路线图", "视频会按论文主线展开：先讲问题和方法，再看关键证据，最后回到限制与下一步方向。", _anchor(fact_pack, 3), "task_matrix", data={"tasks": terms}),
        _scene(5, "data", "证据链从哪里来", "在进入具体结论前，先把论文里可追溯的锚点和核心概念摆出来，让每一页画面都能回到原文依据。", _anchor(fact_pack, 4), "metric_cards", data={"metrics": metrics}),
    ]


def _template_for(kind: str, index: int) -> str:
    options = _TEMPLATES_BY_KIND.get(kind, _FALLBACK_TEMPLATES)
    return options[index % len(options)]


def _anchor_scene(fact_pack: PaperFactPack, scene_index: int, anchor_index: int) -> Scene:
    item = _anchor_item(fact_pack, anchor_index)
    kind = item.get("kind", "evidence")
    if kind not in _TEMPLATES_BY_KIND:
        kind = "evidence"
    claim = item.get("text", "summary/abstract")
    term = _term(fact_pack, anchor_index)
    title_prefix = {
        "problem": "问题",
        "method": "方法",
        "task": "任务",
        "finding": "发现",
        "limitation": "边界",
        "future": "方向",
        "evidence": "证据",
    }.get(kind, "证据")
    narration = f"这一页聚焦论文里的具体锚点：{claim}。把它放回 {term} 这条主线里看，观众能看到作者不是在泛泛描述，而是在逐步建立可验证的判断。"
    data = {
        "tasks": fact_pack.key_terms[:4],
        "rows": fact_pack.key_terms[:5],
        "bars": [(label.upper()[:12], value) for label, value in zip(fact_pack.key_terms[:4], [92, 76, 61, 44])],
    }
    return _scene(
        scene_index,
        kind,
        f"{title_prefix}：{_headline(claim)}",
        narration,
        f"{item.get('kind', 'evidence')}: {claim}",
        _template_for(kind, anchor_index),
        22.0,
        data=data,
    )


def _ending_scene(fact_pack: PaperFactPack, index: int) -> Scene:
    title = "回到论文的核心判断"
    term0 = _term(fact_pack, 0)
    term1 = _term(fact_pack, 1, "证据")
    narration = f"最后回到这篇论文本身：它真正留下的不是一个孤立结论，而是一条关于 {term0}、{term1} 和证据边界的判断路径。好的论文视频应该让观众记住这条路径，而不是只记住几个热闹名词。"
    return _scene(index, "ending", title, narration, _anchor(fact_pack, 0), "hero_title", 20.0)


def build_storyboard(fact_pack: PaperFactPack, target_scene_count: int = 28) -> list[Scene]:
    if target_scene_count < 8:
        raise ValueError("target_scene_count must be at least 8 for a longform storyboard")

    scenes = _base_scenes(fact_pack)
    anchor_index = 0
    while len(scenes) < target_scene_count - 1:
        scenes.append(_anchor_scene(fact_pack, len(scenes), anchor_index))
        anchor_index += 1

    scenes = scenes[: target_scene_count - 1]
    scenes.append(_ending_scene(fact_pack, len(scenes)))
    return [
        Scene(
            index=i,
            kind=("ending" if i == len(scenes) - 1 else scene.kind),
            title=scene.title,
            narration=scene.narration,
            paper_anchor=scene.paper_anchor,
            template_hint=scene.template_hint,
            duration_sec=scene.duration_sec,
            data=scene.data,
        )
        for i, scene in enumerate(scenes)
    ]
