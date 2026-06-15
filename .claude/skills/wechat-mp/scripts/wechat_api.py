#!/usr/bin/env python3
"""WeChat MP API wrapper for draft/publish operations.

This module encapsulates all WeChat Official Account (公众号) MP API interactions:
- Access token management (get, cache, refresh)
- Permanent material upload (cover images)
- Article image upload (inline images)
- Draft creation (草稿箱)
- Draft publishing (发布)
- Publish status checking

All API calls use the stable_token endpoint for reliability.
Token caching prevents redundant API calls (token valid for 2 hours).

Usage:
  python3 wechat_api.py get-token --config <config-file>
  python3 wechat_api.py upload-cover --filepath <image-path> --config <config-file>
  python3 wechat_api.py create-draft --title <title> --content <html-file> --thumb-media-id <id> --config <config-file>

NOTE: This module requires a certified WeChat MP account. Uncertified accounts
cannot call draft/publish APIs since July 2025.
"""

import argparse
import json
import os
import time
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: 'requests' package is required. Install with: pip install requests")
    sys.exit(1)

WECHAT_API_BASE = "https://api.weixin.qq.com"


NO_PROXY = {"http": None, "https": None}  # Bypass env proxy for WeChat API (IP whitelist)

def load_config(config_path: str) -> dict:
    """Load config from JSON file. Reads AppID/Secret from config or env vars."""
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    # Resolve AppID/Secret: prefer config values, fallback to env vars
    appid_key = cfg.get("appid_env_key", "WECHAT_MP_APPID")
    secret_key = cfg.get("secret_env_key", "WECHAT_MP_SECRET")

    if not cfg.get("appid"):
        cfg["appid"] = os.environ.get(appid_key, "")
    if not cfg.get("secret"):
        cfg["secret"] = os.environ.get(secret_key, "")

    if not cfg["appid"] or not cfg["secret"]:
        print("Warning: WECHAT_MP_APPID or WECHAT_MP_SECRET not set.")
        print("Set them in config.json or environment before running.")

    return cfg


def get_access_token(cfg: dict, force_refresh: bool = False) -> str:
    """Get a valid WeChat MP access_token, with local caching.

    Token is cached in the file specified by cfg['token_cache_path'].
    Tokens are valid for 7200 seconds (2 hours).
    """
    cache_path = cfg.get("token_cache_path", os.path.expanduser("~/.wechat-mp/token_cache.json"))

    # Check cache
    if not force_refresh and os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            cache = json.load(f)
        if cache.get("expires_at", 0) > time.time() + 300:  # 5 min buffer
            return cache["access_token"]

    appid = cfg["appid"]
    secret = cfg["secret"]
    if not appid or not secret:
        raise ValueError("WECHAT_MP_APPID and WECHAT_MP_SECRET must be set")

    # Use stable_token endpoint (more reliable than /cgi-bin/token)
    url = f"{WECHAT_API_BASE}/cgi-bin/stable_token"
    payload = {
        "grant_type": "client_credential",
        "appid": appid,
        "secret": secret,
    }
    resp = requests.post(url, json=payload, timeout=30, proxies=NO_PROXY)
    data = resp.json()

    if "access_token" not in data:
        raise RuntimeError(f"Failed to get access_token: {data}")

    token = data["access_token"]
    expires_in = data.get("expires_in", 7200)

    # Cache the token
    cache = {
        "access_token": token,
        "expires_at": time.time() + expires_in,
    }
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache, f)

    return token


def upload_permanent_material(token: str, filepath: str, media_type: str = "thumb") -> str:
    """Upload a permanent material (image) to WeChat MP.

    Returns the media_id for use as thumb_media_id in draft creation.
    Media type should be "thumb" for cover images or "image" for general images.

    Note: Permanent materials count against the 5,000 total limit.
    """
    url = f"{WECHAT_API_BASE}/cgi-bin/material/add_material?access_token={token}&type={media_type}"
    with open(filepath, "rb") as f:
        files = {"media": (os.path.basename(filepath), f)}
        resp = requests.post(url, files=files, timeout=60, proxies=NO_PROXY)
    data = resp.json()

    if "media_id" not in data:
        raise RuntimeError(f"Failed to upload material: {data}")

    return data["media_id"]


def upload_article_image(token: str, filepath: str) -> str:
    """Upload an image for use within article body content.

    Returns a URL that can be used in <img src="..."> tags in the HTML content.
    This URL is WeChat-hosted and will pass the image filter.
    """
    url = f"{WECHAT_API_BASE}/cgi-bin/media/uploadimg?access_token={token}"
    with open(filepath, "rb") as f:
        files = {"media": (os.path.basename(filepath), f)}
        resp = requests.post(url, files=files, timeout=60, proxies=NO_PROXY)
    data = resp.json()

    if "url" not in data:
        raise RuntimeError(f"Failed to upload article image: {data}")

    return data["url"]


