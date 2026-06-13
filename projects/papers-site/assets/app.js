const state = {
  papers: [],
  filtered: [],
  query: "",
  theme: "all",
  grade: "all",
  video: "all",
  sort: "collected_desc",
};

const els = {
  list: document.querySelector("#paper-list"),
  empty: document.querySelector("#empty-state"),
  search: document.querySelector("#search"),
  theme: document.querySelector("#theme-filter"),
  grade: document.querySelector("#grade-filter"),
  video: document.querySelector("#video-filter"),
  sort: document.querySelector("#sort-select"),
  reset: document.querySelector("#reset-button"),
  categoryLinks: document.querySelector("#category-links"),
  count: document.querySelector("#result-count"),
  total: document.querySelector("#stat-total"),
  videoStat: document.querySelector("#stat-video"),
  updated: document.querySelector("#stat-updated"),
  modal: document.querySelector("#player-modal"),
  playerTitle: document.querySelector("#player-title"),
  playerBody: document.querySelector("#player-body"),
};

const collator = new Intl.Collator("zh-CN", { numeric: true, sensitivity: "base" });

fetch("data/papers.json")
  .then((response) => {
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  })
  .then((data) => init(data))
  .catch((error) => {
    els.list.innerHTML = `<article class="paper-card">数据加载失败：${escapeHtml(error.message)}</article>`;
  });

function init(data) {
  state.papers = data.papers || [];
  populateStats(data);
  populateFilters();
  populateCategoryLinks();
  bindEvents();
  applyFilters();
}

function populateStats(data) {
  els.total.textContent = String(data.stats?.total ?? state.papers.length);
  els.videoStat.textContent = String(data.stats?.with_public_video ?? state.papers.filter(hasPublicVideo).length);
  els.updated.textContent = formatDateOnly(data.generated_at);
}

function populateFilters() {
  const themes = uniqueOptions(state.papers, "theme", "theme_label");
  const grades = uniqueOptions(state.papers, "grade", "grade_label");
  fillSelect(els.theme, "全部分类", themes);
  fillSelect(els.grade, "全部等级", grades);
}

function uniqueOptions(items, valueKey, labelKey) {
  const map = new Map();
  for (const item of items) {
    const value = item[valueKey] || "";
    if (value) map.set(value, item[labelKey] || value);
  }
  return [...map.entries()].sort((a, b) => collator.compare(a[1], b[1]));
}

function fillSelect(select, allLabel, options) {
  select.innerHTML = `<option value="all">${allLabel}</option>`;
  for (const [value, label] of options) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    select.appendChild(option);
  }
}

function populateCategoryLinks() {
  if (!els.categoryLinks) return;
  const counts = new Map();
  const labels = new Map();
  for (const paper of state.papers) {
    if (!paper.theme) continue;
    counts.set(paper.theme, (counts.get(paper.theme) || 0) + 1);
    labels.set(paper.theme, paper.theme_label || paper.theme);
  }
  const items = [...counts.entries()].sort((a, b) => b[1] - a[1] || collator.compare(labels.get(a[0]), labels.get(b[0])));
  els.categoryLinks.innerHTML = items
    .map(([theme, count]) => {
      const label = labels.get(theme) || theme;
      return `<a href="categories/${escapeAttr(theme)}/">${escapeHtml(label)}<span>${escapeHtml(String(count))}</span></a>`;
    })
    .join("");
}

function bindEvents() {
  const params = new URLSearchParams(window.location.search);
  const initialQuery = params.get("q") || "";
  if (initialQuery) {
    state.query = initialQuery.trim().toLowerCase();
    els.search.value = initialQuery;
  }
  els.search.addEventListener("input", () => {
    state.query = els.search.value.trim().toLowerCase();
    applyFilters();
  });
  els.theme.addEventListener("change", () => {
    state.theme = els.theme.value;
    applyFilters();
  });
  els.grade.addEventListener("change", () => {
    state.grade = els.grade.value;
    applyFilters();
  });
  els.video.addEventListener("change", () => {
    state.video = els.video.value;
    applyFilters();
  });
  els.sort.addEventListener("change", () => {
    state.sort = els.sort.value;
    applyFilters();
  });
  els.reset.addEventListener("click", resetFilters);
  els.list.addEventListener("click", handleListClick);
  document.querySelectorAll("[data-close-player]").forEach((node) => {
    node.addEventListener("click", closePlayer);
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closePlayer();
  });
}

function resetFilters() {
  state.query = "";
  state.theme = "all";
  state.grade = "all";
  state.video = "all";
  state.sort = "collected_desc";
  els.search.value = "";
  els.theme.value = "all";
  els.grade.value = "all";
  els.video.value = "all";
  els.sort.value = "collected_desc";
  applyFilters();
}

