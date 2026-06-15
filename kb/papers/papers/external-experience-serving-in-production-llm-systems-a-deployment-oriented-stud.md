---
title: "External Experience Serving in Production LLM Systems: A Deployment-Oriented Study of Quality-Cost Trade-offs"
authors: [Lin Sun, Heming Zhang, Xiangzheng Zhang]
year: 2026
venue: "cs.CL"
tags: []
arxiv_id: "2606.11806"
ingested: "2026-06-11"
---

# 🧠 External Experience Serving in Production LLM Systems: A Deployment-Oriented Study of Quality-Cost Trade-offs

- **Authors**: Lin Sun, Heming Zhang, Xiangzheng Zhang
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.11806)
- **Category**: cs.CL

## Abstract

Production LLM systems accumulate reusable operational experience, but the practical deployment issue is not merely whether such experience can help. It is how different serving strategies trade off quality against online cost under realistic constraints. Injecting external experience can improve task quality, yet it also increases prompt burden, latency, and serving pressure. We study \textit{external experience serving} as a deployment-oriented quality-cost trade-off problem. We evaluate this question in a real production moderation setting, with tool-use and GPQA as supporting contrast tasks that expose different output-cost regimes. We compare no-experience baselines, random experience controls, global prompt injection, and retrieval-based selective injection, and analyze both task quality and serving cost. The results show that, once experience becomes case-dependent, selective retrieval provides a stronger operating point than unconditional global injection. They further show that retrieval quality matters more than simply increasing Top-$K$, and that the same serving policy can exhibit substantially different cost-benefit profiles across short-output and decode-heavy regimes. These findings suggest that external experience is best treated as a selective, cost-aware serving decision rather than as a universal add-on. Overall, in the settings studied here, external experience pays off only when both the serving interface and the task-specific cost structure make its quality gains worth the online cost.

## Notes

<!-- Claude 在此添加中文解读 -->
