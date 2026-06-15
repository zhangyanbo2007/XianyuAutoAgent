---
title: "Supra-Tuning: Combining Outlier and Low-Rank Adaptation for Sparse and Efficient LLM Fine-Tuning"
authors: [Ivan Ilin, Philip Zmushko, Peter Richtárik]
year: 2025
venue: "Submitted to ICLR 2026"
tags: []
ingested: "2026-06-11"
---

# 🔬 Supra-Tuning: Combining Outlier and Low-Rank Adaptation for Sparse and Efficient LLM Fine-Tuning

- **Authors**: Ivan Ilin, Philip Zmushko, Peter Richtárik
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=FFIn2TH7aU)
- **Category**: Submitted to ICLR 2026

## Abstract

Large language models (LLMs) have demonstrated remarkable capabilities but remain expensive to fine-tune due to their size. Recent parameter-efficient tuning methods, such as Low-Rank Adaptation (LoRA), reduce the number of trainable parameters while maintaining performance. In this work, we introduce Super, a novel sparse adaptation technique that selects and trains only a small set of influential weights—so-called super weights—identified via outlier metrics such as WANDA. We show that fine-tuning these outlier weights yields strong performance with minimal parameter updates. Building on this idea, we propose Supra, a hybrid method that combines Super with LoRA, merging sparse and low-rank adaptations into a unified tuning strategy. Our experiments on several LLMs and downstream tasks demonstrate that both Super and Supra outperform existing sparse or low-rank methods alone in perplexity and task performance, while reducing computational and memory overhead. Supra-Tuning offers a simple yet powerful framework for efficient and scalable adaptation of LLMs.

## Notes

<!-- Claude 在此添加中文解读 -->
