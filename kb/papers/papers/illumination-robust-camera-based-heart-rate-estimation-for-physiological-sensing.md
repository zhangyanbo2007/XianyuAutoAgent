---
title: "Illumination-Robust Camera-Based Heart-Rate Estimation for Physiological Sensing in Robots"
authors: [Zhi Wei Xu, Torbjörn E. M. Nordling]
year: 2026
venue: "cs.CV, cs.AI"
tags: []
arxiv_id: "2606.12378"
ingested: "2026-06-11"
---

# 🤖 Illumination-Robust Camera-Based Heart-Rate Estimation for Physiological Sensing in Robots

- **Authors**: Zhi Wei Xu, Torbjörn E. M. Nordling
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12378)
- **Category**: cs.CV, cs.AI

## Abstract

Physiological awareness is important for service, social, and assistive robots that interact with humans in everyday environments. Remote photoplethysmography (rPPG) enables non-contact heart-rate (HR) estimation from an RGB camera, making it a promising sensing modality for robot-mounted vision systems. However, illumination variation remains a major barrier to robust deployment. This paper presents an end-to-end spatial-temporal transformer framework for remote HR estimation on a new dataset with varied illumination. Our estimator integrates PRNet-based 3D face alignment, clip-level illumination augmentation, the Residual Temporal Standardization Module, and controlled hybrid temporal-frequency supervision. The training objective combines a Soft-Shifted Pearson waveform loss with a spectral Kullback-Leibler divergence loss, where a tuned weight ($\mathbfβ$) controls the contribution of frequency-domain heart-rate guidance. Experiments on a static all-level mix protocol covering three illumination levels show that $\mathbfβ=5$ provides the strongest result among the tested beta settings, achieving a best-run HR mean absolute error (MAE) of 0.79 bpm and an HR correlation of 0.982. Compared with the PhysFormer baseline evaluated on our dataset, our estimator reduces HR MAE by 93.6 %, while increasing HR correlation from 0.088 to 0.982, making it usable when illumination varies.

## Notes

<!-- Claude 在此添加中文解读 -->
