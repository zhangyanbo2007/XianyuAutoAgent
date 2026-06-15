---
title: "Task-Aligned Stability Analysis of Vision-Language Models for Autonomous Driving Hazard Detection"
authors: [Everett Richards]
year: 2026
venue: "cs.CV, cs.AI, cs.RO"
tags: []
arxiv_id: "2606.11889"
ingested: "2026-06-11"
---

# 🤖 Task-Aligned Stability Analysis of Vision-Language Models for Autonomous Driving Hazard Detection

- **Authors**: Everett Richards
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.11889)
- **Category**: cs.CV, cs.AI, cs.RO

## Abstract

Vision-language models (VLMs) are increasingly used for scene understanding in autonomous driving, but robustness analysis often relies on task-agnostic embedding stability alone. We study whether corruption-induced embedding drift predicts changes in a task-aligned hazard score derived from CLIP image-text similarities. Using controlled corruptions on BDD100K road scenes, we compare embedding drift against margin drift, defined as the change in hazard score under perturbation. The relationship is highly corruption-dependent: some families exhibit strong coupling between representation drift and decision drift, while others induce hazardous decision instability despite relatively modest embedding change. Furthermore, corruption families differ in failure direction: most suppress hazard detections via false negatives, while occlusion instead triggers false alarms, suggesting that benchmark design should account for asymmetric failure modes, not just overall instability rates. These results suggest that robustness benchmarks should include task-aligned stability measures in addition to embedding-level perturbation statistics.

## Notes

<!-- Claude 在此添加中文解读 -->
