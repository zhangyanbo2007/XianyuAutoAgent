---
title: "Non-Additive Time-Series Forecasting via Cross-Decomposition and Linear Attention"
authors: [Binli Luo, Han Zhou, Shiyuan Teng, Ning Gui, Xianhan Tan]
year: 2025
venue: "Submitted to ICLR 2026"
tags: []
ingested: "2026-06-11"
---

# 🔬 Non-Additive Time-Series Forecasting via Cross-Decomposition and Linear Attention

- **Authors**: Binli Luo, Han Zhou, Shiyuan Teng, Ning Gui, Xianhan Tan
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=JWQtXbVRbs)
- **Category**: Submitted to ICLR 2026

## Abstract

Many multivariate forecasters model additive effects well but miss non-additive interactions among temporal bases, variables, and exogenous drivers, which harms long-horizon accuracy and attribution. We present  time-series interaction machine (${TIM}$), an all-MLP forecaster designed from the ANOVA/Hoeffding target: the regression function is decomposed into main effects and an orthogonal interaction component. TIM assigns the interaction to a DCN-style cross stack that explicitly synthesizes bounded-degree polynomial crosses with controllable CP rank, while lightweight branches capture main effects. Axis-wise linear self-attention (time and variables) transports information without increasing polynomial degree and maintains linear time and memory complexity. A decomposition regularizer encourages orthogonality and yields per-component attributions. We establish degree and rank guarantees and a risk identity showing that the additive error gap equals the energy of the interaction subspace. TIM achieves state-of-the-art accuracy on long-term benchmarks with clear cross-term interpretability.

## Notes

<!-- Claude 在此添加中文解读 -->
