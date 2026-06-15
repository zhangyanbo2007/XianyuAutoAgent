---
title: "Adaptive Mixing of Non-Invariant Information for Generalized Diffusion Policy"
authors: [Pingrui Zhang, Yu Zhang, Pengyuan Wu, Zhaxizhuoma, Zhigang Wang]
year: 2025
venue: "Submitted to ICLR 2026"
tags: []
ingested: "2026-06-11"
---

# 🔬 Adaptive Mixing of Non-Invariant Information for Generalized Diffusion Policy

- **Authors**: Pingrui Zhang, Yu Zhang, Pengyuan Wu, Zhaxizhuoma, Zhigang Wang
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=WtbIU6tDc3)
- **Category**: Submitted to ICLR 2026

## Abstract

Diffusion policies (DP) have emerged as a leading paradigm for learning-based robotic manipulation, offering temporally coherent action synthesis from high-dimensional observations. 
However, despite their centrality to downstream tasks, DPs exhibit fragile generalization capabilities. Minor variations in observations, such as changes in lighting, appearance, or camera pose, can lead to significant performance degradation, even when operating on familiar trajectories.
To address the issue, we introduce a factorized, fine-grained benchmark that isolates the impact of individual perturbation factors on zero-shot generalization.
Based on it, we reveal camera pose as a dominant driver of performance degradation, explaining the pronounced drops observed at higher levels of domain randomization. 
In this case, we propose $A$daptive $M$ixing of non-$I$nvariant (AMI) information, a model-agnostic training strategy that requires no additional data and reinforces invariant correlations while suppressing spurious ones.
Across simulated evaluations, AMI consistently and significantly outperforms strong baselines, mitigating DP's sensitivity to observation shifts and yielding robust zero-shot generalization over diverse perturbation factors. 
We further validate these improvements in real-world experiments by zero-shot deploying the policies in natural settings, demonstrating their robustness to observation variations.

## Notes

<!-- Claude 在此添加中文解读 -->
