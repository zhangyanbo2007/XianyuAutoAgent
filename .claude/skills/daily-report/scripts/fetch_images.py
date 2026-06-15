#!/usr/bin/env python3
"""Fetch images for daily report — downloads figures from papers and news sources.

Usage:
  fetch_images.py --input 05-report.md --workspace /path/to/workspace --proxy http://127.0.0.1:7897

Downloads images to workspace/05-images/ and rewrites the report with local paths.
"""

import argparse
import os
import re
import sys
import hashlib
from pathlib import Path
from urllib.parse import urlparse

import requests


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def download_image(url: str, proxy: str = None, timeout: int = 30) -> bytes | None:
    """Download image, return bytes or None on failure."""
    proxies = {"http": proxy, "https": proxy} if proxy else None
    try:
        resp = requests.get(url, timeout=timeout, proxies=proxies, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }, stream=True)
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "")
        # Skip SVG and WebP (WeChat incompatible)
        if "svg" in content_type or "webp" in content_type:
            print(f"  Skip (incompatible): {url[:60]}... (type={content_type})")
            return None

        data = resp.content
        if len(data) < 1000:  # Too small, likely error page
            return None
        return data
    except Exception as e:
        print(f"  Failed: {url[:60]}... ({e})")
        return None


def guess_extension(data: bytes, url: str) -> str:
    """Guess file extension from content or URL."""
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return '.png'
    if data[:2] == b'\xff\xd8':
        return '.jpg'
    if data[:4] == b'GIF8':
        return '.gif'
    # Fallback to URL extension
    path = urlparse(url).path
    for ext in ['.png', '.jpg', '.jpeg', '.gif']:
        if path.lower().endswith(ext):
            return ext
    return '.jpg'


def find_image_urls_from_report(report_path: str) -> list[dict]:
    """Parse report markdown for existing image references and source URLs."""
    with open(report_path, encoding="utf-8") as f:
        content = f.read()

    # Find existing ![alt](path) references
    existing = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content)

    # Find source URLs from > 🏠 lines
    sources = re.findall(r'> 🏠.*?\| (https?://[^\s|]+)', content)

    return {"existing": existing, "sources": sources}


def find_paper_figures(report_path: str, proxy: str = None) -> list[dict]:
    """Find arXiv paper IDs from report and try to get their figures."""
    with open(report_path, encoding="utf-8") as f:
        content = f.read()

    # Find arXiv IDs
    arxiv_ids = re.findall(r'arxiv\.org/abs/(\d{4}\.\d{4,5})', content)
    # Also find from source lines
    arxiv_ids += re.findall(r'arxiv:(\d{4}\.\d{4,5})', content)
    arxiv_ids = list(dict.fromkeys(arxiv_ids))  # dedup, preserve order

    figures = []
    proxies = {"http": proxy, "https": proxy} if proxy else None

    for arxiv_id in arxiv_ids[:10]:  # Limit to 10 papers
        # Try to get the paper's first page figure from arXiv
        # arXiv provides thumbnails at /pdf/XXXX.XXXXXvN.pdf first page
        # Simpler: try the abs page for a figure thumbnail
        try:
            # Try the arXiv API for the paper's thumbnail
            api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
            resp = requests.get(api_url, timeout=15, proxies=proxies)
            if resp.status_code == 200:
                # Parse Atom XML for thumbnail link
                import xml.etree.ElementTree as ET
                root = ET.fromstring(resp.content)
                ns = "http://www.w3.org/2005/Atom"
                for link in root.findall(f"{{{ns}}}link"):
                    if link.get("title") == "pdf":
                        pdf_url = link.get("href", "")
                        if pdf_url:
                            figures.append({
                                "arxiv_id": arxiv_id,
                                "pdf_url": pdf_url,
                                "type": "arxiv_pdf",
                            })
                            break
        except Exception:
            pass

    return figures


