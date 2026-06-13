#!/usr/bin/env python3
"""Generate static paper detail pages from papers.json."""

import json
import os
import html

SITE_TITLE = "DAST Papers"
SITE_URL = "https://papers.dast.ai"


def escape(text):
    return html.escape(str(text or ""))


def escape_attr(text):
    return escape(text).replace("`", "&#096;")


def format_date(value):
    if not value:
        return ""
    text = str(value)
    match_len = 10 if len(text) >= 10 else len(text)
    return text[:match_len]


def render_detail_page(paper, all_papers):
    title = paper.get("title", "")
    theme_label = paper.get("theme_label", paper.get("theme", ""))
    grade_label = paper.get("grade_label", paper.get("grade", ""))
    published = format_date(paper.get("published_at", ""))
    summary = paper.get("summary", "")
    abstract = paper.get("abstract", "")
    abstract_zh = paper.get("abstract_zh", "")
    doi = paper.get("doi", "")
    arxiv_id = paper.get("arxiv_id", "")
    source_url = paper.get("source_url", "")
    detail_url = paper.get("detail_url", "")
    has_video = paper.get("has_video", False)
    videos = paper.get("videos", [])
    repo_urls = paper.get("repo_urls", [])
    project_urls = paper.get("project_urls", [])
    pdf_download_url = paper.get("pdf_download_url", "")

    # Find related papers (same theme)
    related = [p for p in all_papers if p.get("theme") == paper.get("theme") and p.get("id") != paper.get("id")][:6]

    # Build badges
    video_badge = '<span class="badge video">有讲解视频</span>' if has_video else '<span class="badge no-video">暂无讲解视频</span>'

    # Build meta
    meta_parts = []
    if published:
        meta_parts.append(f'<div><dt>发表时间</dt><dd>{escape(published)}</dd></div>')
    if doi:
        meta_parts.append(f'<div><dt>DOI</dt><dd><a href="https://doi.org/{escape_attr(doi)}" target="_blank" rel="noopener noreferrer">{escape(doi)}</a></dd></div>')
    if arxiv_id:
        meta_parts.append(f'<div><dt>arXiv</dt><dd><a href="https://arxiv.org/abs/{escape_attr(arxiv_id)}" target="_blank" rel="noopener noreferrer">{escape(arxiv_id)}</a></dd></div>')

    # Build fact list from summary
    fact_items = ""
    if summary:
        paragraphs = [p.strip() for p in summary.split("\n") if p.strip()]
        labels = ["问题/背景", "方法/机制", "结果/证据", "收录价值"]
        for i, para in enumerate(paragraphs):
            label = labels[i] if i < len(labels) else f"要点 {i+1}"
            fact_items += f'<div><dt>{escape(label)}</dt><dd>{escape(para)}</dd></div>'

    # Build abstract section
    abstract_section = ""
    if abstract or abstract_zh:
        abstract_section = """
        <section class="detail-section abstract-section">
          <h2>原始摘要与中文对照</h2>
          <div class="abstract-pair">
            <div class="abstract-block abstract-translation">
              <h3>中文对照翻译</h3>
              <p>{abstract_zh}</p>
            </div>
            <div class="abstract-block abstract-original">
              <h3>原始摘要</h3>
              <p>{abstract}</p>
            </div>
          </div>
        </section>""".format(abstract_zh=escape(abstract_zh), abstract=escape(abstract))

    # Build citation
    citation_section = ""
    if source_url:
        bibtex = f"""@misc{{paper{published.replace("-", "")}{paper.get("slug", "").replace("-", "")[:10]},
  title = {{{title}}},
  year = {{{published[:4] if published else "Unknown"}}},
  url = {{{source_url}}},
  note = {{DAST Papers collection page: {SITE_URL}/{detail_url}}}
}}"""
        apa = f"Unknown author ({published[:4] if published else 'Unknown'}). {title}. {source_url}"
        citation_section = """
        <section class="detail-section citation-section">
          <h2>引用</h2>
          <div class="citation-grid">
            <div class="citation-box">
              <h3>BibTeX</h3>
              <pre><code>{bibtex}</code></pre>
            </div>
            <div class="citation-box">
              <h3>APA</h3>
              <p>{apa}</p>
            </div>
          </div>
        </section>""".format(bibtex=escape(bibtex), apa=escape(apa))

    # Build related
    related_section = ""
    if related:
        items = ""
        for r in related:
            r_url = r.get("detail_url", "")
            r_title = escape(r.get("title", ""))
            r_theme = escape(r.get("theme_label", ""))
            r_date = format_date(r.get("published_at", ""))
            items += f"""
            <a class="related-item" href="../../{escape_attr(r_url)}">
              <span>{r_title}</span>
              <small>{r_theme} · {r_date}</small>
            </a>"""
        related_section = f"""
        <section class="detail-section">
          <h2>相关论文</h2>
          <div class="related-list">{items}
          </div>
        </section>"""

    # Build links
    links_html = ""
    link_items = []
    if source_url:
        link_items.append(f'<a href="{escape_attr(source_url)}" target="_blank" rel="noopener noreferrer">论文链接</a>')
    for url in project_urls:
        link_items.append(f'<a href="{escape_attr(url)}" target="_blank" rel="noopener noreferrer">项目</a>')
    for url in repo_urls:
        link_items.append(f'<a href="{escape_attr(url)}" target="_blank" rel="noopener noreferrer">代码</a>')
    if pdf_download_url:
        link_items.append(f'<a href="{escape_attr(pdf_download_url)}" target="_blank" rel="noopener noreferrer">PDF 下载</a>')
    if link_items:
        links_html = f"""
        <section class="detail-section">
          <h2>链接</h2>
          <div class="links">{"".join(link_items)}</div>
        </section>"""

    # Expandable summary
    expander = ""
    if summary:
        paragraphs = "".join(f"<p>{escape(p)}</p>" for p in summary.split("\n") if p.strip())
        expander = f"""
        <details class="detail-section detail-expander">
          <summary>完整收录解读</summary>
          <div class="detail-expander-body">
          {paragraphs}
          </div>
        </details>"""

    page = """<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title} | {site_title}</title>
    <meta name="description" content="{description}" />
    <meta name="robots" content="index,follow,max-image-preview:large" />
    <link rel="canonical" href="{site_url}/{detail_url}" />
    <link rel="stylesheet" href="../../assets/styles.css" />
    <meta property="og:type" content="article" />
    <meta property="og:site_name" content="{site_title}" />
    <meta property="og:title" content="{title}" />
    <meta property="og:description" content="{description}" />
    <meta property="og:url" content="{site_url}/{detail_url}" />
    <meta name="twitter:card" content="summary" />
    <meta name="twitter:title" content="{title}" />
    <meta name="twitter:description" content="{description}" />
  </head>
  <body>
    <header class="site-header compact-header">
      <div class="header-inner">
        <div>
          <p class="eyebrow"><a href="../../">{site_title_lower}</a></p>
          <h1>{title}</h1>
          <p class="subtitle">{theme_label} · 发表：{published}</p>
        </div>
      </div>
    </header>
    <main class="detail-main">
      <article class="paper-card detail-card">
        <div class="badges detail-badges">
          <span class="badge">{theme_label}</span>
          <span class="badge grade">{grade_label}</span>
          {video_badge}
        </div>
        <dl class="detail-meta">
          {meta_parts}
        </dl>

        <section class="detail-section fact-section">
          <h2>核心要点</h2>
          <dl class="fact-list">
          {fact_items}
          </dl>
        </section>

        {expander}

        {abstract_section}

        {citation_section}

        {related_section}
        {links_html}
      </article>
    </main>
    <footer>
      <p>不提供 PDF 在线预览。站点只发布轻量索引和外部链接。</p>
    </footer>
  </body>
</html>""".format(
        title=escape(title),
        site_title=SITE_TITLE,
        site_title_lower="papers.dast.ai",
        site_url=SITE_URL,
        detail_url=escape_attr(detail_url),
        description=escape((summary or "")[:200]),
        theme_label=escape(theme_label),
        grade_label=escape(grade_label),
        published=escape(published),
        video_badge=video_badge,
        meta_parts="\n          ".join(meta_parts),
        fact_items=fact_items,
        expander=expander,
        abstract_section=abstract_section,
        citation_section=citation_section,
        related_section=related_section,
        links_html=links_html,
    )
    return page


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "data", "papers.json")

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    papers = data.get("papers", [])
    print(f"Loaded {len(papers)} papers")

    papers_dir = os.path.join(base_dir, "papers")
    os.makedirs(papers_dir, exist_ok=True)

    count = 0
    for paper in papers:
        slug = paper.get("slug", "")
        if not slug:
            continue
        detail_dir = os.path.join(papers_dir, slug)
        os.makedirs(detail_dir, exist_ok=True)
        page = render_detail_page(paper, papers)
        with open(os.path.join(detail_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(page)
        count += 1

    print(f"Generated {count} detail pages")


if __name__ == "__main__":
    main()
