---
title: "Not All Who Wander Are Lost: Hallucinations as Neutral Dynamics in Residual Transformers"
authors: [V. Dwarka, Albert Blom]
year: 2025
venue: "Submitted to ICLR 2026"
tags: []
ingested: "2026-06-11"
---

# 🔬 Not All Who Wander Are Lost: Hallucinations as Neutral Dynamics in Residual Transformers

- **Authors**: V. Dwarka, Albert Blom
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=fDfctZ8Fhg)
- **Category**: Submitted to ICLR 2026

## Abstract

Hallucinations in autoregressive models arise in two stages: an initial deviation from the truth and its continued propagation during decoding. Existing work addresses the first stage with empirical or diagnostic methods, but there is no fundamental account of the second stage. We give the first structural analysis of how paired continuations of the same prompt evolve inside pre-LayerNorm residual transformers, which form the backbone of most modern LLMs. By examining the residual stack and decoder, we show that their dynamics contain no built-in pull that suppresses deviations and no push that amplifies them. This neutrality is necessary, but not sufficient, for semantic hallucinations: it permits deviations to continue, yet a model can still correct the meaning even when predictive differences persist. Neutrality also yields an explicit upper bound, a separation between deterministic and stochastic effects, and a statistical validation rule at finite sample sizes. A population-level version follows by treating the small deviations across many continuations as agents in a mean-field average, showing that neutrality persists at scale without requiring access to individual weights. Experiments on GPT2 variants and Qwen2.5 models from 0.5B to 3B match the theoretical predictions.

## Notes

<!-- Claude 在此添加中文解读 -->
