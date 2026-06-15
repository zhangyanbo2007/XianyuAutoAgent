---
title: "DyCodeExplainer: Explainable Dynamic Graph Attention for Multi-Agent Reinforcement Learning in Collaborative Coding"
authors: [Fan An]
year: 2025
venue: "Submitted to ICLR 2026"
tags: []
ingested: "2026-06-11"
---

# 🔬 DyCodeExplainer: Explainable Dynamic Graph Attention for Multi-Agent Reinforcement Learning in Collaborative Coding

- **Authors**: Fan An
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=U7pWkp90qA)
- **Category**: Submitted to ICLR 2026

## Abstract

We propose \textbf{DyCodeExplainer}, a novel multi-agent reinforcement learning (MARL) framework that integrates dynamic graph attention with explainability techniques to improve collaborative coding. Existing MARL systems typically depend on static communication protocols which are not flexible and transparent in performing coding tasks that are more complicated. The above method suffers from this limitation by treating the interaction of agents in the form of a time-evolving graph in which the nodes represent coding agents, and edges indicate messages exchanged between them. A dynamic graph attention network (DGAT) dynamically prioritizes the messages considering contextually relevant message, whereas hard attention gate eliminates noises and helps improve decision-making efficiency. Furthermore, the framework includes gradient-based attention attribution and rule-based post-hoc explanations to explain message prioritization for providing interpretable budgetary information about the collaborative process. The policy and critic networks use Transformer-XL and graph neural networks respectively for managing the long-range dependencies and assessing the memory argument of the joint state values. Experiments show DyCodeExplainer to be more accurate in terms of code correctness and collaborative efficiency than traditional MARL baselines. The novelty of the system is the simultaneous optimization of thresholds for dynamic attention and explainability rules to bridge an important gap in transparent multi-agent coding systems. This work will move the field forward by providing a scalable and interpretable solution for collaborative software development.

## Notes

<!-- Claude 在此添加中文解读 -->
