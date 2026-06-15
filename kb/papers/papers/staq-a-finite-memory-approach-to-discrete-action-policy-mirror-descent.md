---
title: "StaQ: a Finite Memory Approach to Discrete Action Policy Mirror Descent"
authors: [Alena Shilova, Alex Davey, Brahim Driss, Riad Akrour]
year: 2025
venue: "Submitted to ICLR 2026"
tags: []
ingested: "2026-06-11"
---

# 🔬 StaQ: a Finite Memory Approach to Discrete Action Policy Mirror Descent

- **Authors**: Alena Shilova, Alex Davey, Brahim Driss, Riad Akrour
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=FgDmszDBKb)
- **Category**: Submitted to ICLR 2026

## Abstract

In Reinforcement Learning (RL), regularization with a Kullback-Leibler divergence that penalizes large deviations between successive policies has emerged as a popular tool both in theory and practice. This family of algorithms, often referred to as Policy Mirror Descent (PMD), has the property of averaging out policy evaluation errors which are bound to occur when using function approximators. However, exact PMD has remained a mostly theoretical framework, as its closed-form solution involves the sum of all past Q-functions which is generally intractable. A common practical approximation of PMD is to follow the natural policy gradient, but this potentially introduces errors in the policy update. In this paper, we propose and analyze PMD-like algorithms for discrete action spaces that only keep the last $M$ Q-functions in memory. We show theoretically that for a finite and large enough $M$, an RL algorithm can be derived that introduces no errors from the policy update, yet keeps the desirable PMD property of averaging out policy evaluation errors. Using an efficient GPU implementation, we then show empirically on several medium-scale RL benchmarks such as Mujoco and MinAtar that increasing $M$ improves performance up to a certain threshold where performance becomes indistinguishable with exact PMD, reinforcing the theoretical findings that using an infinite sum might be unnecessary and that keeping in memory the last $M$ Q-functions is a practical alternative to the natural policy gradient instantiation of PMD.

## Notes

<!-- Claude 在此添加中文解读 -->
