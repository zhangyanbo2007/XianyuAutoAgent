---
title: "OVA-LP: A Simple and Efficient Framework for Federated Learning on Non-IID Data"
authors: [Dongjin Park, Hasung Yeo, Joon-Woo Lee]
year: 2025
venue: "Submitted to ICLR 2026"
tags: []
ingested: "2026-06-11"
---

# 🔬 OVA-LP: A Simple and Efficient Framework for Federated Learning on Non-IID Data

- **Authors**: Dongjin Park, Hasung Yeo, Joon-Woo Lee
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=lbEUvx1ILN)
- **Category**: Submitted to ICLR 2026

## Abstract

Federated fine-tuning (FFT) adapts foundation models to decentralized data but remains fragile under heterogeneous client distributions due to local drift—client-level update divergences that induce systematic bias and amplified variance in the global model. Existing aggregation and personalization approaches largely correct drift post hoc, which can be brittle under extreme Non-IID conditions. We introduce OvA-LP, a minimalist FFT framework that suppresses drift at its source by combining linear probing on a frozen encoder, one-vs-all heads, and a two-stage schedule informed by a bias–variance perspective. OvA-LP demonstrates strong Non-IID robustness and substantially outperforms state-of-the-art PEFT baselines on CIFAR-100 and DomainNet, while maintaining stable performance across participation ratios. Although performance decreases under the most severe domain-shift configuration, OvA-LP exhibits significantly improved stability in practical settings and generalizes across diverse datasets, model architectures, and modalities. These results highlight source-level drift suppression as a viable alternative direction for federated fine-tuning, expanding the design space beyond adaptation-centric approaches.

## Notes

<!-- Claude 在此添加中文解读 -->
