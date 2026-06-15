---
title: "A Controlled Study of Decoding-Time Truthfulness Methods on Instruction-Tuned LLMs"
authors: [Ao Sun]
year: 2026
venue: "cs.CL"
tags: []
arxiv_id: "2606.12160"
ingested: "2026-06-11"
---

# 🤖 A Controlled Study of Decoding-Time Truthfulness Methods on Instruction-Tuned LLMs

- **Authors**: Ao Sun
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12160)
- **Category**: cs.CL

## Abstract

In this work, we introduce CHAIR (Classifier of Hallucination As ImproveR), a supervised framework for detecting hallucinations by analyzing internal logits from each layer of every token. Our method extracts a compact set of features such as maximum, minimum, mean, standard deviation, and slope-from the token logits across all layers, enabling effective hallucination detection without overfitting. Experiments on TruthfulQA and MMLU datasets demonstrate that CHAIR significantly improves detection accuracy, particularly in zero-shot scenarios, showcasing its robustness and generalizability. Beyond hallucination detection, CHAIR highlights the potential of using internal representations for designing advanced decoding strategies. By leveraging patterns in logits, we suggest that more sophisticated models and adaptive decoding methods could further reduce hallucinations and enhance text completion quality. CHAIR not only offers a practical solution for detecting hallucinations but also lays the groundwork for exploring richer representations in LLMs to improve their factuality and coherence.

## Notes

<!-- Claude 在此添加中文解读 -->
