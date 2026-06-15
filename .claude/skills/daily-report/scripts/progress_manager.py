#!/usr/bin/env python3
"""Progress manager for daily-report skill.

Usage:
  progress_manager.py init <board> <date> <workspace>
  progress_manager.py update <workspace> <step_key> <status>
  progress_manager.py check <workspace>
"""

import json
import sys
import os


ALL_STEPS = [
    "01_search",
    "02_dedup",
    "03_wiki_ingest",
    "04_index_update",
    "05_report_md",
    "06_feishu",
    "07_cover",
    "08_cover_upload",
    "09_wechat_html",
    "10_wechat_draft",
    "11_result",
]


def init(board: str, date: str, workspace: str):
    """Create progress.json with all steps pending."""
    progress = {
        "板块": board,
        "日期": date,
        "steps": {step: "pending" for step in ALL_STEPS},
    }
    path = os.path.join(workspace, "progress.json")
    os.makedirs(workspace, exist_ok=True)
    with open(path, "w") as f:
        json.dump(progress, f, indent=2)
    print(f"Created {path} for board={board}, date={date}")


def update(workspace: str, step_key: str, status: str):
    """Update a step's status in progress.json."""
    path = os.path.join(workspace, "progress.json")
    with open(path) as f:
        progress = json.load(f)
    if step_key not in progress["steps"]:
        print(f"ERROR: step_key '{step_key}' not found. Valid keys: {ALL_STEPS}")
        sys.exit(1)
    if status not in ("done", "failed", "pending"):
        print(f"ERROR: status '{status}' not valid. Use: done, failed, pending")
        sys.exit(1)
    progress["steps"][step_key] = status
    with open(path, "w") as f:
        json.dump(progress, f, indent=2)
    print(f"Updated {step_key} → {status}")


def check(workspace: str):
    """Print current status and identify next step."""
    path = os.path.join(workspace, "progress.json")
    with open(path) as f:
        progress = json.load(f)
    print(f"Board: {progress['板块']} | Date: {progress['日期']}")
    done_count = 0
    next_step = None
    for step in ALL_STEPS:
        status = progress["steps"].get(step, "pending")
        icon = "✓" if status == "done" else "✗" if status == "failed" else "○"
        print(f"  {icon} {step}: {status}")
        if status == "done":
            done_count += 1
        if next_step is None and status in ("pending", "failed"):
            next_step = step
    print(f"Progress: {done_count}/{len(ALL_STEPS)} done")
    if next_step:
        print(f"Next step: {next_step}")
    else:
        print("All steps complete!")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "init":
        if len(sys.argv) != 5:
            print("Usage: progress_manager.py init <board> <date> <workspace>")
            sys.exit(1)
        init(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "update":
        if len(sys.argv) != 5:
            print("Usage: progress_manager.py update <workspace> <step_key> <status>")
            sys.exit(1)
        update(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "check":
        if len(sys.argv) != 3:
            print("Usage: progress_manager.py check <workspace>")
            sys.exit(1)
        check(sys.argv[2])
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()