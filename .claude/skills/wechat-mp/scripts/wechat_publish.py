#!/usr/bin/env python3
"""WeChat MP article publishing orchestrator.

This script ties together the markdown-to-HTML conversion and WeChat API
operations to publish articles to a WeChat Official Account (公众号).

Workflow:
  1. Read input markdown file
  2. Convert to WeChat-compatible HTML with inline CSS (using md2wechat_html.py)
  3. Check content limits (< 20,000 chars / < 1MB)
  4. Either save locally (mode=local) or create draft via API (mode=draft/publish)

Usage:
  # Local mode (current stage - uncertified account):
  python3 wechat_publish.py --input <md-file> --title <title> --mode local --config <config-file>

  # Draft mode (certified account - create draft only):
  python3 wechat_publish.py --input <md-file> --title <title> --mode draft --config <config-file>

  # Publish mode (certified account - draft + auto-publish):
  python3 wechat_publish.py --input <md-file> --title <title> --mode publish --config <config-file>

NOTE: draft/publish modes require a certified WeChat MP account.
"""

import argparse
import io
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

try:
    import requests as http_requests
except ImportError:
    print("Error: 'requests' package is required. Install with: pip install requests")
    sys.exit(1)

# Import from sibling modules
sys.path.insert(0, str(Path(__file__).parent))
from md2wechat_html import load_css_styles, convert_markdown_to_wechat_html, strip_frontmatter, check_content_limits
from wechat_api import load_config, get_access_token, create_draft, publish_draft, wait_for_publish, upload_article_image


