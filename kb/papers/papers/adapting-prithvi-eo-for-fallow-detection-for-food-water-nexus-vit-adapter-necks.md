---
title: "Adapting Prithvi-EO for Fallow Detection for Food-Water Nexus: ViT-Adapter Necks and Parameter-Efficient Backbone tuning of Geospatial Foundation Model"
authors: [Sk Muhammad Asif, Orhun Aydin]
year: 2026
venue: "cs.CV, cs.AI"
tags: []
arxiv_id: "2606.12218"
ingested: "2026-06-11"
---

# 🤖 Adapting Prithvi-EO for Fallow Detection for Food-Water Nexus: ViT-Adapter Necks and Parameter-Efficient Backbone tuning of Geospatial Foundation Model

- **Authors**: Sk Muhammad Asif, Orhun Aydin
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12218)
- **Category**: cs.CV, cs.AI

## Abstract

Understanding spatial distribution of fallow land is important for optimizing the food-water (FW) nexus, given fallowing's role in crop rotation and water conservation. Fallow is a low accuracy class in USDA Cropland Data Layer (CDL). Geospatial foundation model (GFM), Prithvi-EO has shown strong transferability across computer vision tasks. However, its Vision Transformer (ViT) backbone produces features at a single spatial scale that are ill-suited for the multi-scale features required by object detection heads. Existing approaches synthesise multi-scale pyramids through scaling of single stride tokens, sacrificing spatial heterogeneity, and full backbone fine-tuning is computationally prohibitive for GFMs. We evaluate a fallow detection pipeline combining two parameter-efficient fine tuning (PEFT) schemes: Low-Rank Adaptation (LoRA) and a hybrid PEFT, with three neck designs: pseudo multi-scale, Lite ViT-Adapter, and Full ViT-Adapter. Our best configuration, Lite ViT-Adapter with a one-stage head, achieves a mAP@50 of 0.9479 with the Diou loss, suggesting the effectiveness of center-aware localization for irregular fallow field detection. ViT-Adapter free one-stage detection under LoRA improves the adapter-free anchor-based approach by 6.42%, and the best configuration improves baseline adapter-free anchor-based approach by 25.70%. These results demonstrate that lightweight spatial prior fusion and selective backbone unfreezing enable Prithvi-EO to capture local fallow patterns more effectively, outperforming approaches that rely on reshaped single-stride ViT tokens.

## Notes

<!-- Claude 在此添加中文解读 -->
