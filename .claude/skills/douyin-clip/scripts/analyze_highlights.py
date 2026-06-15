#!/usr/bin/env python3
"""
高光时刻分析模块
使用 Claude API 分析转写文本，自动识别适合做切片的精彩片段
"""
import os
import sys
import json
import argparse
from pathlib import Path

# 路径设置
SKILL_DIR = Path(__file__).parent.parent
CONFIG_PATH = SKILL_DIR / "config.yaml"


def load_config():
    import yaml
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def load_transcript(transcript_path: str) -> dict:
    """加载转写结果"""
    with open(transcript_path) as f:
        return json.load(f)


def format_segments_for_prompt(segments: list) -> str:
    """将 segments 格式化为带时间戳的文本，供 AI 分析"""
    lines = []
    for seg in segments:
        start = seg["start"]
        end = seg["end"]
        text = seg["text"]
        # 格式化时间戳为 mm:ss
        start_str = f"{int(start//60):02d}:{int(start%60):02d}"
        end_str = f"{int(end//60):02d}:{int(end%60):02d}"
        lines.append(f"[{start_str}-{end_str}] {text}")
    return "\n".join(lines)


def analyze_with_clue(segments: list, video_title: str = "",
                       min_duration: int = 15, max_duration: int = 60,
                       max_clips: int = 8) -> list:
    """
    使用 Claude API 分析高光时刻

    Args:
        segments: 转写片段列表
        video_title: 视频标题（提供上下文）
        min_duration: 最短切片时长（秒）
        max_duration: 最长切片时长（秒）
        max_clips: 最多输出几个切片

    Returns:
        list: 高光片段列表
    """
    from openai import OpenAI

    # 读取 API 配置 — 优先百炼 DashScope，其次 OpenAI
    config = load_config()

    # 百炼 DashScope（OpenAI 兼容接口）
    dashscope_key = config.get("dashscope_api_key") or os.environ.get("DASHSCOPE_API_KEY")
    if dashscope_key:
        api_key = dashscope_key
        base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        model = "qwen3.5-flash"  # 百炼上可访问的模型
    else:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model = "gpt-4o-mini"

    client = OpenAI(api_key=api_key, base_url=base_url)

    # 格式化转写文本
    formatted = format_segments_for_prompt(segments)

    # 计算总时长
    total_duration = segments[-1]["end"] if segments else 0

    prompt = f"""你是一个专业的短视频切片编辑。请分析以下抖音视频的转写文本，找出最适合做成短视频切片的高光时刻。

视频标题: {video_title}
视频总时长: {total_duration:.0f}秒
目标切片时长: {min_duration}-{max_duration}秒
最多输出: {max_clips} 个切片

转写文本（带时间戳）:
{formatted}

## 选择标准（按优先级）

1. **搞笑/反转** — 有笑点、意外反转、荒诞情节
2. **名场面** — 金句、有共鸣的发言、情绪爆发点
3. **完整故事** — 有起因-经过-结果的完整叙事弧
4. **互动高潮** — 可能引发弹幕/评论讨论的点
5. **视觉冲击** — 虽然看不到画面，但从文字推断有精彩画面

## 时间合并规则

相邻的高光 segments 应该合并成一个连续片段。例如:
- 如果 [00:15-00:25] 和 [00:25-00:40] 都是高光，应该合并为 [00:15-00:40]
- 切片最短 {min_duration} 秒，最长 {max_duration} 秒

## 输出格式

请严格输出 JSON 数组，不要包含其他文字:

```json
[
  {{
    "title": "切片标题（吸引眼球的中文标题）",
    "start": 15.5,
    "end": 45.2,
    "reason": "选择理由（一句话）",
    "tags": ["搞笑", "反转"],
    "suggested_caption": "发布时的抖音文案（带emoji）",
    "virality_score": 8
  }}
]
```

virality_score 评分 1-10，表示你认为这个片段在抖音上的爆款潜力。"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个专业的短视频内容分析师。只输出 JSON，不要其他文字。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=4000,
        )

        content = response.choices[0].message.content.strip()

        # 提取 JSON（可能被 ```json 包裹）
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        highlights = json.loads(content)

        # 验证和排序
        valid = []
        for h in highlights:
            if all(k in h for k in ["title", "start", "end", "reason"]):
                # 确保时间范围合理
                h["start"] = max(0, float(h["start"]))
                h["end"] = min(total_duration, float(h["end"]))
                if h["end"] - h["start"] >= min_duration:
                    valid.append(h)

        # 按 virality_score 降序排列
        valid.sort(key=lambda x: x.get("virality_score", 0), reverse=True)

        # 只保留最多 max_clips 个
        return valid[:max_clips]

    except json.JSONDecodeError as e:
        print(f"⚠️  AI 返回的 JSON 解析失败: {e}")
        print(f"   原始返回: {content[:500]}")
        return []
    except Exception as e:
        print(f"❌ API 调用失败: {e}")
        return []


def analyze_transcript_file(transcript_path: str, output_path: str = None) -> list:
    """分析转写文件并保存高光结果"""
    config = load_config()
    transcript = load_transcript(transcript_path)

    clip_config = config.get("clip", {})
    highlight_config = config.get("highlight", {})

    video_title = Path(transcript["video_path"]).stem

    print(f"🔍 分析高光时刻: {video_title}")
    print(f"   转写片段数: {transcript['segment_count']}")
    print(f"   视频时长: {transcript['duration']}秒")

    highlights = analyze_with_clue(
        segments=transcript["segments"],
        video_title=video_title,
        min_duration=clip_config.get("min_duration", 15),
        max_duration=clip_config.get("max_duration", 60),
        max_clips=highlight_config.get("max_clips_per_video", 8),
    )

    if not highlights:
        print("⚠️  未找到高光片段")
        return []

    print(f"\n✨ 找到 {len(highlights)} 个高光片段:")
    for i, h in enumerate(highlights, 1):
        duration = h["end"] - h["start"]
        print(f"   {i}. [{h['start']:.1f}s - {h['end']:.1f}s] ({duration:.0f}秒)")
        print(f"      {h['title']}")
        print(f"      理由: {h['reason']}")

    # 保存结果
    if output_path is None:
        output_dir = SKILL_DIR / config["paths"]["highlights"]
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{video_title}.json"
    else:
        output_path = Path(output_path)

    result = {
        "video_path": transcript["video_path"],
        "video_title": video_title,
        "total_duration": transcript["duration"],
        "highlights": highlights,
        "highlight_count": len(highlights),
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n💾 高光分析结果已保存: {output_path}")
    return highlights


def main():
    parser = argparse.ArgumentParser(description="视频高光时刻分析")
    parser.add_argument("transcript", help="转写结果 JSON 文件路径")
    parser.add_argument("--output", "-o", help="输出路径")
    args = parser.parse_args()

    highlights = analyze_transcript_file(args.transcript, args.output)

    if not highlights:
        sys.exit(1)


if __name__ == "__main__":
    main()