function applyFilters() {
  const query = normalize(state.query);
  state.filtered = state.papers.filter((paper) => {
    if (state.theme !== "all" && paper.theme !== state.theme) return false;
    if (state.grade !== "all" && paper.grade !== state.grade) return false;
    const publicVideo = hasPublicVideo(paper);
    if (state.video === "with" && !publicVideo) return false;
    if (state.video === "without" && publicVideo) return false;
    if (!query) return true;
    return searchableText(paper).includes(query);
  });
  sortPapers(state.filtered);
  render();
}

function sortPapers(items) {
  const dateValue = (value) => (value ? Date.parse(value) || 0 : 0);
  items.sort((a, b) => {
    if (state.sort === "published_desc") return dateValue(b.published_at) - dateValue(a.published_at);
    if (state.sort === "published_asc") return dateValue(a.published_at) - dateValue(b.published_at);
    if (state.sort === "title_asc") return collator.compare(a.title, b.title);
    return (b.collection_order || 0) - (a.collection_order || 0);
  });
}

function render() {
  els.count.textContent = String(state.filtered.length);
  els.empty.hidden = state.filtered.length !== 0;
  els.list.innerHTML = state.filtered.map(renderPaper).join("");
}

function renderPaper(paper) {
  const primaryVideo = firstPublicVideo(paper);
  const youtubeVideo = firstYoutubeVideo(paper);
  const videoBadge = primaryVideo
    ? `<span class="badge video">有讲解视频</span>`
    : `<span class="badge no-video">暂无讲解视频</span>`;
  const title = escapeHtml(paper.title);
  const detailUrl = paper.detail_url || (paper.slug ? `papers/${paper.slug}/` : "");
  const titleHtml = detailUrl
    ? `<a href="${escapeAttr(detailUrl)}">${title}</a>`
    : title;
  const links = renderLinks(paper);

  return `
    <article class="paper-card">
      <div class="paper-top">
        <div>
          <h2 class="paper-title">${titleHtml}</h2>
          <div class="paper-id">${escapeHtml(paper.id)}</div>
        </div>
        <div class="badges">
          <span class="badge">${escapeHtml(paper.theme_label || paper.theme)}</span>
          ${paper.grade ? `<span class="badge grade">${escapeHtml(paper.grade_label || paper.grade)}</span>` : ""}
          ${videoBadge}
        </div>
      </div>
      <div class="${youtubeVideo ? "paper-body with-cover" : "paper-body"}">
        ${youtubeVideo ? renderYoutubeCover(paper, youtubeVideo.video, youtubeVideo.url) : ""}
        <div>
          ${paper.summary ? `<p class="summary">${escapeHtml(paper.summary)}</p>` : ""}
          ${primaryVideo ? renderVideoInfo(primaryVideo) : ""}
        </div>
      </div>
      <div class="meta">
        <span>发表：${escapeHtml(formatDateOnly(paper.published_at) || "未知")}</span>
        ${paper.doi ? `<span>DOI：${escapeHtml(paper.doi)}</span>` : ""}
        ${!paper.doi && paper.arxiv_id ? `<span>arXiv：${escapeHtml(paper.arxiv_id)}</span>` : ""}
        <span>收录顺序：#${escapeHtml(String(paper.collection_order || ""))}</span>
      </div>
      ${links}
    </article>
  `;
}

function renderYoutubeCover(paper, video, url) {
  const videoId = youtubeVideoId(url);
  if (!videoId) return "";
  return `
    <div class="video-cover-block">
      <a class="cover-link youtube-cover-link" href="${escapeAttr(url)}" target="_blank" rel="noopener noreferrer" aria-label="打开 YouTube：${escapeAttr(video.title || paper.title)}">
        <img class="cover" src="${escapeAttr(youtubeThumbnailUrl(videoId))}" alt="${escapeHtml(video.title || paper.title)} YouTube 封面" loading="lazy" />
        <span class="play-mark youtube-mark" aria-hidden="true">▶</span>
      </a>
      ${renderPlatformIcons(video)}
    </div>
  `;
}

function renderVideoInfo(video) {
  const description = video.description || video.x_post || "";
  return `
    <div class="video-info">
      <div class="video-title">${escapeHtml(video.title || "解读视频素材")}</div>
      ${description ? `<p>${escapeHtml(truncate(description, 180))}</p>` : ""}
    </div>
  `;
}

function renderPlatformIcons(video) {
  const urls = publicVideoUrls(video);
  if (!urls.length) return "";
  return `<div class="platform-row">${urls.map((url) => platformLink(url)).join("")}</div>`;
}

function platformLink(url) {
  const platform = detectPlatform(url);
  return `<a class="platform ${platform.key}" href="${escapeAttr(url)}" target="_blank" rel="noopener noreferrer" title="${escapeAttr(platform.label)}">${platform.icon}<span>${escapeHtml(platform.short)}</span></a>`;
}

