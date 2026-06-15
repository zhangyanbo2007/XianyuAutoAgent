---
title: "Metadata-Aware Multi-Prompt Reasoning for Zero-Shot Accident Understanding"
authors: [Tarandeep Singh, Soumyanetra Pal, Soham Biswas, Nishanth Chandran]
year: 2026
venue: "cs.CV, cs.AI, stat.ML"
tags: []
arxiv_id: "2606.12047"
ingested: "2026-06-11"
---

# 🤖 Metadata-Aware Multi-Prompt Reasoning for Zero-Shot Accident Understanding

- **Authors**: Tarandeep Singh, Soumyanetra Pal, Soham Biswas, Nishanth Chandran
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12047)
- **Category**: cs.CV, cs.AI, stat.ML

## Abstract

In this paper, we address the problem of zero-shot understanding of accidents from surveillance videos by identifying when an impact event occurs, what type of impact it is, and where in the frame it occurs using natural language. We propose a three-stage pipeline that decomposes the accident understanding into when, what, and where. The first stage extracts a short temporal window around the impact using vision-language similarity. In the second stage, we perform metadata-driven multi-prompt reasoning with five complementary views (baseline, motion, geometry, contrast, and tiebreaker) and resolve disagreement via an entropy-gated pairwise adjudicator. Finally, we localize the impact of an open-vocabulary detector queried on the predicted accident type and scene layout, and aggregate detections across keyframes using a score-weighted centroid. Our pipeline achieves a substantial improvement in the harmonic-mean score over a centre-of-frame baseline on the zero-shot ACCIDENT @ CVPR benchmark. We show that decomposing zero-shot video understanding into temporal localization, semantic classification, and spatial grounding enable more reliable reasoning with vision-language models than direct prompting alone.

## Notes

<!-- Claude 在此添加中文解读 -->
