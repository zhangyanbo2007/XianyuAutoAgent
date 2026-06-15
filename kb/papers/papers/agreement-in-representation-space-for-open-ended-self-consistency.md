---
title: "Agreement in Representation Space for Open-Ended Self-Consistency"
authors: [Paula Ontalvilla, Gorka Azkune, Aitor Ormazabal]
year: 2026
venue: "cs.CL"
tags: []
arxiv_id: "2606.12003"
ingested: "2026-06-11"
---

# 🤖 Agreement in Representation Space for Open-Ended Self-Consistency

- **Authors**: Paula Ontalvilla, Gorka Azkune, Aitor Ormazabal
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12003)
- **Category**: cs.CL

## Abstract

Self-consistency improves LLM reasoning by sampling multiple outputs and selecting the most consistent answer, but existing formulations largely rely on exact matching and therefore remain limited to tasks with categorical outputs. In this work, we study self-consistency in open-ended generation tasks such as code synthesis and text summarization. We hypothesize that consistency can be understood as a geometric property of the generation space, where semantically compatible generations concentrate in similar regions of representation space. To study this hypothesis, we introduce Embedding-Based Agreement (EBA), a simple training-free operationalization that estimates agreement by clustering sampled generations in embedding space. Through experiments on mathematical reasoning, code generation, and summarization, we show that agreement in representation space provides a robust and scalable signal of self-consistency for open-ended tasks. In particular, EBA consistently outperforms random selection and exhibits more stable scaling behavior than recent selection approaches based on LLM evaluation or uncertainty estimation. We further show that these agreement signals remain stable across model families and embedding spaces, even with native hidden representations. Finally, our analysis shows that the geometric location occupied by sampled generations is strongly correlated with generation quality: generations concentrated near central regions of representation space tend to correspond to more reliable outputs, whereas peripheral generations are substantially less accurate. Overall, our findings support viewing self-consistency as a property of the geometric organization of sampled generations rather than exact symbolic overlap.

## Notes

<!-- Claude 在此添加中文解读 -->
