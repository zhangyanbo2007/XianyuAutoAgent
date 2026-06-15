---
title: "Which Speech Representation Better Matches Text-Native Reasoning? A Study of Speech-Text Alignment on Frame Rate and Representation"
authors: [Zhen Ye, Xu Tan, Yiming Li, Guangyan Zhang, Chimin Chan]
year: 2026
venue: "eess.AS, cs.CL, cs.SD"
tags: []
arxiv_id: "2606.12199"
ingested: "2026-06-11"
---

# 🤖 Which Speech Representation Better Matches Text-Native Reasoning? A Study of Speech-Text Alignment on Frame Rate and Representation

- **Authors**: Zhen Ye, Xu Tan, Yiming Li, Guangyan Zhang, Chimin Chan
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12199)
- **Category**: eess.AS, cs.CL, cs.SD

## Abstract

Spoken dialogue models typically start from text LLM backbones, yet reasoning often degrades when conditioning on speech instead of text. We attribute part of this modality gap to a temporal-granularity mismatch: speech tokens are temporally redundant and far longer than text under matched semantics, diluting per-token semantic density and weakening text-native reasoning dynamics. We study speech token design as a representation selection problem and sweep frame rates under a frozen LLM backbone with a fixed information rate. To make low frame rates feasible, we introduce factorized FSQ and a lightweight non-autoregressive audio LM head, scaling capacity to nearly 300\,bits/frame without sacrificing efficient prediction. With the bottleneck removed, we sweep frame rates (50$\rightarrow$2.08\,Hz) and alignment depth, and observe a consistent best regime for speech QA at 4.17\,Hz with intermediate-layer representation alignment.

## Notes

<!-- Claude 在此添加中文解读 -->
