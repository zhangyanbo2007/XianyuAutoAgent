---
title: "Ensemble Learning for AUC Maximization via Surrogate Loss"
authors: [Zhijie Gong, Xiaoyan Chen, Xinyu Zhang]
year: 2025
venue: "ICLR 2026 Conference Withdrawn Submission"
tags: []
ingested: "2026-06-11"
---

# 🔬 Ensemble Learning for AUC Maximization via Surrogate Loss

- **Authors**: Zhijie Gong, Xiaoyan Chen, Xinyu Zhang
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=kbxjkoF42x)
- **Category**: ICLR 2026 Conference Withdrawn Submission

## Abstract

In classification tasks, the area under the ROC curve (AUC) is a key metric for evaluating a model’s ability to discriminate between positive and negative samples. An AUC-maximizing classifier can have significant advantages in cases where ranking correctness is valued or when the outcome is rare. While ensemble learning is a common strategy to improve predictive performance by combining multiple base models, direct AUC maximization for aggregating base learners leads to an NP-hard optimization challenge. To address this challenge, we propose a novel stacking framework that leverages a linear combination of base models through a surrogate loss function designed to maximize AUC. Our approach learns data-driven stacking weights for base models by minimizing a pairwise loss-based objective. Theoretically, we prove that the resulting ensemble is asymptotically optimal with respect to AUC. Moreover, when the set of base models includes correctly specified models, our method asymptotically concentrates all weight on these models, ensuring consistency. In numerical simulations, the proposed method reduces the AUC risk by up to 20\% compared to existing ensemble methods, a finding that is corroborated by real-data analysis, which also shows a reduction of over 30\%.

## Notes

<!-- Claude 在此添加中文解读 -->
