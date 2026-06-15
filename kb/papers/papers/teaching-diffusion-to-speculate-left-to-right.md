---
title: "Teaching Diffusion to Speculate Left-to-Right"
authors: [Lexington Whalen, Yuki Ito, Ryo Sakamoto]
year: 2026
venue: "cs.CL, cs.LG"
tags: []
arxiv_id: "2606.11552"
ingested: "2026-06-11"
---

# 🤖 Teaching Diffusion to Speculate Left-to-Right

- **Authors**: Lexington Whalen, Yuki Ito, Ryo Sakamoto
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.11552)
- **Category**: cs.CL, cs.LG

## Abstract

Large language models (LLMs) achieve remarkable performance across a wide range of tasks, but their autoregressive decoding process incurs substantial inference costs due to inherently sequential token generation. Speculative decoding addresses this bottleneck by employing a lightweight draft model to propose multiple future tokens that are subsequently verified in parallel by a larger target model. Recent work has demonstrated that diffusion language models are well suited for this setting, as they can generate entire blocks of draft tokens in parallel and thereby alleviate the sequential constraints of autoregressive drafting. A subtlety of this regime is that block-diffusion drafters generate tokens bidirectionally within a block, whereas verification is performed by an autoregressive target model that evaluates tokens in a strictly left-to-right manner, leaving a gap between the symmetric training-time objective and the asymmetric verification-time reward. In this work, we offer an empirical analysis of three training-time interventions that narrow this gap: token positional weighting, a first-error focal loss that targets the position that breaks the accepted prefix within each block, and a chain loss term that substitutes a differentiable surrogate for the expected accepted length. The three interventions act along orthogonal axes (position, block-conditional first error, joint prefix) and compose additively; they are likewise orthogonal to test-time alignment mechanisms such as multi-draft self-selection, with which they can in principle be combined. Across four target models and six reasoning, code, and dialogue benchmarks, the three interventions raise accepted draft length by 21-76% per benchmark over a position-uniform baseline, without adding additional forward passes and without changing the inference pipeline or the rejection-sampling exactness contract.

## Notes

<!-- Claude 在此添加中文解读 -->
