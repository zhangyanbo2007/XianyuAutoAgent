---
title: "MODF-SIR: A Multi-agent Omni-modal Distilled Framework for Social Intelligence Reasoning"
authors: [Shang Ma, Jisheng Dang, Wencan Zhang, Yifan Zhang, Bimei Wang]
year: 2026
venue: "cs.AI"
tags: []
arxiv_id: "2606.12018"
ingested: "2026-06-11"
---

# 🤖 MODF-SIR: A Multi-agent Omni-modal Distilled Framework for Social Intelligence Reasoning

- **Authors**: Shang Ma, Jisheng Dang, Wencan Zhang, Yifan Zhang, Bimei Wang
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12018)
- **Category**: cs.AI

## Abstract

We propose a multi-agent collaborative framework built upon a lightweight Multimodal Large Language Model (MLLM), specifically designed for social intelligence reasoning. A key feature of our approach is that both the training and inference phases are augmented via knowledge distillation. Within this architecture, multi-modal data pertinent to social intelligence is precisely localized. Furthermore, relevant long-tail events are identified, extracted, and rendered as formatted, explicit text. This formatting strategy prevents critical long-tail information from being overshadowed by head events and environmental noise during the tokenization process. Specifically, we integrate Test-Time Adaptation (TTA) across the entire reasoning pipeline, encompassing the extraction and representation of long-tail events, Chain-of-Thought (CoT) prompting, and self-reflection. This TTA mechanism is also distillation-enhanced, utilizing Low-Rank Adaptation (LoRA) to fine-tune the foundation model exclusively for instance-level reasoning. Extensive evaluations against various open-source and proprietary AI models across multiple benchmarks demonstrate the effectiveness of the proposed framework. With around 30% of training data from IntentTrain, we achieve state-of-the-art results. Codes are available at https://github.com/eeee-sys/MODF-SIR, demo is available at https://huggingface.co/spaces/Harry-1234/MODF-SIR, LoRA is available at https://huggingface.co/Harry-1234/MODF-SIR and the dataset for training router is available at https://huggingface.co/datasets/Harry-1234/IntentRouterTrain.

## Notes

<!-- Claude 在此添加中文解读 -->
