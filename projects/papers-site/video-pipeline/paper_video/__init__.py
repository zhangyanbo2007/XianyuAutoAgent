"""Paper → audio-visual storyboard → high-quality explainer video pipeline.

A clean, single-entry refactor that unifies the LLM storyboard planning
(formerly ``longform/``) with the high-quality DAST renderer
(formerly ``dast_pipeline.py``):

    paper (url / arxiv id / local text)
        → ingest          (paper_source.py)
        → storyboard      (storyboard.py)    ← fine-grained 音画分镜脚本
        → backgrounds     (backgrounds.py)   ← textless cinematic AI backdrops
        → charts          (charts.py)
        → slides          (slides.py)        ← HTML + backdrop → PNG
        → narration       (narration.py)     ← edge-TTS + timed subtitles
        → assemble        (assemble.py)      ← Ken Burns + mux + burn → video.mp4

The two deliverables are ``storyboard.json`` / ``storyboard.md`` and ``video.mp4``.
"""

from __future__ import annotations

__all__ = ["run_pipeline"]


def run_pipeline(*args, **kwargs):
    # Imported lazily so that importing the package never pulls heavy deps.
    from .pipeline import run_pipeline as _run

    return _run(*args, **kwargs)
