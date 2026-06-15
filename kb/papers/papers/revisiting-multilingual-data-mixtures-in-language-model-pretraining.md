---
title: "Revisiting Multilingual Data Mixtures in Language Model Pretraining"
authors: [Negar Foroutan, Paul Teiletche, Ayush Kumar Tarun, Antoine Bosselut]
year: 2025
venue: "Submitted to ICLR 2026"
tags: []
ingested: "2026-06-11"
---

# 🔬 Revisiting Multilingual Data Mixtures in Language Model Pretraining

- **Authors**: Negar Foroutan, Paul Teiletche, Ayush Kumar Tarun, Antoine Bosselut
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=IKJyRyHpHV)
- **Category**: Submitted to ICLR 2026

## Abstract

The impact of different multilingual data mixtures in pretraining large language models (LLMs) has been a topic of ongoing debate, often raising concerns about potential trade-offs between language coverage and model performance (i.e., the curse of multilinguality). In this work, we investigate these assumptions by training 1B and 3B parameter LLMs on diverse multilingual corpora, varying the number
of languages from 25 to 400. Our study challenges common beliefs surrounding multilingual training. First, we find that combining English and multilingual data does not necessarily degrade the in-language performance of either group, provided that languages have a sufficient number of tokens included in the pretraining corpus. Second, we observe that using English as a pivot language (i.e., the language with the highest data proportion) yields benefits across language groups, and contrary to expectations, selecting a pivot language from within a specific group does not consistently improve performance for languages within that family. Lastly, we do not observe a significant "curse of multilinguality" as the number of training languages increases in models at this scale. Our findings suggest that multilingual data, when balanced appropriately, can enhance language model capabilities without compromising performance, even in low-resource settings.

## Notes

<!-- Claude 在此添加中文解读 -->
