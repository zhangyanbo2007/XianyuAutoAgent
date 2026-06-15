---
title: "APPO: Agentic Procedural Policy Optimization"
authors: [Xucong Wang, Ziyu Ma, Yong Wang, Yuxiang Ji, Shidong Yang]
year: 2026
venue: "cs.LG, cs.AI"
tags: []
arxiv_id: "2606.12384"
ingested: "2026-06-11"
---

# 🤖 APPO: Agentic Procedural Policy Optimization

- **Authors**: Xucong Wang, Ziyu Ma, Yong Wang, Yuxiang Ji, Shidong Yang
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12384)
- **Category**: cs.LG, cs.AI

## Abstract

Recent advances in agentic Reinforcement Learning (RL) have substantially improved the multi-turn tool-use capabilities of large language model agents. However, most existing methods assign credit over coarse heuristic units, such as tool-call boundaries or fixed workflows, making it difficult to identify which intermediate decisions influence downstream outcomes. In this work, we study agentic RL from two perspectives: \textit{where to branch and how to assign credit after branching}. Our pilot analysis shows that influential decision points are broadly distributed throughout the generated sequence rather than concentrated at tool calls, while token entropy alone does not reliably reflect their impact on final outcomes. Motivated by these observations, we propose \textbf{Agentic Procedural Policy Optimization (APPO)}, which shifts branching and credit assignment from coarse interaction units to fine-grained decision points in the sequence. APPO selects branching locations using a Branching Score that combines token uncertainty with policy-induced likelihood gains of subsequent continuations, enabling more targeted exploration while filtering out spurious high-entropy positions. It further introduces procedure-level advantage scaling to better distribute credit across branched rollouts. Experiments on 13 benchmarks show that APPO consistently improves strong agentic RL baselines by nearly 4 points, while keeping efficient tool-calls and maintaining behavior interpretability.

## Notes

<!-- Claude 在此添加中文解读 -->
