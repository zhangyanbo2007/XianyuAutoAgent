---
title: "FedPAC: Consistent Representation Learning for Federated Unsupervised Learning under Data Heterogeneity"
authors: [Shuyi Wu, Qing Hu, Zibin Zheng, Lei Yang, Chuan Chen]
year: 2025
venue: "Submitted to ICLR 2026"
tags: []
ingested: "2026-06-11"
---

# 🔬 FedPAC: Consistent Representation Learning for Federated Unsupervised Learning under Data Heterogeneity

- **Authors**: Shuyi Wu, Qing Hu, Zibin Zheng, Lei Yang, Chuan Chen
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=wiNlIYqe6u)
- **Category**: Submitted to ICLR 2026

## Abstract

Federated unsupervised learning enables collaborative model training on decentralized unlabeled data but faces critical challenges under data heterogeneity, which often leads to representation collapse from weak supervisory signals and semantic misalignment across clients. Without a consistent semantic structure constraint, local models learn disparate feature spaces, and conventional parameter averaging fails to produce a coherent global model. To address these issues, we propose Federated unsupervised learning with Prototype Anchored Consensus (FedPAC), a novel framework that establishes a consistent representation space via a set of learnable prototypes. FedPAC introduces a dual-alignment objective during local training: a semantic alignment loss that steers local models towards a prototype-anchored consensus to ensure cross-client semantic consistency, coupled with a representation alignment loss that promotes the learning of discriminative and stable features. On the server, prototypes are aggregated by an optimization-based strategy that preserves semantic knowledge and ensures the prototypes remain representative. We provide a rigorous convergence analysis for our method, formally proving its convergence under mild assumptions. Extensive experiments on benchmarks including CIFAR-10 and CIFAR-100 demonstrate that FedPAC significantly outperforms state-of-the-art methods across a wide range of heterogeneous settings.

## Notes

<!-- Claude 在此添加中文解读 -->
