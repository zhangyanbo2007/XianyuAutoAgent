"""OpenReview API collector — fetches papers from ICLR and other venues."""

from datetime import datetime, timedelta, timezone
from typing import Optional

import requests

CST = timezone(timedelta(hours=8))
OPENREVIEW_API = "https://api2.openreview.net/notes"


def collect(
    board: str,
    config: dict,
    date: str,
    proxy: Optional[str] = None,
) -> list[dict]:
    """Collect papers from OpenReview for a given board.

    Uses the v2 API with invitation parameter (content.venue doesn't work).

    Args:
        board: Board name (memory, llm, agent)
        config: Full sources.json config
        date: Target date (YYYY-MM-DD)
        proxy: HTTP proxy URL

    Returns:
        List of paper dicts in unified format.
    """
    or_cfg = config.get("openreview", {})
    venues = or_cfg.get("venues", [])
    keywords = or_cfg.get("keywords", [])
    date_range_days = config.get("date_range_days", 1)

    if not venues:
        return []

    try:
        target_dt = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        target_dt = datetime.now(CST)
    cutoff = target_dt - timedelta(days=date_range_days)

    proxies = {"http": proxy, "https": proxy} if proxy else None
    all_papers = []
    seen_ids = set()

    for venue in venues:
        # Build invitation strings for v2 API
        # Try common formats: "ICLR.cc/2026/Conference/-/Submission"
        invitations = [
            f"{venue}/-/Submission",
            f"{venue}/-/Blind_Submission",
        ]

        for invitation in invitations:
            params = {
                "invitation": invitation,
                "limit": 100,
                "offset": 0,
            }

            try:
                resp = requests.get(
                    OPENREVIEW_API,
                    params=params,
                    timeout=30,
                    proxies=proxies,
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"[openreview] Error fetching {invitation}: {e}")
                continue

            notes = data.get("notes", [])
            if not notes:
                continue

            print(f"[openreview] {invitation}: found {len(notes)} papers")

            for note in notes:
                content = note.get("content", {})

                # Extract title
                title_field = content.get("title", {})
                title = title_field.get("value", "") if isinstance(title_field, dict) else str(title_field)

                # Extract abstract
                abstract_field = content.get("abstract", {})
                abstract = abstract_field.get("value", "") if isinstance(abstract_field, dict) else str(abstract_field)

                # Extract authors
                authors_field = content.get("authors", {})
                authors = authors_field.get("value", []) if isinstance(authors_field, dict) else (authors_field if isinstance(authors_field, list) else [])

                # Paper ID
                note_id = note.get("id", "")
                paper_id = f"openreview:{note_id}"

                if paper_id in seen_ids:
                    continue
                seen_ids.add(paper_id)

                # Keyword filter
                if keywords:
                    title_lower = title.lower()
                    abstract_lower = abstract.lower()
                    combined = title_lower + " " + abstract_lower
                    if not any(kw.lower() in combined for kw in keywords):
                        continue

                # Date: use cdate as reference but don't filter by it
                # (venue filtering already guarantees relevance)
                date_str = ""
                cdate = note.get("cdate", 0)
                if cdate:
                    try:
                        dt = datetime.fromtimestamp(cdate / 1000, tz=timezone.utc)
                        date_str = dt.strftime("%Y-%m-%d")
                    except (ValueError, OSError):
                        pass

                # URL
                forum = note.get("forum", note_id)
                url = f"https://openreview.net/forum?id={forum}"

                # Venue
                venue_field = content.get("venue", {})
                venue_name = venue_field.get("value", venue) if isinstance(venue_field, dict) else str(venue_field)

                all_papers.append({
                    "id": paper_id,
                    "title": title,
                    "url": url,
                    "authors": authors[:5],
                    "date": date_str,
                    "source": "openreview",
                    "source_category": venue_name,
                    "abstract": abstract[:2000],
                    "tags": [],
                    "board_match": [board],
                    "collected_by": "openreview_collector",
                })

    print(f"[openreview] Board={board}: collected {len(all_papers)} papers")
    return all_papers
