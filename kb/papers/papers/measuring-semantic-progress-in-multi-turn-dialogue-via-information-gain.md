---
title: "Measuring Semantic Progress in Multi-turn Dialogue via Information Gain"
authors: [Paul He, Shiva Kasiviswanathan, Dominik Janzing]
year: 2026
venue: "cs.CL, cs.LG"
tags: []
arxiv_id: "2606.12332"
ingested: "2026-06-11"
---

# 🤖 Measuring Semantic Progress in Multi-turn Dialogue via Information Gain

- **Authors**: Paul He, Shiva Kasiviswanathan, Dominik Janzing
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12332)
- **Category**: cs.CL, cs.LG

## Abstract

Evaluating multi-turn dialogue is challenging because quality emerges across turns rather than within individual responses. We focus on a key dimension of information-seeking dialogue: semantic progress, defined as the accumulation of new, question-relevant, and non-redundant information over the course of a conversation. We formalize semantic progress as question-conditioned uncertainty reduction and introduce an information-theoretic metric that approximates it in embedding space. Our main estimator uses a tractable Gaussian formulation with closed-form updates, while a complementary maximum-entropy argument shows why log-determinant structure arises more broadly when only second-order embedding information is retained. This formulation yields desirable theoretical properties, including monotonicity, additive decomposition of total information gain across turns, and diminishing returns for redundant evidence. Unlike LLM-as-a-judge approaches, our metric requires no autoregressive inference at evaluation time and is fully reproducible for a fixed embedding model. Experiments on MT-Bench, Chatbot Arena, and UltraFeedback show that the proposed metric achieves competitive agreement with human judgments despite targeting only semantic progress, with improved alignment on MT-Bench and UltraFeedback compared to several LLM-based judges. Notably, the method remains effective with lightweight embedding models under CPU-only execution, indicating that semantic progress can be captured without reliance on large model capacity.

## Notes

<!-- Claude 在此添加中文解读 -->
