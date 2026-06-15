#!/usr/bin/env python3
"""Step 3: Wiki Ingest — generate paper/news page templates and update INDEX.md.

Usage:
  wiki_ingest.py --input 02-new-papers.json --board memory --date 2026-06-11

For academic boards: creates paper pages in kb/papers/papers/
For news boards: creates news pages in kb/tech-news/news/

Also updates INDEX.md with new entries.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

CST = timezone(timedelta(hours=8))


def safe_filename(title: str, max_len: int = 80) -> str:
    """Convert title to a safe filename."""
    # Remove special chars, keep alphanumeric and Chinese
    name = re.sub(r'[^\w一-鿿\s\-]', '', title)
    name = re.sub(r'\s+', '-', name.strip())
    if len(name) > max_len:
        name = name[:max_len].rstrip('-')
    return name.lower()


def generate_paper_page(item: dict, board: str) -> str:
    """Generate a paper page in markdown with frontmatter."""
    title = item.get("title", "Untitled")
    authors = item.get("authors", [])
    date = item.get("date", "")
    url = item.get("url", "")
    abstract = item.get("abstract", "")
    source = item.get("source", "")
    source_category = item.get("source_category", "")
    tags = item.get("tags", [])
    item_id = item.get("id", "")

    # Determine year
    year = date[:4] if date else "2026"

    # Extract arxiv_id if present
    arxiv_id = ""
    if item_id.startswith("arxiv:"):
        arxiv_id = item_id.replace("arxiv:", "")

    # Board emoji
    board_emoji = {"memory": "🔬", "llm": "🤖", "agent": "🧠"}.get(board, "📄")

    # Frontmatter
    lines = [
        "---",
        f"title: \"{title}\"",
        f"authors: [{', '.join(authors[:5])}]",
        f"year: {year}",
        f"venue: \"{source_category or source}\"",
        f"tags: [{', '.join(tags) if tags else ''}]",
    ]
    if arxiv_id:
        lines.append(f"arxiv_id: \"{arxiv_id}\"")
    lines.append(f"ingested: \"{datetime.now(CST).strftime('%Y-%m-%d')}\"")
    lines.append("---")
    lines.append("")

    # Content
    lines.append(f"# {board_emoji} {title}")
    lines.append("")
    lines.append(f"- **Authors**: {', '.join(authors[:5])}")
    lines.append(f"- **Date**: {date}")
    lines.append(f"- **Source**: [{source}]({url})")
    if source_category:
        lines.append(f"- **Category**: {source_category}")
    lines.append("")
    lines.append("## Abstract")
    lines.append("")
    lines.append(abstract)
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("<!-- Claude 在此添加中文解读 -->")
    lines.append("")

    return "\n".join(lines)


def generate_news_page(item: dict) -> str:
    """Generate a news page in markdown with frontmatter."""
    title = item.get("title", "Untitled")
    date = item.get("date", "")
    url = item.get("url", "")
    abstract = item.get("abstract", "")
    source = item.get("source", "")
    source_category = item.get("source_category", "")
    tags = item.get("tags", [])

    # Frontmatter
    lines = [
        "---",
        f"title: \"{title}\"",
        f"source: \"{source}\"",
        f"date: \"{date}\"",
        f"tags: [{', '.join(tags) if tags else ''}]",
        f"url: \"{url}\"",
        f"ingested: \"{datetime.now(CST).strftime('%Y-%m-%d')}\"",
        "---",
        "",
    ]

    # Content
    lines.append(f"# 📰 {title}")
    lines.append("")
    lines.append(f"- **Source**: {source}")
    lines.append(f"- **Date**: {date}")
    lines.append(f"- **URL**: {url}")
    if source_category:
        lines.append(f"- **Category**: {source_category}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(abstract)
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("<!-- Claude 在此添加中文解读 -->")
    lines.append("")

    return "\n".join(lines)


def update_index(index_path: str, items: list[dict], board: str, date: str):
    """Append new entries to INDEX.md."""
    if not items:
        return

    # Determine emoji prefix
    emoji_map = {"memory": "🔬", "llm": "🤖", "agent": "🧠", "news": "📰"}
    emoji = emoji_map.get(board, "📄")

    # Build new entries
    new_lines = []
    for item in items:
        title = item.get("title", "Untitled")
        item_id = item.get("id", "")
        url = item.get("url", "")
        item_date = item.get("date", "")

        # Generate relative path to wiki page
        if board in ("memory", "llm", "agent"):
            filename = safe_filename(title) + ".md"
            page_path = f"papers/{filename}"
        else:
            filename = safe_filename(title) + ".md"
            page_path = f"news/{filename}"

        # Format: - 🔬 [Title](path) | authors | date | source
        authors_str = ", ".join(item.get("authors", [])[:3])
        entry = f"- {emoji} [{title}]({page_path}) | {authors_str} | {item_date}"
        new_lines.append(entry)

    # Read existing index
    content = ""
    if os.path.exists(index_path):
        with open(index_path, encoding="utf-8") as f:
            content = f.read()

    # Find the insertion point (after the month header or at end)
    month_header = f"## {date[:4]}-{date[5:7]}"
    if month_header in content:
        # Insert after the month header comment
        marker = "<!-- 新论文追加到此行下方 -->" if "papers" in index_path else "<!-- 新资讯追加到此行下方 -->"
        if marker in content:
            content = content.replace(marker, marker + "\n" + "\n".join(new_lines))
        else:
            content += "\n" + "\n".join(new_lines) + "\n"
    else:
        # Add new month section
        content += f"\n{month_header}\n\n" + "\n".join(new_lines) + "\n"

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(content)


def update_log(log_path: str, board: str, date: str, count: int):
    """Append entry to LOG.md."""
    emoji_map = {"memory": "🔬", "llm": "🤖", "agent": "🧠", "news": "📰"}
    emoji = emoji_map.get(board, "📄")

    entry = f"| {date} | 入库 | {count} | {emoji} {board} |\n"

    content = ""
    if os.path.exists(log_path):
        with open(log_path, encoding="utf-8") as f:
            content = f.read()

    content += entry

    with open(log_path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    parser = argparse.ArgumentParser(description="Step 3: Wiki ingest")
    parser.add_argument("--input", required=True, help="Path to 02-new-papers.json or 02-dedup.json")
    parser.add_argument("--board", required=True, choices=["memory", "llm", "agent", "news", "builders"])
    parser.add_argument("--date", required=True, help="Date YYYY-MM-DD")
    parser.add_argument("--kb-root", default="kb", help="kb/ root path (default: kb)")

    args = parser.parse_args()

    # Load input
    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("items", [])

    # Determine paths
    is_academic = args.board in ("memory", "llm", "agent")
    if is_academic:
        pages_dir = os.path.join(args.kb_root, "papers", "papers")
        index_path = os.path.join(args.kb_root, "papers", "INDEX.md")
        log_path = os.path.join(args.kb_root, "papers", "LOG.md")
    else:
        pages_dir = os.path.join(args.kb_root, "tech-news", "news")
        index_path = os.path.join(args.kb_root, "tech-news", "INDEX.md")
        log_path = os.path.join(args.kb_root, "tech-news", "LOG.md")

    os.makedirs(pages_dir, exist_ok=True)

    # Generate pages
    created = 0
    for item in items:
        title = item.get("title", "Untitled")
        filename = safe_filename(title) + ".md"
        filepath = os.path.join(pages_dir, filename)

        if os.path.exists(filepath):
            print(f"  Skip (exists): {filename}")
            continue

        if is_academic:
            content = generate_paper_page(item, args.board)
        else:
            content = generate_news_page(item)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        created += 1

    # Update INDEX.md
    update_index(index_path, items, args.board, args.date)

    # Update LOG.md
    update_log(log_path, args.board, args.date, len(items))

    print(f"Wiki ingest: {created} pages created, {len(items)} entries added to INDEX.md")
    print(f"  Pages: {pages_dir}")
    print(f"  Index: {index_path}")


if __name__ == "__main__":
    main()
