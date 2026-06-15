---
title: "Context-Driven Incremental Compression for Multi-Turn Dialogue Generation"
authors: [Yeongseo Jung, Jaehyeok Kim, Eunseo Jung, Jiachuan Wang, Yongqi Zhang]
year: 2026
venue: "cs.CL, cs.LG"
tags: []
arxiv_id: "2606.12411"
ingested: "2026-06-11"
---

# 🔬 Context-Driven Incremental Compression for Multi-Turn Dialogue Generation

- **Authors**: Yeongseo Jung, Jaehyeok Kim, Eunseo Jung, Jiachuan Wang, Yongqi Zhang
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12411)
- **Category**: cs.CL, cs.LG

## Abstract

Modern conversational agents condition on an ever-growing dialogue history at each turn, incurring redundant attention and encoding costs that grow with conversation length. Naive truncation or summarization degrades fidelity, while existing context compressors lack cross-turn memory sharing or revision, causing information loss and compounding errors in long dialogues. We revisit the context compression under conversational dynamics and empirically present its fragility. To improve both efficiency and robustness, we introduce Context-Driven Incremental Compression (C-DIC), which treats a conversation as interleaved contextual threads and stores revisable per-thread compression states in a single, compact dialogue memory. At each turn, a lightweight retrieve, revise, and write-back loop shares information across turns and updates stale memories, stabilizing long-horizon behavior. In addition, we adapt truncated backpropagation-through-time (TBPTT) to our multi-turn setting, learning cross-turn dependencies without full-history backpropagation. Extensive experiments on long-form dialogue benchmarks demonstrate superior performance and efficiency of C-DIC; notably, C-DIC shows stable inference latency and perplexity over hundreds of dialogue turns, supporting a scalable path to high-quality dialogue modeling.

## Notes

<!-- Claude 在此添加中文解读 -->
