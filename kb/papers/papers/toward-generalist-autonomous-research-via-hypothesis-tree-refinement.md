---
title: "Toward Generalist Autonomous Research via Hypothesis-Tree Refinement"
authors: [Jiajie Jin, Yuyang Hu, Kai Qiu, Qi Dai, Chong Luo]
year: 2026
venue: "cs.CL, cs.AI"
tags: []
arxiv_id: "2606.11926"
ingested: "2026-06-11"
---

# 🧠 Toward Generalist Autonomous Research via Hypothesis-Tree Refinement

- **Authors**: Jiajie Jin, Yuyang Hu, Kai Qiu, Qi Dai, Chong Luo
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.11926)
- **Category**: cs.CL, cs.AI

## Abstract

Scientific progress depends on a repeated loop of exploration, experimentation, and abstraction. Researchers test candidate directions, interpret the evidence, and carry the resulting lessons into later attempts. We study how an AI agent can run this loop autonomously over long horizons. We introduce Arbor, a general framework for autonomous research that combines a long-lived coordinator, short-lived executors, and Hypothesis Tree Refinement (HTR), a persistent tree that links hypotheses, artifacts, evidence, and distilled insights across time. The coordinator manages global research strategy over the tree, while executors implement and test individual hypotheses in isolated worktrees. As results return, Arbor updates the tree, propagates reusable lessons, refines the search frontier, and admits verified improvements. This design turns autonomous research from a sequence of local attempts into a cumulative process in which strategy, execution, and evidence are carried across time. We evaluate Arbor under Autonomous Optimization (AO), an operational setting where an agent improves an initial research artifact through iterative experimentation without step-level human supervision. Across six real research tasks in model training, harness engineering, and data synthesis, Arbor achieves the best held-out result on all six tasks, attaining more than 2.5x the average relative held-out gain of Codex and Claude Code under the same task interface and resource budget. On MLE-Bench Lite, Arbor reaches 86.36% Any Medal with GPT-5.5, the strongest result in our comparison.

## Notes

<!-- Claude 在此添加中文解读 -->
