---
title: "IAPO: Input Attribution-Aware Policy Optimization for Tool Use in Small Multimodal Agents"
authors: [Yifan Yang, Zhen Zhang, Jiayi Tian, Liyan Tan, Zheng Zhang]
year: 2026
venue: "cs.LG"
tags: []
arxiv_id: "2606.11652"
ingested: "2026-06-11"
---

# 🤖 IAPO: Input Attribution-Aware Policy Optimization for Tool Use in Small Multimodal Agents

- **Authors**: Yifan Yang, Zhen Zhang, Jiayi Tian, Liyan Tan, Zheng Zhang
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.11652)
- **Category**: cs.LG

## Abstract

This paper investigates reinforcement learning (RL) methods for improving tool-calling capabilities in multimodal small language model (SLM) agents. While existing works have explored various reward designs to improve agentic tool-calling ability, these approaches face inherent limitations for SLM training, especially under multimodal scenarios. First, many existing methods evaluate tool use correctness through exact matching against certain ground-truth or predefined formats. However, this assumption is often unsuitable for multimodal tasks, where multiple tool use paths may be valid and annotated tool trajectories are typically unavailable. Second, such sparse and brittle binary rewards provide little guidance on how to improve the underlying decision process, making them particularly difficult for multimodal SLM to learn from. To address these issues, we propose Input Attribution-Aware Policy Optimization (IAPO), an RL algorithm for improving tool use in multimodal SLM by aligning the model's attribution across input components with that of a stronger teacher. Experiments on Qwen2.5-VL-3B show that the proposed method improves visual question answering accuracy by an average of 3% across six test sets compared with existing visual tool use work, by helping the model attend to the most relevant input evidence.

## Notes

<!-- Claude 在此添加中文解读 -->
