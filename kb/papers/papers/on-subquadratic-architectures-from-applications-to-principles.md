---
title: "On Subquadratic Architectures: From Applications to Principles"
authors: [Anamaria-Roberta Hartl, Levente Zólyomi, David Stap, Pieter-Jan Hoedt, Niklas Schmidinger]
year: 2026
venue: "cs.LG"
tags: []
arxiv_id: "2606.12364"
ingested: "2026-06-11"
---

# 🤖 On Subquadratic Architectures: From Applications to Principles

- **Authors**: Anamaria-Roberta Hartl, Levente Zólyomi, David Stap, Pieter-Jan Hoedt, Niklas Schmidinger
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12364)
- **Category**: cs.LG

## Abstract

Transformers dominate modern sequence modeling, but their quadratic attention incurs substantial computational cost. Subquadratic architectures offer a scalable alternative. However, it remains unclear which designs yield the most effective sequence models. We compare three leading approaches: xLSTM, Mamba-2, and Gated DeltaNet. We evaluate these models on tasks with complex dependencies: (1) code-model pre-training, (2) distillation of code models from large language models, and (3) pre-training of time-series foundation models. Across these settings, xLSTM delivers the strongest overall performance. To explain xLSTM's advantage, we present a unified formulation and analyze the underlying architectural mechanisms, focusing on state tracking and memory dynamics. Our results show that xLSTM enables more flexible and stable memory correction via its gating scheme. We corroborate these findings on controlled synthetic length-generalization tasks. Overall, our findings indicate that xLSTM's gains on complex tasks stem from robust state tracking and accumulation.

## Notes

<!-- Claude 在此添加中文解读 -->
