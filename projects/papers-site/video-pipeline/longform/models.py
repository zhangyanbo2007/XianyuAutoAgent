"""Datamodels for the longform paper-video pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PaperFactPack:
    slug: str
    title: str
    summary: str
    abstract: str
    urls: list[str] = field(default_factory=list)
    problem: str = ""
    method: str = ""
    findings: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    key_terms: list[str] = field(default_factory=list)
    anchors: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Scene:
    index: int
    kind: str
    title: str
    narration: str
    paper_anchor: str
    template_hint: str
    duration_sec: float = 24.0
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VisualScene:
    index: int
    kind: str
    title: str
    narration: str
    paper_anchor: str
    template: str
    duration_sec: float
    data: dict[str, Any] = field(default_factory=dict)
    visual_prompt: str = ""
    accent: str = "cyan"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TimelineEntry:
    scene_index: int
    start_sec: float
    end_sec: float
    transition: str
    narration: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Timeline:
    entries: list[TimelineEntry]
    total_duration_sec: float
    transition_sec: float = 0.45

    def to_dict(self) -> dict[str, Any]:
        return {
            "entries": [entry.to_dict() for entry in self.entries],
            "total_duration_sec": self.total_duration_sec,
            "transition_sec": self.transition_sec,
        }


@dataclass(frozen=True)
class RenderResult:
    html_files: list[Path]
    png_files: list[Path]
    contact_sheet: Path

    def to_dict(self) -> dict[str, Any]:
        return {
            "html_files": [str(path) for path in self.html_files],
            "png_files": [str(path) for path in self.png_files],
            "contact_sheet": str(self.contact_sheet),
        }
