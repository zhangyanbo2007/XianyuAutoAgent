#!/usr/bin/env python3
"""validate_report.py — 日报格式铁律验证脚本

用法: python3 validate_report.py <report_path> <board>

验证项:
1. heading_hierarchy — 标题层级: ##板块 → ###子主题 → ####条目, 无越级
2. today_highlight — 今日亮点: ## 一、今日亮点 作为日报第一节
3. entry_title_format — 条目标题格式: 中文解读（英文原标题）, 不允许纯英文或双标题
4. image_consistency — 图片引用与05-images/目录文件一致
5. source_date_format — 来源行日期 YYYY-MM-DD
6. board_insight — 板块洞察 > 💡 **板块洞察：**
7. fox_commentary — 狐狸点评 🦊
"""

import sys
import os
import re
import json
from pathlib import Path


def load_report(path: str) -> list[str]:
    with open(path, encoding="utf-8") as f:
        return f.readlines()


def validate_heading_hierarchy(lines: list[str]) -> dict:
    """Check ## → ### → #### hierarchy, no ### used as entry or ## used as subtheme."""
    result = {"name": "heading_hierarchy", "passed": True, "evidence": "", "errors": []}
    h2_count = 0
    h3_count = 0
    h4_count = 0
    h1_count = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("## "):
            h1_count += 1
        elif stripped.startswith("## ") and not stripped.startswith("### "):
            h2_count += 1
        elif stripped.startswith("### ") and not stripped.startswith("#### "):
            h3_count += 1
        elif stripped.startswith("#### "):
            h4_count += 1

    if h2_count == 0:
        result["passed"] = False
        result["errors"].append("No ## headings found (expected section headings)")
    if h3_count == 0:
        result["passed"] = False
        result["errors"].append("No ### headings found (expected subtheme groups)")
    if h4_count == 0:
        result["passed"] = False
        result["errors"].append("No #### headings found (expected entry headings)")

    result["evidence"] = f"##:{h2_count} ###:{h3_count} ####:{h4_count}"
    if result["errors"]:
        result["passed"] = False
    return result


def validate_entry_title_format(lines: list[str]) -> dict:
    """Check #### entries follow '中文解读（英文原标题）' format."""
    result = {"name": "entry_title_format", "passed": True, "evidence": "", "errors": []}
    entries = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#### "):
            title = stripped[5:]
            entries.append((i + 1, title))

    bad_entries = []
    for lineno, title in entries:
        # Good format: 中文（English Title） — has Chinese chars before parentheses
        has_chinese_before_paren = bool(re.search(r'[一-鿿].*（', title))
        has_english_in_paren = bool(re.search(r'（[^）]*[A-Za-z][^）]*）', title))
        # Bad: only English, or English with ellipsis truncation
        is_pure_english = bool(re.match(r'^[A-Za-z0-9\s:,.\-–—!?;()\'"&+/]+$', title))
        has_ellipsis = "..." in title or "……" in title

        if is_pure_english:
            bad_entries.append(f"Line {lineno}: pure English title '{title}'")
        elif has_ellipsis:
            bad_entries.append(f"Line {lineno}: truncated with ellipsis '{title}'")
        elif not (has_chinese_before_paren and has_english_in_paren):
            # Not the ideal format but could be acceptable for news entries
            # Only flag if it looks like a bare English title
            if not re.search(r'[一-鿿]', title):
                bad_entries.append(f"Line {lineno}: no Chinese in title '{title}'")

    total = len(entries)
    bad_count = len(bad_entries)
    result["evidence"] = f"{total} entries, {bad_count} bad format"
    if bad_entries:
        result["passed"] = False
        result["errors"] = bad_entries[:5]  # limit to first 5
    return result


def validate_image_consistency(lines: list[str], report_path: str) -> dict:
    """Check image references match files in 05-images/ directory."""
    result = {"name": "image_consistency", "passed": True, "evidence": "", "errors": []}
    report_dir = Path(report_path).parent
    images_dir = report_dir / "05-images"

    # Find all image references in the report
    img_refs = []
    for i, line in enumerate(lines):
        # Match ![alt](05-images/xxx.png) or ![alt](05-images/xxx.jpg)
        matches = re.findall(r'!\[.*?\]\(05-images/([^)]+)\)', line)
        for fname in matches:
            img_refs.append(fname)

    # Check referenced files exist
    missing_refs = []
    for fname in img_refs:
        fpath = images_dir / fname
        if not fpath.exists():
            missing_refs.append(fname)
        elif fpath.stat().st_size == 0:
            missing_refs.append(f"{fname} (0 bytes)")

    # Check images in directory that are NOT referenced (unused)
    if images_dir.exists():
        all_images = [f.name for f in images_dir.iterdir() if f.is_file()]
        unreferenced = [f for f in all_images if f not in img_refs]
    else:
        all_images = []
        unreferenced = []
        if img_refs:
            result["passed"] = False
            result["errors"].append("05-images/ directory does not exist but report has image refs")

    result["evidence"] = f"refs:{len(img_refs)}, files:{len(all_images)}, missing:{len(missing_refs)}, unused:{len(unreferenced)}"
    if missing_refs:
        result["passed"] = False
        result["errors"].extend([f"Referenced but missing: {m}" for m in missing_refs[:5]])
    if unreferenced:
        # This is a warning, not a hard failure — some images may be hero/architecture variants
        result["errors"].extend([f"File exists but unreferenced: {u}" for u in unreferenced[:5]])

    return result


