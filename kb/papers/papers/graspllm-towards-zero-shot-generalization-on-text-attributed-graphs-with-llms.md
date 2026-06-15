---
title: "GraspLLM: Towards Zero-Shot Generalization on Text-Attributed Graphs with LLMs"
authors: [Hengyi Feng, Zeang Sheng, Meiyi Qiang, Meiyi Qiang, Wentao Zhang]
year: 2026
venue: "cs.CL, cs.LG"
tags: []
arxiv_id: "2606.11898"
ingested: "2026-06-11"
---

# 🤖 GraspLLM: Towards Zero-Shot Generalization on Text-Attributed Graphs with LLMs

- **Authors**: Hengyi Feng, Zeang Sheng, Meiyi Qiang, Meiyi Qiang, Wentao Zhang
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.11898)
- **Category**: cs.CL, cs.LG

## Abstract

Research on Text-Attributed Graphs (TAGs) has gained significant attention recently due to its broad applications across various real-world data scenarios, such as citation networks, e-commerce platforms, social media, and web pages. Inspired by the remarkable semantic understanding ability of Large Language Models (LLMs), there have been numerous attempts to integrate LLMs into TAGs. However, existing methods still struggle to generalize across diverse graphs and tasks, and their ability to capture transferable graph structural patterns remains limited. To address this, we introduce the GraspLLM, a framework that combines Graph structural comprehension with semantic understanding prowess of LLMs to enhance the cross-dataset and cross-task generalizability. Specifically, we represent node texts from different graphs in a unified semantic space with a frozen general embedding model, on top of which we perform motif-aware contrastive learning across multiple motif-induced adjacency matrices to extract dataset-agnostic structural information. Then, with our proposed optimal contextual subgraph, we extract the most contextually relevant subgraph for each target node and align these subgraphs to the token space of LLM via an alignment projector. Extensive experiments on TAG benchmark datasets spanning diverse domains reveal that GraspLLM consistently outperforms previous LLM-based methods for TAGs, especially in zero-shot scenarios, highlighting its strong generalizability across different datasets and tasks. Our code is available at https://github.com/Heinz217/GraspLLM.

## Notes

<!-- Claude 在此添加中文解读 -->
