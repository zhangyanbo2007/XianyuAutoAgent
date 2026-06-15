#!/usr/bin/env python3
"""Step 2: Dedup — filter items already in Wiki index.

Usage:
  dedup.py --input 01-search.json --board memory --output 02-new-papers.json

Reads the Wiki INDEX.md, extracts existing paper/news IDs and URLs,
then filters the input JSON to keep only new items.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


def load_index(index_path: str) -> tuple[set, set, set]:
    """Parse INDEX.md to extract existing paper/news IDs, URLs, and filenames.

    Returns:
        (ids, urls, filenames): Sets of existing identifiers, URLs, and page filenames.
    """
    ids = set()
    urls = set()
    filenames = set()

    if not os.path.exists(index_path):
        return ids, urls, filenames

    with open(index_path, encoding="utf-8") as f:
        content = f.read()

    # Extract arXiv IDs: arxiv:XXXX.XXXXX
    for match in re.finditer(r"arxiv:(\d{4}\.\d{4,5})", content):
        ids.add(f"arxiv:{match.group(1)}")

    # Extract PubMed IDs: pubmed:NNNNN
    for match in re.finditer(r"pubmed:(\d+)", content):
        ids.add(f"pubmed:{match.group(1)}")

    # Extract OpenReview IDs: openreview:XXX
    for match in re.finditer(r"openreview:([a-zA-Z0-9]+)", content):
        ids.add(f"openreview:{match.group(1)}")

    # Extract URLs (https://...)
    for match in re.finditer(r"https?://[^\s\)\"]+", content):
        url = match.group(0).rstrip(".,;:")
        urls.add(url)

    # Extract page filenames from markdown links: [title](path/file.md)
    for match in re.finditer(r"\[([^\]]+)\]\(([^)]+\.md)\)", content):
        title = match.group(1)
        filepath = match.group(2)
        # Extract filename from path
        fname = filepath.rsplit("/", 1)[-1] if "/" in filepath else filepath
        filenames.add(fname)
        # Also add normalized title for matching
        filenames.add(title.lower().strip())

    return ids, urls, filenames


def load_recent_reports(workspace_base: str, days: int = 3) -> set:
    """Load URLs from recent daily reports (for news dedup)."""
    urls = set()
    # This would scan recent report files - placeholder for now
    return urls


def dedup_items(items: list[dict], existing_ids: set, existing_urls: set,
                existing_filenames: set) -> list[dict]:
    """Filter out items that already exist in the Wiki."""
    new_items = []
    removed = 0

    for item in items:
        item_id = item.get("id", "")
        url = item.get("url", "")
        title = item.get("title", "")

        # Check ID match
        if item_id and item_id in existing_ids:
            removed += 1
            continue

        # Check URL match
        if url and url in existing_urls:
            removed += 1
            continue

        # Check filename/title match (for wiki_ingest generated entries)
        if title:
            # Normalize title to filename: remove special chars, lowercase, truncate
            name = re.sub(r'[^\w一-鿿\s\-]', '', title)
            name = re.sub(r'\s+', '-', name.strip())
            if len(name) > 80:
                name = name[:80].rstrip('-')
            fname = name.lower() + ".md"
            if fname in existing_filenames or title.lower().strip() in existing_filenames:
                removed += 1
                continue

        new_items.append(item)

    return new_items, removed


def main():
    parser = argparse.ArgumentParser(description="Step 2: Dedup against Wiki index")
    parser.add_argument("--input", required=True, help="Path to 01-search.json")
    parser.add_argument("--board", required=True, choices=["memory", "llm", "agent", "news", "builders"])
    parser.add_argument("--output", required=True, help="Output path for deduped items")
    parser.add_argument("--index", help="Override INDEX.md path (auto-detected from board)")

    args = parser.parse_args()

    # Determine INDEX.md path
    if args.index:
        index_path = args.index
    elif args.board in ("memory", "llm", "agent"):
        index_path = "kb/papers/INDEX.md"
    else:
        index_path = "kb/tech-news/INDEX.md"

    # Resolve relative to project root (privacy-engineering/)
    if not os.path.isabs(index_path):
        # Walk up from script dir to find project root
        script_dir = Path(__file__).resolve().parent
        # scripts/ → daily-report/ → skills/ → .claude/ → project root
        project_root = script_dir.parent.parent.parent.parent
        index_path = str(project_root / index_path)

    # Load input
    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("items", [])

    # Load existing IDs from INDEX.md
    existing_ids, existing_urls, existing_filenames = load_index(index_path)

    # Dedup
    new_items, removed = dedup_items(items, existing_ids, existing_urls, existing_filenames)

    # Update output
    data["items"] = new_items
    data["stats"]["total"] = len(new_items)
    data["stats"]["dedup_removed"] = removed

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Dedup: {len(items)} → {len(new_items)} new items ({removed} removed)")
    print(f"Existing in index: {len(existing_ids)} IDs, {len(existing_urls)} URLs, {len(existing_filenames)} filenames/titles")
    print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()
