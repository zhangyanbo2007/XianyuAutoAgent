---
title: "Adaptive Multi-Resolution Procedural Knowledge Compression for Large Language Models"
authors: [Changyue Wang, Weihang Su, Qingyao Ai, Yichen Tang, Runzhong Qiao]
year: 2026
venue: "cs.CL"
tags: []
arxiv_id: "2606.12203"
ingested: "2026-06-11"
---

# 🤖 Adaptive Multi-Resolution Procedural Knowledge Compression for Large Language Models

- **Authors**: Changyue Wang, Weihang Su, Qingyao Ai, Yichen Tang, Runzhong Qiao
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12203)
- **Category**: cs.CL

## Abstract

Large language models (LLMs) are widely used to tackle complex tasks with autonomous workflows. Recently, reusable natural language skills have emerged as a popular paradigm to inject procedural knowledge into LLM applications. Since popular skills are often invoked repeatedly, placing their full text in every context significantly increases prefill cost and latency. While text compression techniques have the potential to solve this problem, most existing methods are designed to compress factual knowledge in documents instead of procedural knowledge, making them insufficient for skill compression. In this paper, we argue that an effective skill compression method should: 1) preserve logical dependencies among workflows and tool protocols, 2) enable lightweight, offline compression for frequently updated community skills, and 3) be adaptable to varying complexities across skills. To address this, we present SKIM (SKIll coMpression), an adaptive multi-resolution soft token compression framework for procedural skills. Depending on the complexity of each skill, SKIM creates different numbers of soft tokens that not only improve the efficiency of LLM inference, but also preserve the effectiveness of skill usage. Experiments indicate that SKIM compresses skills to 30 to 60 percent of their original token length while preserving task performance better than existing compression methods.We have released our code at https://github.com/bebr2/SKIM .

## Notes

<!-- Claude 在此添加中文解读 -->
