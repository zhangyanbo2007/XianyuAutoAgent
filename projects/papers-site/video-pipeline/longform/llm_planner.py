"""LLM-driven, paper-grounded longform planning."""

from __future__ import annotations

import json
import re
from typing import Any, Protocol

from .llm_client import OpenAICompatibleJsonClient
from .models import PaperFactPack, Scene, VisualScene


class LLMJsonClient(Protocol):
    def complete_json(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        ...


class LLMPlanValidationError(ValueError):
    """Raised when an LLM longform plan is too generic or malformed."""


_ALLOWED_TEMPLATES = {
    "hero_title",
    "core_question",
    "paper_gap_iceberg",
    "method_transfer",
    "task_matrix",
    "metric_cards",
    "split_comparison",
    "bar_finding",
    "ranking_board",
    "takeaway_cards",
    "future_direction",
}
_ACCENTS = ["cyan", "magenta", "green", "gold"]
_STYLE_REQUIREMENTS = ("cinematic", "high-tech", "dark background", "neon", "HUD", "no readable text")
_STYLE_SUFFIX = (
    "cinematic high-tech paper explainer visual, dark background, neon HUD, "
    "holographic interface, technical data flow, no readable text, no labels, "
    "no letters, no numbers, no watermark"
)
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{3,}|[\u4e00-\u9fff]{2,}")


def _paper_context(paper: dict[str, Any]) -> str:
    fields = []
    for key in ("slug", "title", "summary", "abstract_zh", "abstract"):
        value = paper.get(key)
        if value:
            fields.append(f"{key}: {value}")
    for key in ("paper_urls", "project_urls", "repo_urls", "dataset_urls"):
        value = paper.get(key)
        if value:
            fields.append(f"{key}: {value}")
    return "\n".join(fields)


def build_planning_messages(paper: dict[str, Any], scene_count: int) -> list[dict[str, str]]:
    """Build a generic planning prompt; all paper specifics come from input."""
    schema = {
        "fact_pack": {
            "slug": "paper slug",
            "title": "paper title",
            "summary": "one-sentence grounded summary",
            "abstract": "paper abstract or concise source summary",
            "urls": ["source urls"],
            "problem": "research problem",
            "method": "core method",
            "findings": ["key findings"],
            "limitations": ["limitations or caveats"],
            "key_terms": ["paper-specific terms"],
            "anchors": [{"kind": "problem|method|task|finding|limitation|future", "text": "claim from paper", "evidence": "where it came from"}],
        },
        "scenes": [
            {
                "kind": "title|question|gap|method|overview|data|task|finding|insight|evidence|limitation|ending",
                "title": "Chinese scene title",
                "narration": "Chinese narration, at least 80 characters",
                "paper_anchor": "one concrete paper-grounded claim",
                "template_hint": "one allowed visual template",
                "duration_sec": 18,
                "data": {"paper_specific_key": "paper_specific_value"},
            }
        ],
        "visual_scenes": [
            {
                "template": "one allowed visual template",
                "visual_prompt": "English image prompt derived from this scene and paper, cinematic high-tech dark background neon HUD, no readable text",
                "accent": "cyan|magenta|green|gold",
                "data": {"paper_specific_key": "paper_specific_value"},
            }
        ],
    }
    system = (
        "You are a senior paper-video director. Generate a paper-grounded longform video plan as JSON only. "
        "You must derive every scene from the supplied paper. Do not reuse a fixed paper-specific scene list. "
        "Do not assume the paper is about memory, agents, RL, safety, or benchmarks unless the supplied paper says so. "
        "Every visual prompt must describe image content only; code will render all readable text later."
    )
    user = (
        f"Create exactly {scene_count} scenes for a longform paper explainer video.\n"
        "Requirements:\n"
        "- Every scene must have a paper_anchor tied to the supplied paper.\n"
        "- Use Chinese for titles and narration.\n"
        "- visual_prompt must be specific to the scene's actual paper content, not a generic neon dashboard.\n"
        "- Overall visual style is high-tech: dark technical spaces, holographic interfaces, clean neon HUD overlays, depth, and cinematic lighting.\n"
        "- visual_prompt must include: cinematic, high-tech, dark background, neon, HUD, no readable text.\n"
        "- Avoid repeating the same primary visual metaphor more than twice.\n"
        f"- Allowed templates: {sorted(_ALLOWED_TEMPLATES)}.\n"
        f"- Return this JSON shape exactly: {json.dumps(schema, ensure_ascii=False)}\n\n"
        f"Supplied paper:\n{_paper_context(paper)}"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _paper_fact_pack(payload: dict[str, Any], paper: dict[str, Any]) -> PaperFactPack:
    return PaperFactPack(
        slug=str(payload.get("slug") or paper.get("slug") or "paper"),
        title=str(payload.get("title") or paper.get("title") or "论文解读"),
        summary=str(payload.get("summary") or paper.get("summary") or ""),
        abstract=str(payload.get("abstract") or paper.get("abstract") or ""),
        urls=[str(value) for value in _as_list(payload.get("urls"))],
        problem=str(payload.get("problem") or ""),
        method=str(payload.get("method") or ""),
        findings=[str(value) for value in _as_list(payload.get("findings"))],
        limitations=[str(value) for value in _as_list(payload.get("limitations"))],
        key_terms=[str(value) for value in _as_list(payload.get("key_terms")) if str(value).strip()],
        anchors=[dict(item) for item in _as_list(payload.get("anchors")) if isinstance(item, dict)],
    )


def _scene_from_payload(index: int, item: dict[str, Any]) -> Scene:
    template = str(item.get("template_hint") or "takeaway_cards")
    if template not in _ALLOWED_TEMPLATES:
        template = "takeaway_cards"
    return Scene(
        index=index,
        kind=str(item.get("kind") or "insight"),
        title=str(item.get("title") or f"论文要点 {index + 1}"),
        narration=str(item.get("narration") or ""),
        paper_anchor=str(item.get("paper_anchor") or ""),
        template_hint=template,
        duration_sec=float(item.get("duration_sec") or 22.0),
        data=item.get("data") if isinstance(item.get("data"), dict) else {},
    )


def _normalize_visual_prompt(prompt: str) -> str:
    text = " ".join(str(prompt or "").split())
    text = re.sub(r"(['\"])[^'\"]{1,40}\1", "abstract visual marker", text)
    text = re.sub(r"\blabeled?\s+(with|as|for|by)?\b", "marked by abstract visual markers", text, flags=re.IGNORECASE)
    text = re.sub(r"\blabels?\b", "abstract visual markers", text, flags=re.IGNORECASE)
    lower = text.lower()
    missing = [term for term in _STYLE_REQUIREMENTS if term.lower() not in lower]
    if missing or "no labels" not in lower:
        text = f"{text}, {_STYLE_SUFFIX}" if text else _STYLE_SUFFIX
    return text


def _visual_from_payload(index: int, scene: Scene, item: dict[str, Any]) -> VisualScene:
    template = str(item.get("template") or scene.template_hint)
    if template not in _ALLOWED_TEMPLATES:
        template = scene.template_hint if scene.template_hint in _ALLOWED_TEMPLATES else "takeaway_cards"
    accent = str(item.get("accent") or _ACCENTS[index % len(_ACCENTS)])
    if accent not in _ACCENTS:
        accent = _ACCENTS[index % len(_ACCENTS)]
    data = {}
    if isinstance(item.get("data"), dict):
        data.update(item["data"])
    data.update(scene.data)
    return VisualScene(
        index=index,
        kind=scene.kind,
        title=scene.title,
        narration=scene.narration,
        paper_anchor=scene.paper_anchor,
        template=template,
        duration_sec=scene.duration_sec,
        data=data,
        visual_prompt=_normalize_visual_prompt(str(item.get("visual_prompt") or "")),
        accent=accent,
    )


def _keywords(*values: Any) -> set[str]:
    text = " ".join(str(value) for value in values if value)
    return {match.group(0).lower() for match in _WORD_RE.finditer(text)}


def _validate_plan(
    paper: dict[str, Any],
    fact_pack: PaperFactPack,
    scenes: list[Scene],
    visual_scenes: list[VisualScene],
    scene_count: int,
) -> None:
    if len(scenes) != scene_count or len(visual_scenes) != scene_count:
        raise LLMPlanValidationError(f"expected {scene_count} scenes and visuals")
    if not fact_pack.anchors:
        raise LLMPlanValidationError("fact_pack must include paper anchors")
    if any(not scene.paper_anchor.strip() for scene in scenes):
        raise LLMPlanValidationError("every scene must include a paper_anchor")

    prompts = [scene.visual_prompt.strip() for scene in visual_scenes]
    if len({prompt.lower() for prompt in prompts}) < max(3, int(scene_count * 0.75)):
        raise LLMPlanValidationError("visual prompts are too repetitive")

    paper_words = _keywords(_paper_context(paper), fact_pack.key_terms, fact_pack.findings, fact_pack.method, fact_pack.problem)
    for scene, visual in zip(scenes, visual_scenes):
        prompt_lower = visual.visual_prompt.lower()
        missing_style = [term for term in _STYLE_REQUIREMENTS if term.lower() not in prompt_lower]
        if missing_style:
            raise LLMPlanValidationError(f"visual prompt missing style terms: {missing_style}")
        scene_words = _keywords(scene.title, scene.paper_anchor, scene.data, fact_pack.key_terms)
        if not (scene_words | paper_words) or not ((scene_words | paper_words) & _keywords(visual.visual_prompt)):
            raise LLMPlanValidationError(f"visual prompt is not grounded in scene content: {scene.title}")

    source_lower = _paper_context(paper).lower()
    all_prompts_lower = "\n".join(prompts).lower()
    for suspicious in ("m3eval", "n-back", "memory interference", "hippocampus"):
        if suspicious in all_prompts_lower and suspicious not in source_lower:
            raise LLMPlanValidationError(f"visual prompt leaked unrelated paper-specific term: {suspicious}")


def plan_longform_with_llm(
    paper: dict[str, Any],
    scene_count: int = 28,
    llm: LLMJsonClient | None = None,
) -> tuple[PaperFactPack, list[Scene], list[VisualScene]]:
    """Ask an LLM for a complete paper-grounded plan and validate it."""
    client = llm or OpenAICompatibleJsonClient()
    payload = client.complete_json(build_planning_messages(paper, scene_count))
    fact_pack = _paper_fact_pack(payload.get("fact_pack", {}) if isinstance(payload.get("fact_pack"), dict) else {}, paper)
    raw_scenes = [item for item in _as_list(payload.get("scenes")) if isinstance(item, dict)]
    raw_visuals = [item for item in _as_list(payload.get("visual_scenes")) if isinstance(item, dict)]
    scenes = [_scene_from_payload(index, item) for index, item in enumerate(raw_scenes[:scene_count])]
    visual_scenes = [
        _visual_from_payload(index, scene, raw_visuals[index] if index < len(raw_visuals) else {})
        for index, scene in enumerate(scenes)
    ]
    _validate_plan(paper, fact_pack, scenes, visual_scenes, scene_count)
    return fact_pack, scenes, visual_scenes