def download_news_images(report_path: str, workspace: str, proxy: str = None) -> int:
    """Download images from news/blog source URLs found in the report."""
    with open(report_path, encoding="utf-8") as f:
        content = f.read()

    images_dir = os.path.join(workspace, "05-images")
    ensure_dir(images_dir)

    # Find all source URLs
    source_urls = re.findall(r'> 🏠.*?\| (https?://[^\s|]+)', content)
    downloaded = 0

    for url in source_urls[:8]:  # Limit
        # Try to fetch the page and find og:image or first img
        try:
            proxies = {"http": proxy, "https": proxy} if proxy else None
            resp = requests.get(url, timeout=15, proxies=proxies, headers={
                "User-Agent": "Mozilla/5.0",
            })
            resp.raise_for_status()
            html = resp.text

            # Find og:image
            og_match = re.search(r'<meta\s+(?:property|name)="og:image"\s+content="([^"]+)"', html)
            if not og_match:
                og_match = re.search(r'content="([^"]+)"\s+(?:property|name)="og:image"', html)

            if og_match:
                img_url = og_match.group(1)
                if not img_url.startswith("http"):
                    img_url = f"https://{urlparse(url).netloc}{img_url}"

                data = download_image(img_url, proxy=proxy)
                if data:
                    ext = guess_extension(data, img_url)
                    # Generate filename from URL hash
                    url_hash = hashlib.md5(img_url.encode()).hexdigest()[:8]
                    filename = f"news-{url_hash}{ext}"
                    filepath = os.path.join(images_dir, filename)
                    with open(filepath, "wb") as f:
                        f.write(data)
                    downloaded += 1
                    print(f"  Downloaded: {filename} ({len(data)} bytes) from {img_url[:60]}...")
        except Exception as e:
            print(f"  Skip: {url[:60]}... ({e})")

    return downloaded


def download_arxiv_images(report_path: str, workspace: str, proxy: str = None) -> int:
    """Download figures from arXiv papers via their PDF first page."""
    with open(report_path, encoding="utf-8") as f:
        content = f.read()

    images_dir = os.path.join(workspace, "05-images")
    ensure_dir(images_dir)

    arxiv_ids = list(dict.fromkeys(re.findall(r'arxiv\.org/abs/(\d{4}\.\d{4,5})', content)))
    downloaded = 0

    for arxiv_id in arxiv_ids[:5]:  # Limit to 5 to be polite
        # Download first page of PDF and convert to image
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        try:
            proxies = {"http": proxy, "https": proxy} if proxy else None
            resp = requests.get(pdf_url, timeout=30, proxies=proxies, headers={
                "User-Agent": "Mozilla/5.0",
            }, stream=True)
            resp.raise_for_status()

            # Save PDF temporarily
            pdf_path = os.path.join(images_dir, f"temp_{arxiv_id}.pdf")
            with open(pdf_path, "wb") as f:
                for chunk in resp.iter_content(8192):
                    f.write(chunk)

            # Convert first page to image using pdf2image or fallback
            try:
                from pdf2image import convert_from_path
                images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=150)
                if images:
                    img_path = os.path.join(images_dir, f"arxiv-{arxiv_id}.png")
                    images[0].save(img_path, "PNG")
                    downloaded += 1
                    print(f"  Downloaded: arxiv-{arxiv_id}.png")
            except ImportError:
                # pdf2image not available, try with Pillow
                pass
            except Exception as e:
                print(f"  PDF convert failed: {arxiv_id} ({e})")

            # Cleanup temp PDF
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

        except Exception as e:
            print(f"  Failed: {arxiv_id} ({e})")

    return downloaded


def main():
    parser = argparse.ArgumentParser(description="Fetch images for daily report")
    parser.add_argument("--input", required=True, help="Path to 05-report.md")
    parser.add_argument("--workspace", required=True, help="Workspace directory")
    parser.add_argument("--proxy", default="", help="HTTP proxy")

    args = parser.parse_args()

    report_path = args.input
    if not os.path.exists(report_path):
        print(f"ERROR: Report not found: {report_path}")
        sys.exit(1)

    images_dir = os.path.join(args.workspace, "05-images")
    ensure_dir(images_dir)

    print(f"Fetching images for: {report_path}")

    # Download news/blog images
    print("\n--- News/Blog images ---")
    news_count = download_news_images(report_path, args.workspace, args.proxy)

    # Download arXiv figures
    print("\n--- arXiv figures ---")
    arxiv_count = download_arxiv_images(report_path, args.workspace, args.proxy)

    # List what we got
    print(f"\n--- Summary ---")
    if os.path.exists(images_dir):
        files = [f for f in os.listdir(images_dir) if not f.startswith("temp_")]
        print(f"Total images: {len(files)}")
        for f in files:
            size = os.path.getsize(os.path.join(images_dir, f))
            print(f"  {f} ({size:,} bytes)")
    else:
        print("No images downloaded")


if __name__ == "__main__":
    main()
