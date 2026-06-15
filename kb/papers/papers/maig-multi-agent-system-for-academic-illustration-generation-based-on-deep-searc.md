---
title: "MAIG: Multi-agent system for Academic Illustration Generation based on deep search and reflection"
authors: [Yifan Chang, Jianwen Sun, Chuanhao Li, Jiaxin Ai, Yukang Feng]
year: 2025
venue: "ICLR 2026 Conference Desk Rejected Submission"
tags: []
ingested: "2026-06-11"
---

# 🔬 MAIG: Multi-agent system for Academic Illustration Generation based on deep search and reflection

- **Authors**: Yifan Chang, Jianwen Sun, Chuanhao Li, Jiaxin Ai, Yukang Feng
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=0ZRne2Nt8t)
- **Category**: ICLR 2026 Conference Desk Rejected Submission

## Abstract

While text-to-image models have revolutionized creative content generation, they fall short in the domain of academic illustration, which demands stringent scientific accuracy and informational completeness, creating a significant bottleneck in automated scientific communication. Existing models often produce illustrations that are factually incorrect, omit critical information, and are limited to simple structured diagrams, failing to render the complex, unstructured conceptual visuals common in science. To address these challenges, we introduce \textbf{MAIG}, a novel multi-agent framework that mimics an expert's workflow. MAIG first employs a deep research agent to ground the generation process in a factual knowledge base, ensuring all necessary background information is available. Subsequently, reflection and editing agents iteratively verify the visual output against this knowledge, identifying and correcting scientific errors. In the meantime, evaluating scientific figures is a parallel challenge plagued by subjective and unscalable methods, we also propose a novel Question-Answering (QA) based Evaluator. This method leverages the strong reasoning capabilities of modern Multimodal Large Language Models (MLLMs) to quantitatively measure both informational completeness and factual correctness, providing an objective and scalable assessment of an illustration's quality. Extensive experiments across various scientific disciplines demonstrate the effectiveness of MAIG, which achieves minimal factual errors and the most complete knowledge coverage, significantly outperforming state-of-the-art models.Our results validate that the proposed research-reflect-edit loop is crucial for generating high-fidelity scientific illustrations and that our QA-based evaluator offers a reliable assessment methodology, together forming a comprehensive solution for advancing automated scientific visualization.

## Notes

<!-- Claude 在此添加中文解读 -->
