---
title: "GUIrilla: A Scalable Framework for Automated Desktop UI Exploration"
authors: [Sofiya Garkot, Maksym Shamrai, Ivan Synytsia, Mariya Hirna]
year: 2025
venue: "ICLR 2026 Conference Withdrawn Submission"
tags: []
ingested: "2026-06-11"
---

# 🔬 GUIrilla: A Scalable Framework for Automated Desktop UI Exploration

- **Authors**: Sofiya Garkot, Maksym Shamrai, Ivan Synytsia, Mariya Hirna
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=dpHw6PFKio)
- **Category**: ICLR 2026 Conference Withdrawn Submission

## Abstract

Autonomous agents capable of operating complex graphical user interfaces (GUIs) have the potential to transform desktop automation. While recent advances in large language models (LLMs) have significantly improved UI understanding, navigating full-window, multi-application desktop environments remains a major challenge. Data availability is limited by costly manual annotation, closed-source datasets and surface-level synthetic pipelines. 

We introduce GUIrilla, an automated scalable framework that systematically explores applications via native accessibility APIs to address the critical data collection challenge in GUI automation. Our framework focuses on macOS - an ecosystem with limited representation in current UI datasets - though many of its components are designed for broader cross-platform applicability. GUIrilla organizes discovered interface elements and crawler actions into hierarchical GUI graphs and employs specialized interaction handlers to achieve comprehensive application coverage. 

Using the application graphs from GUIrilla crawler, we construct and release GUIrilla‑Task, a large-scale dataset of 27,171 functionally grounded tasks across 1,108 macOS applications, each annotated with full-desktop and window-level screenshots, accessibility metadata, and semantic action traces. 

Empirical results show that tuning LLM-based agents on GUIrilla‑Task significantly improves performance on downstream UI tasks, outperforming synthetic baselines on the ScreenSpot Pro benchmark while using 97% less data. We also release macapptree, an open-source library for reproducible collection of structured accessibility metadata, along with the full GUIrilla‑Task dataset, the manually verified GUIrilla-Gold benchmark, and the framework code to support open research in desktop autonomy.

## Notes

<!-- Claude 在此添加中文解读 -->
