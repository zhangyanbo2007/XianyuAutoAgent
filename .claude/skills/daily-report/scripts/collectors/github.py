"""GitHub Releases collector — fetches recent releases for tracked repos."""

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
    """Collect GitHub releases for a given board.

    Args:
        board: Board name (news)
        config: Full sources.json config
        date: Target date (YYYY-MM-DD)
        proxy: HTTP proxy URL

    Returns:
        List of release dicts in unified format.
    """
    repos = config.get("github_repos", [])
    date_range_days = config.get("date_range_days", 1)

    try:
        target_dt = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        target_dt = datetime.now(CST)
    cutoff = target_dt - timedelta(days=date_range_days)

    proxies = {"http": proxy, "https": proxy} if proxy else None
    all_items = []

    for repo_cfg in repos:
        repo_boards = repo_cfg.get("boards", [])
        if repo_boards and board not in repo_boards:
            continue

        owner = repo_cfg.get("owner", "")
        repo = repo_cfg.get("repo", "")
        if not owner or not repo:
            continue

        api_url = f"https://api.github.com/repos/{owner}/{repo}/releases?per_page=5"
        headers = {"Accept": "application/vnd.github+json"}

        try:
            resp = requests.get(api_url, timeout=30, proxies=proxies, headers=headers)
            resp.raise_for_status()
            releases = resp.json()
        except Exception as e:
            print(f"[github] Error fetching {owner}/{repo}: {e}")
            continue

        count = 0
        for release in releases:
            published_at = release.get("published_at", "")
            date_str = ""
            if published_at:
                try:
                    dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                    date_str = dt.strftime("%Y-%m-%d")
                    if dt.replace(tzinfo=None) < cutoff:
                        continue
                except ValueError:
                    pass

            tag = release.get("tag_name", "")
            name = release.get("name", "") or tag
            body = release.get("body", "") or ""
            body_preview = body[:300] + "..." if len(body) > 300 else body

            all_items.append({
                "id": f"github:{owner}/{repo}:{tag}",
                "title": f"{owner}/{repo} {name}",
                "url": release.get("html_url", ""),
                "authors": [owner],
                "date": date_str,
                "source": "github",
                "source_category": "release",
                "abstract": body_preview,
                "tags": [],
                "board_match": [board],
                "collected_by": "github_collector",
            })
            count += 1

        print(f"[github] {owner}/{repo}: collected {count} releases")

    print(f"[github] Board={board}: collected {len(all_items)} total releases")
    return all_items
