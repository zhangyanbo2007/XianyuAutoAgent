---
title: "TacCoRL: Integrating Tactile Feedback into VLA via Simulation"
authors: [Siyu Ma, Yuqi Liang, Chang Yu, Yunuo Chen, Hao Su]
year: 2026
venue: "cs.RO, cs.GR, cs.LG"
tags: []
arxiv_id: "2606.11743"
ingested: "2026-06-11"
---

# 🤖 TacCoRL: Integrating Tactile Feedback into VLA via Simulation

- **Authors**: Siyu Ma, Yuqi Liang, Chang Yu, Yunuo Chen, Hao Su
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.11743)
- **Category**: cs.RO, cs.GR, cs.LG

## Abstract

Vision-language-action (VLA) models provide strong visual, language, and action priors for robot manipulation, but visual observations alone often miss the local contact state required for contact-rich tasks. We present TacCoRL, a scalable framework that injects Tactile feedback into VLA policies and improves them through sim-real Co-training and simulation-based reinforcement learning (RL), without requiring large-scale tactile pretraining or extensive real-world contact exploration. The key idea is not only adding touch as an input, but learning how contact readings should modulate action responses in near-failure states that are rare in demonstrations and risky to collect on hardware. We use a real-aligned simulator as a closed-loop training environment for contact interaction. Mixed simulated and real trajectories first warm-start tactile-conditioned actions in the pretrained policy. Reinforcement learning with verifiable task rewards then optimizes the policy using simulated contact rollouts. It reinforces tactile-conditioned actions that lead to task completion, while a supervised objective on real trajectories keeps the refined policy anchored to deployment visual, tactile, and action distributions. The resulting policy transfers directly to the real robot without privileged simulation state or online real-world RL. Across four bimanual contact-rich tasks, the final visuo-tactile policy achieves an average success rate of 72.5%, compared to baseline of 50.0%. Result videos and more details are available at https://tac-corl.github.io/

## Notes

<!-- Claude 在此添加中文解读 -->
