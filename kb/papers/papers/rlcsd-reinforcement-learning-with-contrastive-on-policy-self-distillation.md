---
title: "RLCSD: Reinforcement Learning with Contrastive On-Policy Self-Distillation"
authors: [Leyi Pan, Shuchang Tao, Yunpeng Zhai, Lingzhe Zhang, Zhaoyang Liu]
year: 2026
venue: "cs.LG, cs.CL"
tags: []
arxiv_id: "2606.11709"
ingested: "2026-06-11"
---

# 🤖 RLCSD: Reinforcement Learning with Contrastive On-Policy Self-Distillation

- **Authors**: Leyi Pan, Shuchang Tao, Yunpeng Zhai, Lingzhe Zhang, Zhaoyang Liu
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.11709)
- **Category**: cs.LG, cs.CL

## Abstract

On-policy self-distillation (OPSD) provides dense, token-level supervision for reasoning models by aligning a model's own distribution with the distribution it produces under privileged context, typically a verified solution. However, we show that the learning signal drawn from this distributional gap concentrates on style tokens rather than task-bearing ones, as the hinted model tends to produce more direct, shorter outputs. We term this pathology \emph{privilege-induced style drift}, which destabilizes training or causes response length to shrink. To address this, we propose \textbf{RLCSD} (Reinforcement Learning with Contrastive on-policy Self-Distillation), which mitigates this drift by contrasting the teacher-student gap under a correct hint against that under a wrong hint, suppressing the style shift that conditioning on a hint tends to induce regardless of correctness, and yielding a signal that is more concentrated on task-bearing tokens. Experiments on Qwen3 (1.7B/4B/8B) and Olmo-3-7B-Think across mathematical and logical reasoning show that RLCSD consistently outperforms GRPO and prior OPSD methods. We further show that the contrastive principle is general: it plugs into existing OPSD methods to improve them, and its underlying insight extends to the broader cross-model on-policy distillation setting.

## Notes

<!-- Claude 在此添加中文解读 -->
