---
title: "Task-Aware Structured Memory for Dynamic Multi-modal In-Context Learning"
authors: [Zhirui Chen, Ziwei Chen, Ling Shao]
year: 2026
venue: "cs.CV, cs.AI"
tags: []
arxiv_id: "2606.11853"
ingested: "2026-06-11"
---

# 🔬 Task-Aware Structured Memory for Dynamic Multi-modal In-Context Learning

- **Authors**: Zhirui Chen, Ziwei Chen, Ling Shao
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.11853)
- **Category**: cs.CV, cs.AI

## Abstract

Multi-modal large language models (MLLMs) depend on in-context learning (ICL) for rapid task adaptation, but their scalability is severely limited by finite context windows and the growing cost of key-value (KV) caches in long multi-modal sequences. Existing memory compression approaches typically rely on rigid token removal or sample-dependent importance estimation, which introduces bias, disrupts semantic structure, particularly for visual representations, and yields static memories that cannot adapt to new queries. We introduce TASM (Task-Aware Structured Memory), a training-free framework that addresses these limitations through task-aware, structure-preserving, and dynamically accessible memory construction. TASM employs task-vector guided compression to replace sample-specific signals with a task-level direction that captures shared relevance across demonstrations. To preserve the underlying manifold, it applies semantics-aware token merging via bipartite graph matching, aggregating tokens without destructive pruning. Finally, TASM structures memory into a hierarchy comprising a compact Core Memory and a Latent Bank, facilitating query-adaptive dynamic retrieval. Evaluations confirm TASM maintains high performance under heavy compression, effectively balancing efficiency with adaptability.

## Notes

<!-- Claude 在此添加中文解读 -->