def create_draft(token: str, articles: list[dict]) -> str:
    """Create a draft in the WeChat MP draft box (草稿箱).

    articles: list of article dicts, each containing:
      - title (max 64 chars)
      - content (HTML, max 20,000 chars / 1MB)
      - thumb_media_id (cover image media_id)
      - author (optional)
      - digest (optional, auto-generated from first 54 chars if omitted)
      - content_source_url (optional, original article link)
      - show_cover_pic (optional, 0 or 1)

    Returns the media_id of the created draft.

    NOTE: Must send JSON with ensure_ascii=False to keep Chinese chars as UTF-8
    bytes instead of escaped unicode sequences. The escaped form inflates
    the payload ~2x, causing error 45004 "description size out of limit".
    """
    url = f"{WECHAT_API_BASE}/cgi-bin/draft/add?access_token={token}"
    payload = {"articles": articles}
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json; charset=utf-8"}
    resp = requests.post(url, data=body, headers=headers, timeout=60, proxies=NO_PROXY)
    data = resp.json()

    if "media_id" not in data:
        raise RuntimeError(f"Failed to create draft: {data}")

    return data["media_id"]


def publish_draft(token: str, media_id: str) -> str:
    """Publish a draft from the draft box.

    This is an asynchronous operation. Returns a publish_id
    that can be used with check_publish_status() to poll completion.

    Note: Publishing does NOT consume the mass-send quota.
    It publishes to the account's article history/articles page.
    """
    url = f"{WECHAT_API_BASE}/cgi-bin/freepublish/submit?access_token={token}"
    payload = {"media_id": media_id}
    resp = requests.post(url, json=payload, timeout=30, proxies=NO_PROXY)
    data = resp.json()

    if "publish_id" not in data:
        raise RuntimeError(f"Failed to publish draft: {data}")

    return data["publish_id"]


def check_publish_status(token: str, publish_id: str) -> dict:
    """Check the status of a published draft.

    Status values:
      0 = success (published successfully)
      1 = in review (内容审核中)
      2 = original check (原创校验中)
      3 = failed (发布失败)
      4 = deleted (已删除)

    Returns the full response dict including article_url on success.
    """
    url = f"{WECHAT_API_BASE}/cgi-bin/freepublish/get?access_token={token}"
    payload = {"publish_id": publish_id}
    resp = requests.post(url, json=payload, timeout=30, proxies=NO_PROXY)
    return resp.json()


def wait_for_publish(token: str, publish_id: str, max_wait: int = 180, interval: int = 10) -> dict:
    """Poll publish status until completion or timeout.

    max_wait: maximum seconds to wait (default 180 = 3 minutes)
    interval: seconds between polls (default 10)
    """
    elapsed = 0
    while elapsed < max_wait:
        status = check_publish_status(token, publish_id)
        publish_status = status.get("publish_status", -1)

        if publish_status == 0:
            return status  # Success
        elif publish_status == 3 or publish_status == 4:
            raise RuntimeError(f"Publish failed or deleted: {status}")

        time.sleep(interval)
        elapsed += interval

    raise TimeoutError(f"Publish status check timed out after {max_wait}s, last status: {status}")


def main():
    parser = argparse.ArgumentParser(description="WeChat MP API operations")
    parser.add_argument("--config", default=os.path.expanduser("~/.wechat-mp/config.json"), help="Config file path")

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # get-token
    subparsers.add_parser("get-token", help="Get and cache access token")

    # upload-cover
    cover_parser = subparsers.add_parser("upload-cover", help="Upload cover image as permanent material")
    cover_parser.add_argument("--filepath", required=True, help="Image file path")

    # create-draft
    draft_parser = subparsers.add_parser("create-draft", help="Create a draft in draft box")
    draft_parser.add_argument("--title", required=True, help="Article title (max 64 chars)")
    draft_parser.add_argument("--content-file", required=True, help="HTML content file path")
    draft_parser.add_argument("--thumb-media-id", required=True, help="Cover image media_id")
    draft_parser.add_argument("--author", default="", help="Author name")
    draft_parser.add_argument("--digest", default="", help="Article digest/summary")

    # publish-draft
    publish_parser = subparsers.add_parser("publish-draft", help="Publish a draft")
    publish_parser.add_argument("--media-id", required=True, help="Draft media_id to publish")

    # check-status
    status_parser = subparsers.add_parser("check-status", help="Check publish status")
    status_parser.add_argument("--publish-id", required=True, help="Publish ID to check")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cfg = load_config(args.config)

    if args.command == "get-token":
        token = get_access_token(cfg)
        print(f"Access token obtained: {token[:20]}...")
        print(f"Token cached at: {cfg.get('token_cache_path', '~/.wechat-mp/token_cache.json')}")

    elif args.command == "upload-cover":
        token = get_access_token(cfg)
        media_id = upload_permanent_material(token, args.filepath, "thumb")
        print(f"Cover image uploaded. thumb_media_id: {media_id}")
        print("Update config.json cover_media_id with this value.")

    elif args.command == "create-draft":
        token = get_access_token(cfg)
        with open(args.content_file, "r", encoding="utf-8") as f:
            content = f.read()

        article = {
            "title": args.title[:64],  # WeChat max 64 chars
            "content": content,
            "thumb_media_id": args.thumb_media_id,
            "author": args.author or cfg.get("author", ""),
            "digest": args.digest or "",
            "show_cover_pic": 0,
            "need_open_comment": 0,
            "only_fans_can_comment": 0,
        }
        media_id = create_draft(token, [article])
        print(f"Draft created. media_id: {media_id}")
        print(f"Check the draft at: https://mp.weixin.qq.com -> 草稿箱")

    elif args.command == "publish-draft":
        token = get_access_token(cfg)
        publish_id = publish_draft(token, args.media_id)
        print(f"Draft submitted for publishing. publish_id: {publish_id}")

    elif args.command == "check-status":
        token = get_access_token(cfg)
        status = check_publish_status(token, args.publish_id)
        print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()