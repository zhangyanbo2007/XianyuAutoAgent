#!/usr/bin/env python3
"""Generate static category index pages and paper-index from papers.json."""

import json
import os
import html

SITE_TITLE = "DAST Papers"

CATEGORY_DESCRIPTIONS = {
    "agents_and_autonomous_science": "涵盖自主代理、科学发现自动化、工具使用与编排系统的研究。",
    "neuroscience_and_cognitive_science": "脑机制、认知模型与神经科学对 AI 的启发。",
    "chemistry_biology_and_lab_automation": "化学、生物与自动化实验室相关的 AI 研究。",
    "reasoning_memory_and_inference_control": "推理、记忆与推理时控制的研究。",
    "multimodal_foundation_models": "多模态基础模型的研究。",
    "reinforcement_learning": "强化学习相关的研究。",
    "physics_and_ai_for_science": "物理与 AI for Science 的研究。",
    "ai_hardware_and_accelerator_design": "AI 硬件与加速器设计的研究。",
    "generative_modeling_and_diffusion": "生成建模与扩散模型的研究。",
    "robotics_and_embodied_intelligence": "机器人与具身智能的研究。",
    "safety_governance_and_reliability": "安全、治理与可靠性的研究。",
}


def escape(text):
    return html.escape(str(text or ""))


def escape_attr(text):
    return escape(text).replace("`", "&#096;")


def format_date(value):
    if not value:
        return ""
    return str(value)[:10]


def render_category_page(theme_key, theme_label, papers):
    description = CATEGORY_DESCRIPTIONS.get(theme_key, "")
    items = ""
    for p in papers:
        url = p.get("detail_url", "")
        title = escape(p.get("title", ""))
        date = format_date(p.get("published_at", ""))
        grade = escape(p.get("grade_label", ""))
        items += f"""
          <div class="category-item">
            <h2><a href="../../{escape_attr(url)}">{title}</a></h2>
            <p class="category-meta">{grade} · {date}</p>
          </div>"""

    return """<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{theme_label} | {site_title}</title>
    <meta name="description" content="{description}" />
    <meta name="robots" content="index,follow,max-image-preview:large" />
    <link rel="stylesheet" href="../../assets/styles.css" />
  </head>
  <body>
    <header class="site-header compact-header">
      <div class="header-inner">
        <div>
          <p class="eyebrow"><a href="../../">papers.dast.ai</a></p>
          <h1>{theme_label}</h1>
          <p class="subtitle">{description}</p>
        </div>
      </div>
    </header>
    <main class="detail-main">
      <div class="detail-card">
        <p class="category-meta">共 {count} 篇论文</p>
        <div class="category-list">
          {items}
        </div>
      </div>
    </main>
    <footer>
      <p>不提供 PDF 在线预览。站点只发布轻量索引和外部链接。</p>
    </footer>
  </body>
</html>""".format(
        theme_label=escape(theme_label),
        site_title=SITE_TITLE,
        description=escape(description),
        count=len(papers),
        items=items,
    )


def render_paper_index(papers, page_num, total_pages, per_page):
    start = page_num * per_page
    end = min(start + per_page, len(papers))
    page_papers = papers[start:end]

    items = ""
    for p in page_papers:
        url = p.get("detail_url", "")
        title = escape(p.get("title", ""))
        date = format_date(p.get("published_at", ""))
        theme = escape(p.get("theme_label", ""))
        items += f"""
          <div class="category-item">
            <h2><a href="../{escape_attr(url)}">{title}</a></h2>
            <p class="category-meta">{theme} · {date}</p>
          </div>"""

    # Pagination
    pagination = ""
    if total_pages > 1:
        links = []
        for i in range(total_pages):
            if i == page_num:
                links.append(f'<span aria-current="page">{i + 1}</span>')
            else:
                filename = "index.html" if i == 0 else f"page-{i + 1}.html"
                links.append(f'<a href="{filename}">{i + 1}</a>')
        pagination = f'<div class="index-pagination">{"".join(links)}</div>'

    return """<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>全部论文索引{page_suffix} | {site_title}</title>
    <meta name="description" content="全部论文索引" />
    <meta name="robots" content="index,follow,max-image-preview:large" />
    <link rel="stylesheet" href="../assets/styles.css" />
  </head>
  <body>
    <header class="site-header compact-header">
      <div class="header-inner">
        <div>
          <p class="eyebrow"><a href="../">papers.dast.ai</a></p>
          <h1>全部论文索引</h1>
          <p class="subtitle">共 {total} 篇论文</p>
        </div>
      </div>
    </header>
    <main class="detail-main">
      <div class="detail-card">
        {pagination}
        <div class="category-list">
          {items}
        </div>
        {pagination2}
      </div>
    </main>
    <footer>
      <p>不提供 PDF 在线预览。站点只发布轻量索引和外部链接。</p>
    </footer>
  </body>
</html>""".format(
        site_title=SITE_TITLE,
        total=len(papers),
        page_suffix=f"（第 {page_num + 1} 页）" if page_num > 0 else "",
        pagination=pagination,
        pagination2=pagination,
        items=items,
    )


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "data", "papers.json")

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    papers = data.get("papers", [])
    print(f"Loaded {len(papers)} papers")

    # Generate category pages
    themes = {}
    for p in papers:
        theme = p.get("theme", "")
        if theme:
            themes.setdefault(theme, []).append(p)

    categories_dir = os.path.join(base_dir, "categories")
    os.makedirs(categories_dir, exist_ok=True)

    for theme_key, theme_papers in themes.items():
        theme_label = theme_papers[0].get("theme_label", theme_key)
        theme_dir = os.path.join(categories_dir, theme_key)
        os.makedirs(theme_dir, exist_ok=True)
        page = render_category_page(theme_key, theme_label, theme_papers)
        with open(os.path.join(theme_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(page)
        print(f"  {theme_key}: {len(theme_papers)} papers")

    # Generate paper-index (paginated, 100 per page)
    per_page = 100
    total_pages = (len(papers) + per_page - 1) // per_page
    index_dir = os.path.join(base_dir, "paper-index")
    os.makedirs(index_dir, exist_ok=True)

    for page_num in range(total_pages):
        page = render_paper_index(papers, page_num, total_pages, per_page)
        filename = "index.html" if page_num == 0 else f"page-{page_num + 1}.html"
        with open(os.path.join(index_dir, filename), "w", encoding="utf-8") as f:
            f.write(page)

    print(f"Generated {total_pages} paper-index pages")
    print("Done!")


if __name__ == "__main__":
    main()
