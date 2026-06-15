"""arXiv API collector — searches arXiv by board keywords and categories."""

import re
import time
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests

CST = timezone(timedelta(hours=8))
ARXIV_API = "http://export.arxiv.org/api/query"
ATOM_NS = "http://www.w3.org/2005/Atom"


def _build_query(keywords: list[str], categories: list[str]) -> str:
    """Build arXiv API search query.

    Format: cat:cs.AI AND (abs:"KV cache" OR abs:"context compression" ...)
    """
    cat_parts = [f"cat:{c}" for c in categories]
    kw_parts = [f'abs:"{kw}"' for kw in keywords]

    if len(kw_parts) == 1:
        kw_clause = kw_parts[0]
    else:
        kw_clause = "(" + " OR ".join(kw_parts) + ")"

    if len(cat_parts) == 1:
        cat_clause = cat_parts[0]
    else:
        cat_clause = "(" + " OR ".join(cat_parts) + ")"

    return f"{cat_clause} AND {kw_clause}"


def _parse_entry(entry: ET.Element) -> Optional[dict]:
    """Parse a single arXiv Atom entry into a dict."""
    title_el = entry.find(f"{{{ATOM_NS}}}title")
    summary_el = entry.find(f"{{{ATOM_NS}}}summary")
    published_el = entry.find(f"{{{ATOM_NS}}}published")
    id_el = entry.find(f"{{{ATOM_NS}}}id")

    if id_el is None or id_el.text is None:
        return None

    raw_id = id_el.text.strip()
    # Extract arXiv ID: http://arxiv.org/abs/2605.16289v1 -> 2605.16289
    arxiv_id_match = re.search(r"(\d{4}\.\d{4,5})(v\d+)?$", raw_id)
    if not arxiv_id_match:
        return None
    arxiv_id = arxiv_id_match.group(1)

    title = title_el.text.strip().replace("\n", " ") if title_el is not None and title_el.text else ""
    abstract = summary_el.text.strip().replace("\n", " ") if summary_el is not None and summary_el.text else ""
    published = published_el.text.strip() if published_el is not None and published_el.text else ""

    # Parse authors
    authors = []
    for author_el in entry.findall(f"{{{ATOM_NS}}}author"):
        name_el = author_el.find(f"{{{ATOM_NS}}}name")
        if name_el is not None and name_el.text:
            authors.append(name_el.text.strip())

    # Parse categories
    categories = []
    for cat_el in entry.findall(f"{{{ATOM_NS}}}category"):
        term = cat_el.get("term", "")
        if term:
            categories.append(term)

    # Parse date
    date_str = ""
    if published:
        try:
            dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
            date_str = dt.strftime("%Y-%m-%d")
        except ValueError:
            date_str = published[:10]

    return {
        "id": f"arxiv:{arxiv_id}",
        "title": title,
        "url": f"https://arxiv.org/abs/{arxiv_id}",
        "authors": authors,
        "date": date_str,
        "source": "arxiv",
        "source_category": ", ".join(categories[:3]),
        "abstract": abstract[:2000],
        "tags": [],
        "board_match": [],
        "collected_by": "arxiv_collector",
    }


def collect(
    board: str,
    config: dict,
    date: str,
    proxy: Optional[str] = None,
) -> list[dict]:
    """Collect papers from arXiv for a given board.

    Args:
        board: Board name (memory, llm, agent)
        config: Full sources.json config
        date: Target date (YYYY-MM-DD)
        proxy: HTTP proxy URL

    Returns:
        List of paper dicts in unified format.
    """
    arxiv_cfg = config.get("arxiv", {})
    keywords_cfg = config.get("keywords", {}).get(board, {})

    categories = arxiv_cfg.get("categories", {}).get(board, [])
    max_results = arxiv_cfg.get("max_results", 100)
    date_range_days = config.get("date_range_days", 3)

    if not categories:
        return []

    # Flatten all keyword groups for this board
    all_keywords = []
    for group_name, kws in keywords_cfg.items():
        if isinstance(kws, list):
            all_keywords.extend(kws)

    if not all_keywords:
        return []

    # Build query
    query = _build_query(all_keywords, categories)

    # Calculate cutoff date
    try:
        target_dt = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        target_dt = datetime.now(CST)
    cutoff = target_dt - timedelta(days=date_range_days)

    proxies = {"http": proxy, "https": proxy} if proxy else None

    # Split keywords into batches to avoid overly long queries
    # arXiv API has URL length limits
    batch_size = 6
    all_papers = []
    seen_ids = set()

    for i in range(0, len(all_keywords), batch_size):
        batch_kws = all_keywords[i : i + batch_size]
        batch_query = _build_query(batch_kws, categories)

        params = {
            "search_query": batch_query,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": min(max_results, 50),
        }

        try:
            resp = requests.get(
                ARXIV_API,
                params=params,
                timeout=30,
                proxies=proxies,
                headers={"User-Agent": "daily-report-collector/1.0"},
            )
            resp.raise_for_status()
        except Exception as e:
            print(f"[arxiv] Error fetching batch {i // batch_size + 1}: {e}")
            continue

        # Parse Atom XML
        try:
            root = ET.fromstring(resp.content)
        except ET.ParseError as e:
            print(f"[arxiv] XML parse error: {e}")
            continue

        for entry in root.findall(f"{{{ATOM_NS}}}entry"):
            paper = _parse_entry(entry)
            if paper is None:
                continue

            # Deduplicate by arXiv ID
            if paper["id"] in seen_ids:
                continue
            seen_ids.add(paper["id"])

            # Filter by date
            if paper["date"]:
                try:
                    paper_dt = datetime.strptime(paper["date"], "%Y-%m-%d")
                    if paper_dt < cutoff:
                        continue
                except ValueError:
                    pass

            paper["board_match"] = [board]
            all_papers.append(paper)

        # Be polite to arXiv API — 3 second delay between batches
        if i + batch_size < len(all_keywords):
            time.sleep(3)

    print(f"[arxiv] Board={board}: collected {len(all_papers)} papers")
    return all_papers
