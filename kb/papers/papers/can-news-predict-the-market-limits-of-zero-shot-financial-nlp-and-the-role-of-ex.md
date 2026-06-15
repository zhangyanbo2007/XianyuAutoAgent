---
title: "Can News Predict the Market? Limits of Zero-Shot Financial NLP and the Role of Explainable AI"
authors: [Ali M Karaoglu, Shreyank N Gowda]
year: 2026
venue: "cs.CL"
tags: []
arxiv_id: "2606.12210"
ingested: "2026-06-11"
---

# 🤖 Can News Predict the Market? Limits of Zero-Shot Financial NLP and the Role of Explainable AI

- **Authors**: Ali M Karaoglu, Shreyank N Gowda
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12210)
- **Category**: cs.CL

## Abstract

Can financial news reliably predict short-term stock movements? Despite advances in large language models, this question remains unresolved. We revisit this problem using a zero-shot natural language processing framework, investigating whether models can extract actionable signals from financial news without domain-specific training. We design a structured pipeline that combines zero-shot natural language inference with temporal aggregation, explicitly modelling recency and event-dependent impact horizons when integrating information across articles. To address the need for transparency in high-stakes settings, we introduce a multi-layered explainability framework that links predictions to token-level, article-level, and aggregate evidence, and produces grounded natural language rationales. Across multiple models and prediction horizons, we find that zero-shot approaches consistently fail to outperform simple baselines, with particularly weak performance on negative movements, suggesting deeper structural limitations in mapping news sentiment to short-term price dynamics. However, explainability signals reliably distinguish between trustworthy and unreliable predictions, offering practical value even when accuracy is limited. These findings highlight the limits of zero-shot financial NLP and motivate a shift toward decision-support systems that prioritise transparency and uncertainty awareness. Code: https://github.com/alimert05/zero-shot-stock-xai

## Notes

<!-- Claude 在此添加中文解读 -->
