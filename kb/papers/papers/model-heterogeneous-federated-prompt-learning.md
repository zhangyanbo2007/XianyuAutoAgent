---
title: "Model-Heterogeneous Federated Prompt Learning"
authors: [Yunfeng Zhao, Qiaoyu Tan, Bo An, Dong Zhang, Jun Wang]
year: 2025
venue: "ICLR 2026 Conference Withdrawn Submission"
tags: []
ingested: "2026-06-11"
---

# 🔬 Model-Heterogeneous Federated Prompt Learning

- **Authors**: Yunfeng Zhao, Qiaoyu Tan, Bo An, Dong Zhang, Jun Wang
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=FTQZvzRKEg)
- **Category**: ICLR 2026 Conference Withdrawn Submission

## Abstract

Large-scale vision-language models (VLMs) have shown remarkable transferability across tasks, and their integration into federated learning (FL) frameworks offers promising privacy-preserving learning capabilities. Recent advances in federated prompt learning (FPL) leverage prompt tuning to reduce computational and communication overhead. However, existing FPL methods assume a homogeneous model setting, where all clients share the same VLMs, which is an unrealistic constraint given the heterogeneous computational capacities of clients in real-world scenarios. To bridge this gap, we propose model-heterogeneous federated prompt learning (MHFPL),  a novel setting where clients with diverse VLM backbones collaboratively learn prompts. We further introduce FedAPPR, a principled framework for MHFPL built on two key components: (a) server-level adversarial prompt alignment for aligning client semantics via adversarial training, and (b) client-level proximity regularization to further constrain prompt drift between clients. Extensive experiments on six datasets with diverse architectures and data distributions demonstrate the superiority and generality of FedAPPR compared to baselines, confirming it as an effective solution for FL scenarios with varying VLMs.

## Notes

<!-- Claude 在此添加中文解读 -->