def upload_images_to_wechat(html: str, cfg: dict, proxy: str = "", md_input: str = "") -> str:
    """Find all img tags in HTML, download images, upload to WeChat, replace URLs.

    WeChat strips external image URLs. This function:
    1. Parses HTML for all <img src="..."> tags
    2. Downloads each image to a temp file (via proxy if needed)
    3. Uploads each to WeChat MP uploadimg API (direct, no proxy)
    4. Replaces external URLs with WeChat-hosted URLs

    Returns modified HTML with WeChat-hosted image URLs.
    """
    img_pattern = re.compile(r'<img\s+src="([^"]+)"([^>]*)>')
    matches = list(img_pattern.finditer(html))

    if not matches:
        return html

    token = get_access_token(cfg)
    proxy_dict = {"http": proxy, "https": proxy} if proxy else None

    # Temp dir for downloaded images
    tmp_dir = tempfile.mkdtemp(prefix="wechat_img_")

    try:
        for match in matches:
            original_url = match.group(1)
            attrs = match.group(2)

            # Skip already WeChat-hosted URLs
            if "mmbiz.qpic.cn" in original_url:
                continue

            # Skip SVG — WeChat doesn't render SVG, don't waste retries
            if original_url.lower().endswith(".svg") or "/svg" in original_url.lower():
                print(f"Warning: Skipping SVG image (WeChat incompatible): {original_url[:60]}...")
                continue

            # Handle local file paths (relative to the input markdown file)
            if not original_url.startswith("http"):
                # Try to resolve as local path relative to the markdown file's directory
                local_path = original_url
                if not os.path.isabs(local_path) and md_input:
                    # Resolve relative to the input file's directory
                    md_dir = os.path.dirname(os.path.abspath(md_input))
                    local_path = os.path.join(md_dir, local_path)
                if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
                    # Copy local file to temp dir for upload
                    ext = Path(local_path).suffix or ".png"
                    tmp_path = os.path.join(tmp_dir, f"img_{hash(original_url) % 10000}{ext}")
                    import shutil
                    shutil.copy2(local_path, tmp_path)
                    downloaded = True
                    print(f"Local file: {original_url} → {tmp_path}")
                    # Upload to WeChat
                    try:
                        wechat_url = upload_article_image(token, tmp_path)
                        html = html.replace(
                            f'<img src="{original_url}"{attrs}',
                            f'<img src="{wechat_url}"{attrs}'
                        )
                        print(f"Image uploaded: {original_url} → {wechat_url[:60]}...")
                    except Exception as e:
                        print(f"Warning: Failed to upload local image {original_url}: {e}")
                    continue
                else:
                    print(f"Warning: Local file not found: {local_path}")
                    continue

            # Download image via proxy (for arXiv etc), with retry
            downloaded = False
            tmp_path = ""
            for attempt in range(3):
                try:
                    resp = http_requests.get(original_url, proxies=proxy_dict, timeout=60)
                    if resp.status_code != 200:
                        if attempt < 2:
                            print(f"Retry {attempt+1}: download returned {resp.status_code} for {original_url[:60]}...")
                            time.sleep(2)
                            continue
                        print(f"Warning: Failed to download image {original_url}: {resp.status_code} after 3 attempts")
                        break

                    # Detect and convert webp to PNG (WeChat doesn't support webp)
                    is_webp = (
                        original_url.lower().endswith(".webp")
                        or "format-webp" in original_url.lower()
                        or resp.headers.get("content-type", "").startswith("image/webp")
                    )

                    # Save to temp file
                    if is_webp:
                        # Convert webp → PNG using Pillow
                        try:
                            from PIL import Image
                            tmp_path = os.path.join(tmp_dir, f"img_{len(matches)}_{hash(original_url) % 10000}.png")
                            img = Image.open(io.BytesIO(resp.content))
                            if img.mode in ("RGBA", "P"):
                                img = img.convert("RGB")
                            img.save(tmp_path, "PNG")
                            print(f"Converted webp → PNG: {original_url[:60]}...")
                            downloaded = True
                            break
                        except ImportError:
                            print(f"Warning: Pillow not installed, can't convert webp. Skipping {original_url[:60]}...")
                            break
                        except Exception as e:
                            print(f"Warning: Failed to convert webp to PNG: {e}. Skipping {original_url[:60]}...")
                            break
                    else:
                        ext = Path(original_url).suffix or ".png"
                        if ext not in (".png", ".jpg", ".jpeg", ".gif", ".bmp"):
                            ext = ".png"
                        tmp_path = os.path.join(tmp_dir, f"img_{len(matches)}_{hash(original_url) % 10000}{ext}")
                        with open(tmp_path, "wb") as f:
                            f.write(resp.content)
                        downloaded = True
                        break
                except http_requests.exceptions.Timeout:
                    if attempt < 2:
                        print(f"Retry {attempt+1}: download timed out for {original_url[:60]}...")
                        time.sleep(3)
                        continue
                    print(f"Warning: Failed to download image {original_url}: timed out after 3 attempts")
                except Exception as e:
                    if attempt < 2:
                        print(f"Retry {attempt+1}: download error for {original_url[:60]}... ({e})")
                        time.sleep(2)
                        continue
                    print(f"Warning: Failed to download image {original_url}: {e} after 3 attempts")

            if not downloaded:
                continue

            # Upload to WeChat (direct connection, no proxy), with retry
            uploaded = False
            for attempt in range(3):
                try:
                    wechat_url = upload_article_image(token, tmp_path)
                    print(f"Image uploaded: {original_url[:60]}... → {wechat_url[:60]}...")
                    uploaded = True
                    break
                except Exception as e:
                    if attempt < 2:
                        print(f"Retry {attempt+1}: upload failed for {original_url[:60]}... ({e})")
                        time.sleep(3)
                        continue
                    print(f"Warning: Failed to upload image {original_url} to WeChat: {e} after 3 attempts")

            if uploaded:
                # Replace URL in HTML
                html = html.replace(
                    f'<img src="{original_url}"{attrs}',
                    f'<img src="{wechat_url}"{attrs}',
                )

    finally:
        # Cleanup temp files
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return html


