"""Build paper-grounded fact packs for longform video planning."""

from __future__ import annotations

import re
from collections import Counter
from typing import Iterable

from .models import PaperFactPack


_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9^-]*")
_SENTENCE_RE = re.compile(r"(?<=[。.!?？])\s+|\n+")
_FRAGMENT_RE = re.compile(r"[，,；;、]")
_STOPWORDS = {
    "about", "after", "against", "also", "and", "are", "based", "been",
    "being", "between", "both", "can", "does", "during", "each",
    "for", "from", "have", "how", "into", "its", "more", "not", "over",
    "paper", "papers", "rethinking", "that", "the", "their", "then",
    "these", "this", "through", "via", "when", "where", "which", "with",
    "without", "using",
}


def _as_text(value: object) -> str:
    return value if isinstance(value, str) else ""


def _urls(paper: dict) -> list[str]:
    values: list[str] = []
    for key in ("paper_url", "source_url"):
        value = paper.get(key)
        if isinstance(value, str) and value:
            values.append(value)
    for key in ("paper_urls", "project_urls", "repo_urls", "dataset_urls"):
        raw = paper.get(key, [])
        if isinstance(raw, Iterable) and not isinstance(raw, (str, bytes)):
            values.extend(str(item) for item in raw if item)
    seen = set()
    deduped = []
    for url in values:
        if url not in seen:
            seen.add(url)
            deduped.append(url)
    return deduped


def _sentences(text: str) -> list[str]:
    return [piece.strip() for piece in _SENTENCE_RE.split(text) if piece.strip()]


def _sentence(text: str, fallback: str) -> str:
    pieces = _sentences(text)
    return pieces[0] if pieces else fallback


def _words(text: str) -> list[str]:
    return [word.lower() for word in _WORD_RE.findall(text) if len(word) >= 3]


def _content_words(text: str) -> list[str]:
    return [word for word in _words(text) if word not in _STOPWORDS]


def _key_terms(text: str) -> list[str]:
    words = _content_words(text)
    title_words = set(_content_words(_sentences(text)[0] if _sentences(text) else text))
    counts: Counter[str] = Counter()
    for n in (3, 2, 1):
        for i in range(0, max(len(words) - n + 1, 0)):
            parts = words[i : i + n]
            if len(parts) == n and all(part not in _STOPWORDS for part in parts):
                counts[" ".join(parts)] += 1

    scored: list[tuple[int, str]] = []
    for term, count in counts.items():
        parts = term.split()
        title_bonus = 2 if any(part in title_words for part in parts) else 0
        phrase_bonus = len(parts)
        scored.append((count * 4 + title_bonus + phrase_bonus, term))
    scored.sort(key=lambda item: (-item[0], item[1]))

    terms: list[str] = []
    for _score, term in scored:
        if any(term in existing or existing in term for existing in terms):
            continue
        terms.append(term)
        if len(terms) >= 8:
            break

    chinese_terms = []
    for marker in ("记忆", "检索", "证据", "智能体", "视频", "评估", "语料库"):
        if marker in text:
            chinese_terms.append(marker)
    for term in chinese_terms:
        if term not in terms:
            terms.append(term)
    return terms[:10] or ["paper", "evidence", "method"]


def _classify_anchor(text: str, context: str) -> str:
    lower = text.lower()
    context_lower = context.lower()
    if any(word in lower for word in ("limitation", "caveat", "fail", "struggle", "challenge", "weakness", "缺陷", "失败")):
        return "limitation"
    if any(word in lower for word in ("future", "direction", "next", "open", "未来", "方向")):
        return "future"
    if any(word in lower for word in ("find", "result", "show", "outperform", "measure", "finding", "发现", "结果")):
        return "finding"
    if any(word in lower for word in ("method", "approach", "introduce", "propose", "framework", "interaction", "方法", "提出")):
        return "method"
    if any(word in context_lower for word in ("task", "benchmark", "evaluation", "evaluate", "test", "measure", "任务", "评估", "测试")):
        return "task"
    return "problem"


def _fragments(sentence: str) -> list[str]:
    values = [part.strip(" .。") for part in _FRAGMENT_RE.split(sentence) if part.strip(" .。")]
    return [value for value in values if 8 <= len(value) <= 120]


def _anchor_text(value: str) -> str:
    return " ".join(value.split())[:180]


def _anchors(text: str) -> list[dict[str, str]]:
    anchors: list[dict[str, str]] = []
    seen: set[str] = set()

    def add(kind: str, value: str, evidence: str) -> None:
        anchor = _anchor_text(value)
        key = anchor.lower()
        if anchor and key not in seen:
            seen.add(key)
            anchors.append({"kind": kind, "text": anchor, "evidence": evidence})

    for sentence in _sentences(text):
        add(_classify_anchor(sentence, text), sentence, "title/summary/abstract")
        for fragment in _fragments(sentence):
            add(_classify_anchor(fragment, text), fragment, "paper sentence fragment")
        if len(anchors) >= 12:
            break

    for term in _key_terms(text):
        kind = "task" if any(word in text.lower() for word in ("task", "benchmark", "evaluation", "test", "measure")) else "problem"
        add(kind, f"paper-specific concept: {term}", "extracted key term")
        if len(anchors) >= 12:
            break

    if not anchors:
        add("problem", "论文提出了一个需要系统评估的问题。", "summary/abstract")
    return anchors


def _method_sentence(body: str) -> str:
    for sentence in _sentences(body):
        lower = sentence.lower()
        if len(sentence) >= 40 and any(word in lower for word in ("method", "approach", "introduce", "propose", "framework", "benchmark", "evaluate", "measure", "方法", "提出", "评估")):
            return sentence
    return "将论文中的问题、方法、证据和结论转写为可追溯的长视频叙事结构。"


def build_fact_pack(paper: dict) -> PaperFactPack:
    title = _as_text(paper.get("title"))
    summary = _as_text(paper.get("summary"))
    abstract = _as_text(paper.get("abstract"))
    abstract_zh = _as_text(paper.get("abstract_zh"))
    body = "\n".join(part for part in (summary, abstract_zh, abstract) if part)
    source = "\n".join(part for part in (title, body) if part)
    anchors = _anchors(source)

    problem = _sentence(summary or abstract_zh or abstract, "现有研究留下了一个需要被系统解释和验证的关键问题。")
    method = _method_sentence(body)
    findings = [anchor["text"] for anchor in anchors if anchor["kind"] == "finding"] or [
        "论文给出了能指导系统设计或评估判断的关键证据。"
    ]
    limitations = [anchor["text"] for anchor in anchors if anchor["kind"] == "limitation"] or [
        "视频解读需要区分论文实证结论和面向未来的设计推断。"
    ]

    return PaperFactPack(
        slug=_as_text(paper.get("slug")) or "paper",
        title=title,
        summary=summary,
        abstract=abstract,
        urls=_urls(paper),
        problem=problem,
        method=method,
        findings=findings,
        limitations=limitations,
        key_terms=_key_terms(source),
        anchors=anchors,
    )
