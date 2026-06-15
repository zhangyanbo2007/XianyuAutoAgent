---
title: "LASA: A Weak Supervision Method for Open-Vocabulary Scene Sketch Semantic Segmentation"
authors: [Liwen Yi, Xianlin Zhang, Yue Zhang, Yue Ming, Xueming Li]
year: 2026
venue: "cs.CV, cs.AI"
tags: []
arxiv_id: "2606.11837"
ingested: "2026-06-11"
---

# 🤖 LASA: A Weak Supervision Method for Open-Vocabulary Scene Sketch Semantic Segmentation

- **Authors**: Liwen Yi, Xianlin Zhang, Yue Zhang, Yue Ming, Xueming Li
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.11837)
- **Category**: cs.CV, cs.AI

## Abstract

Open-vocabulary scene sketch semantic segmentation aims to assign dense semantic labels to sparse line drawings based on flexible category vocabularies specified at inference time, without relying on pixel-level annotations during training. Unlike natural images, sketches lack texture and color cues, making semantic understanding heavily dependent on stroke layout and spatial configuration, a challenge that renders single-layer vision-language features inherently unstable. Our key observation is that attention maps from different Vision Transformer layers encode complementary spatial cues: shallow layers capture global structural layouts, while deeper layers focus on local stroke intersections and object parts. This suggests that cross-layer aggregation provides a more robust structural prior than any individual layer alone. Leveraging this insight, we propose a structure-aware framework built upon \textbf{L}ayer-wise \textbf{A}ccumulated \textbf{S}tructural \textbf{A}ttention (\textbf{LASA}), which aggregates multi-layer attention to guide hierarchical semantic alignment under weak supervision and refine predictions during inference. Experiments on FS-COCO, SFSD, and FrISS show that LASA improves mIoU by $+3.43$, $+8.01$, and $+15.74$ over the prior weakly supervised baselines, demonstrating consistent gains in both segmentation accuracy and spatial coherence. Our source code will be made publicly available.

## Notes

<!-- Claude 在此添加中文解读 -->
