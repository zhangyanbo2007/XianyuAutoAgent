---
title: "Contrastive-Online-Meta (COM): A Dynamic Adaptation Mechanism for Instruction-Tuned CodeLLMs"
authors: [Han Ying]
year: 2025
venue: "Submitted to ICLR 2026"
tags: []
ingested: "2026-06-11"
---

# 🔬 Contrastive-Online-Meta (COM): A Dynamic Adaptation Mechanism for Instruction-Tuned CodeLLMs

- **Authors**: Han Ying
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=TjF9WLcu8o)
- **Category**: Submitted to ICLR 2026

## Abstract

We propose Contrastive-Online-Meta (COM), a dynamic adaptation framework for instruction-tuned CodeLLMs that coefficients to the issues of catastrophic forgetting and noisy feedback at the time of deployment. The framework combines contrastive pre-training and online meta-learning to separate the task-invariant representation learning and fast adaptation, which helps preserve core programming knowledge while achieving real-time adaptation. A contrastive pre-training module takes a first step at clustering semantically similar instructions and unionizing dissimilar ones, to guarantee its robustness to task variations. During inference, an online meta-learner takes pairs of instruction-feedback streaming and does a light-weight gradient-based update to meta-parameters, which dynamically adjust the model behavior in a way that does not destabilize the pre-trained behavior-effective thing. Furthermore, the dynamic memory buffer simply retains coherence with recent interactions by deriving pairs stored in the buffer for the sake of contrastive match. Unlike monolithic fine-tuning or prompt engineering, COM explicitly separates the processes of representation learning and adaptation, hence avoiding forgetting and overfitting. Experiments using benchmark datasets show that the framework has a better capacity for adaptation efficiency and task generalization than static and incremental tuning baselines. The proposed method fills in the missing link between the offline pre-training and the online accelerated deployment, which provides a scalable solution to real-world code generation systems that require continuous learning. And, its modular nature also supports integration with existing CodeLLMs, which makes it practical for different programming assistance scenarios.

## Notes

<!-- Claude 在此添加中文解读 -->