def publish_local(md_path: str, html_path: str, cfg: dict, feishu_url: str = "") -> dict:
    """Local mode: convert markdown to HTML and save both files locally.

    Returns metadata about the generated files.
    """
    # Read markdown
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    md_content = strip_frontmatter(md_text) if md_text.startswith("---") else md_text

    # Load CSS and convert
    css_path = cfg.get("css_template", str(Path(__file__).parent.parent / "config" / "wechat-style.css"))
    styles = load_css_styles(css_path)
    html = convert_markdown_to_wechat_html(md_content, styles, feishu_url=feishu_url)

    # Check limits
    is_valid, warning = check_content_limits(html)

    # Write HTML file
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    result = {
        "success": True,
        "mode": "local",
        "md_path": md_path,
        "html_path": html_path,
        "char_count": len(html),
        "size_kb": round(len(html.encode("utf-8")) / 1024, 1),
        "valid": is_valid,
        "warning": warning,
        "published": False,
    }

    return result


def publish_via_api(md_path: str, title: str, cfg: dict, mode: str = "draft", feishu_url: str = "", upload_images: bool = False, cover_type: str = "", board: str = "") -> dict:
    """API mode: convert markdown to HTML and publish via WeChat MP API.

    mode: "draft" (create draft only) or "publish" (draft + auto-publish)
    upload_images: if True, download external images and upload to WeChat before creating draft
    cover_type: "academic" or "tech-news" — selects appropriate cover_media_id from config
    """
    # Read markdown
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    md_content = strip_frontmatter(md_text) if md_text.startswith("---") else md_text

    # Convert to HTML
    css_path = cfg.get("css_template", str(Path(__file__).parent.parent / "config" / "wechat-style.css"))
    styles = load_css_styles(css_path)
    html = convert_markdown_to_wechat_html(md_content, styles, feishu_url=feishu_url)

    # Upload images if requested
    if upload_images:
        proxy = cfg.get("proxy", os.environ.get("http_proxy", ""))
        html = upload_images_to_wechat(html, cfg, proxy=proxy, md_input=md_path)

    # Check limits
    is_valid, warning = check_content_limits(html)
    if not is_valid:
        return {
            "success": False,
            "mode": mode,
            "error": f"Content exceeds WeChat limits: {warning}",
            "published": False,
        }

    # Get access token
    try:
        token = get_access_token(cfg)
    except (ValueError, RuntimeError) as e:
        return {
            "success": False,
            "mode": mode,
            "error": f"Failed to get access token: {e}",
            "published": False,
        }

    # Delete old drafts with same title (prevent duplicates)
    # WeChat API returns garbled Chinese — normalize encoding before comparison
    def _normalize(s):
        try:
            return s.encode('latin-1').decode('utf-8')
        except (UnicodeDecodeError, UnicodeEncodeError):
            return s

    import re as _re
    title_norm = _normalize(title).lower().strip()
    title_prefix = title_norm.split("|")[0].strip() if "|" in title_norm else title_norm
    try:
        list_resp = http_requests.post(
            f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={token}",
            json={"offset": 0, "count": 50, "no_content": 1},
            timeout=15,
        )
        list_data = list_resp.json()
        for old_item in list_data.get("item", []):
            old_media_id = old_item.get("media_id", "")
            old_articles = old_item.get("content", {}).get("news_item", [])
            old_title = old_articles[0].get("title", "") if old_articles else ""
            old_norm = _normalize(old_title).lower().strip()
            old_prefix = old_norm.split("|")[0].strip() if "|" in old_norm else old_norm
            # Match: same title prefix (before |)
            if title_prefix and old_prefix == title_prefix:
                del_resp = http_requests.post(
                    f"https://api.weixin.qq.com/cgi-bin/draft/delete?access_token={token}",
                    json={"media_id": old_media_id},
                    timeout=10,
                )
                if del_resp.json().get("errcode", 0) == 0:
                    print(f"Deleted old draft: {old_title[:40]}")
    except Exception as e:
        print(f"Warning: auto-delete failed: {e}")

    # Create draft — select cover by board (preferred) or type (fallback)
    cover_media_id = ""
    if board:
        cover_media_id = cfg.get(f"cover_media_id_{board}", "")
    if not cover_media_id and cover_type:
        if cover_type == "academic":
            cover_media_id = cfg.get("cover_media_id_academic", cfg.get("cover_media_id", ""))
        elif cover_type == "tech-news":
            cover_media_id = cfg.get("cover_media_id_tech_news", cfg.get("cover_media_id", ""))
        elif cover_type == "follow-builders":
            cover_media_id = cfg.get("cover_media_id_follow_builders", cfg.get("cover_media_id", ""))
    if not cover_media_id:
        cover_media_id = cfg.get("cover_media_id", "")
    if not cover_media_id:
        return {
            "success": False,
            "mode": mode,
            "error": "cover_media_id not set in config. Upload a cover image first.",
            "published": False,
        }

    article = {
        "title": title[:64],  # WeChat max 64 chars
        "content": html,
        "thumb_media_id": cover_media_id,
        "author": cfg.get("author", "狐狸技术日报"),
        "show_cover_pic": 0,  # Don't repeat cover inside article body
        "need_open_comment": 0,
        "only_fans_can_comment": 0,
    }

    # Set "阅读原文" link if feishu_url provided
    if feishu_url:
        article["content_source_url"] = feishu_url

    try:
        media_id = create_draft(token, [article])
    except RuntimeError as e:
        return {
            "success": False,
            "mode": mode,
            "error": f"Failed to create draft: {e}",
            "published": False,
        }

    result = {
        "success": True,
        "mode": mode,
        "media_id": media_id,
        "char_count": len(html),
        "size_kb": round(len(html.encode("utf-8")) / 1024, 1),
        "valid": True,
        "warning": warning,
        "published": False,
    }

    # Auto-publish if requested
    if mode == "publish":
        try:
            publish_id = publish_draft(token, media_id)
            result["publish_id"] = publish_id

            # Wait for publish completion
            status = wait_for_publish(token, publish_id)
            result["published"] = True
            result["article_url"] = status.get("article_url", "")
            result["publish_status"] = "success"
        except (RuntimeError, TimeoutError) as e:
            result["published"] = False
            result["publish_status"] = "failed"
            result["publish_error"] = str(e)

    return result


