#!/usr/bin/env python3
"""
Paper-to-Video: 入口脚本

用法:
    python paper_to_video.py <paper_input> -o <output_dir> [options]

示例:
    # 从论文 URL 生成（全文抓取 + LLM分镜 + 高质量成片）
    python paper_to_video.py https://arxiv.org/abs/2606.05008 -o output/dast-analysis

    # 从论文本地文件（如 paper_url.txt）
    python paper_to_video.py projects/papers-site/dast_analysis/paper_url.txt -o projects/papers-site/dast_analysis

    # 只生成分镜脚本（不调 TTS/图像/视频）
    python paper_to_video.py paper_url.txt -o out/ --steps storyboard

    # 只渲染视频（跳过分镜、图像，用已有的 storyboard.json）
    python paper_to_video.py paper_url.txt -o out/ --steps slides,narration,video

    # 跳过 AI 背景图生成（纯代码渲染，更快）
    python paper_to_video.py paper_url.txt -o out/ --skip-backgrounds

    # 控制分镜数量
    python paper_to_video.py paper_url.txt -o out/ --scenes 14
"""

import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="论文输入 → 精细音画分镜脚本 → 高质量讲解视频",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "paper",
        help="论文 URL / arxiv ID / 本地文本文件路径",
    )
    parser.add_argument(
        "-o", "--output",
        default="",
        help="输出目录（将存放 storyboard.json、video.mp4 等）。默认: videos/<paper-slug>/",
    )
    parser.add_argument(
        "--scenes", type=int, default=18,
        help="分镜数量（默认 18，建议 14-24）",
    )
    parser.add_argument(
        "--steps",
        default="storyboard,backgrounds,charts,slides,narration,video",
        help="逗号分隔的步骤列表，默认全部执行",
    )
    parser.add_argument(
        "--clean", action="store_true",
        help="清除输出目录后重新生成",
    )
    parser.add_argument(
        "--skip-backgrounds", action="store_true",
        help="跳过 AI 背景图生成（用代码渲染替代，更快）",
    )
    args = parser.parse_args()

    steps = [s.strip() for s in args.steps.split(",") if s.strip()]

    from pathlib import Path as _P
    from paper_video.paper_source import extract_arxiv_id, _read_input
    from paper_video.pipeline import run_pipeline

    # Auto-derive output dir: videos/<arxiv_id or slug>/
    out = args.output
    if not out:
        raw_text, _ = _read_input(args.paper)
        aid = extract_arxiv_id(raw_text) or "paper"
        out = str(_P(__file__).resolve().parents[1] / "videos" / aid)

    result = run_pipeline(
        args.paper,
        out,
        scene_count=args.scenes,
        steps=steps,
        clean=args.clean,
        skip_backgrounds=args.skip_backgrounds,
    )

    for name, path in result.items():
        print(f"\n{name}: {path}")


if __name__ == "__main__":
    main()
