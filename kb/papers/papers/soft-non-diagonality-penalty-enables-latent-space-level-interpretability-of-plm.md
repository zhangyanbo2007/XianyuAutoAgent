---
title: "Soft Non-Diagonality Penalty Enables Latent Space-Level Interpretability of pLM at No Performance Cost"
authors: [Evgeniy V. Nam, Yevgeniya Din, Nikita Serov]
year: 2025
venue: "Submitted to ICLR 2026"
tags: []
ingested: "2026-06-11"
---

# 🔬 Soft Non-Diagonality Penalty Enables Latent Space-Level Interpretability of pLM at No Performance Cost

- **Authors**: Evgeniy V. Nam, Yevgeniya Din, Nikita Serov
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=7wjqoJj62s)
- **Category**: Submitted to ICLR 2026

## Abstract

Emergence of large scale protein language models (pLMs) has led to significant performance gains in predictive protein modeling. However, it comes at a high price of interpretability, and efforts to push representation learning towards explainable feature spaces remain scarce. The prevailing use of domain-agnostic and sparse encodings in such models fosters a perception that developing both parameter-efficient and generalizable models in a low-data regime is not feasible. In this work, we explore an alternative approach to develop compact models with interpretable embeddings while maintaining competitive performance. With the Bidirectional Long Short-Term Memory Autoencoder (BiLSTM-AE) model as an example trained on positional property matrices, we introduce a soft weight matrix non-diagonality penalty. Through Jacobian analysis, we show that this penalty aligns embeddings with the initial feature space while leading to a marginal increase in performance on a suite of four common peptide biological activity classification benchmarks. Moreover, it was demonstrated that the use of one-hot encoded sequence clustering-based contrastive loss to produce semantically meaningful latent space allows to further improve benchmarking performance. The use of amino acid physicochemical properties and density functional theory (DFT) derived cofactor interaction energies as input features provides a foundation for intrinsic interpretability, which we demonstrate on fundamental peptide properties. The resulting model is over 33,000 times more compact than the state-of-the-art pLM ProtT5. It demonstrates performance stability across diverse benchmarks without task-specific fine-tuning, showcasing that domain-tailored architectural design can yield highly parameter-efficient models with fast inference and preserved generalization capabilities.

## Notes

<!-- Claude 在此添加中文解读 -->
