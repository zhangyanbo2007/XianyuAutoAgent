---
title: "Mind the Perspective: Let's Reason Recursively for Theory of Mind"
authors: [Chao Lei, Guang Hu, Meng Yang, Yanbei Jiang, Nir Lipovetzky]
year: 2026
venue: "cs.AI"
tags: []
arxiv_id: "2606.11724"
ingested: "2026-06-11"
---

# 🧠 Mind the Perspective: Let's Reason Recursively for Theory of Mind

- **Authors**: Chao Lei, Guang Hu, Meng Yang, Yanbei Jiang, Nir Lipovetzky
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.11724)
- **Category**: cs.AI

## Abstract

Theory of Mind (ToM) reasoning requires inferring agents' beliefs from partial and asymmetric observations, which remains an open challenge for LLMs. Existing prompting-based approaches improve ToM reasoning through observable-event filtering or temporal belief chains, without explicitly modeling nested beliefs. We introduce RecToM, an inference-time framework for ToM reasoning that models nested beliefs via recursive perspective construction. RecToM constructs each character perspective from the preceding character perspective along the character chain specified by the question, reducing higher-order belief questions to actual-world questions within the final constructed perspective. We further provide a KD45 analysis showing that RecToM's perspective construction induces a well-formed belief modality beyond simple event filtering. Experiments on ToM benchmarks, including Hi-ToM, Big-ToM, and FanToM, across multiple LLM backbones show that RecToM consistently outperforms recent advanced approaches, achieving state-of-the-art performance. Notably, RecToM reaches 100\% accuracy on Hi-ToM with GPT-5.4 and Qwen3.5, a benchmark requiring higher-order ToM reasoning.

## Notes

<!-- Claude 在此添加中文解读 -->
