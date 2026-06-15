---
title: "Beyond Fully Random Masking: Attention-Guided Denoising and Optimization for Diffusion Language Models"
authors: [Jia Deng, Junyi Li, Wayne Xin Zhao, Jinpeng Wang, Hongyu Lu]
year: 2026
venue: "cs.CL"
tags: []
arxiv_id: "2606.12273"
ingested: "2026-06-11"
---

# 🤖 Beyond Fully Random Masking: Attention-Guided Denoising and Optimization for Diffusion Language Models

- **Authors**: Jia Deng, Junyi Li, Wayne Xin Zhao, Jinpeng Wang, Hongyu Lu
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12273)
- **Category**: cs.CL

## Abstract

Diffusion large language models (dLLMs) offer an efficient alternative to autoregressive models through parallel decoding, yet existing post-training methods largely rely on random masking strategies that overlook intrinsic token dependencies. In this work, we present an empirical analysis of attention in dLLMs and show that tokens attending more strongly to unmasked context exhibit greater generation stability and play a critical role in reasoning. Motivated by these findings, we propose AGDO, an attention-guided denoising and optimization framework that aligns both training and optimization with attention-derived dependencies. AGDO determines the denoising order based on attention structure and emphasizes attention-critical tokens during supervised fine-tuning and reinforcement learning. Experiments on mathematical and coding benchmarks demonstrate that AGDO consistently improves reasoning performance, outperforming state-of-the-art post-training methods for dLLMs.

## Notes

<!-- Claude 在此添加中文解读 -->
