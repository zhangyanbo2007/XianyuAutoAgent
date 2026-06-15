---
title: "LaMbDA: Local Latent Embedding Alignment for Cross-modal Time-Series Diffusion"
authors: [Sharmita Dey, Sarath Ravindran Nair]
year: 2025
venue: "Submitted to ICLR 2026"
tags: []
ingested: "2026-06-11"
---

# 🔬 LaMbDA: Local Latent Embedding Alignment for Cross-modal Time-Series Diffusion

- **Authors**: Sharmita Dey, Sarath Ravindran Nair
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=eIlgfA962J)
- **Category**: Submitted to ICLR 2026

## Abstract

We present a mutually aligned diffusion framework for cross‑modal time‑series generation that treats paired modalities X and Y as complementary observations of a shared latent dynamical process and couples their denoising trajectories through stepwise alignment of local latent embeddings. We instantiate this as LaMbDA (Local latent eMbedDing Alignment), a lightweight objective that enforces phase consistency by encouraging local latent neighborhoods of X and Y to inhabit a shared local manifold. LaMbDA augments the diffusion loss by incorporating first-order sequence-contrastive and second-order covariance alignment terms across modalities at matched timesteps. Aligning their local embeddings allows each modality to help denoise the other and resolve ambiguities throughout the reverse process. Human biomechanics provides a strong testbed for this approach: paired, synchronized measurements (e.g., joint kinematics and ground‑reaction forces) capture the same movement state while reflecting practical constraints such as sensor dropout and cost. We evaluate LaMbDA extensively on biomechanical data and complement this with controlled studies on canonical synthetic dynamical systems (Lorenz attractor; double pendulum in non‑chaotic and chaotic regimes) to probe generality under varying dynamical complexity. Across all these settings, aligning local latent statistics consistently improves generation fidelity, phase coherence, and representation quality for downstream probes, without architectural changes or inference overhead.

## Notes

<!-- Claude 在此添加中文解读 -->
