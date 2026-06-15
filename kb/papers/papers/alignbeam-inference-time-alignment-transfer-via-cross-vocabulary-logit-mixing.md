---
title: "ALIGNBEAM : Inference-Time Alignment Transfer via Cross-Vocabulary Logit Mixing"
authors: [Chirag Chawla, Pratinav Seth, Vinay Kumar Sankarapu]
year: 2026
venue: "cs.CL, cs.AI, cs.ET"
tags: []
arxiv_id: "2606.12342"
ingested: "2026-06-11"
---

# 🤖 ALIGNBEAM : Inference-Time Alignment Transfer via Cross-Vocabulary Logit Mixing

- **Authors**: Chirag Chawla, Pratinav Seth, Vinay Kumar Sankarapu
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12342)
- **Category**: cs.CL, cs.AI, cs.ET

## Abstract

Domain fine-tuning degrades the safety of large language models: fine-tuned specialists readily comply with harmful prompts framed in domain language. Existing inference-time defenses that mix logits from a safe anchor model require both models to share a vocabulary, which rules them out for the cross-family specialists where safety is most degraded. We present ALIGNBEAM, a training-free method that lifts this restriction by translating anchor logits into the target model's vocabulary token-by-token at each decoding step; a small LLM judge then selects the safest among K candidate continuations. No weights are changed, and the safety-utility trade-off can be tuned at deployment without retraining. Across both cross-vocabulary and same-vocabulary evaluation pairs, ALIGNBEAM substantially raises refusal on adversarial benchmarks while keeping task accuracy and inference overhead within practical bounds. The results show that safety alignment can be transferred between model families at inference time, without touching either model's weights.

## Notes

<!-- Claude 在此添加中文解读 -->
