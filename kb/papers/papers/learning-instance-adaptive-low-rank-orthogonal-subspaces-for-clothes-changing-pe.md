---
title: "Learning Instance-Adaptive Low-Rank Orthogonal Subspaces for Clothes-Changing Person Re-Identification"
authors: [Dong-Woo Kim, Tae-Kyun Kim]
year: 2026
venue: "cs.CV, cs.LG"
tags: []
arxiv_id: "2606.11661"
ingested: "2026-06-11"
---

# 🤖 Learning Instance-Adaptive Low-Rank Orthogonal Subspaces for Clothes-Changing Person Re-Identification

- **Authors**: Dong-Woo Kim, Tae-Kyun Kim
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.11661)
- **Category**: cs.CV, cs.LG

## Abstract

Clothes-changing person re-identification (CC-ReID) aims to recognize individuals despite drastic appearance changes caused by clothing variation. While existing methods rely on adversarial learning to disentangle clothing features, we propose Ortho-ReID, which explicitly models a low-rank clothing subspace from VLM text descriptions and extracts clothing-invariant representations via direct geometric constraints. A critical component is our transformer-based Basis Maker, which refines a shared, low-dimensional clothing prior into an instance-adaptive low-rank subspace through cross-attention with image patches, enabling robust clothing feature extraction even under varying visibility conditions. This instance-adaptive subspace is supervised via alignment with clothing text embeddings, while identity features are extracted via a learnable projection head and geometrically constrained to be strictly orthogonal to it. Extensive experiments demonstrate state-of-the-art performance on PRCC (+5.9% top-1), Celeb-reID-light (+3.5%), and LaST (+5.3%), with competitive results on LTCC.

## Notes

<!-- Claude 在此添加中文解读 -->
