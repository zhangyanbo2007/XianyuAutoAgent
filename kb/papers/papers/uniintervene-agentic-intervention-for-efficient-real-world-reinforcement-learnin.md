---
title: "UniIntervene: Agentic Intervention for Efficient Real-World Reinforcement Learning"
authors: [Haoyuan Deng, Yitong Gao, Yudong Lin, Haichao Liu, Zhenyu Wu]
year: 2026
venue: "cs.RO, cs.LG"
tags: []
arxiv_id: "2606.12372"
ingested: "2026-06-11"
---

# 🧠 UniIntervene: Agentic Intervention for Efficient Real-World Reinforcement Learning

- **Authors**: Haoyuan Deng, Yitong Gao, Yudong Lin, Haichao Liu, Zhenyu Wu
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12372)
- **Category**: cs.RO, cs.LG

## Abstract

Human-in-the-loop reinforcement learning (HiL-RL) has emerged as an effective paradigm for real-world robotic manipulation, enabling online policy improvement with human guidance. However, current HiL-RL frameworks remain intervention-intensive, relying on frequent human corrections to redirect the policy out of unproductive exploration, which incurs high labor cost and limits real-world scalability. To address this, we propose UniIntervene, an agentic intervention model that detects unproductive exploration and autonomously recovers the policy toward high-value states, taking over the bulk of interventions from human operators. Specifically, UniIntervene first performs future-conditioned action-value estimation, predicting the latent consequence of the current action and evaluating its induced value, which provides a more stable progress signal. Building on this, a temporal value-risk critic aggregates recent value dynamics and triggers intervention when the estimated value exhibits sustained stagnation or degradation. When intervention is required, UniIntervene retrieves a high-value recovery target from a memory of past intervention episodes and produces executable corrective actions through a goal-conditioned recovery policy. In this way, UniIntervene turns intervention from passive human correction into a value-aware recovery process for efficient real-world RL. Extensive experiments on diverse real-world manipulation tasks demonstrate that UniIntervene improves the average success rate by 8.6% while reducing human interventions by 57% relative to state-of-the-art HiL-RL baselines.

## Notes

<!-- Claude 在此添加中文解读 -->