function detectPlatform(url) {
  if (/bilibili\.com|b23\.tv/i.test(url)) {
    return {
      key: "bilibili",
      label: "Bilibili",
      short: "B站",
      icon: `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="6" width="18" height="14" rx="3"></rect><path d="M8 4 6 2M16 4l2-2M9 10v5M15 10v5"></path></svg>`,
    };
  }
  if (/youtu\.be|youtube\.com/i.test(url)) {
    return {
      key: "youtube",
      label: "YouTube",
      short: "YouTube",
      icon: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M22 12s0-3.4-.44-5a2.8 2.8 0 0 0-2-2C17.8 4.5 12 4.5 12 4.5s-5.8 0-7.56.5a2.8 2.8 0 0 0-2 2C2 8.6 2 12 2 12s0 3.4.44 5a2.8 2.8 0 0 0 2 2c1.76.5 7.56.5 7.56.5s5.8 0 7.56-.5a2.8 2.8 0 0 0 2-2c.44-1.6.44-5 .44-5Z"></path><path d="m10 9 5.2 3L10 15Z" class="youtube-play"></path></svg>`,
    };
  }
  return { key: "external", label: "外部视频", short: "外链", icon: "" };
}

function firstPublicVideo(paper) {
  return (paper.videos || []).find((video) => publicVideoUrls(video).length) || null;
}

function firstYoutubeVideo(paper) {
  for (const video of paper.videos || []) {
    const url = publicVideoUrls(video).find((item) => youtubeVideoId(item));
    if (url) return { video, url };
  }
  return null;
}

function hasPublicVideo(paper) {
  return Boolean(firstPublicVideo(paper));
}

function publicVideoUrls(video) {
  return [...new Set([...(video.platform_urls || []), video.url].filter(isPublicVideoUrl))];
}

function isPublicVideoUrl(url) {
  return /(?:bilibili\.com\/video\/|b23\.tv\/|youtube\.com\/watch\?v=|youtu\.be\/)/i.test(String(url || ""));
}

function youtubeVideoId(url) {
  const match = String(url || "").match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([A-Za-z0-9_-]+)/);
  return match ? match[1] : "";
}

function youtubeThumbnailUrl(videoId) {
  return `https://i.ytimg.com/vi/${encodeURIComponent(videoId)}/mqdefault.jpg`;
}

function handleListClick(event) {
  const button = event.target.closest("[data-video-url]");
  if (!button) return;
  const url = button.getAttribute("data-video-url");
  const title = button.getAttribute("data-video-title") || "解读视频";
  if (!url) return;
  openPlayer(url, title);
}

function openPlayer(url, title) {
  const embed = embedUrl(url);
  els.playerTitle.textContent = title;
  if (embed) {
    els.playerBody.innerHTML = `<iframe src="${escapeAttr(embed)}" title="${escapeAttr(title)}" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>`;
    els.modal.hidden = false;
    document.body.classList.add("modal-open");
    return;
  }
  window.open(url, "_blank", "noopener,noreferrer");
}

function closePlayer() {
  if (!els.modal || els.modal.hidden) return;
  els.modal.hidden = true;
  els.playerBody.innerHTML = "";
  document.body.classList.remove("modal-open");
}

function embedUrl(url) {
  const youtube = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([A-Za-z0-9_-]+)/);
  if (youtube) return `https://www.youtube.com/embed/${youtube[1]}`;
  const bilibili = url.match(/bilibili\.com\/video\/(BV[A-Za-z0-9]+)/i);
  if (bilibili) return `https://player.bilibili.com/player.html?bvid=${bilibili[1]}&autoplay=1`;
  return "";
}

function renderLinks(paper) {
  const links = [];
  if (paper.source_url) links.push(link("论文链接", paper.source_url));
  for (const url of paper.project_urls || []) links.push(link("项目", url));
  for (const url of paper.repo_urls || []) links.push(link("代码", url));
  if (paper.pdf_download_url) links.push(link("PDF 下载", paper.pdf_download_url));
  for (const video of paper.videos || []) {
    for (const url of publicVideoUrls(video)) links.push(link("解读视频", url));
  }
  if (!links.length) return "";
  return `<div class="links">${links.join("")}</div>`;
}

function truncate(value, length) {
  const text = String(value || "").replace(/\s+/g, " ").trim();
  return text.length > length ? `${text.slice(0, length - 1)}…` : text;
}

function link(label, url) {
  return `<a href="${escapeAttr(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)}</a>`;
}

function searchableText(paper) {
  return normalize(
    [
      paper.id,
      paper.title,
      paper.summary,
      paper.theme,
      paper.theme_label,
      paper.grade,
      paper.grade_label,
      paper.published_at,
      ...(paper.videos || []).map((video) => video.title),
    ].join(" ")
  );
}

function normalize(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[^\p{Letter}\p{Number}]+/gu, " ")
    .trim();
}

function formatDateOnly(value) {
  if (!value) return "";
  const text = String(value);
  const match = text.match(/\d{4}-\d{2}-\d{2}/);
  return match ? match[0] : text.slice(0, 10);
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value).replaceAll("`", "&#096;");
}
