---
title: "HealthSLM-Bench: Benchmarking Small Language Models for On-device Healthcare Monitoring"
authors: [Xin Wang, Ting Dang, Xinyu Zhang, Vassilis Kostakos, Michael J. Witbrock]
year: 2025
venue: "ICLR 2026 Conference Withdrawn Submission"
tags: []
ingested: "2026-06-11"
---

# 🔬 HealthSLM-Bench: Benchmarking Small Language Models for On-device Healthcare Monitoring

- **Authors**: Xin Wang, Ting Dang, Xinyu Zhang, Vassilis Kostakos, Michael J. Witbrock
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=R9MzJjvzXv)
- **Category**: ICLR 2026 Conference Withdrawn Submission

## Abstract

On-device healthcare monitoring play a vital role in facilitating timely interventions, managing chronic health conditions, and ultimately improving individuals’ quality of life. Previous studies on large language models (LLMs) have highlighted their impressive generalization abilities and effectiveness in healthcare prediction tasks. However, most LLM-based healthcare solutions are cloud-based, which raises significant privacy concerns and results in increased memory usage and latency. To address these challenges, there is growing interest in compact models, Small Language Models (SLMs), which are lightweight and designed to run locally and efficiently on mobile and wearable devices. Nevertheless, how well these models perform in healthcare prediction remains largely unexplored.
We systematically evaluated SLMs on health prediction tasks using zero-shot, few-shot, and instruction fine-tuning approaches, and deployed the best performing fine-tuned SLMs on mobile devices to evaluate their real-world efficiency and predictive performance in practical healthcare scenarios. Our results show that SLMs can achieve performance comparable to LLMs while offering substantial gains in efficiency, reaching up to 17$\times$ lower latency and 16$\times$ faster inference speed on mobile platforms. However, challenges remain, particularly in handling class imbalance and few-shot scenarios. These findings highlight SLMs, though imperfect in their current form, as a promising solution for next-generation, privacy-preserving healthcare monitoring.

## Notes

<!-- Claude 在此添加中文解读 -->
