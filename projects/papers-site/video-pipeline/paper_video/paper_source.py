"""Ingest a paper from a URL / arxiv id / local file into a grounded fact bundle.

Resolution order is robustness-first:

1. Resolve an arxiv id (and any direct text) from the input.
2. Load the local ``papers.json`` entry as a reliable grounded base
   (title, abstract, abstract_zh, editorial summary, urls).
3. Best-effort fetch the arxiv full text (HTML/ar5iv) to enrich the base.

The result is a plain ``dict`` (a "PaperDoc") consumed by ``storyboard.py``.
"""

from __future__ import annotations

import json
import re
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Optional
from xml.etree import ElementTree as ET

_ARXIV_RE = re.compile(r"(\d{4}\.\d{4,5})(v\d+)?")
_PROXY = "http://127.0.0.1:7897"
_UA = "Mozilla/5.0 (paper-video-pipeline)"


# ── input resolution ────────────────────────────────────────────────


def _read_input(paper_input: str) -> tuple[str, str]:
    """Return (raw_text, hint). ``paper_input`` may be a file path or a string."""
    path = Path(paper_input)
    if path.exists() and path.is_file():
        return path.read_text(encoding="utf-8").strip(), str(path)
    return str(paper_input).strip(), ""


def extract_arxiv_id(text: str) -> Optional[str]:
    match = _ARXIV_RE.search(text or "")
    return match.group(1) if match else None


# ── local papers.json ───────────────────────────────────────────────


def _papers_json_path() -> Path:
    # paper_video/ → video-pipeline/ → papers-site/ → data/papers.json
    return Path(__file__).resolve().parents[2] / "data" / "papers.json"


def load_local_entry(arxiv_id: str, data_path: Optional[Path] = None) -> Optional[dict[str, Any]]:
    path = data_path or _papers_json_path()
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    papers = data.get("papers", data if isinstance(data, list) else [])
    for paper in papers:
        if str(paper.get("arxiv_id", "")).strip() == arxiv_id:
            return paper
        urls = " ".join(str(paper.get(k, "")) for k in ("paper_url", "source_url", "paper_urls"))
        if arxiv_id in urls:
            return paper
    return None


# ── arxiv fetching (best-effort) ────────────────────────────────────


def _open(url: str, timeout: int = 20) -> Optional[bytes]:
    """Try direct first, then via the local proxy. Returns body bytes or None."""
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception:
        pass
    try:
        handler = urllib.request.ProxyHandler({"http": _PROXY, "https": _PROXY})
        opener = urllib.request.build_opener(handler)
        with opener.open(req, timeout=timeout) as resp:
            return resp.read()
    except Exception:
        return None


def fetch_arxiv_metadata(arxiv_id: str) -> dict[str, Any]:
    """Title / abstract / authors via the arxiv Atom export API."""
    body = _open(f"https://export.arxiv.org/api/query?id_list={arxiv_id}")
    if not body:
        return {}
    try:
        ns = {"a": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(body)
        entry = root.find("a:entry", ns)
        if entry is None:
            return {}
        title = (entry.findtext("a:title", default="", namespaces=ns) or "").strip()
        summary = (entry.findtext("a:summary", default="", namespaces=ns) or "").strip()
        authors = [
            (a.findtext("a:name", default="", namespaces=ns) or "").strip()
            for a in entry.findall("a:author", ns)
        ]
        return {"title": title, "abstract": summary, "authors": [a for a in authors if a]}
    except Exception:
        return {}


class _TextExtractor(HTMLParser):
    _SKIP = {"script", "style", "head", "nav", "footer"}

    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self.chunks: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in self._SKIP and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._skip_depth == 0:
            text = data.strip()
            if text:
                self.chunks.append(text)


def fetch_arxiv_fulltext(arxiv_id: str, max_chars: int = 14000) -> str:
    """Best-effort full body text from arxiv HTML / ar5iv mirror."""
    for url in (
        f"https://arxiv.org/html/{arxiv_id}",
        f"https://ar5iv.labs.arxiv.org/html/{arxiv_id}",
        f"https://ar5iv.org/abs/{arxiv_id}",
    ):
        body = _open(url, timeout=25)
        if not body:
            continue
        try:
            parser = _TextExtractor()
            parser.feed(body.decode("utf-8", errors="ignore"))
            text = " ".join(parser.chunks)
            text = re.sub(r"\s+", " ", text).strip()
            if len(text) > 1200:  # got a real body, not an error page
                return text[:max_chars]
        except Exception:
            continue
    return ""


# ── public entry ────────────────────────────────────────────────────


def ingest_paper(paper_input: str, *, fetch_fulltext: bool = True) -> dict[str, Any]:
    """Resolve ``paper_input`` into a grounded PaperDoc dict."""
    raw, _hint = _read_input(paper_input)
    arxiv_id = extract_arxiv_id(raw)

    doc: dict[str, Any] = {
        "arxiv_id": arxiv_id or "",
        "title": "",
        "authors": [],
        "abstract": "",
        "abstract_zh": "",
        "summary": "",
        "full_text": "",
        "urls": [],
        "sources": [],
    }

    # If the input is not a url/id, treat it as raw paper text.
    if not arxiv_id and len(raw) > 400:
        doc["full_text"] = raw[:14000]
        doc["abstract"] = raw[:1500]
        doc["sources"].append("inline-text")
        return doc

    if arxiv_id:
        entry = load_local_entry(arxiv_id)
        if entry:
            doc.update(
                title=entry.get("title", "") or doc["title"],
                authors=entry.get("authors", []) or [],
                abstract=entry.get("abstract", "") or "",
                abstract_zh=entry.get("abstract_zh", "") or "",
                summary=entry.get("summary", "") or "",
            )
            for key in ("paper_urls", "project_urls", "repo_urls"):
                value = entry.get(key)
                if isinstance(value, list):
                    doc["urls"].extend(str(v) for v in value)
                elif value:
                    doc["urls"].append(str(value))
            doc["sources"].append("papers.json")

        meta = fetch_arxiv_metadata(arxiv_id)
        if meta.get("title"):
            doc["title"] = doc["title"] or meta["title"]
            doc["abstract"] = doc["abstract"] or meta.get("abstract", "")
            doc["authors"] = doc["authors"] or meta.get("authors", [])
            doc["sources"].append("arxiv-api")

        if fetch_fulltext:
            full = fetch_arxiv_fulltext(arxiv_id)
            if full:
                doc["full_text"] = full
                doc["sources"].append("arxiv-fulltext")

        doc["urls"].append(f"https://arxiv.org/abs/{arxiv_id}")

    # de-duplicate urls, keep order
    seen: set[str] = set()
    doc["urls"] = [u for u in doc["urls"] if not (u in seen or seen.add(u))]
    return doc


def paper_context(doc: dict[str, Any], max_chars: int = 9000) -> str:
    """A compact, LLM-ready grounding string from a PaperDoc."""
    parts = []
    for key in ("title", "summary", "abstract_zh", "abstract"):
        value = doc.get(key)
        if value:
            parts.append(f"## {key}\n{value}")
    if doc.get("full_text"):
        parts.append(f"## full_text (truncated)\n{doc['full_text']}")
    if doc.get("urls"):
        parts.append("## urls\n" + "\n".join(doc["urls"]))
    text = "\n\n".join(parts)
    return text[:max_chars]
