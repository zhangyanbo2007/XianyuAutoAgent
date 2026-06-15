---
title: "Fine-tuning Multi-modal LLMs with ART: Art-based Reinforcement Training"
authors: [Michal Chudoba, Sergey Alyaev, Petra Galuscakova, Tomasz Wiktorski]
year: 2026
venue: "cs.LG, cs.AI, cs.CL"
tags: []
arxiv_id: "2606.11854"
ingested: "2026-06-11"
---

# 🧠 Fine-tuning Multi-modal LLMs with ART: Art-based Reinforcement Training

- **Authors**: Michal Chudoba, Sergey Alyaev, Petra Galuscakova, Tomasz Wiktorski
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.11854)
- **Category**: cs.LG, cs.AI, cs.CL

## Abstract

There are two main Parameter-Efficient Fine-Tuning (PEFT) techniques for Large Language Models (LLMs). While Low-Rank Adaptation (LoRA) introduces additional weights between the LLM layers, Soft Prompting introduces additional fine-tuning-specific raw tokens to an LLM input. However, both require modification to the computational graphs of precompiled, preoptimized LLMs. As a result, neither is fully supported in high-throughput engines like vLLM. We propose fine-tuning with ART (Art-based Reinforcement Training). The method injects information into a frozen Multimodal Large Language Model (MLLM) by optimizing only its raw visual input, thus enabling the soft-token approach on pre-compiled computational graphs. It relies on backpropagation of gradients back into a plain pixel array and thus supports any fine-tuning objective. Moreover, the optimized visual input can be stylized as task-relevant computational artworks. The approach's effectiveness is confirmed for different sizes of a popular open Qwen architecture and for several textual benchmarks. Specifically, ART reaches accuracy competitive with LoRA across mathematics and structured-tool-use benchmarks.

## Notes

<!-- Claude 在此添加中文解读 -->
