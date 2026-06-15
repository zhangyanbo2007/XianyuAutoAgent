---
title: "The Art of Interrogation: Consistency Amplifies Factuality in Spatial Reasoning"
authors: [Theo Uscidda, Marta Tintore Gazulla, Maks Ovsjanikov, Federico Tombari, Leonidas Guibas]
year: 2026
venue: "cs.AI"
tags: []
arxiv_id: "2606.11918"
ingested: "2026-06-11"
---

# 🤖 The Art of Interrogation: Consistency Amplifies Factuality in Spatial Reasoning

- **Authors**: Theo Uscidda, Marta Tintore Gazulla, Maks Ovsjanikov, Federico Tombari, Leonidas Guibas
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.11918)
- **Category**: cs.AI

## Abstract

Current Large Reasoning Models (LRMs) exhibit remarkable general capabilities but significantly underperform in spatial reasoning tasks. Existing approaches treat this gap as a knowledge deficit, relying on supervised fine-tuning (SFT) to ingest labeled spatial data from external vision sources or synthetic engines. In contrast, we argue that for many tasks, spatial reasoning capabilities are already present in pre-trained LRMs but require alignment through logical coherence under geometric 2D and 3D constraints. In this work, we propose a self-supervised reinforcement learning (RL) framework that targets the internal reasoning process without requiring ground-truth annotations. By formalizing the notion of consistency verifiers -- reward functions that check for geometric and semantic consistency under transformations -- we demonstrate that models can improve their spatial reasoning abilities. We use both image transformations, like flipping, and textual transformations, like swapping the order of objects in the question, and propose a new optimal transport-based RL strategy, OT-GRPO, which is a minimal-matching variant of group relative policy optimization tailored to pairwise verifiers. We show that this label-free consistency training approaches the accuracy of models trained with ground-truth supervision and achieves similar generalization across diverse tasks and data domains.

## Notes

<!-- Claude 在此添加中文解读 -->
