---
title: "PAWS: Preference Learning with Advantage-Weighted Segments"
authors: [Aleksandar Taranovic, Onur Celik, Niklas Freymuth, Ge Li, Serge Thilges]
year: 2026
venue: "cs.LG"
tags: []
arxiv_id: "2606.11982"
ingested: "2026-06-11"
---

# 🤖 PAWS: Preference Learning with Advantage-Weighted Segments

- **Authors**: Aleksandar Taranovic, Onur Celik, Niklas Freymuth, Ge Li, Serge Thilges
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.11982)
- **Category**: cs.LG

## Abstract

Preference-based reinforcement learning (PbRL) learns policies from human trajectory-level comparisons, avoiding explicit reward design and expert demonstrations. Existing methods typically train utility functions on trajectory or segment-level preferences while relying on per-step utility estimates during policy optimization. This training and inference mismatch induces a distribution shift that severely degrades temporal credit assignment and limits policy learning. We analyze this issue and propose PAWS, a segment-based preference learning method that performs policy updates directly using segment-level advantage functions. By aligning utility training with policy optimization, PAWS preserves trajectory-level preference information and avoids unreliable per-step learning signals. Experiments on simulated robotic manipulation and locomotion tasks demonstrate that PAWS consistently outperforms existing PbRL approaches, highlighting the importance of distribution-consistent preference learning.

## Notes

<!-- Claude 在此添加中文解读 -->
