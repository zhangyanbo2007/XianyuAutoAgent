"""Map storyboard scenes to concrete visual templates."""

from __future__ import annotations

from .models import Scene, VisualScene


_ALLOWED = {
    "hero_title", "core_question", "paper_gap_iceberg", "method_transfer",
    "task_matrix", "metric_cards", "split_comparison", "bar_finding",
    "ranking_board", "takeaway_cards", "future_direction",
}
_TEMPLATE_DIRECTIONS = {
    "hero_title": "central symbolic object from the paper inside a holographic technical interface",
    "core_question": "large investigative question structure with evidence particles and data paths",
    "paper_gap_iceberg": "visible surface claim above a hidden mechanism layer made of luminous data blocks",
    "method_transfer": "source problem transforming into a method pipeline and evaluation architecture",
    "task_matrix": "four quadrant technical matrix showing paper concepts as modular system nodes",
    "metric_cards": "floating measurement panels and audit cards arranged in a clean interface",
    "split_comparison": "two technical systems compared side by side with signal paths between them",
    "bar_finding": "holographic evidence chart rising from a dark analytical workspace",
    "ranking_board": "model or method comparison board with progress bars and confidence traces",
    "takeaway_cards": "three concise insight panels connected by luminous data-flow lines",
    "future_direction": "roadmap of next-step system modules connected through a technical network",
}
_ACCENTS = ["cyan", "magenta", "green", "gold"]


def _flatten_data(value: object) -> list[str]:
    if isinstance(value, dict):
        parts: list[str] = []
        for item in value.values():
            parts.extend(_flatten_data(item))
        return parts
    if isinstance(value, (list, tuple)):
        parts = []
        for item in value:
            parts.extend(_flatten_data(item))
        return parts
    if value is None:
        return []
    text = str(value).strip()
    return [text] if text else []


def _scene_content(scene: Scene) -> str:
    values = [scene.title, scene.paper_anchor]
    values.extend(_flatten_data(scene.data))
    compact = " ".join(" ".join(value.split()) for value in values if value)
    return compact[:260]


def _visual_prompt(scene: Scene, template: str) -> str:
    content = _scene_content(scene)
    direction = _TEMPLATE_DIRECTIONS[template]
    return (
        f"{content}; {direction}; cinematic high-tech paper explainer visual, "
        "dark background, neon HUD, holographic interface, technical data flow, "
        "sharp depth, no readable text, no watermark"
    )


def build_visual_plan(scenes: list[Scene]) -> list[VisualScene]:
    visual_scenes: list[VisualScene] = []
    for scene in scenes:
        template = scene.template_hint if scene.template_hint in _ALLOWED else "takeaway_cards"
        visual_scenes.append(
            VisualScene(
                index=scene.index,
                kind=scene.kind,
                title=scene.title,
                narration=scene.narration,
                paper_anchor=scene.paper_anchor,
                template=template,
                duration_sec=scene.duration_sec,
                data=scene.data,
                visual_prompt=_visual_prompt(scene, template),
                accent=_ACCENTS[scene.index % len(_ACCENTS)],
            )
        )
    return visual_scenes
