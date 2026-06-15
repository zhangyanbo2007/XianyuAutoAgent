"""HuggingFace Trending collector — fetches trending models."""

from datetime import datetime, timedelta, timezone
from typing import Optional

import requests

CST = timezone(timedelta(hours=8))


def collect(
    board: str,
    config: dict,
    date: str,
    proxy: Optional[str] = None,
) -> list[dict]:
    """Collect HuggingFace trending models for a board.

    Args:
        board: Board name (news)
        config: Full sources.json config
        date: Target date (YYYY-MM-DD)
        proxy: HTTP proxy URL

    Returns:
        List of model dicts in unified format.
    """
    hf_cfg = config.get("huggingface", {})
    limit = hf_cfg.get("limit", 20)
    date_range_days = config.get("date_range_days", 1)

    try:
        target_dt = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        target_dt = datetime.now(CST)
    cutoff = target_dt - timedelta(days=date_range_days)

    proxies = {"http": proxy, "https": proxy} if proxy else None
    api_url = f"https://huggingface.co/api/models?sort=lastModified&direction=-1&limit={limit * 3}"

    try:
        resp = requests.get(api_url, timeout=30, proxies=proxies, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        models = resp.json()
    except Exception as e:
        print(f"[huggingface] Error fetching trending: {e}")
        return []

    all_items = []
    for model in models:
        model_id = model.get("id", "")
        if not model_id:
            continue

        # Filter by lastModified date
        last_modified = model.get("lastModified", "")
        date_str = ""
        if last_modified:
            try:
                dt = datetime.fromisoformat(last_modified.replace("Z", "+00:00"))
                date_str = dt.strftime("%Y-%m-%d")
                if dt.replace(tzinfo=None) < cutoff:
                    continue
            except ValueError:
                pass

        all_items.append({
            "id": f"huggingface:{model_id}",
            "title": model_id,
            "url": f"https://huggingface.co/{model_id}",
            "authors": [model_id.split("/")[0] if "/" in model_id else ""],
            "date": date_str,
            "source": "huggingface",
            "source_category": model.get("pipeline_tag", ""),
            "abstract": f"Downloads: {model.get('downloads', 0):,} | Likes: {model.get('likes', 0):,}",
            "tags": [],
            "board_match": [board],
            "collected_by": "huggingface_collector",
        })

        if len(all_items) >= limit:
            break

    print(f"[huggingface] Board={board}: collected {len(all_items)} models")
    return all_items
