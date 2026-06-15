---
title: "Doc-to-Atom: Learning to Compile and Compose Memory Atoms"
authors: [Xingjian Diao, Wenbo Li, Yashas Malur Saidutta, Avinash Amballa, Lazar Valkov]
year: 2026
venue: "cs.CL, cs.IR"
tags: []
arxiv_id: "2606.12400"
ingested: "2026-06-11"
---

# 🤖 Doc-to-Atom: Learning to Compile and Compose Memory Atoms

- **Authors**: Xingjian Diao, Wenbo Li, Yashas Malur Saidutta, Avinash Amballa, Lazar Valkov
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12400)
- **Category**: cs.CL, cs.IR

## Abstract

Long input sequences are central to document understanding and multi-step reasoning in Large Language Models, yet the quadratic cost of attention makes inference both memory-intensive and slow. Context distillation mitigates this by compressing contextual information into model parameters, and recent work such as Doc-to-LoRA amortizes context distillation into a single forward pass that generates one LoRA adapter per document. However, producing a single monolithic adapter for all queries leads to irrelevant-query interference, limited compositional recall, and poor scalability to long-document reasoning. To address these challenges, we propose Doc-to-Atom (Doc2Atom), a compositional parametric memory framework that decomposes each document into semantically typed knowledge atoms. Each atom is compiled into an independent micro-LoRA adapter and a provenance retrieval key. At inference time, a lightweight query router selects and assembles only the relevant atoms into a query-specific adapter, which is then injected into a frozen base model. The entire system is trained end-to-end through a multi-objective distillation framework. Experiments on six diverse QA benchmarks demonstrate that Doc2Atom outperforms Doc-to-LoRA baselines while reducing the memory cost of document internalization.

## Notes

<!-- Claude 在此添加中文解读 -->
