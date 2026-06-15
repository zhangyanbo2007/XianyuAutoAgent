#!/usr/bin/env python3
"""Batch fetch images for every entry in a daily report — accurate version.

Strategy per source type:
- arXiv papers: download PDF first page via pdf2image (unique per paper)
- News/blog: og:image from article URL (unique per article)
- bioRxiv: og:image from article page
- No image found: skip (don't add wrong placeholder)

Usage:
  fetch_all_images.py --report 05-report.md --data 01-search.json --workspace /path --proxy URL --board memory
"""

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def download_bytes(url: str, proxy: str = None, timeout: int = 20) -> bytes | None:
    proxies = {"http": proxy, "https": proxy} if proxy else None
    try:
        resp = requests.get(url, timeout=timeout, proxies=proxies, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })
        resp.raise_for_status()
        ct = resp.headers.get("Content-Type", "")
        if "svg" in ct or "webp" in ct:
            return None
        if len(resp.content) < 1000:
            return None
        return resp.content
    except Exception:
        return None


def fetch_arxiv_figure(arxiv_id: str, workspace: str, proxy: str = None) -> str | None:
    """Fetch paper figure from arXiv HTML version using wget."""
    import subprocess
    html_url = f"https://arxiv.org/html/{arxiv_id}v1"
    proxies = {"http": proxy, "https": proxy} if proxy else None

    # Step 1: Fetch HTML page
    try:
        resp = requests.get(html_url, timeout=30, proxies=proxies, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            return None
        html = resp.text
    except Exception as e:
        print(f"  arXiv HTML fetch failed: {arxiv_id} ({e})")
        return None

    # Step 2: Find figure images
    figures = re.findall(r'<figure[^>]*>.*?<img[^>]+src="([^"]+)"', html, re.DOTALL)

    # Step 3: Download each figure via wget (more reliable than requests)
    env = os.environ.copy()
    if proxy:
        env["http_proxy"] = proxy
        env["https_proxy"] = proxy

    for img_url in figures:
        if any(skip in img_url.lower() for skip in ['logo', 'icon', 'badge', 'button', 'avatar', 'arxiv']):
            continue
        if not img_url.startswith('http'):
            img_url = urljoin(html_url, img_url)

        img_path = os.path.join(workspace, f"arxiv-{arxiv_id}.png")
        cmd = ["wget", "-q", "--timeout=30", "-O", img_path, img_url]
        if proxy:
            cmd.extend(["--proxy", proxy])

        try:
            result = subprocess.run(cmd, capture_output=True, timeout=60, env=env)
            if os.path.exists(img_path) and os.path.getsize(img_path) > 5000:
                return img_path
        except Exception:
            continue

    return None


def fetch_og_image(url: str, proxy: str = None) -> str | None:
    """Fetch og:image from a page URL. Returns remote URL or None."""
    proxies = {"http": proxy, "https": proxy} if proxy else None
    try:
        resp = requests.get(url, timeout=15, proxies=proxies, headers={
            "User-Agent": "Mozilla/5.0",
        }, allow_redirects=True)
        resp.raise_for_status()
        html = resp.text[:50000]

        patterns = [
            r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']',
            r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']',
            r'<meta[^>]*name=["\']twitter:image["\'][^>]*content=["\']([^"\']+)["\']',
        ]
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                img_url = match.group(1)
                if not img_url.startswith("http"):
                    img_url = urljoin(url, img_url)
                return img_url
    except Exception:
        pass
    return None


def main():
    parser = argparse.ArgumentParser(description="Fetch images for daily report (accurate)")
    parser.add_argument("--report", required=True, help="Path to 05-report.md")
    parser.add_argument("--data", required=True, help="Path to 01-search.json or 02-new-papers.json")
    parser.add_argument("--workspace", required=True, help="Workspace directory")
    parser.add_argument("--proxy", default="", help="HTTP proxy")
    parser.add_argument("--board", default="memory", help="Board name")

    args = parser.parse_args()
    images_dir = os.path.join(args.workspace, "05-images")
    ensure_dir(images_dir)

    with open(args.report, encoding="utf-8") as f:
        report = f.read()

    with open(args.data, encoding="utf-8") as f:
        data = json.load(f)

    # Build URL lookup: title_keyword → url
    items = data.get("items", [])
    url_lookup = {}
    for item in items:
        title = item.get("title", "")
        url = item.get("url", "")
        if title and url:
            key = " ".join(title.lower().split()[:5])
            url_lookup[key] = url

    # Find all #### entries
    entries = re.findall(r'#### \d+\.\s*(.+?)(?:\n|$)', report)
    source_urls = re.findall(r'> 🏠.*?\]\((https?://[^)]+)\)', report)

    print(f"Found {len(entries)} entries, {len(source_urls)} source URLs")

    downloaded = 0
    used_images = set()  # Track which images we've already used

    for i, entry_title in enumerate(entries):
        # Skip if entry already has an image
        entry_pos = report.find(f"#### {i+1}.")
        next_entry = report.find(f"#### {i+2}.", entry_pos + 1) if f"#### {i+2}." in report[entry_pos+1:] else len(report)
        # Also check for ### or ## as section boundaries
        next_section = len(report)
        for marker in ["### ", "## "]:
            pos = report.find(marker, entry_pos + 5)
            if pos > 0 and pos < next_section:
                next_section = pos
        entry_end = min(next_entry, next_section)
        entry_block = report[entry_pos:entry_end]
        if re.search(r'!\[', entry_block):
            continue  # Already has image

        # Find source URL for this entry
        source_url = ""
        if i < len(source_urls):
            source_url = source_urls[i]
        else:
            for key, url in url_lookup.items():
                if any(w in entry_title.lower() for w in key.split()[:3]):
                    source_url = url
                    break

        if not source_url:
            print(f"  SKIP (no URL): {entry_title[:60]}")
            continue

        img_path = None

        # Strategy 1: arXiv paper → download PDF first page
        arxiv_match = re.search(r'arxiv\.org/abs/(\d{4}\.\d{4,5})', source_url)
        if arxiv_match:
            arxiv_id = arxiv_match.group(1)
            print(f"  arXiv figure: {arxiv_id} — {entry_title[:50]}...")
            img_path = fetch_arxiv_figure(arxiv_id, images_dir, proxy=args.proxy)
            if img_path:
                downloaded += 1
                print(f"    OK: {os.path.basename(img_path)}")
            else:
                print(f"    No figure extracted")
        else:
            # Strategy 2: News/blog → og:image
            print(f"  og:image: {entry_title[:50]}...")
            img_url = fetch_og_image(source_url, proxy=args.proxy)
            if img_url:
                # Skip if we already downloaded this exact image
                url_hash = hashlib.md5(img_url.encode()).hexdigest()[:8]
                if url_hash in used_images:
                    print(f"    Skip (duplicate): {img_url[:60]}")
                    continue
                used_images.add(url_hash)

                img_data = download_bytes(img_url, proxy=args.proxy)
                if img_data:
                    ct = img_url.lower()
                    ext = ".png" if ".png" in ct else ".jpg"
                    filename = f"entry-{downloaded:02d}{ext}"
                    filepath = os.path.join(images_dir, filename)
                    with open(filepath, "wb") as f:
                        f.write(img_data)
                    downloaded += 1
                    print(f"    OK: {filename} ({len(img_data):,} bytes)")
                else:
                    print(f"    Download failed")
            else:
                print(f"    No og:image found")

    print(f"\nTotal downloaded: {downloaded} images")


if __name__ == "__main__":
    main()
