---
title: "Compositional HyperModules for Few-Shot Code Adaptation in Meta-Reinforcement Learning"
authors: [Hua Ji]
year: 2025
venue: "Submitted to ICLR 2026"
tags: []
ingested: "2026-06-11"
---

# 🔬 Compositional HyperModules for Few-Shot Code Adaptation in Meta-Reinforcement Learning

- **Authors**: Hua Ji
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=NWoHQbALl4)
- **Category**: Submitted to ICLR 2026

## Abstract

We propose Compositional HyperModules (CHM), which is a novel architectural framework for few-shot code adaptation in meta-reinforcement learning (Meta-RL), that dynamically composes reusable neural modules in order to capture the syntactic and semantic structure of code. Existing Meta-RL methods often have a difficult time with codes since they are monolithic and do not model the hierarchical and compositional nature of programming languages. For this purpose, CHM combines a transformer based hypernetwork with a hierarchical code representation layer, which allows the system to break code apart into function blocks (e.g. loops, conditionals) and recompose them smoothly for new tasks. The hypernetwork generates the task-specific weights for lightweight sub-modules, which are used to perform computations on structured code subgraphs as well as keeping the residual connections that preserve the functionalities of pre-trained modules. In addition, a gated attention mechanism aggregates the module outputs to jointly produce a global representation which serves as guidance to a Meta-RL policy network in order to generate context-aware actions (e.g., code edits). In contrast to previous work, CHM explicitly models code compositionality which allows for interpretable and efficient few-shot adaptation without full-fine-tuning. Experiments on code synthesis and bug fixing demonstrate a 20\% improvement in few-shot accuracy over monolithic baselines, highlighting the framework's ability to generalize across diverse code patterns. The modular design not only gives adaptability but understanding what neural components correspond to specific code construct, leveraging neural procedures towards program undertaking analysis.

## Notes

<!-- Claude 在此添加中文解读 -->
