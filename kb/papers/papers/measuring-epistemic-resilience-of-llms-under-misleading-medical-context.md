---
title: "Measuring Epistemic Resilience of LLMs Under Misleading Medical Context"
authors: [Hongjian Zhou, Xinyu Zou, Jinge Wu, Sean Wu, Junchi Yu]
year: 2026
venue: "cs.CL"
tags: []
arxiv_id: "2606.12291"
ingested: "2026-06-11"
---

# 🤖 Measuring Epistemic Resilience of LLMs Under Misleading Medical Context

- **Authors**: Hongjian Zhou, Xinyu Zou, Jinge Wu, Sean Wu, Junchi Yu
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12291)
- **Category**: cs.CL

## Abstract

Large language models (LLMs) now reach expert-level scores on medical licensing exams, encouraging the assumption that high scores imply safe medical judgment while patients increasingly use them for health advice. We show this assumption is fragile: when misleading context is injected into questions that LLMs originally answer correctly, they abandon the correct answer. We call the ability to maintain correct judgment under adversarial context epistemic resilience, and introduce MedMisBench to measure it. MedMisBench contains 10,932 medical question items and 48,889 misleading context-option pairs spanning medical reasoning, agentic capability, and patient-journey evaluation. Across 11 model configurations, mean accuracy falls from 71.1% on original questions to 38.0% under focused misleading context, with 51.5% attack success. The most damaging injections are formal, rule-like fabrications: authority-framed falsehoods reach 69.5% attack success and exception-poisoning claims reach 64.1%. A 14-member clinical panel from 7 countries identified serious potential harm in 38.2% of reviewed cases. MedMisBench exposes a structural blind spot in LLM evaluation in medical settings: existing benchmarks measure what models know, but not whether they preserve correct medical judgment under misleading context.

## Notes

<!-- Claude 在此添加中文解读 -->
