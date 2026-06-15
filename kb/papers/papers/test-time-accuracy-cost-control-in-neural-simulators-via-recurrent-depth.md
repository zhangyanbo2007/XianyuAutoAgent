---
title: "Test-Time Accuracy-Cost Control in Neural Simulators via Recurrent-Depth"
authors: [Harris Abdul Majid, Pietro Sittoni, Francesco Tudisco]
year: 2025
venue: "ICLR 2026 Poster"
tags: []
ingested: "2026-06-11"
---

# 🔬 Test-Time Accuracy-Cost Control in Neural Simulators via Recurrent-Depth

- **Authors**: Harris Abdul Majid, Pietro Sittoni, Francesco Tudisco
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=U2j9ZNgHqw)
- **Category**: ICLR 2026 Poster

## Abstract

Accuracy-cost trade-offs are a fundamental aspect of scientific computing. Classical numerical methods inherently offer such a trade-off: increasing resolution, order, or precision typically yields more accurate solutions at higher computational cost. We introduce \textbf{Recurrent-Depth Simulator} (\textbf{RecurrSim}) an architecture-agnostic framework that enables explicit test-time control over accuracy-cost trade-offs in neural simulators without requiring retraining or architectural redesign. By setting the number of recurrent iterations $K$, users can generate fast, less-accurate simulations for exploratory runs or real-time control loops, or increase $K$ for more-accurate simulations in critical applications or offline studies. We demonstrate RecurrSim's effectiveness across fluid dynamics benchmarks (Burgers, Korteweg-De Vries, Kuramoto-Sivashinsky), achieving physically faithful simulations over long horizons even in low-compute settings. On high-dimensional 3D compressible Navier-Stokes simulations with 262k points, a 0.8B parameter RecurrFNO outperforms 1.6B parameter baselines while using 13.5\% less training memory. RecurrSim consistently delivers superior accuracy-cost trade-offs compared to alternative adaptive-compute models, including Deep Equilibrium and diffusion-based approaches. We further validate broad architectural compatibility: RecurrViT reduces error accumulation by 90\% compared to standard Vision Transformers on Active Matter, while RecurrUPT matches UPT performance on ShapeNet-Car using 44\% fewer parameters.

## Notes

<!-- Claude 在此添加中文解读 -->
