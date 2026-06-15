---
title: "SAVIOR: Sample-efficient Alignment of Vision-Language Models for OCR Representation"
authors: [Akshata A Bhat, Sharath Naganna, Saiful Haq, Prashant Khatri, Neha Arun]
year: 2025
venue: "ICLR 2026 Conference Withdrawn Submission"
tags: []
ingested: "2026-06-11"
---

# 🔬 SAVIOR: Sample-efficient Alignment of Vision-Language Models for OCR Representation

- **Authors**: Akshata A Bhat, Sharath Naganna, Saiful Haq, Prashant Khatri, Neha Arun
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=kiVIVBmMTP)
- **Category**: ICLR 2026 Conference Withdrawn Submission

## Abstract

Modern enterprises are increasingly adopting business document understanding workflows that leverage Vision Language Models (VLMs) for optical character recognition (OCR), given their ability to jointly model layout and language. However, deployment is impeded by data and compute barriers: large enterprises face de-identification pipelines requiring manual validation, while smaller ones lack access to sufficiently large and varied datasets. Synthetic data pipelines that generate millions of $<$document, OCR$>$ pairs also fall short, as they often fail to capture the nuanced structural and semantic challenges of real-world documents. To address this gap, we introduce SAVIOR, a sample-efficient data curation methodology that identifies common failure cases in pretrained VLMs and explicitly curates examples for challenging scenarios such as vertical text, stylized logo text, fine print, and degraded scans. Using SAVIOR, we construct SAVIOR-TRAIN, a compact training dataset of 2,234 $<$document, OCR$>$ tuples, and SAVIOR-Bench, a benchmark of 509 financial documents annotated by domain experts. We further introduce SAVIOR-OCR, a Qwen-2.5-VL-7B-Instruct model fine-tuned on SAVIOR-TRAIN. Experiments show that SAVIOR-OCR achieves a word-level recall of 0.9257 on SAVIOR-Bench, outperforming PaddleOCR 3.0 (0.8685) and Nanonets-OCR-s (0.9040). Beyond recall, we propose PAIRS, a structure-aware evaluation metric that quantifies layout fidelity via pairwise spatial relations between tokens; SAVIOR-OCR achieves a PAIRS score of 0.802, demonstrating superior preservation of document structure. To the best of our knowledge, SAVIOR is the first methodology to enable sample-efficient adaptation of VLMs for OCR in enterprise settings, delivering both high accuracy and strong layout fidelity with minimal data and compute.

## Notes

<!-- Claude 在此添加中文解读 -->
