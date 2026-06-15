---
title: "Which Models Are Our Models Built On? Auditing Invisible Dependencies in Modern LLMs"
authors: [Sanjay Adhikesaven, Haoxiang Sun, Sewon Min]
year: 2026
venue: "cs.CL"
tags: []
arxiv_id: "2606.12385"
ingested: "2026-06-11"
---

# 🤖 Which Models Are Our Models Built On? Auditing Invisible Dependencies in Modern LLMs

- **Authors**: Sanjay Adhikesaven, Haoxiang Sun, Sewon Min
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12385)
- **Category**: cs.CL

## Abstract

Modern LLM training pipelines increasingly rely on other models to generate data, filter corpora, judge outputs, and guide development decisions. These dependencies are recursive: a model may depend on an upstream artifact whose own dependencies are documented only in separate releases and artifacts. As a result, the full dependency structure is fragmented across heterogeneous public artifacts, with complexity and recursive depth far outpacing humans' ability to trace. We introduce ModSleuth, an agentic system that recursively reconstructs LLM dependency graphs from public artifacts with source-grounded evidence. We find that the primary challenge is no longer information extraction, but defining what constitutes a dependency and reconciling artifact references across inconsistent documentation. We address these challenges through a formalization that distinguishes direct and indirect dependencies, represents heterogeneous pipeline roles through operation-centered relationships, and resolves artifact identities across names, versions, and repositories. Applying ModSleuth to four public-artifact-rich LLM releases, we recover 1,060 source-verified dependencies and construct large-scale dependency graphs of modern LLM development. These graphs reveal multi-hop license obligations, train-evaluation coupling, discrepancies between released and training-time artifacts, and documentation inconsistencies that would otherwise be difficult to uncover. We release ModSleuth and the resulting dependency graphs to support transparent analysis of the increasingly complex ecosystems underlying modern LLMs.

## Notes

<!-- Claude 在此添加中文解读 -->
