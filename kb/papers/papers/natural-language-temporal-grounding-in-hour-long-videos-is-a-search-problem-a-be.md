---
title: "Natural-Language Temporal Grounding in Hour-Long Videos is a Search Problem: A Benchmark and Empirical Decomposition"
authors: [Sukmin Seo, Geewook Kim]
year: 2026
venue: "cs.CV, cs.AI"
tags: []
arxiv_id: "2606.12300"
ingested: "2026-06-11"
---

# 🤖 Natural-Language Temporal Grounding in Hour-Long Videos is a Search Problem: A Benchmark and Empirical Decomposition

- **Authors**: Sukmin Seo, Geewook Kim
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12300)
- **Category**: cs.CV, cs.AI

## Abstract

Temporal grounding--returning the interval $[t_s, t_e]$ for a natural-language query over a video--is the language interface to long-form video, yet has been studied on short videos; the dynamics of hour-scale natural-language grounding remain underexplored. We take the position that at hour-scale, the binding constraint is search, not recognition: Video-LLMs are bottlenecked not by localizing a nearby event, but--given a natural-language query--by searching for the relevant region of a long video. To test this, we release ExtremeWhenBench, the first open hour-scale grounding benchmark (2,273 queries over 194 videos, mean 75.7 min, max 9 hr) with an open-form query distribution. Every open Video-LLM collapses while a frame-level retrieval baseline outperforms them; a failure taxonomy attributes 85% of failures to search; and a retrieve-then-ground hybrid recovers 6.7x over the monolithic Video-LLM--mirroring retrieve-then-read in open-domain QA.

## Notes

<!-- Claude 在此添加中文解读 -->
