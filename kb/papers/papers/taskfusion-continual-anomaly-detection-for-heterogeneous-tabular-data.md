---
title: "TaskFusion: Continual Anomaly Detection for Heterogeneous Tabular Data"
authors: [Dayananda Herurkar, Federico Raue, Joachim Folz, Jörn Hees, Andreas Dengel]
year: 2026
venue: "cs.LG"
tags: []
arxiv_id: "2606.11844"
ingested: "2026-06-11"
---

# 🔬 TaskFusion: Continual Anomaly Detection for Heterogeneous Tabular Data

- **Authors**: Dayananda Herurkar, Federico Raue, Joachim Folz, Jörn Hees, Andreas Dengel
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.11844)
- **Category**: cs.LG

## Abstract

Continual anomaly detection in tabular data is challenging and remains largely underexplored, particularly in settings with heterogeneous feature schemas, distribution shifts, and severe class imbalance. In many real-world applications, data arrive sequentially from diverse domains, rendering conventional continual learning methods ineffective due to their reliance on a fixed input space. We propose a continual learning (CL) method, which can overcome these challenges and continually learn from different tasks. Our method consists of three main parts: our AGF model, Taskfusion augmentation, and outlier exposure. The AGF-model maps task-specific features into a shared space, then aligns distributions to reduce representation drift, and learns anomaly decision boundaries in the aligned space. To improve stability, we introduce Taskfusion augmentation, combining boundary-aware interpolation within tasks to refine the model anomaly boundaries and cross-task mixing to transfer anomaly structure across datasets. To handle class imbalance and memory constraints, we employ tabular dataset distillation to store compact synthetic replay samples, which are jointly used with augmented data in an outlier exposure objective for robust anomaly detection. We evaluate the approach on 21 heterogeneous datasets across multiple domains. Results show that our approach substantially improves continual anomaly detection performance over sequential fine-tuning and other CL baselines while reducing catastrophic forgetting and maintaining stable detection across heterogeneous datasets.

## Notes

<!-- Claude 在此添加中文解读 -->
