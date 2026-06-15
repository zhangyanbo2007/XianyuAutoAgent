---
title: "HERO: Hindsight-Enhanced Reflection from Environment Observations for Agentic Self-Distillation"
authors: [Haoran Liu, Yuwei Zhang, Xiyao Li, Bohan Lyu, Jingbo Shang]
year: 2026
venue: "cs.AI"
tags: []
arxiv_id: "2606.11559"
ingested: "2026-06-11"
---

# 🤖 HERO: Hindsight-Enhanced Reflection from Environment Observations for Agentic Self-Distillation

- **Authors**: Haoran Liu, Yuwei Zhang, Xiyao Li, Bohan Lyu, Jingbo Shang
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.11559)
- **Category**: cs.AI

## Abstract

Reinforcement learning typically improves multi-turn agent capabilities through the terminal outcome of the trajectories, which makes it difficult to determine credit assignments for each intermediate turns. Recent on-policy self-distillation methods offer a promising alternative by converting privileged feedback into dense token-level supervision through a self-teacher. Our study is motivated by the unexpected performance degradation observed when naively extending this paradigm to multi-turn settings, which we attribute to a lack of alignment between privileged feedback, such as successful trajectories or terminal outcomes, and the student's current decision context. We introduce HERO, a hindsight-enhanced self-distillation framework that uses next environment observations as locally aligned feedback. After each rollout, HERO reflects on the completed interaction to convert each observation into a compact turn-level diagnosis, that captures actionable feedback about the original action such as its necessity, validity or failure cause. On TauBench and WebShop, HERO improves task success and reduces unnecessary turns over environment-feedback-only self-distillation and GRPO. It is especially effective under limited training turn budgets, where successful rollouts are rare and GRPO provides weak reward-contrast signals.

## Notes

<!-- Claude 在此添加中文解读 -->
