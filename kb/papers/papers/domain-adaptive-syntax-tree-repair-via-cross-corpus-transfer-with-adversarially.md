---
title: "Domain-Adaptive Syntax Tree Repair via Cross-Corpus Transfer with Adversarially Aligned Transformers"
authors: [Fan Kui]
year: 2025
venue: "Submitted to ICLR 2026"
tags: []
ingested: "2026-06-11"
---

# 🔬 Domain-Adaptive Syntax Tree Repair via Cross-Corpus Transfer with Adversarially Aligned Transformers

- **Authors**: Fan Kui
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=gOf2ht5O0d)
- **Category**: Submitted to ICLR 2026

## Abstract

We propose a domain-adaptive syntax tree repair system that meets the challenges of code correction tasks of cross corpus generalization. The natural heterogeneity of code corpora in terms of domains biases the average algorithmic repair model most of the time to the extent that the performance is not optimal when applied to see programming contexts. To reduce this, we propose Domain-Aligned Syntax Tree Transformer (DASTT), a hierarchical neural model that simultaneously optimizes syntactic feasibility and domain-invariant features. The model takes raw source code as input through a byte pair encoding tokenizer and uses a multi-layer encoder of Transformer with adversarial training to align pairwise distributions of the tokens across domains. A gradient reversal layer reduces domain discrimination while maintaining the accuracy of repairs so that the system adapts to different codebases without ever needing to retrain. Furthermore, the decoder includes a pointer amplified mechanism to directly manipulate the syntax trees, inducing exact repair actions (insertion of nodes or deletion of nodes). The proposed method fits smoothly into the existing compiler pipelines, where existing lexers and parsers are substituted; compatibility with downstream activities is assured. Experiments show that DASTT outperforms domain-specific baselines on cross-corpus repair tasks by a large margin, achieving strong performance on multiple programming languages and coding styles. The adversarial alignment framework guarantees the syntactic fidelity even under large domain shifts and hence is suitable for real-world deployment in heterogeneous development environment. This work significantly advances the state-of-the-art on automated code repair by bringing together techniques of domain adaptation and structural syntax tree manipulation.

## Notes

<!-- Claude 在此添加中文解读 -->
