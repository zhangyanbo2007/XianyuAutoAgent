"""Generate detailed 15+ section video script from paper data."""

import json
import os
from openai import OpenAI
from config import API_BASE_URL, API_KEY, LLM_MODEL


def generate_script_v2(paper: dict) -> dict:
    """Generate a detailed 15-20 section video script.

    Returns structured script with per-section visual instructions.
    """
    client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)

    title = paper.get("title", "")
    summary = paper.get("summary", "")
    abstract = paper.get("abstract", "")
    abstract_zh = paper.get("abstract_zh", "")
    theme = paper.get("theme_label", "")
    arxiv_id = paper.get("arxiv_id", "")
    doi = paper.get("doi", "")
    source_url = paper.get("source_url", "")

    prompt = f"""你是一个顶级科研视频脚本写手。你的任务是根据论文信息，生成一个25-35段的中文视频解说脚本。

论文标题：{title}
分类：{theme}
中文解读：{summary}
英文摘要：{abstract[:1000]}

你现在必须生成一个25-35段的详细脚本。每个段落都必须是独立的解说词，不是复制粘贴摘要。

以下是你要输出的JSON格式（必须严格遵守，输出完整JSON）：

{{"video_title": "悬念式标题","sections": [{{"id": 0,"type": "title","duration_sec": 15,"label": "封面","text": "开场白","visual": "标题画面"}},{{"id": 1,"type": "question","duration_sec": 30,"label": "问题引入","text": "第一段解说词","visual": "画面描述"}}]}}

具体要求：
- type只能是：title/question/background/method/detail/chart/comparison/ending
- text字段：口语化中文解说词，每段50-120字，像科普博主在聊天
- visual字段：描述画面内容，要具体（"天平左边放人类大脑右边放AI芯片"不是"对比图"）
- chart类型必须有chart_data字段：{{"type":"bar","title":"标题","labels":["A","B"],"values":[78,53],"colors":["#38bdf8","#f472b6"]}}
- 前3段必须是question类型，中间要有5-8个chart类型，最后1段是ending
- 总段数必须≥25段
- 每段text必须是原创的解说词，不能复制论文摘要

现在开始生成完整JSON："""

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=12000,
        temperature=0.7,
    )

    content = response.choices[0].message.content.strip()

    # Extract JSON
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    try:
        script = json.loads(content)
    except json.JSONDecodeError:
        # Fallback: create basic script from summary
        paragraphs = [p.strip() for p in summary.split("\n") if p.strip()]
        script = {
            "video_title": title[:40],
            "sections": [],
        }
        labels = ["问题引入", "背景铺垫", "方法介绍", "实验数据", "总结展望"]
        for i, para in enumerate(paragraphs[:5]):
            script["sections"].append({
                "id": i + 1,
                "type": "detail" if i > 0 and i < 4 else ("question" if i == 0 else "ending"),
                "duration_sec": 30,
                "label": labels[i] if i < len(labels) else f"段落{i+1}",
                "text": para,
                "visual": "文字画面",
            })

    # Ensure title and ending
    if not script.get("sections") or script["sections"][0].get("type") != "title":
        script["sections"].insert(0, {
            "id": 0,
            "type": "title",
            "duration_sec": 15,
            "label": "封面",
            "text": "开场白",
            "visual": "标题画面",
        })
    if script["sections"][-1].get("type") != "ending":
        script["sections"].append({
            "id": len(script["sections"]),
            "type": "ending",
            "duration_sec": 15,
            "label": "总结",
            "text": "核心发现总结",
            "visual": "结尾画面",
        })

    # Calculate total
    script["total_duration_sec"] = sum(s.get("duration_sec", 30) for s in script["sections"])

    return script


if __name__ == "__main__":
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "papers.json")
    with open(data_path) as f:
        data = json.load(f)

    paper = data["papers"][0]
    print(f"Paper: {paper['title'][:60]}")
    script = generate_script_v2(paper)
    print(f"Sections: {len(script['sections'])}")
    print(f"Total: {script['total_duration_sec']}s")
    print(json.dumps(script, ensure_ascii=False, indent=2))
