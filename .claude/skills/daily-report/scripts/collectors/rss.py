"""RSS feed collector — fetches and parses RSS feeds for multiple boards."""

import re
from datetime import datetime, timedelta, timezone
from typing import Optional

import feedparser
import requests

CST = timezone(timedelta(hours=8))


def _strip_html(text: str) -> str:
    """Crude HTML tag removal, first 500 chars."""
    text = re.sub(r"<[^>]+>", "", text)
    text = text.strip()
    if len(text) > 500:
        text = text[:500] + "..."
    return text


def _parse_entry(entry: dict, source_name: str, source_category: str) -> Optional[dict]:
    """Parse a single RSS entry into unified format."""
    title = getattr(entry, "title", "") or ""
    link = getattr(entry, "link", "") or ""
    summary = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
    summary = _strip_html(summary)

    # Parse date
    published = ""
    if hasattr(entry, "published") and entry.published:
        published = entry.published
    elif hasattr(entry, "updated") and entry.updated:
        published = entry.updated

    date_str = ""
    if published:
        # Try common formats
        for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"]:
            try:
                dt = datetime.strptime(published.strip(), fmt)
                date_str = dt.strftime("%Y-%m-%d")
                break
            except ValueError:
                continue
        if not date_str and len(published) >= 10:
            date_str = published[:10]

    if not title and not link:
        return None

    # Generate unique ID from URL or title
    item_id = link if link else f"rss:{source_name}:{hash(title) & 0xFFFFFFFF:08x}"

    return {
        "id": item_id,
        "title": title.strip(),
        "url": link,
        "authors": [],
        "date": date_str,
        "source": source_name.lower().replace(" ", "-"),
        "source_category": source_category,
        "abstract": summary,
        "tags": [],
        "board_match": [],
        "collected_by": "rss_collector",
    }


def collect(
    board: str,
    config: dict,
    date: str,
    proxy: Optional[str] = None,
    max_entries_per_feed: int = 30,
) -> list[dict]:
    """Collect RSS entries for a given board.

    Args:
        board: Board name (memory, llm, agent, news)
        config: Full sources.json config
        date: Target date (YYYY-MM-DD)
        proxy: HTTP proxy URL
        max_entries_per_feed: Max entries to keep per feed (prevents flood)

    Returns:
        List of entry dicts in unified format.
    """
    date_range_days = config.get("date_range_days", 1)
    rss_feeds = config.get("rss_feeds", [])

    try:
        target_dt = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        target_dt = datetime.now(CST)
    cutoff = target_dt - timedelta(days=date_range_days)

    proxies = {"http": proxy, "https": proxy} if proxy else None
    all_items = []

    for feed_cfg in rss_feeds:
        # Filter by board
        feed_boards = feed_cfg.get("boards", [])
        if feed_boards and board not in feed_boards:
            continue

        url = feed_cfg.get("url", "")
        name = feed_cfg.get("name", "unknown")
        category = feed_cfg.get("category", "unknown")

        if not url:
            continue

        try:
            resp = requests.get(
                url,
                timeout=30,
                proxies=proxies,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/rss+xml,application/xml,text/xml,*/*",
                },
            )
            resp.raise_for_status()
            parsed = feedparser.parse(resp.content)
        except Exception as e:
            print(f"[rss] Error fetching {name}: {e}")
            continue

        count = 0
        for entry in parsed.entries:
            if count >= max_entries_per_feed:
                break

            item = _parse_entry(entry, name, category)
            if item is None:
                continue

            # Filter by date
            if item["date"]:
                try:
                    item_dt = datetime.strptime(item["date"], "%Y-%m-%d")
                    if item_dt < cutoff:
                        continue
                except ValueError:
                    pass

            item["board_match"] = [board]
            all_items.append(item)
            count += 1

        print(f"[rss] {name}: collected {count} entries")

    print(f"[rss] Board={board}: collected {len(all_items)} total entries")
    return all_items
