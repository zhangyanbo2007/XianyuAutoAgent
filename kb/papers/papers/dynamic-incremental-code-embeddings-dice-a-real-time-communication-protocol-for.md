---
title: "Dynamic Incremental Code Embeddings (DICE):  A Real-Time Communication Protocol for Multi-Agent Reinforcement Learning"
authors: [Du Qi]
year: 2025
venue: "Submitted to ICLR 2026"
tags: []
ingested: "2026-06-11"
---

# 🔬 Dynamic Incremental Code Embeddings (DICE):  A Real-Time Communication Protocol for Multi-Agent Reinforcement Learning

- **Authors**: Du Qi
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=lFaLBotlag)
- **Category**: Submitted to ICLR 2026

## Abstract

We propose Dynamic Incremental Code Embeddings (DICE), a real-time communication protocol to address the inefficiency of static or periodically updated embeddings in dynamic coding environments for multi-agent reinforcement learning (MARL) in collaborative code completion. The proposed method combines two novel mechanisms-inside the context encoder is used to represent a code called dynamic semantic drift encoding (DSDE) and a code called dynamic contextual embedding adaptation (DCEA) which allows to retain the code representations that can be updated with lightweight operations and boosted with new local or shared with collaborative inputs from other agents to be adapted. DSDE captures semantic drift with a continuous-time process, i.e., embeddings can be learned to evolve with little calculation cost, and DCEA considers dynamically adaptive pretend with graph attention networks (GATs), which integrates related context of adjacent agents. These various mechanisms are integrated in a single common state-level representation, and embeddings are used in place of traditional static inputs in the policy networks, with the reward function being updated to penalize semantic deviation among systems, which encourages the system to make some of its objectives coincide with the system's unity. Furthermore, the system is also linear in the number of agents with quadratic complexity in full retraining approaches. Empirical results demonstrate a 40\% reduction in redundant suggestions compared to static embedding baselines, highlighting the practical significance of DICE in real-world collaborative coding scenarios. The framework is realized by fine-tuned GPT-3.5-turbo encoder and 4-head GAT which provide a scalable and efficient solution for MARL in code completion tasks.

## Notes

<!-- Claude 在此添加中文解读 -->
