---
title: "Efficient High-Resolution Image Editing with Hallucination-Aware Loss and Adaptive Tiling"
authors: [Young D. Kwon, Abhinav Mehrotra, Malcolm Chadwick, Alberto Gil Couto Pimentel Ramos, Sourav Bhattacharya]
year: 2025
venue: "ICLR 2026 Conference Withdrawn Submission"
tags: []
ingested: "2026-06-11"
---

# 🔬 Efficient High-Resolution Image Editing with Hallucination-Aware Loss and Adaptive Tiling

- **Authors**: Young D. Kwon, Abhinav Mehrotra, Malcolm Chadwick, Alberto Gil Couto Pimentel Ramos, Sourav Bhattacharya
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=OqZFfDks0Q)
- **Category**: ICLR 2026 Conference Withdrawn Submission

## Abstract

High-resolution (4K) image-to-image synthesis has become increasingly important for mobile applications. Existing diffusion models for image editing face significant challenges, in terms of memory and image quality, when deployed on resource-constrained devices. In this paper, we present MobilePicasso, a novel system that enables on-device image editing at high resolutions, while minimising computational cost and memory usage. MobilePicasso comprises three stages: (i) performing image editing at a standard resolution with hallucination-aware loss, (ii) applying latent projection to overcome going to the pixel space, and (iii) upscaling the edited image latent to a higher resolution with adaptive context-preserving tiling. Our user study with 46 participants reveals that MobilePicasso not only improves image quality by 18-48% but reduces hallucinations by 14-51% over existing methods. MobilePicasso demonstrates significantly lower latency, e.g., up to 55.8x speed-up, yet with a small increase in runtime memory, e.g., a mere 9% increase over prior work. Surprisingly, the on-device runtime of MobilePicasso is observed to be faster than a server-based high-resolution image editing model running on an A100 GPU.

## Notes

<!-- Claude 在此添加中文解读 -->
