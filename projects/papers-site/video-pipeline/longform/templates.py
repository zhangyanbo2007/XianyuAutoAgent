"""HTML infographic templates for longform slides."""

from __future__ import annotations

import html
import re
from .content_spec import content_labels, content_pair
from .models import VisualScene

_ACCENT = {"cyan": "#22d3ee", "magenta": "#f472b6", "green": "#4ade80", "gold": "#fbbf24"}
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{3,}")
_STOPWORDS = {
    "cinematic", "dark", "background", "neon", "with", "text", "readable",
    "watermark", "illustration", "visual", "prompt", "scene", "quality",
    "overlays", "glowing", "holographic", "paper", "finding",
    "method", "problem", "future", "limitation", "takeaway",
}


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _cards(items: list[dict[str, object]]) -> str:
    cells = [f"<div class='card'><b>{_esc(item.get('value', ''))}</b><span>{_esc(item.get('label', ''))}</span></div>" for item in items]
    return "<div class='cards'>" + "".join(cells) + "</div>"


def _concept_terms(scene: VisualScene) -> list[str]:
    return [label.lower() for label in content_labels(scene, count=8)]


def _concept_labels(scene: VisualScene) -> tuple[str, str]:
    return content_pair(scene)


def _concept_list(scene: VisualScene, count: int, fallback: list[str]) -> list[str]:
    terms = content_labels(scene, count=count)
    values = terms[:count]
    while len(values) < count:
        values.append(fallback[len(values) % len(fallback)])
    return values


def _template_body(scene: VisualScene) -> str:
    if scene.template == "hero_title":
        left, right = _concept_labels(scene)
        if (left, right) == ("MEMORY", "CIRCUIT"):
            return "<div class='hero-brain'><div class='hemisphere organic'>MEMORY</div><div class='hemisphere circuit'>CIRCUIT</div><div class='synapse'></div></div>"
        return f"<div class='hero-brain'><div class='hemisphere organic'>{_esc(left)}</div><div class='hemisphere circuit'>{_esc(right)}</div><div class='synapse'></div></div>"
    if scene.template == "core_question":
        left, right = _concept_labels(scene)
        return f"<div class='question-visual'><div class='scroll'>{_esc(left)}</div><strong>?</strong><div class='fragments'>{_esc(right)}</div></div>"
    if scene.template == "metric_cards":
        return _cards(scene.data.get("metrics", []))
    if scene.template == "task_matrix":
        tasks = scene.data.get("tasks") or _concept_list(scene, 4, ["Problem", "Method", "Evidence", "Takeaway"])
        return "<div class='matrix'>" + "".join(f"<div>{_esc(task)}</div>" for task in tasks) + "</div>"
    if scene.template == "ranking_board":
        rows = scene.data.get("rows") or scene.data.get("ranking") or _concept_list(scene, 5, ["Baseline", "Method", "Ablation", "Variant", "Result"])
        return "<div class='rank'>" + "".join(f"<div><span>{_esc(row)}</span><i style='width:{90 - i*12}%'></i></div>" for i, row in enumerate(rows)) + "</div>"
    if scene.template == "bar_finding":
        bars = scene.data.get("bars") or [(label, value) for label, value in zip(_concept_list(scene, 4, ["Baseline", "Method", "Ablation", "Result"]), [92, 64, 48, 30])]
        return "<div class='bars'>" + "".join(f"<div><b>{value}%</b><i style='height:{value*3}px'></i><span>{_esc(label)}</span></div>" for label, value in bars) + "</div>"
    if scene.template == "split_comparison":
        left, right = _concept_labels(scene)
        return f"<div class='split'><div><h3>{_esc(left)}</h3><p>source · evidence · trace</p></div><div><h3>{_esc(right)}</h3><p>risk · gap · decision</p></div></div>"
    if scene.template == "future_direction":
        nodes = _concept_list(scene, 3, ["Evidence", "Mechanism", "System"])
        return "<div class='roadmap'>" + "".join(f"<div>{_esc(node)}</div>" for node in nodes) + "</div>"
    if scene.template == "paper_gap_iceberg":
        left, right = _concept_labels(scene)
        return f"<div class='iceberg'><div>{_esc(left)}</div><strong>{_esc(right)}</strong><div>hidden evidence · failure mode · mechanism</div></div>"
    if scene.template == "method_transfer":
        left, right = _concept_labels(scene)
        return f"<div class='transfer'><div>{_esc(left)}</div><b>→</b><div>{_esc(right)}</div></div>"
    if scene.template == "takeaway_cards":
        cards = _concept_list(scene, 3, ["Problem", "Method", "Takeaway"])
        return "<div class='takeaways'>" + "".join(f"<div>{_esc(card)}</div>" for card in cards) + "</div>"
    return "<div class='orb'>?</div>"


