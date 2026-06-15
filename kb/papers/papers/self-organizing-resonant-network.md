---
title: "Self-Organizing Resonant Network"
authors: [Weilin Zhou]
year: 2025
venue: "Submitted to ICLR 2026"
tags: []
ingested: "2026-06-11"
---

# 🔬 Self-Organizing Resonant Network

- **Authors**: Weilin Zhou
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=kuaZXtReJ0)
- **Category**: Submitted to ICLR 2026

## Abstract

We introduce the Self-Organizing Resonant Network (SORN), a novel learning paradigm that operates without backpropagation. To address core challenges in representation quality, learning stability, and adaptability faced by existing continual learning models, SORN operates within a robust feature space encoded online. Its learning process is driven by two tightly coupled, biologically-inspired plasticity principles: (1) Novelty-Gated Structural Plasticity: The system dynamically creates a new neural prototype only when an input cannot be adequately represented by existing knowledge (resonators), a mechanism analogous to a self-growing vector-quantized codebook. (2) Stable Hebbian Synaptic Plasticity: By incorporating Hebbian variants with normalization and homeostatic mechanisms, the network's association matrix stably learns sparse inter-concept correlations, effectively circumventing weight explosion and saturation issues. We theoretically demonstrate the framework's computational efficiency and convergence. Extensive experiments on standard continual learning benchmarks and unbounded data streams show that SORN not only surpasses mainstream methods in catastrophic forgetting resistance and accuracy, but also exhibits superior autonomous concept formation and stable adaptation when handling continuous, non-stationary environments.

## Notes

<!-- Claude 在此添加中文解读 -->
