---
title: "Tabular Foundation Models for Clinical Survival Analysis via Survival-Aware Adaptation"
authors: [Minh-Khoi Pham, Luca Cotugno, Alina Sirbu, Tai Tan Mai, Martin Crane]
year: 2026
venue: "cs.LG, cs.AI"
tags: []
arxiv_id: "2606.12006"
ingested: "2026-06-11"
---

# 🤖 Tabular Foundation Models for Clinical Survival Analysis via Survival-Aware Adaptation

- **Authors**: Minh-Khoi Pham, Luca Cotugno, Alina Sirbu, Tai Tan Mai, Martin Crane
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12006)
- **Category**: cs.LG, cs.AI

## Abstract

Predicting time-to-event outcomes such as mortality is a fundamental task in clinical decision-making, commonly addressed through survival analysis. While classical statistical and deep learning approaches have been widely studied, they typically require task-specific training and sufficient labeled data. Recent advances in tabular foundation models offer a new paradigm by learning general-purpose representations for structured data. However, their applicability to censored time-to-event prediction in clinical settings remains underexplored, as typical applications are restricted to discrete classification rather than survival analysis tasks.   In this work, we propose a lightweight adaptation approach for applying tabular foundation models to clinical survival analysis by directly training a survival-aware head on top of the pretrained representations. We study representative architectures, including TabPFN, TabDPT, and TabICL, and adapt them using a multi-task logistic regression (MTLR) head to model right-censored time-to-event outcomes. We evaluate this approach on a diverse set of public survival benchmarks and two large-scale ICU cohorts, MIMIC-IV and eICU.   Our results show that this transfer learning approach achieves competitive or superior performance compared to strong baselines. On MIMIC-IV, TabDPT-FT-MTLR reaches a C-index of 0.856, corresponding to a relative improvement of +1.4% over the best non-FM baseline (DeepSurv, 0.844) and +6.7% over the best zero-shot model (0.802). On eICU, TabICL-FT-MTLR achieves 0.797, yielding gains of +1.7% (DeepSurv, 0.784) and +6.4% (0.749), respectively. These findings highlight the importance of combining pretrained tabular representations with survival-aware objectives and suggest that tabular foundation models provide a practical and effective alternative for clinical survival prediction.

## Notes

<!-- Claude 在此添加中文解读 -->
