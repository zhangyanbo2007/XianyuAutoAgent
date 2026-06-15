---
title: "VICX: Generalizable Robot Manipulation via Video Generation and In-Context Operator Network"
authors: [Song Chen, Linyan Xiang, Ying Zhou, Liu Yang]
year: 2026
venue: "cs.RO"
tags: []
arxiv_id: "2606.12028"
ingested: "2026-06-11"
---

# 🧠 VICX: Generalizable Robot Manipulation via Video Generation and In-Context Operator Network

- **Authors**: Song Chen, Linyan Xiang, Ying Zhou, Liu Yang
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12028)
- **Category**: cs.RO

## Abstract

Generalizable robot manipulation requires not only task-level reasoning over unseen scenes, but also reliable grounding of visual plans into embodiment-specific execution. To bridge this gap, we propose VICX (Video generation and In-Context eXecution), a decoupled closed-loop manipulation framework. In VICX, a frozen video generation model produces vision-language-conditioned high-level visual plans, while a Video-to-Trajectory In-Context Operator Network (V2T-ICON) serves as the task-agnostic interface that grounds these plans into executable robot-state trajectories. To improve execution generalization, V2T-ICON operates on segmentation-extracted arm-only frame observations and uses retrieved image-state pairs as in-context prompts, allowing a robust and generalizable visual-to-state mapping at inference time without parameter updates. Experiments on Meta-World show that VICX supports cross-task generalization, closed-loop self-correction, and cross-embodiment transfer, demonstrating dual generalization across both task semantics and robot execution. The project webpage can be found here: https://scaling-group.github.io/vicx/.

## Notes

<!-- Claude 在此添加中文解读 -->
