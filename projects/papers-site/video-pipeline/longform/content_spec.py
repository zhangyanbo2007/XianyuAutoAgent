"""Extract paper-content labels for visual rendering."""

from __future__ import annotations

import re
from typing import Any

from .models import VisualScene

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{2,}")
_STYLE_WORDS = {
    "abstract", "background", "cinematic", "clean", "dark", "flow",
    "glow", "glowing", "grid", "high-tech", "holographic", "hud",
    "illustration", "interface", "label", "labels", "letter", "letters",
    "marker", "markers", "neon", "number", "numbers", "overlay",
    "paper", "prompt", "readable", "scene", "sharp", "style", "technical",
    "text", "visual", "watermark",
}
_PHRASES = [
    ("direct corpus interaction", "DIRECT CORPUS"),
    ("direct corpus", "DIRECT CORPUS"),
    ("agentic search", "AGENTIC SEARCH"),
    ("semantic similarity", "SEMANTIC SIM"),
    ("interface resolution", "INTERFACE RES"),
    ("retrieval trace", "RETRIEVAL TRACE"),
    ("citation faithfulness", "CITATION"),
    ("command-based", "COMMAND"),
    ("offline index", "NO INDEX"),
    ("no index", "NO INDEX"),
    ("top-k", "TOP-K"),
    ("vector index", "VECTOR INDEX"),
    ("embedding", "EMBEDDING"),
    ("reranking", "RERANKING"),
    ("retrieval", "RETRIEVAL"),
    ("corpus", "CORPUS"),
    ("evidence", "EVIDENCE"),
    ("grep", "GREP"),
    ("shell", "SHELL"),
    ("command", "COMMAND"),
    ("file read", "FILE READ"),
    ("bright", "BRIGHT"),
    ("beir", "BEIR"),
    ("browsecomp", "BROWSECOMP"),
]
_ZH_PHRASES = [
    ("直接语料库", "DIRECT CORPUS"),
    ("语料库", "CORPUS"),
    ("智能体搜索", "AGENTIC SEARCH"),
    ("智能体", "AGENT"),
    ("语义相似", "SEMANTIC SIM"),
    ("检索轨迹", "RETRIEVAL TRACE"),
    ("检索", "RETRIEVAL"),
    ("证据", "EVIDENCE"),
    ("接口分辨率", "INTERFACE RES"),
    ("不需要离线索引", "NO INDEX"),
    ("无需离线索引", "NO INDEX"),
    ("离线索引", "OFFLINE INDEX"),
    ("动态语料库", "DYNAMIC CORPUS"),
    ("分辨率", "RESOLUTION"),
    ("索引", "INDEX"),
    ("终端", "TERMINAL"),
    ("命令", "COMMAND"),
]
_PINNED_ORDER = ["TOP-K", "DIRECT CORPUS", "COMMAND", "NO INDEX", "RETRIEVAL TRACE", "INTERFACE RES", "EVIDENCE"]


def _flatten(value: Any) -> list[str]:
    if isinstance(value, dict):
        parts: list[str] = []
        for item in value.values():
            parts.extend(_flatten(item))
        return parts
    if isinstance(value, (list, tuple, set)):
        parts = []
        for item in value:
            parts.extend(_flatten(item))
        return parts
    if value is None or isinstance(value, bool):
        return []
    text = str(value).strip()
    return [text] if text else []


def _add(labels: list[str], label: str) -> None:
    value = " ".join(label.upper().split())[:18]
    if value and value not in labels:
        labels.append(value)


def _source(scene: VisualScene, include_prompt: bool = False) -> str:
    values = [scene.paper_anchor, scene.title]
    values.extend(_flatten(scene.data))
    if include_prompt:
        values.append(scene.visual_prompt)
    return " ".join(values)


def _labels_from_text(text: str, labels: list[str]) -> None:
    lower = text.lower()
    matches: list[tuple[int, str]] = []
    for phrase, label in _PHRASES:
        index = lower.find(phrase)
        if index >= 0:
            matches.append((index, label))
    for phrase, label in _ZH_PHRASES:
        index = text.find(phrase)
        if index >= 0:
            matches.append((index, label))
    for _index, label in sorted(matches, key=lambda item: item[0]):
        _add(labels, label)
    for match in _WORD_RE.finditer(text):
        word = match.group(0).lower()
        if word in _STYLE_WORDS:
            continue
        if any(word in phrase.split() for phrase, _label in _PHRASES):
            continue
        _add(labels, word)


def _prioritize(labels: list[str]) -> list[str]:
    values = [label for label in labels if label]
    if "NO INDEX" in values:
        values = [label for label in values if label not in {"OFFLINE INDEX", "INDEX"}]
    ordered: list[str] = []
    for label in _PINNED_ORDER:
        if label in values and label not in ordered:
            ordered.append(label)
    for label in values:
        if label not in ordered:
            ordered.append(label)
    return ordered


def content_labels(scene: VisualScene, count: int = 5) -> list[str]:
    """Return content labels suitable for on-screen diagrams.

    Scene data and paper anchors are the source of truth. The visual prompt is
    only a filtered fallback because it contains style instructions.
    """
    labels: list[str] = []
    text = _source(scene)
    if "brain circuit" in text.lower() or "memory" in text.lower():
        _add(labels, "MEMORY")
        _add(labels, "CIRCUIT")
    _labels_from_text(text, labels)
    if len(labels) < count:
        _labels_from_text(scene.visual_prompt, labels)
    labels = _prioritize(labels)
    fallback_index = 0
    fallback_labels = ["EVIDENCE", "METHOD", "RESULT", "SYSTEM"]
    while len(labels) < count:
        label = fallback_labels[fallback_index % len(fallback_labels)]
        if label in labels:
            label = f"{label} {fallback_index // len(fallback_labels) + 2}"
        _add(labels, label)
        fallback_index += 1
    return labels[:count]


def content_pair(scene: VisualScene) -> tuple[str, str]:
    labels = content_labels(scene, count=10)
    if "TOP-K" in labels and "DIRECT CORPUS" in labels:
        return "TOP-K", "DIRECT CORPUS"
    for preferred in ("DIRECT CORPUS", "RETRIEVAL TRACE", "INTERFACE RES", "EVIDENCE"):
        if preferred in labels and labels[0] != preferred:
            return labels[0], preferred
    return labels[0], labels[1]