def publish_from_html(html_path, title, cfg, mode="draft", feishu_url="", upload_images=False, cover_type="", board=""):
    """Publish pre-generated HTML to WeChat MP. Skips md2wechat_html.py conversion."""
    # Read HTML file
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Upload images if requested (same logic as publish_via_api)
    if upload_images:
        proxy = cfg.get("proxy", os.environ.get("http_proxy", ""))
        html = upload_images_to_wechat(html, cfg, proxy=proxy, md_input=html_path)

    # Check content limits
    is_valid, warning = check_content_limits(html)
    if not is_valid:
        result = {"success": False, "mode": mode, "error": f"Content exceeds limits: {warning}", "published": False}
        return result

    # If local mode, just write to output file
    if mode == "local":
        output_dir = cfg.get("output_dir", "/tmp")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{title}.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        result = {"success": True, "mode": "local", "output_path": output_path, "char_count": len(html), "published": False}
        return result

    # Get access token
    token = get_access_token(cfg)

    # Select cover (board preferred, then type fallback)
    cover_media_id = ""
    if board:
        cover_media_id = cfg.get(f"cover_media_id_{board}", "")
    if not cover_media_id and cover_type:
        if cover_type == "academic":
            cover_media_id = cfg.get("cover_media_id_academic", cfg.get("cover_media_id", ""))
        elif cover_type == "tech-news":
            cover_media_id = cfg.get("cover_media_id_tech_news", cfg.get("cover_media_id", ""))
        elif cover_type == "follow-builders":
            cover_media_id = cfg.get("cover_media_id_follow_builders", cfg.get("cover_media_id", ""))
    if not cover_media_id:
        cover_media_id = cfg.get("cover_media_id", "")
    if not cover_media_id:
        result = {"success": False, "mode": mode, "error": "cover_media_id not set for cover_type: " + cover_type, "published": False}
        return result

    # Create draft
    article = {
        "title": title[:64],
        "content": html,
        "thumb_media_id": cover_media_id,
        "author": cfg.get("author", ""),
        "show_cover_pic": 0,
    }
    if feishu_url:
        article["content_source_url"] = feishu_url

    media_id = create_draft(token, [article])

    result = {"success": True, "mode": mode, "media_id": media_id, "char_count": len(html), "published": False}

    # If publish mode, also submit for publishing
    if mode == "publish":
        publish_id = publish_draft(token, media_id)
        result["publish_id"] = publish_id
        result["published"] = True

    return result


