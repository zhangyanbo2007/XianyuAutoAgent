"""Quality reporting for generated Douyin reference-style videos."""

import json
import os
import subprocess
from pathlib import Path


BAD_MARKERS = ["【画面】", "【字幕】", "项目1", "项目2", "步骤1", "步骤2", "步骤3"]
INFOGRAPHIC_TEMPLATES = {
    "data_release",
    "process_flow",
    "zone_cards",
    "policy_explain",
    "material_grid",
    "channel_steps",
    "cta_summary",
}
DATA_OR_PROCESS_TEMPLATES = {
    "data_release",
    "process_flow",
    "zone_cards",
    "material_grid",
    "channel_steps",
}


def find_parse_residue(payload) -> list[str]:
    """Return bad text markers found in nested dictionaries and lists."""
    found = []

    def visit(value):
        if isinstance(value, dict):
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)
        elif isinstance(value, str):
            for marker in BAD_MARKERS:
                if marker in value and marker not in found:
                    found.append(marker)

    visit(payload)
    return found


def build_quality_report(
    output_dir,
    script: dict,
    storyboard: dict,
    video_path,
    audio_path,
    subtitle_path,
    tts_status: str,
) -> dict:
    """Write quality_report.json and quality_report.md, then return the report."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    video_path = Path(video_path)
    audio_path = Path(audio_path)
    subtitle_path = Path(subtitle_path)
    shots = storyboard.get("shots", [])
    templates = [shot.get("template", "") for shot in shots]
    residue = find_parse_residue({"script": script, "storyboard": storyboard})

    report = {
        "input": {
            "source_file": script.get("source_file", ""),
            "sheet_name": script.get("sheet_name", ""),
            "block_index": script.get("block_index", 0),
        },
        "media": {
            "video": _probe_media(video_path),
            "audio": _probe_media(audio_path),
            "subtitle_path": str(subtitle_path),
            "tts_status": tts_status,
        },
        "storyboard": {
            "shot_count": len(shots),
            "templates": templates,
            "average_shot_duration": _average_duration(shots),
        },
        "checks": {
            "has_video": _exists(video_path),
            "has_audio": _exists(audio_path),
            "has_subtitles": _exists(subtitle_path),
            "has_top_title_bar": bool(shots),
            "has_bottom_subtitle_bar": bool(shots) and all(shot.get("subtitle") for shot in shots),
            "has_infographic_body": any(template in INFOGRAPHIC_TEMPLATES for template in templates),
            "has_data_or_process": any(template in DATA_OR_PROCESS_TEMPLATES for template in templates),
            "has_parse_residue": bool(residue),
            "has_empty_placeholder": bool(residue),
        },
        "parse_residue": residue,
    }

    (output_dir / "quality_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "quality_report.md").write_text(_format_markdown(report), encoding="utf-8")
    return report


def _exists(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0


def _average_duration(shots: list[dict]) -> float:
    if not shots:
        return 0.0
    return round(sum(float(shot.get("duration_sec") or 0) for shot in shots) / len(shots), 2)


def _probe_media(path: Path) -> dict:
    info = {"path": str(path), "exists": _exists(path)}
    if not info["exists"]:
        return info

    ffmpeg = _get_ffmpeg()
    result = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", str(path), "-f", "null", "-"],
        capture_output=True,
        text=True,
    )
    info["probe_returncode"] = result.returncode
    info["summary"] = "\n".join(result.stderr.splitlines()[:16])
    return info


def _get_ffmpeg() -> str:
    try:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        if os.path.exists(ffmpeg):
            return ffmpeg
    except Exception:
        pass
    return "ffmpeg"


def _format_markdown(report: dict) -> str:
    input_info = report["input"]
    lines = [
        "# 视频质量报告",
        "",
        "## 输入",
        "",
        "| 字段 | 值 |",
        "| --- | --- |",
        f"| source_file | {input_info.get('source_file', '')} |",
        f"| sheet_name | {input_info.get('sheet_name', '')} |",
        f"| block_index | {input_info.get('block_index', '')} |",
        "",
        "## 检查项",
        "",
        "| 检查 | 结果 |",
        "| --- | --- |",
    ]

    for key, value in report["checks"].items():
        lines.append(f"| {key} | {'PASS' if value else 'FAIL'} |")

    lines.extend([
        "",
        "## 分镜",
        "",
        f"- shot_count: {report['storyboard']['shot_count']}",
        f"- average_shot_duration: {report['storyboard']['average_shot_duration']}",
        f"- templates: {', '.join(report['storyboard']['templates'])}",
        "",
        "## 解析残留",
        "",
        ", ".join(report["parse_residue"]) if report["parse_residue"] else "无",
        "",
    ])
    return "\n".join(lines)
