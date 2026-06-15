---
title: "CHORUS: Decentralized Multi-Embodiment Collaboration with One VLA Policy"
authors: [Ria Doshi, Tian Gao, Annie Chen, Chelsea Finn, Jeannette Bohg]
year: 2026
venue: "cs.RO, cs.AI"
tags: []
arxiv_id: "2606.12352"
ingested: "2026-06-11"
---

# 🤖 CHORUS: Decentralized Multi-Embodiment Collaboration with One VLA Policy

- **Authors**: Ria Doshi, Tian Gao, Annie Chen, Chelsea Finn, Jeannette Bohg
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12352)
- **Category**: cs.RO, cs.AI

## Abstract

Multi-robot collaboration allows robots to efficiently take on a wide range of tasks, from moving a couch through a doorway to assembling structures on a construction site. However, achieving such coordination in mobile multi-robot settings remains challenging: centralized methods conditioned on the combined observations of a team scale poorly with team size, and decentralized methods that train one policy per robot often require explicit alignment procedures or information sharing at inference time to overcome partial observability. Our key insight is that the visuomotor priors of pretrained vision-language-action (VLA) models should enable reactive, decentralized collaboration from each robot's local observations alone, without these inference-time assumptions. We propose CHORUS, a framework that adapts a single VLA backbone to control diverse, multi-robot teams. At inference time, each robot runs an independent copy of CHORUS, conditioned only on its own observations and a robot-identifying prompt. In real-world experiments including mobile tape measurement, library book handovers, and laundry basket lifting, CHORUS achieves a 64% point improvement over decentralized, from-scratch models, improves reactivity to teammate behavior by 40% points, and outperforms centralized baselines. Together, these results show that a shared VLA backbone is capable of achieving decentralized multi-robot collaboration, without per-robot policies or inter-robot communication at inference.

## Notes

<!-- Claude 在此添加中文解读 -->
