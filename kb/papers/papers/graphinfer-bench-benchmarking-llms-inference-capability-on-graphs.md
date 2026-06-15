---
title: "GraphInfer-Bench: Benchmarking LLM's Inference Capability on Graphs"
authors: [Zhuoyi Peng, Jingzhou Jiang, Hanlin Gu, Lixin Fan, Yi Yang]
year: 2026
venue: "cs.LG, cs.CL"
tags: []
arxiv_id: "2606.11562"
ingested: "2026-06-11"
---

# 🤖 GraphInfer-Bench: Benchmarking LLM's Inference Capability on Graphs

- **Authors**: Zhuoyi Peng, Jingzhou Jiang, Hanlin Gu, Lixin Fan, Yi Yang
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.11562)
- **Category**: cs.LG, cs.CL

## Abstract

Graph analysis underlies many applications whose answers cannot be looked up in a single record or retrieved along a path: laundering rings, drug repurposing, user preference, and scientific theme are all inferred from a node together with its neighbourhood. We introduce GraphInfer-Bench, a benchmark for whether LLMs can perform this graph inference: producing an open-ended answer that no single node supports and no path retrieves. Existing graph-QA protocols cannot test this capability: algorithm simulation, node classification, single-node description, KG-QA, and GraphRAG all admit answers retrievable from one node or along a path. GraphInfer-Bench defines five tasks along Description (what a region is) and Comparison (how regions differ), each constructed so the ground truth lives in no single node. The release contains 42,000 samples across six real-world graphs, produced automatically and screened by a four-layer quality-control protocol. We evaluate four method families against the same tasks: graph-token alignment models, zero-shot frontier closed-source LLMs, Graph2Text supervised fine-tuning, and plain GNNs as a structural reference. No method family closes the gap. Graph-token alignment partially handles description tasks (relational, theme) but collapses on comparison tasks. Frontier LLMs lead on outlier detection and community partition among LLM-based methods but lag on masked-node prediction. Graph2Text SFT is the strongest LLM-based method on the description side yet falls behind frontier LLMs on comparison. Across every task, plain GNNs match or beat the strongest LLM-based row, with the largest margin on community detection. GraphInfer-Bench surfaces graph inference as an open capability gap rather than a property of any one architecture.

## Notes

<!-- Claude 在此添加中文解读 -->
