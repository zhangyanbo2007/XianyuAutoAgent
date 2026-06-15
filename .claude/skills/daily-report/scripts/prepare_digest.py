#!/usr/bin/env python3
"""
Tech News Daily Report - Deterministic Data Fetching Script

Fetches RSS feeds, GitHub releases, and HuggingFace trending models,
outputs a structured JSON blob for downstream LLM processing.
"""

import json
import sys
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
import feedparser


CST = timezone(timedelta(hours=8))


def load_config():
    """Read sources.json from config/ dir, determine skill_dir from script location."""
    script_dir = Path(__file__).resolve().parent
    skill_dir = script_dir.parent
    config_path = skill_dir / "config" / "sources.json"

    if not config_path.exists():
        print(json.dumps({
            "status": "error",
            "generated_at": datetime.now(CST).isoformat(),
            "errors": [f"Config file not found: {config_path}"],
        }))
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    return config


def fetch_rss_feed(url, name, category, proxy=None):
    """
    Fetch and parse an RSS feed. Uses requests (with proxy support) to fetch
    the raw content, then feedparser to parse it.

    Returns a list of article dicts:
      {title, url, summary, published_date, source_name, category}
    """
    articles = []
    proxies = {"http": proxy, "https": proxy} if proxy else None

    try:
        resp = requests.get(url, timeout=30, proxies=proxies, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "application/rss+xml,application/xml,text/xml,*/*",
        })
        resp.raise_for_status()
        parsed = feedparser.parse(resp.content)

        for entry in parsed.entries:
            published_date = ""
            if hasattr(entry, "published") and entry.published:
                published_date = entry.published
            elif hasattr(entry, "updated") and entry.updated:
                published_date = entry.updated

            summary = ""
            if hasattr(entry, "summary") and entry.summary:
                summary = entry.summary
            elif hasattr(entry, "description") and entry.description:
                summary = entry.description
            # Strip HTML tags crudely - take first 500 chars
            import re
            summary = re.sub(r"<[^>]+>", "", summary).strip()
            if len(summary) > 500:
                summary = summary[:500] + "..."

            link = ""
            if hasattr(entry, "link") and entry.link:
                link = entry.link

            title = ""
            if hasattr(entry, "title") and entry.title:
                title = entry.title

            if title or link:
                articles.append({
                    "title": title,
                    "url": link,
                    "summary": summary,
                    "published_date": published_date,
                    "source_name": name,
                    "category": category,
                })

    except Exception as e:
        return {"error": f"Failed to fetch RSS feed '{name}' from {url}: {e}"}

    return articles


def fetch_github_releases(owner, repo, proxy=None):
    """
    Fetch recent GitHub releases for a repo.

    Returns a list of release dicts:
      {tag_name, name, url, published_at, body_preview, repo}
    """
    api_url = f"https://api.github.com/repos/{owner}/{repo}/releases?per_page=3"
    proxies = {"http": proxy, "https": proxy} if proxy else None
    headers = {"Accept": "application/vnd.github+json"}

    releases = []

    try:
        resp = requests.get(api_url, timeout=30, proxies=proxies, headers=headers)
        resp.raise_for_status()
        data = resp.json()

        for release in data:
            body_preview = ""
            if release.get("body"):
                body_preview = release["body"][:200]
                if len(release["body"]) > 200:
                    body_preview += "..."

            releases.append({
                "tag_name": release.get("tag_name", ""),
                "name": release.get("name", ""),
                "url": release.get("html_url", ""),
                "published_at": release.get("published_at", ""),
                "body_preview": body_preview,
                "repo": f"{owner}/{repo}",
            })

    except Exception as e:
        return {"error": f"Failed to fetch GitHub releases for {owner}/{repo}: {e}"}

    return releases


