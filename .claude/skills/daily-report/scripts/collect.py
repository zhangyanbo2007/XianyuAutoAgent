#!/usr/bin/env python3
"""Daily-Report unified collector CLI.

Usage:
  collect.py --board <board> --date <YYYY-MM-DD> --output <path> [options]

Examples:
  # Collect memory papers
  python scripts/collect.py --board memory --date 2026-06-11 --output $WORKSPACE/01-search.json

  # Collect news (deterministic only, no websearch needs)
  python scripts/collect.py --board news --date 2026-06-11 --no-websearch --output $WORKSPACE/01-search.json

  # Dry run
  python scripts/collect.py --board memory --dry-run
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

CST = timezone(timedelta(hours=8))


def load_config() -> dict:
    """Load sources.json from config/ dir."""
    script_dir = Path(__file__).resolve().parent
    skill_dir = script_dir.parent
    config_path = skill_dir / "config" / "sources.json"

    if not config_path.exists():
        print(f"ERROR: Config not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def dedup(items: list[dict]) -> list[dict]:
    """Deduplicate items by ID and URL."""
    seen_ids = set()
    seen_urls = set()
    result = []

    for item in items:
        item_id = item.get("id", "")
        url = item.get("url", "")

        if item_id and item_id in seen_ids:
            continue
        if url and url in seen_urls:
            continue

        if item_id:
            seen_ids.add(item_id)
        if url:
            seen_urls.add(url)
        result.append(item)

    return result


# Collector registry: board → list of (module_name, condition_fn)
# condition_fn returns True if this collector should run for the board
def _has_arxiv_categories(board, config):
    return bool(config.get("arxiv", {}).get("categories", {}).get(board, []))

def _has_rss_feeds(board, config):
    return any(board in f.get("boards", []) for f in config.get("rss_feeds", []))

def _has_pubmed_queries(board, config):
    return bool(config.get("pubmed", {}).get("queries", {}).get(board, []))

def _has_openreview_venues(board, config):
    return board in ("memory", "llm", "agent") and bool(config.get("openreview", {}).get("venues", []))

def _has_github_repos(board, config):
    return any(board in r.get("boards", []) for r in config.get("github_repos", []))

def _has_huggingface(board, config):
    return board in ("news",)  # HF only for news

def _always(board, config):
    return True


COLLECTORS = [
    ("arxiv", _has_arxiv_categories),
    ("rss", _has_rss_feeds),
    ("pubmed", _has_pubmed_queries),
    ("openreview", _has_openreview_venues),
    ("github", _has_github_repos),
    ("huggingface", _has_huggingface),
    ("websearch", _always),
]


def collect_board(board: str, config: dict, date: str) -> tuple[list[dict], list[dict]]:
    """Run all applicable collectors for a board.

    Returns:
        (items, needs_websearch): Deterministic items and websearch needs list.
    """
    proxy = config.get("proxy")
    all_items = []
    all_ws_needs = []

    for module_name, condition in COLLECTORS:
        if not condition(board, config):
            continue

        try:
            mod = __import__(f"collectors.{module_name}", fromlist=["collect"])
            result = mod.collect(board=board, config=config, date=date, proxy=proxy)

            if module_name == "websearch":
                # websearch returns (items, needs_list)
                items, ws_needs = result
                all_items.extend(items)
                all_ws_needs.extend(ws_needs)
            else:
                all_items.extend(result)

        except Exception as e:
            print(f"[collect] {module_name} collector failed: {e}", file=sys.stderr)

    # Dedup across all collectors
    all_items = dedup(all_items)

    return all_items, all_ws_needs


def build_output(board: str, date: str, items: list[dict],
                 ws_needs: list[dict], config: dict) -> dict:
    """Build the unified output JSON."""
    by_source = {}
    for item in items:
        src = item.get("source", "unknown")
        by_source[src] = by_source.get(src, 0) + 1

    by_board = {}
    for item in items:
        for b in item.get("board_match", [board]):
            by_board[b] = by_board.get(b, 0) + 1

    output = {
        "board": board,
        "date": date,
        "generated_at": datetime.now(CST).isoformat(),
        "items": items,
        "stats": {
            "total": len(items),
            "by_source": by_source,
            "by_board": by_board,
            "errors": [],
        },
    }

    if ws_needs:
        output["needs_websearch"] = ws_needs

    return output


def main():
    parser = argparse.ArgumentParser(description="Daily-Report unified collector")
    parser.add_argument("--board", required=True,
                        choices=["memory", "llm", "agent", "news", "builders"],
                        help="Board to collect for")
    parser.add_argument("--date", default=datetime.now(CST).strftime("%Y-%m-%d"),
                        help="Target date YYYY-MM-DD (default: today)")
    parser.add_argument("--output", help="Output JSON file path")
    parser.add_argument("--no-websearch", action="store_true",
                        help="Exclude websearch needs from output")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show collection plan without executing")

    args = parser.parse_args()
    config = load_config()

    if args.dry_run:
        print(f"Board: {args.board}")
        print(f"Date: {args.date}")
        print(f"Date range: {config.get('date_range_days', 1)} days")
        print()
        for module_name, condition in COLLECTORS:
            if condition(args.board, config):
                print(f"  ✓ {module_name}")
            else:
                print(f"  · {module_name} (skipped)")
        return

    print(f"Collecting for board={args.board}, date={args.date}")
    items, ws_needs = collect_board(args.board, config, args.date)
    output = build_output(args.board, args.date, items, ws_needs, config)

    if args.no_websearch:
        output.pop("needs_websearch", None)

    output_json = json.dumps(output, ensure_ascii=False, indent=2)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Saved to {args.output} ({len(items)} items)")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