def render_slide_html(scene: VisualScene, total: int) -> str:
    color = _ACCENT.get(scene.accent, _ACCENT["cyan"])
    body = _template_body(scene)
    css = f"""
* {{ box-sizing: border-box; }}
body {{ margin:0; width:1920px; height:1080px; overflow:hidden; background:#05070d; color:#f8fafc; font-family:'Noto Sans CJK SC','Noto Sans SC',Arial,sans-serif; }}
.stage {{ position:relative; width:100%; height:100%; padding:54px 72px; background: radial-gradient(circle at 50% 25%, {color}22, transparent 34%), linear-gradient(135deg,#05070d,#0b1020 55%,#05070d); }}
.stage:before {{ content:''; position:absolute; inset:24px; border:2px solid {color}88; box-shadow:0 0 28px {color}66 inset; }}
.kicker {{ position:relative; z-index:2; color:{color}; font-size:28px; letter-spacing:1px; }}
h1 {{ position:relative; z-index:2; margin:24px 0 20px; font-size:72px; line-height:1.12; text-shadow:0 0 22px {color}99; }}
.anchor {{ position:absolute; z-index:2; right:72px; top:64px; max-width:560px; color:#9ca3af; font-size:23px; text-align:right; }}
.visual {{ position:relative; z-index:2; height:650px; margin-top:20px; display:flex; align-items:center; justify-content:center; }}
.subtitle-safe {{ position:absolute; z-index:1; left:72px; right:72px; bottom:58px; height:170px; background:linear-gradient(180deg,transparent,#02061799); }}
.count {{ position:absolute; right:82px; bottom:26px; color:#64748b; font-size:20px; }}
.cards,.matrix,.takeaways,.roadmap {{ display:grid; grid-template-columns:repeat(2,minmax(260px,1fr)); gap:28px; width:1200px; }}
.card,.matrix div,.takeaways div,.roadmap div,.split div,.transfer div {{ min-height:150px; padding:28px; border:1px solid {color}99; background:#0f172acc; box-shadow:0 0 28px {color}44; border-radius:16px; }}
.card b {{ display:block; font-size:82px; color:{color}; }} .card span {{ font-size:28px; color:#cbd5e1; }}
.matrix div,.takeaways div,.roadmap div {{ font-size:38px; display:flex; align-items:center; justify-content:center; text-align:center; }}
.split,.transfer {{ display:grid; grid-template-columns:1fr 1fr; align-items:center; gap:42px; width:1280px; }}
.split div h3 {{ color:{color}; font-size:54px; margin:0 0 24px; }} .split div p,.transfer div {{ font-size:34px; line-height:1.45; }}
.transfer b {{ font-size:92px; color:{color}; }}
.bars {{ display:flex; align-items:end; gap:80px; height:420px; }} .bars div {{ display:flex; flex-direction:column; align-items:center; gap:16px; }} .bars b {{ font-size:42px; color:{color}; }} .bars i {{ display:block; width:116px; background:linear-gradient({color},#7c3aed); box-shadow:0 0 26px {color}; border-radius:14px 14px 0 0; }} .bars span {{ font-size:28px; }}
.rank {{ width:1240px; display:flex; flex-direction:column; gap:24px; }} .rank div {{ display:flex; align-items:center; gap:24px; font-size:32px; }} .rank span {{ width:280px; }} .rank i {{ height:34px; display:block; background:linear-gradient(90deg,{color},#f472b6); border-radius:999px; box-shadow:0 0 18px {color}; }}
.iceberg {{ text-align:center; color:#cbd5e1; }} .iceberg strong {{ display:block; margin:28px auto; width:620px; height:260px; padding-top:92px; font-size:44px; color:{color}; background:linear-gradient(145deg,#0f172a,#111827); clip-path:polygon(50% 0,100% 100%,0 100%); filter:drop-shadow(0 0 28px {color}); }}
.orb {{ width:360px; height:360px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:180px; color:{color}; border:2px solid {color}; box-shadow:0 0 80px {color}; }}
"""
    return "\n".join([
        "<!doctype html>",
        "<html lang='zh-CN'><head><meta charset='utf-8' />",
        f"<style>{css}</style></head>",
        "<body><main class='stage'>",
        f"<div class='kicker'>{_esc(scene.template)} · Scene {scene.index + 1:02d}</div>",
        f"<div class='anchor'>{_esc(scene.paper_anchor)}</div>",
        f"<h1>{_esc(scene.title)}</h1>",
        f"<section class='visual'>{body}</section>",
        "<div class='subtitle-safe'></div>",
        f"<div class='count'>{scene.index + 1:02d} / {total:02d}</div>",
        "</main></body></html>",
    ])
