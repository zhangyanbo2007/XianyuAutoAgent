"""Generate video script from paper data using LLM."""

import json
from openai import OpenAI
from config import API_BASE_URL, API_KEY, LLM_MODEL


def generate_script(paper: dict) -> dict:
    """Generate a structured video script from paper data.

    Returns:
        {
            "title": "悬念式中文标题",
            "sections": [
                {"label": "问题引入", "text": "...", "duration_sec": 45},
                {"label": "方法讲解", "text": "...", "duration_sec": 60},
                {"label": "结果展示", "text": "...", "duration_sec": 45},
                {"label": "价值总结", "text": "...", "duration_sec": 30},
            ],
            "total_duration_sec": 180
        }
    """
    client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)

    title = paper.get("title", "")
    summary = paper.get("summary", "")
    abstract = paper.get("abstract", "")
    theme = paper.get("theme_label", "")
    authors = paper.get("authors", [])

    prompt = f"""你是一个科研视频脚本写手。根据以下论文信息，生成一个中文视频解说脚本。

论文标题：{title}
分类：{theme}
中文解读：{summary}
英文摘要：{abstract[:500]}

请严格按以下 JSON 格式输出，不要输出其他内容：

{{
  "title": "悬念式中文视频标题（25-35字，用疑问句或惊叹句制造好奇心）",
  "sections": [
    {{
      "label": "问题引入",
      "text": "口语化的解说词，用'你有没有想过...'或'想象一下...'开头，50-80字",
      "duration_sec": 40
    }},
    {{
      "label": "方法讲解",
      "text": "讲解论文的核心方法/机制，用通俗类比，60-100字",
      "duration_sec": 55
    }},
    {{
      "label": "结果展示",
      "text": "关键实验结果和数据，用具体数字增强说服力，50-80字",
      "duration_sec": 40
    }},
    {{
      "label": "价值总结",
      "text": "为什么这项研究重要，对未来的启示，40-60字",
      "duration_sec": 30
    }}
  ]
}}

要求：
- 语气口语化、有节奏感，像在跟朋友聊天
- 不要出现英文专业术语，必要时用中文解释
- 每段之间自然过渡
- text 字段只输出纯文本，不要有标点符号以外的格式"""

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
        temperature=0.7,
    )

    content = response.choices[0].message.content.strip()

    # Extract JSON from response (handle markdown code blocks)
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    try:
        script = json.loads(content)
    except json.JSONDecodeError:
        # Fallback: create a basic script from summary
        paragraphs = [p.strip() for p in summary.split("\n") if p.strip()]
        labels = ["问题引入", "方法讲解", "结果展示", "价值总结"]
        script = {
            "title": title[:35],
            "sections": [],
        }
        for i, para in enumerate(paragraphs[:4]):
            script["sections"].append({
                "label": labels[i] if i < len(labels) else f"第{i+1}段",
                "text": para,
                "duration_sec": 40,
            })

    # Calculate total duration
    script["total_duration_sec"] = sum(s.get("duration_sec", 40) for s in script["sections"])

    return script


if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "papers.json")
    with open(data_path) as f:
        data = json.load(f)

    # Test with first paper
    paper = data["papers"][0]
    print(f"Paper: {paper['title'][:60]}")
    script = generate_script(paper)
    print(json.dumps(script, ensure_ascii=False, indent=2))
