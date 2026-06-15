---
title: "AC-ODM: Actor–Critic Online Data Mixing for Sample-Efficient LLM Pretraining"
authors: [Jing Ma, Chenhao Dang, Mingjie Liao]
year: 2025
venue: "ICLR 2026 Conference Withdrawn Submission"
tags: []
ingested: "2026-06-11"
---

# 🔬 AC-ODM: Actor–Critic Online Data Mixing for Sample-Efficient LLM Pretraining

- **Authors**: Jing Ma, Chenhao Dang, Mingjie Liao
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=mRjzWksbGR)
- **Category**: ICLR 2026 Conference Withdrawn Submission

## Abstract

Pretraining data coverage and composition strongly influence the generalization of large language models (LLMs). While recent data-mixing approaches transfer domain weights learned by a small proxy model to a larger one to reduce computational costs and carbon footprint, they are typically static and ignore training dynamics. Online Data Mixing (ODM) mitigates this with a multi-armed bandit sampler but overlooks intra-domain interactions. We introduce AC-ODM, an actor–critic online data-mixing method that treats the LLM as the environment, uses auxiliary actor–critic networks to dynamically adjust domain sampling weights, and encodes intra-domain interactions through the reward. AC-ODM supports (i) a non-proxy mode that co-trains the actor–critic with the target LLM from scratch, and (ii) a proxy mode that first trains the actor–critic with a small, trainable proxy LLM and then transfers the learned actor to guide the target LLM’s pretraining. Empirically, the proxy mode incurs additional wall-clock time relative to the non-proxy mode but delivers stronger target-LLM performance. Across both modes, AC-ODM enables efficient, adaptive data mixing and accelerates target-model convergence, with negligible per-step wall-clock overhead. On Pythia-1B pretraining over The Pile and SlimPajama, AC-ODM-410M (a policy learned with a 410M-parameter proxy) reaches the optimal validation perplexity of ODM using 71\% and 65\% fewer training steps, respectively. It achieves a 27.5\% relative improvement in zero-shot MMLU accuracy, a 2.23$\times\$ higher pass@1 on HumanEval, and an average +3.44\% accuracy gain across five additional benchmarks. We further show that AC-ODM maintains the fastest pretraining convergence on LLaMA3-style architectures compared to prior data-mixing baselines.

## Notes

<!-- Claude 在此添加中文解读 -->
