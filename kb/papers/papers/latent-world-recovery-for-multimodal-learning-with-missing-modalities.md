---
title: "Latent World Recovery for Multimodal Learning with Missing Modalities"
authors: [Hui Wang, Tianyu Ren, Joseph Butler, Christopher Baker, Karen Rafferty]
year: 2026
venue: "cs.LG, cs.AI"
tags: []
arxiv_id: "2606.12362"
ingested: "2026-06-11"
---

# 🤖 Latent World Recovery for Multimodal Learning with Missing Modalities

- **Authors**: Hui Wang, Tianyu Ren, Joseph Butler, Christopher Baker, Karen Rafferty
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12362)
- **Category**: cs.LG, cs.AI

## Abstract

We study multimodal learning under missing modalities, with particular motivation from bioscience applications in which heterogeneous modalities are often only partially available when decisions need to be made. We propose Latent World Recovery (LWR), a framework built on two key ideas: (i) modality-specific embeddings from different modalities are aligned in a shared latent space, and (ii) a unified representation is constructed by fusing only the embeddings of the modalities that are actually available at both training and inference time. Rather than imputing missing modalities or requiring a fixed modality set, LWR treats each modality as a partial perception of an underlying latent state and performs availability-aware representation learning directly from the observed modalities. This combination of neighbor-based latent alignment and availability-aware modality fusion enables robust multimodal prediction under partial observation, while avoiding error propagation from explicit reconstruction of missing modalities. We evaluate the proposed framework on real-world incomplete multi-omics benchmarks and demonstrate that it provides an effective approach to downstream tasks such as cancer phenotype classification and survival prediction.

## Notes

<!-- Claude 在此添加中文解读 -->
