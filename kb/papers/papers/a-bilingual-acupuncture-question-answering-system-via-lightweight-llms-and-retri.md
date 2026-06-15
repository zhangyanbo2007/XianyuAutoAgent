---
title: "A Bilingual Acupuncture Question Answering System via Lightweight LLMs and Retrieval-Augmented Generation"
authors: [Yaoqi Wang, Yeyun Wan, Ruizhe Wang, Ruoxuan Mai, Qilei Sun]
year: 2025
venue: "ICLR 2026 Conference Desk Rejected Submission"
tags: []
ingested: "2026-06-11"
---

# 🔬 A Bilingual Acupuncture Question Answering System via Lightweight LLMs and Retrieval-Augmented Generation

- **Authors**: Yaoqi Wang, Yeyun Wan, Ruizhe Wang, Ruoxuan Mai, Qilei Sun
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=wfTt4wZtaj)
- **Category**: ICLR 2026 Conference Desk Rejected Submission

## Abstract

Large language models (LLMs) are prone to hallucinations and often lack reliable access to structured, domain-specific knowledge in Traditional Chinese Medicine (TCM). We present the first bilingual (Chinese--English) acupuncture question answering system built on lightweight LLM backbones and retrieval-augmented generation (RAG). The system integrates a curated ontology covering 361 acupoints and 14 meridians, clinician-authored case records, and a triple-constraint decoding strategy (terminology checking, evidence grounding, and safety filtering) to deliver controlled, verifiable answers. On our evaluation suite, the best-performing configuration (bert+baichuan) achieves 94.4% context recall, 97.2% faithfulness, and 96.1% answer relevance (RAGAS), together with 0.88 BLEU, 0.94 ROUGE, a 94 GPT score, and a 90 expert score. These results confirm that bilingual embedding fusion plus constraint-based decoding substantially improves factuality and clinical usefulness over pure LLM baselines, establishing a strong foundation for reliable and accessible question answering system in acupuncture-specific.

## Notes

<!-- Claude 在此添加中文解读 -->