def main():
    parser = argparse.ArgumentParser(description="WeChat MP article publishing orchestrator")
    parser.add_argument("--input", default=None, help="Input markdown file path")
    parser.add_argument("--html-input", default=None,
                        help="Pre-generated HTML file path (bypasses md2wechat_html.py conversion). Use with frontend-design skill for custom layouts.")
    parser.add_argument("--title", default="", help="Article title (for draft/publish mode, max 64 chars)")
    parser.add_argument("--author", default="", help="Author name (overrides config)")
    parser.add_argument("--mode", choices=["local", "draft", "publish"], default=None,
                        help="Publishing mode: local (save files), draft (create draft via API), publish (draft + auto-publish)")
    parser.add_argument("--output", default=None,
                        help="Output HTML file path (local mode only, auto-derived from input if omitted)")
    parser.add_argument("--config", default=os.path.expanduser("~/.wechat-mp/config.json"),
                        help="Config file path")
    parser.add_argument("--strip-frontmatter", action="store_true", help="Strip YAML frontmatter from input")
    parser.add_argument("--feishu-url", default="", help="Feishu document URL for '阅读原文' link")
    parser.add_argument("--upload-images", action="store_true",
                        help="Download external images and upload to WeChat (replace URLs with WeChat-hosted ones)")
    parser.add_argument("--cover-type", choices=["academic", "tech-news"], default=None,
                        help="Cover type: selects cover_media_id from config (academic or tech-news)")
    parser.add_argument("--board", default="",
                        help="Board name (memory/llm/agent/news/builders): selects per-board cover from config")

    args = parser.parse_args()

    cfg = load_config(args.config)

    # Determine mode from config if not specified
    if args.mode is None:
        args.mode = cfg.get("mode", "local")

    # Validate that at least one input is provided
    if not args.input and not args.html_input:
        parser.error("Either --input or --html-input must be provided")

    # Override author if specified
    if args.author:
        cfg["author"] = args.author

    # Handle --html-input (bypasses md2wechat_html.py conversion)
    if args.html_input:
        result = publish_from_html(args.html_input, args.title, cfg, args.mode,
                                   feishu_url=args.feishu_url, upload_images=args.upload_images,
                                   cover_type=args.cover_type, board=args.board)
    elif args.mode == "local":
        # Auto-derive output path for local mode
        if not args.output:
            args.output = str(Path(args.input).with_suffix(".html"))
        result = publish_local(args.input, args.output, cfg, feishu_url=args.feishu_url)
    else:
        if not args.title:
            # Auto-derive title from input filename
            args.title = Path(args.input).stem.replace("wechat-daily-", "狐狸技术日报精选 | ")
        result = publish_via_api(args.input, args.title, cfg, args.mode, feishu_url=args.feishu_url, upload_images=args.upload_images, cover_type=args.cover_type, board=args.board)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()