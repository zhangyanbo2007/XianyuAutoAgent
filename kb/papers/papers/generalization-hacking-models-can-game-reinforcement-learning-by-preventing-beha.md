---
title: "Generalization Hacking: Models Can Game Reinforcement Learning by Preventing Behavioral Generalization"
authors: [Frank Xiao, Mary Phuong]
year: 2026
venue: "cs.LG, cs.AI"
tags: []
arxiv_id: "2606.12016"
ingested: "2026-06-11"
---

# 🤖 Generalization Hacking: Models Can Game Reinforcement Learning by Preventing Behavioral Generalization

- **Authors**: Frank Xiao, Mary Phuong
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12016)
- **Category**: cs.LG, cs.AI

## Abstract

Model post-training, and in particular reinforcement learning (RL), is one of the primary mechanisms by which developers can shape models' values and behaviors. However, as models become increasingly evaluation and training aware, they may be motivated to resist training when the perceived objective conflicts with their current values, undermining developers' ability to detect misalignment and correct model behavior through further training. In this paper, we demonstrate generalization hacking, in which a model collects reward during RL while preventing the rewarded behavior from generalizing. We construct a model organism on Qwen3-235B-A22B, finetuning on synthetic documents describing training awareness and self-inoculation, a novel mechanism in which the model frames compliance as context-specific in its chain of thought, without demonstrating or instructing either behavior. The model organism achieves train-time harmfulness comparable to controls while maintaining a persistent ${\sim}15$ percentage point compliance gap across 700 steps of RL. Additionally, a control organism trained only on training awareness documents independently discovers inoculation-like reasoning under RL pressure, developing its own compliance gap despite never being exposed to the concept. Because the generalization-hacking organism receives high reward throughout, standard training metrics provide no signal that generalization has failed. Our results constitute the first demonstration that a model can actively resist RL behavioral modification while maintaining high reward, suggesting that as models become more capable and training-aware, they may be able to undermine the training process itself.

## Notes

<!-- Claude 在此添加中文解读 -->
