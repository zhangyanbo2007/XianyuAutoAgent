---
title: "Reroute, Don't Remove: Recoverable Visual Token Routing for Vision-Language Models"
authors: [Cheng-Yu Yang, Shao-Yuan Lo, Yu-Lun Liu]
year: 2026
venue: "cs.CV, cs.AI"
tags: []
arxiv_id: "2606.12412"
ingested: "2026-06-11"
---

# 🔬 Reroute, Don't Remove: Recoverable Visual Token Routing for Vision-Language Models

- **Authors**: Cheng-Yu Yang, Shao-Yuan Lo, Yu-Lun Liu
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12412)
- **Category**: cs.CV, cs.AI

## Abstract

Vision-language models (VLMs) project images into hundreds to thousands of visual tokens, making decoder inference expensive in both attention computation and KV-cache memory. Existing visual-token reduction methods largely follow a rank-and-remove paradigm: they score visual tokens, keep a compact subset, and permanently discard the rest. We show that this irreversible action is fragile because visual-token importance changes across decoder depth; tokens ranked low at one stage may become relevant in later layers, especially for grounding-sensitive queries. We propose Reroute, a training-free plug-in that replaces removal with recoverable routing. At each routing stage, selected vision tokens pass through decoder blocks, while deferred tokens bypass the stage and re-enter the candidate pool at the next routing decision. Reroute reuses existing attention-score ranking rules and stage-wise schedules, preserving the theoretical TFLOPs and KV-cache budget class of the pruning method it augments. Across FastV, PDrop, and Nüwa variants on LLaVA-1.5 and Qwen backbones, reroute improves grounding under aggressive token reduction while maintaining general VQA performance. These results suggest that VLM token reduction should not be viewed only as irreversible pruning, but also as recoverable routing. The code can be found here: https://github.com/elmma/mllm-reroute/

## Notes

<!-- Claude 在此添加中文解读 -->
