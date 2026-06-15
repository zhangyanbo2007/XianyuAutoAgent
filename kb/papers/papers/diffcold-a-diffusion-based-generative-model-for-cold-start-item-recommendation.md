---
title: "DiffCold: A Diffusion-based Generative Model for Cold-Start Item Recommendation"
authors: [Kangning Zhang, Yingjie Qin, Weinan Zhang, Yong Yu, Jianghao Lin]
year: 2026
venue: "cs.IR, cs.AI"
tags: []
arxiv_id: "2606.12245"
ingested: "2026-06-11"
---

# 🤖 DiffCold: A Diffusion-based Generative Model for Cold-Start Item Recommendation

- **Authors**: Kangning Zhang, Yingjie Qin, Weinan Zhang, Yong Yu, Jianghao Lin
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12245)
- **Category**: cs.IR, cs.AI

## Abstract

Cold-start item recommendation remains a persistent challenge in real-world systems due to the absence of interaction histories. While prior models attempt to bridge this gap using item content features, they universally suffer from the \textbf{seesaw dilemma}: enhancing performance for cold items inevitably degrades performance for warm items, and vice versa. We identify that this dilemma stems from a fundamental \textbf{distributional disparity}: warm item embeddings occupy a complex ``behavioral manifold" shaped by rich interaction signals, whereas cold item embeddings are constrained to a ``semantic manifold" derived solely from auxiliary content. Existing methods often force a rigid mapping between these inconsistent spaces, causing the model to sacrifice the precision of warm representations to accommodate cold ones. To address this, we propose \textbf{DiffCold}, a diffusion-based generative model that unifies warm and cold representations. Unlike GANs or VAEs, DiffCold leverages conditional diffusion to reconstruct warm item embeddings from content, preserving the underlying manifold structure without degradation. We further tailor this paradigm with two specific designs: a \textbf{Retrieval-enhanced Aggregator} that initializes generation using semantically similar warm items to bypass inefficient noise, and a \textbf{Simulation-based Representation Alignment} module that enforces distribution consistency between generated and real embeddings via contrastive learning. Experiments on three benchmarks confirm that DiffCold resolves the seesaw dilemma, consistently outperforming state-of-the-art methods across all metrics.

## Notes

<!-- Claude 在此添加中文解读 -->