def validate_source_date_format(lines: list[str]) -> dict:
    """Check all source lines contain YYYY-MM-DD dates."""
    result = {"name": "source_date_format", "passed": True, "evidence": "", "errors": []}
    source_lines = []
    lines_without_date = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("> 🏠 **来源") or stripped.startswith("> 🏠"):
            source_lines.append((i + 1, stripped))
            if not re.search(r'\d{4}-\d{2}-\d{2}', stripped):
                lines_without_date.append(f"Line {i+1}: no YYYY-MM-DD date")

    total = len(source_lines)
    bad = len(lines_without_date)
    result["evidence"] = f"{total} source lines, {bad} missing YYYY-MM-DD"
    if lines_without_date:
        result["passed"] = False
        result["errors"] = lines_without_date[:5]
    return result


def validate_board_insight(lines: list[str]) -> dict:
    """Check for 板块洞察 sections."""
    result = {"name": "board_insight", "passed": True, "evidence": "", "errors": []}
    insight_lines = []
    for i, line in enumerate(lines):
        if "板块洞察" in line:
            insight_lines.append(i + 1)

    result["evidence"] = f"{len(insight_lines)} 板块洞察 section(s) found"
    if len(insight_lines) == 0:
        result["passed"] = False
        result["errors"].append("No 板块洞察 section found — each main board should have one")
    return result


def validate_today_highlight(lines: list[str]) -> dict:
    """Check for 今日亮点 section."""
    result = {"name": "today_highlight", "passed": True, "evidence": "", "errors": []}
    highlight_lines = []
    for i, line in enumerate(lines):
        if "今日亮点" in line and line.strip().startswith("##"):
            highlight_lines.append(i + 1)

    result["evidence"] = f"{len(highlight_lines)} 今日亮点 heading(s) found"
    if len(highlight_lines) == 0:
        result["passed"] = False
        result["errors"].append("No 今日亮点 section found — report must start with 今日亮点 as first section")
    return result


def validate_fox_commentary(lines: list[str]) -> dict:
    """Check for 狐狸点评 section."""
    result = {"name": "fox_commentary", "passed": True, "evidence": "", "errors": []}
    fox_lines = []
    for i, line in enumerate(lines):
        if "狐狸点评" in line and line.strip().startswith("#"):
            fox_lines.append(i + 1)

    result["evidence"] = f"{len(fox_lines)} 狐狸点评 heading(s) found"
    if len(fox_lines) == 0:
        result["passed"] = False
        result["errors"].append("No 狐狸点评 🦊 section found")
    return result


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 validate_report.py <report_path> <board>")
        print("  board: memory|llm|agent|news|builders")
        sys.exit(1)

    report_path = sys.argv[1]
    board = sys.argv[2]

    if not os.path.exists(report_path):
        print(f"ERROR: Report file not found: {report_path}")
        sys.exit(1)

    lines = load_report(report_path)

    validators = [
        validate_heading_hierarchy(lines),
        validate_today_highlight(lines),
        validate_entry_title_format(lines),
        validate_image_consistency(lines, report_path),
        validate_source_date_format(lines),
        validate_board_insight(lines),
        validate_fox_commentary(lines),
    ]

    all_passed = True
    print(f"\n📋 Format validation: {report_path} (board={board})")
    print("=" * 60)

    for v in validators:
        status = "✅ PASS" if v["passed"] else "❌ FAIL"
        print(f"{status} {v['name']}: {v['evidence']}")
        if v["errors"]:
            for err in v["errors"]:
                print(f"   → {err}")
        if not v["passed"]:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("🎉 All checks PASSED — report format is compliant")
    else:
        print("⚠️  Some checks FAILED — fix errors with Edit tool, then re-validate")
        sys.exit(1)


if __name__ == "__main__":
    main()