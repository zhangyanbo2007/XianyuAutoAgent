---
title: "When Does Language Matter? Multilingual Instructions Reveal Step-wise Language Sensitivity in Vision-Language-Action Models"
authors: [Xuan Dong, Zhe Han, Tianhao Niu, Qingfu Zhu, Wanxiang Che]
year: 2026
venue: "cs.CL"
tags: []
arxiv_id: "2606.11906"
ingested: "2026-06-11"
---

# 🤖 When Does Language Matter? Multilingual Instructions Reveal Step-wise Language Sensitivity in Vision-Language-Action Models

- **Authors**: Xuan Dong, Zhe Han, Tianhao Niu, Qingfu Zhu, Wanxiang Che
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.11906)
- **Category**: cs.CL

## Abstract

Vision-Language-Action (VLA) models have shown strong performance in language-conditioned robotic manipulation, yet their robustness to linguistic variation remains poorly understood. In this work, we present the first systematic multilingual evaluation of VLA models by translating the LIBERO benchmark into ten languages, revealing severe performance degradation under non-English instructions, with success rates dropping by 30-50%. Through fine-grained analysis of task executions, we find that language influence is highly non-uniform across steps: certain steps exhibit strong language dependence and dominate overall task failure, while others are largely language-agnostic. Based on this insight, we propose a step-wise inference-time intervention that aligns representations according to step language sensitivity, substantially improving performance under linguistic variation. Our results indicate that language robustness in VLA models is fundamentally a step-wise control problem, highlighting the importance of temporally structured analysis for reliable embodied agents.

## Notes

<!-- Claude 在此添加中文解读 -->
