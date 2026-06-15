---
title: "UniReason-Med: A Shared Grounded Reasoning Interface for 2D-to-3D Transfer in Medical VQA"
authors: [Mengzhuo Chen, Yan Shu, Chi Liu, Hongming Piao, Xidong Wang]
year: 2026
venue: "cs.CV, cs.CL"
tags: []
arxiv_id: "2606.11740"
ingested: "2026-06-11"
---

# 🤖 UniReason-Med: A Shared Grounded Reasoning Interface for 2D-to-3D Transfer in Medical VQA

- **Authors**: Mengzhuo Chen, Yan Shu, Chi Liu, Hongming Piao, Xidong Wang
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.11740)
- **Category**: cs.CV, cs.CL

## Abstract

We study whether grounded reasoning supervision from abundant 2D medical images can improve 3D medical VQA when both input types are aligned through a common reasoning interface. We introduce UniReason-Med, a single-checkpoint framework that processes either a 2D image or a slice-serialized 3D volume at inference time, generating interleaved textual reasoning and localized visual evidence through shared box syntax, region-token injection, and a common grounded reasoning policy. To train this interface, we construct UniMed-CoT, a 220K instruction-tuning dataset with interleaved textual reasoning and grounded visual evidence, including 170K 2D and 50K 3D samples. Through supervised fine-tuning followed by outcome-level reinforcement learning, UniReason-Med learns to generate grounded reasoning traces without IoU/Dice-based localization rewards during RL. Data-mixture and component ablations show that joint 2D+3D grounded supervision substantially improves 3D reasoning over 3D-only training, while grounding and region-token injection consistently benefit both 2D and 3D tasks. These results suggest that a shared grounded reasoning interface can transfer reasoning structure from 2D images to slice-serialized volumetric medical understanding. The code and data are publicly available at https://github.com/IQuestLab/unireason-med.

## Notes

<!-- Claude 在此添加中文解读 -->