def fetch_huggingface_trending(limit=20, proxy=None):
    """
    Fetch trending models from HuggingFace.

    Returns a list of model dicts:
      {model_id, downloads, likes, pipeline_tag, url}
    """
    api_url = f"https://huggingface.co/api/models?limit={limit}"
    proxies = {"http": proxy, "https": proxy} if proxy else None

    models = []

    try:
        resp = requests.get(api_url, timeout=30, proxies=proxies, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        data = resp.json()

        for model in data:
            model_id = model.get("id", "")
            url = f"https://huggingface.co/{model_id}" if model_id else ""

            models.append({
                "model_id": model_id,
                "downloads": model.get("downloads", 0),
                "likes": model.get("likes", 0),
                "pipeline_tag": model.get("pipeline_tag", ""),
                "url": url,
            })

    except Exception as e:
        return {"error": f"Failed to fetch HuggingFace trending models: {e}"}

    return models


def main():
    """Orchestrate all fetches, build output JSON, print to stdout."""
    config = load_config()

    proxy = config.get("proxy")
    today = datetime.now(CST)
    today_date = today.strftime("%Y-%m-%d")

    errors = []
    rss_articles = []
    github_releases = []
    huggingface_models = []

    # --- RSS Feeds ---
    for feed_cfg in config.get("rss_feeds", []):
        result = fetch_rss_feed(
            url=feed_cfg["url"],
            name=feed_cfg["name"],
            category=feed_cfg["category"],
            proxy=proxy,
        )
        if isinstance(result, dict) and "error" in result:
            errors.append(result["error"])
        else:
            rss_articles.extend(result)

    # --- GitHub Releases ---
    for repo_cfg in config.get("github_repos", []):
        result = fetch_github_releases(
            owner=repo_cfg["owner"],
            repo=repo_cfg["repo"],
            proxy=proxy,
        )
        if isinstance(result, dict) and "error" in result:
            errors.append(result["error"])
        else:
            github_releases.extend(result)

    # --- HuggingFace Trending ---
    hf_cfg = config.get("huggingface_models", {})
    hf_limit = hf_cfg.get("limit", 20)
    result = fetch_huggingface_trending(limit=hf_limit, proxy=proxy)
    if isinstance(result, dict) and "error" in result:
        errors.append(result["error"])
    else:
        huggingface_models.extend(result)

    # --- Sources that need LLM search (no RSS) ---
    needs_llm_search = [
        {"source": "Anthropic 官方博客", "url": "https://anthropic.com/news", "reason": "No RSS feed"},
        {"source": "OpenAI 官方博客", "url": "https://openai.com/blog", "reason": "No RSS feed"},
        {"source": "Meta AI 官方博客", "url": "https://ai.meta.com/blog", "reason": "No RSS feed"},
        {"source": "Mistral 官方新闻", "url": "https://mistral.ai/news", "reason": "No RSS feed"},
        {"source": "Cohere 官方博客", "url": "https://cohere.com/blog", "reason": "No RSS feed"},
        {"source": "xAI", "url": "https://x.ai", "reason": "No RSS feed"},
        {"source": "百度/文心", "url": "https://baidu.com", "reason": "No RSS feed, Chinese company"},
        {"source": "阿里/Qwen", "url": "https://qwenlm.github.io", "reason": "No RSS feed, Chinese company"},
        {"source": "字节/Doubao", "url": "https://bytedance.com", "reason": "No RSS feed, Chinese company"},
        {"source": "腾讯/混元", "url": "https://tencent.com", "reason": "No RSS feed, Chinese company"},
        {"source": "月之暗面/Kimi", "url": "https://moonshot.cn", "reason": "No RSS feed, Chinese company"},
        {"source": "DeepSeek", "url": "https://deepseek.com", "reason": "No RSS feed, Chinese company"},
        {"source": "智谱/GLM", "url": "https://zhipuai.cn", "reason": "No RSS feed, Chinese company"},
        {"source": "MiniMax/海螺AI", "url": "https://minimax.com", "reason": "No RSS feed, Chinese company"},
        {"source": "商汤/日日新", "url": "https://sensetime.com", "reason": "No RSS feed, Chinese company"},
        {"source": "昆仑万维/天工", "url": "https://kunlun.com", "reason": "No RSS feed, Chinese company"},
    ]

    # --- Build output ---
    output = {
        "status": "ok" if not errors else "partial",
        "generated_at": today.isoformat(),
        "config": {
            "date": today_date,
            "proxy": proxy,
        },
        "rss_articles": rss_articles,
        "github_releases": github_releases,
        "huggingface_models": huggingface_models,
        "needs_llm_search": needs_llm_search,
        "stats": {
            "rss_articles_count": len(rss_articles),
            "github_releases_count": len(github_releases),
            "huggingface_models_count": len(huggingface_models),
            "needs_llm_search_count": len(needs_llm_search),
        },
        "errors": errors,
    }

    # If all fetches failed, mark status as error
    if not rss_articles and not github_releases and not huggingface_models and errors:
        output["status"] = "error"

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()