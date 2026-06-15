"""PubMed/PMC collector — searches NCBI E-utilities for biomedical memory research."""

import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests

CST = timezone(timedelta(hours=8))
ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def _esearch(query: str, retmax: int, proxy: Optional[str] = None) -> list[str]:
    """Search PubMed and return list of IDs."""
    proxies = {"http": proxy, "https": proxy} if proxy else None
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": retmax,
        "sort": "date",
        "retmode": "json",
    }
    try:
        resp = requests.get(ESEARCH_URL, params=params, timeout=30, proxies=proxies)
        resp.raise_for_status()
        data = resp.json()
        return data.get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        print(f"[pubmed] esearch error for '{query}': {e}")
        return []


def _efetch_details(ids: list[str], proxy: Optional[str] = None) -> list[dict]:
    """Fetch article details for a list of PubMed IDs."""
    if not ids:
        return []

    proxies = {"http": proxy, "https": proxy} if proxy else None
    params = {
        "db": "pubmed",
        "id": ",".join(ids),
        "rettype": "abstract",
        "retmode": "xml",
    }

    try:
        resp = requests.get(EFETCH_URL, params=params, timeout=30, proxies=proxies)
        resp.raise_for_status()
    except Exception as e:
        print(f"[pubmed] efetch error: {e}")
        return []

    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as e:
        print(f"[pubmed] XML parse error: {e}")
        return []

    articles = []
    for article_el in root.findall(".//PubmedArticle"):
        medline = article_el.find("MedlineCitation")
        if medline is None:
            continue

        pmid_el = medline.find("PMID")
        pmid = pmid_el.text if pmid_el is not None and pmid_el.text else ""

        article = medline.find("Article")
        if article is None:
            continue

        # Title
        title_el = article.find("ArticleTitle")
        title = title_el.text.strip() if title_el is not None and title_el.text else ""

        # Abstract
        abstract_parts = []
        abstract_el = article.find("Abstract")
        if abstract_el is not None:
            for text_el in abstract_el.findall("AbstractText"):
                label = text_el.get("Label", "")
                text = "".join(text_el.itertext()).strip()
                if label:
                    abstract_parts.append(f"{label}: {text}")
                else:
                    abstract_parts.append(text)
        abstract = " ".join(abstract_parts)[:2000]

        # Authors
        authors = []
        author_list = article.find("AuthorList")
        if author_list is not None:
            for author_el in author_list.findall("Author"):
                last = author_el.find("LastName")
                init = author_el.find("Initials")
                name_parts = []
                if last is not None and last.text:
                    name_parts.append(last.text)
                if init is not None and init.text:
                    name_parts.append(init.text)
                if name_parts:
                    authors.append(" ".join(name_parts))

        # Date
        date_str = ""
        pub_date = article.find("ArticleDate")
        if pub_date is not None:
            y = pub_date.find("Year")
            m = pub_date.find("Month")
            d = pub_date.find("Day")
            if y is not None and y.text:
                date_str = y.text
                if m is not None and m.text:
                    date_str += f"-{m.text.zfill(2)}"
                    if d is not None and d.text:
                        date_str += f"-{d.text.zfill(2)}"

        # Journal
        journal_el = article.find("Journal/Title")
        journal = journal_el.text if journal_el is not None and journal_el.text else ""

        if not title:
            continue

        articles.append({
            "id": f"pubmed:{pmid}",
            "title": title,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "authors": authors[:5],
            "date": date_str,
            "source": "pubmed",
            "source_category": journal,
            "abstract": abstract,
            "tags": [],
            "board_match": [],
            "collected_by": "pubmed_collector",
        })

    return articles


def collect(
    board: str,
    config: dict,
    date: str,
    proxy: Optional[str] = None,
) -> list[dict]:
    """Collect PubMed papers for a given board.

    Args:
        board: Board name (memory)
        config: Full sources.json config
        date: Target date (YYYY-MM-DD)
        proxy: HTTP proxy URL

    Returns:
        List of paper dicts in unified format.
    """
    pubmed_cfg = config.get("pubmed", {})
    queries = pubmed_cfg.get("queries", {}).get(board, [])
    retmax = pubmed_cfg.get("retmax", 50)
    date_range_days = config.get("date_range_days", 1)

    if not queries:
        return []

    try:
        target_dt = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        target_dt = datetime.now(CST)
    cutoff = target_dt - timedelta(days=date_range_days)

    all_papers = []
    seen_ids = set()

    for query in queries:
        # Search
        ids = _esearch(query, retmax=retmax, proxy=proxy)
        if not ids:
            continue

        # Batch fetch (PubMed recommends batches of 200)
        for i in range(0, len(ids), 200):
            batch_ids = ids[i:i + 200]
            articles = _efetch_details(batch_ids, proxy=proxy)

            for paper in articles:
                if paper["id"] in seen_ids:
                    continue
                seen_ids.add(paper["id"])

                # Filter by date
                if paper["date"]:
                    try:
                        paper_dt = datetime.strptime(paper["date"][:10], "%Y-%m-%d")
                        if paper_dt < cutoff:
                            continue
                    except ValueError:
                        pass

                paper["board_match"] = [board]
                all_papers.append(paper)

            time.sleep(0.5)  # Be polite to NCBI

    print(f"[pubmed] Board={board}: collected {len(all_papers)} papers")
    return all_papers
